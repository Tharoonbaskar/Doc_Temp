import { zodResolver } from '@hookform/resolvers/zod';
import { Box, Button, Checkbox, Chip, FormControl, FormControlLabel, FormHelperText, InputLabel, MenuItem, OutlinedInput, Select, Stack, TextField } from '@mui/material';
import { useEffect, useMemo } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';

import { DATA_TYPE_OPTIONS, SOURCE_TYPE_OPTIONS, STATUS_OPTIONS } from '../../shared/constants';
import { useDocuments } from '../../documents/hooks/useDocuments';
import type { VariablePayload } from '../types';

const variableSchema = z.object({
  code: z.string().min(3, 'Code must be at least 3 characters.'),
  name: z.string().min(1, 'Name must be at least 1 character.'),
  display_name: z.string().min(2, 'Display name is required.'),
  description: z.string(),
  group_id: z.string().uuid('Group ID must be a valid UUID.'),
  data_type: z.enum(DATA_TYPE_OPTIONS),
  source_type: z.enum(SOURCE_TYPE_OPTIONS),
  source_reference: z.string(),
  default_value: z.string(),
  is_required: z.boolean(),
  document_ids: z.array(z.string().uuid()).optional(),
  status: z.enum(STATUS_OPTIONS),
});

type FormValues = z.infer<typeof variableSchema>;

type Props = {
  initialValue?: VariablePayload;
  existingCodes?: string[];
  submitLabel: string;
  onSubmit: (payload: VariablePayload) => Promise<void>;
};

const defaultValue: VariablePayload = {
  code: '',
  name: '',
  display_name: '',
  description: '',
  group_id: '',
  data_type: 'STRING',
  source_type: 'INPUT',
  source_reference: '',
  default_value: '',
  is_required: false,
  document_ids: [],
  status: 'DRAFT',
};

const buildUuid = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const randomValue = Math.floor(Math.random() * 16);
    const value = char === 'x' ? randomValue : (randomValue & 0x3) | 0x8;
    return value.toString(16);
  });
};

const escapeRegExp = (value: string): string => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const normalizeDisplayToken = (value: string): string =>
  value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);

const normalizeTechnicalName = (value: string): string => {
  const base = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');

  if (!base) {
    return '';
  }

  if (/^[0-9]/.test(base)) {
    return `var_${base}`;
  }

  return base;
};

const generateVariableCode = (displayName: string, existingCodes: string[]): string => {
  const token = normalizeDisplayToken(displayName);
  if (!token) {
    return '';
  }

  const prefix = `DOC_${token}_`;
  const matcher = new RegExp(`^${escapeRegExp(prefix)}(\\d{6})$`);
  let maxSequence = 0;

  for (const existingCode of existingCodes) {
    const match = existingCode.match(matcher);
    if (match) {
      maxSequence = Math.max(maxSequence, Number(match[1]));
    }
  }

  const nextSequence = String(maxSequence + 1).padStart(6, '0');
  return `${prefix}${nextSequence}`;
};

