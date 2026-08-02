import { zodResolver } from '@hookform/resolvers/zod';
import { Box, Button, Checkbox, FormControl, FormControlLabel, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material';
import { useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';

import { STATUS_OPTIONS } from '../../shared/constants';
import type { DocumentItem } from '../../documents/types';
import type { WorkflowPayload } from '../types';

const workflowSchema = z.object({
  code: z.string().min(3, 'Code must be at least 3 characters.'),
  name: z.string().min(2, 'Name is required.'),
  description: z.string(),
  workflow_type: z.string().min(2, 'Workflow type is required.'),
  applicable_document_id: z.string().uuid('Document ID must be a valid UUID.'),
  version: z.number().int().min(1, 'Version must be > 0'),
  is_default: z.boolean(),
  status: z.enum(STATUS_OPTIONS),
});

type FormValues = z.infer<typeof workflowSchema>;

type Props = {
  initialValue?: WorkflowPayload;
  existingCodes?: string[];
  documents?: DocumentItem[];
  submitLabel: string;
  onSubmit: (payload: WorkflowPayload) => Promise<void>;
};

const defaultValue: WorkflowPayload = {
  code: '',
  name: '',
  description: '',
  workflow_type: 'APPROVAL',
  applicable_document_id: '',
  version: 1,
  is_default: false,
  status: 'DRAFT',
};

const escapeRegExp = (value: string): string => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const normalizeNameToken = (value: string): string =>
  value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);

const generateWorkflowCode = (name: string, existingCodes: string[]): string => {
  const token = normalizeNameToken(name);
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

export function WorkflowForm({ initialValue, existingCodes = [], documents = [], submitLabel, onSubmit }: Props) {
  const {
    register,
    handleSubmit,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(workflowSchema),
    defaultValues: initialValue ?? defaultValue,
  });

  const values = useWatch<FormValues>({ control });

  useEffect(() => {
    register('applicable_document_id');
    register('status');
    register('is_default');
    register('version');
  }, [register]);

  useEffect(() => {
    if (initialValue) {
      return;
    }

    const nextCode = generateWorkflowCode(values.name ?? '', existingCodes);
    setValue('code', nextCode, { shouldValidate: true, shouldDirty: false });
  }, [existingCodes, initialValue, setValue, values.name]);

  return (
    <Box component="form" onSubmit={handleSubmit(async (payload) => onSubmit(payload))} noValidate>
      <Stack spacing={2}>
        <TextField
          label="Name"
          {...register('name')}
          error={Boolean(errors.name)}
          helperText={errors.name?.message ?? 'Enter name to auto-generate the code.'}
          fullWidth
        />

        <TextField
          label="Code"
          value={values.code}
          error={Boolean(errors.code)}
          helperText={errors.code?.message ?? 'Code is generated automatically from Name.'}
          fullWidth
          slotProps={{
            input: {
              readOnly: true,
            },
          }}
        />
        <input type="hidden" {...register('code')} />

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            label="Workflow Type"
            {...register('workflow_type')}
            error={Boolean(errors.workflow_type)}
            helperText={errors.workflow_type?.message}
            fullWidth
          />

          <FormControl fullWidth error={Boolean(errors.applicable_document_id)}>
            <InputLabel id="workflow-document-name">Document Name</InputLabel>
            <Select
              labelId="workflow-document-name"
              label="Document Name"
              value={values.applicable_document_id}
              onChange={(event) =>
                setValue('applicable_document_id', event.target.value as FormValues['applicable_document_id'], {
                  shouldValidate: true,
                })
              }
            >
              <MenuItem value="">Select Document</MenuItem>
              {documents.map((documentItem) => (
                <MenuItem key={documentItem.id} value={documentItem.id}>
                  {documentItem.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>

        <TextField
          label="Document ID"
          value={values.applicable_document_id}
          error={Boolean(errors.applicable_document_id)}
          helperText={errors.applicable_document_id?.message ?? 'Auto-populated from selected document.'}
          disabled
          fullWidth
        />

        <input type="hidden" {...register('applicable_document_id')} />

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            label="Version"
            type="number"
            value={values.version}
            onChange={(event) => setValue('version', Number(event.target.value || 1), { shouldValidate: true })}
            fullWidth
          />

          <FormControl fullWidth>
            <InputLabel id="workflow-status">Status</InputLabel>
            <Select
              labelId="workflow-status"
              label="Status"
              value={values.status}
              onChange={(event) =>
                setValue('status', event.target.value as FormValues['status'], { shouldValidate: true })
              }
            >
              {STATUS_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>

        <TextField label="Description" {...register('description')} multiline minRows={3} fullWidth />

        <FormControlLabel
          control={
            <Checkbox
              checked={values.is_default}
              onChange={(event) => setValue('is_default', event.target.checked, { shouldValidate: true })}
            />
          }
          label="Default Workflow"
        />

        <Button type="submit" variant="contained" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : submitLabel}
        </Button>
      </Stack>
    </Box>
  );
}