export function VariableForm({ initialValue, existingCodes = [], submitLabel, onSubmit }: Props) {
  const documentsQuery = useDocuments();
  const generatedGroupId = useMemo(() => initialValue?.group_id || buildUuid(), [initialValue?.group_id]);

  const defaultValues = useMemo<FormValues>(
    () => ({
      ...(initialValue ?? defaultValue),
      group_id: generatedGroupId,
    }),
    [generatedGroupId, initialValue],
  );

  const {
    register,
    handleSubmit,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(variableSchema),
    defaultValues,
  });

  const values = useWatch<FormValues>({ control });

  useEffect(() => {
    register('data_type');
    register('source_type');
    register('status');
    register('is_required');
    register('document_ids');
  }, [register]);

  useEffect(() => {
    const technicalName = normalizeTechnicalName(values.display_name ?? '');
    setValue('name', technicalName, { shouldValidate: true, shouldDirty: false });
  }, [setValue, values.display_name]);

  useEffect(() => {
    if (initialValue) {
      return;
    }

    const nextCode = generateVariableCode(values.display_name ?? '', existingCodes);
    setValue('code', nextCode, { shouldValidate: true, shouldDirty: false });
  }, [existingCodes, initialValue, setValue, values.display_name]);

  return (
    <Box component="form" onSubmit={handleSubmit(async (payload) => onSubmit(payload))} noValidate>
      <Stack spacing={2}>
        <TextField
          label="Display Name"
          {...register('display_name')}
          error={Boolean(errors.display_name)}
          helperText={errors.display_name?.message ?? 'Enter display name to auto-generate code and technical name.'}
          fullWidth
        />

        <TextField
          label="Code"
          value={values.code}
          error={Boolean(errors.code)}
          helperText={errors.code?.message ?? 'Code is generated automatically from Display Name.'}
          fullWidth
          slotProps={{
            input: {
              readOnly: true,
            },
          }}
        />
        <input type="hidden" {...register('code')} />

        <TextField
          label="Name"
          value={values.name}
          error={Boolean(errors.name)}
          helperText={errors.name?.message ?? 'Technical field name (lowercase, underscore).'}
          fullWidth
          slotProps={{
            input: {
              readOnly: true,
            },
          }}
        />
        <input type="hidden" {...register('name')} />

        <TextField
          label="Group ID"
          value={values.group_id}
          error={Boolean(errors.group_id)}
          helperText={errors.group_id?.message ?? 'Auto-generated UUID for this variable group.'}
          disabled
          fullWidth
        />
        <input type="hidden" {...register('group_id')} />

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <FormControl fullWidth>
            <InputLabel id="var-data-type">Data Type</InputLabel>
            <Select
              labelId="var-data-type"
              label="Data Type"
              value={values.data_type}
              onChange={(event) => setValue('data_type', event.target.value as FormValues['data_type'], { shouldValidate: true })}
            >
              {DATA_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel id="var-source-type">Source Type</InputLabel>
            <Select
              labelId="var-source-type"
              label="Source Type"
              value={values.source_type}
              onChange={(event) => setValue('source_type', event.target.value as FormValues['source_type'], { shouldValidate: true })}
            >
              {SOURCE_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>

        <TextField label="Source Reference" {...register('source_reference')} fullWidth />

        <TextField label="Default Value" {...register('default_value')} fullWidth />

        <FormControl fullWidth>
          <InputLabel id="var-status">Status</InputLabel>
          <Select
            labelId="var-status"
            label="Status"
            value={values.status}
            onChange={(event) => setValue('status', event.target.value as FormValues['status'], { shouldValidate: true })}
          >
            {STATUS_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel id="var-documents">Link to Documents</InputLabel>
          <Select
            labelId="var-documents"
            label="Link to Documents"
            multiple
            value={values.document_ids || []}
            onChange={(event) => {
              const value = event.target.value;
              setValue('document_ids', typeof value === 'string' ? value.split(',') : value, { shouldValidate: true });
            }}
            input={<OutlinedInput label="Link to Documents" />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((docId) => {
                  const doc = documentsQuery.data?.find((d) => d.id === docId);
                  return (
                    <Chip
                      key={docId}
                      label={doc?.name || docId.slice(0, 8)}
                      size="small"
                    />
                  );
                })}
              </Box>
            )}
          >
            {(documentsQuery.data || []).map((doc) => (
              <MenuItem key={doc.id} value={doc.id}>
                {doc.name} ({doc.document_type})
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>
            Select one or more documents where this variable will be available (e.g., Sanction Letter, Disbursement Letter)
          </FormHelperText>
        </FormControl>

        <TextField label="Description" {...register('description')} multiline minRows={3} fullWidth />

        <FormControlLabel
          control={
            <Checkbox
              checked={values.is_required}
              onChange={(event) => setValue('is_required', event.target.checked, { shouldValidate: true })}
            />
          }
          label="Required Variable"
        />

        <Stack direction="row" spacing={2}>
          <Button type="submit" variant="contained" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : submitLabel}
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}
