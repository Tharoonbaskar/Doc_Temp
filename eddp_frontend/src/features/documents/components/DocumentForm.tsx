import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Button,
  Checkbox,
  FormControl,
  FormHelperText,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  Stack,
  TextField,
} from '@mui/material';
import { useEffect, useMemo } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';

import { DOCUMENT_TYPE_OPTIONS, OUTPUT_FORMAT_OPTIONS, STATUS_OPTIONS } from '../../shared/constants';
import type { DocumentPayload } from '../types';

const BUSINESS_MODULE_OPTIONS = ['PRIME', 'EB'] as const;
const PRODUCT_OPTIONS = ['HOME LOAN', 'PLOT LOAN', 'LAP'] as const;

const documentSchema = z.object({
  code: z.string().min(3, 'Code must be at least 3 characters.'),
  name: z.string().min(2, 'Name must be at least 2 characters.'),
  description: z.string(),
  category_id: z.string().uuid('Category ID must be a valid UUID.'),
  document_type: z.enum(DOCUMENT_TYPE_OPTIONS),
  business_module: z.enum(BUSINESS_MODULE_OPTIONS),
  product: z.array(z.enum(PRODUCT_OPTIONS)).min(1, 'Select at least one product.'),
  output_format: z.enum(OUTPUT_FORMAT_OPTIONS),
  status: z.enum(STATUS_OPTIONS),
});

type FormValues = z.infer<typeof documentSchema>;

type Props = {
  initialValue?: DocumentPayload;
  existingCodes?: string[];
  submitLabel: string;
  onSubmit: (payload: DocumentPayload) => Promise<void>;
};

const defaultValue: DocumentPayload = {
  code: '',
  name: '',
  description: '',
  category_id: '',
  document_type: 'LETTER',
  business_module: 'PRIME',
  product: [],
  output_format: 'PDF',
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

const normalizeNameToken = (value: string): string =>
  value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);

const generateDocumentCode = (name: string, existingCodes: string[]): string => {
  const token = normalizeNameToken(name);
  if (!token) {
    return '';
  }

  const prefix = `DOC_${token}_`;
  const matcher = new RegExp(`^${escapeRegExp(prefix)}(\\d{6})$`);
  const usedSequences = new Set<number>();

  for (const existingCode of existingCodes) {
    const match = existingCode.match(matcher);
    if (match) {
      usedSequences.add(Number(match[1]));
    }
  }

  let nextValue = 1;
  while (usedSequences.has(nextValue) && nextValue <= 999999) {
    nextValue += 1;
  }

  const nextSequence = String(nextValue).padStart(6, '0');
  return `${prefix}${nextSequence}`;
};

export function DocumentForm({ initialValue, existingCodes = [], submitLabel, onSubmit }: Props) {
  const generatedCategoryId = useMemo(() => initialValue?.category_id || buildUuid(), [initialValue?.category_id]);

  const defaultValues = useMemo<FormValues>(
    () => ({
      ...(initialValue ?? defaultValue),
      category_id: generatedCategoryId,
    }),
    [generatedCategoryId, initialValue],
  );

  const {
    register,
    handleSubmit,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(documentSchema),
    defaultValues,
  });

  const values = useWatch<FormValues>({ control });

  useEffect(() => {
    register('document_type');
    register('output_format');
    register('business_module');
    register('product');
    register('status');
  }, [register]);

  useEffect(() => {
    if (initialValue) {
      return;
    }

    const nextCode = generateDocumentCode(values.name ?? '', existingCodes);
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

        <TextField
          label="Category ID"
          value={values.category_id}
          error={Boolean(errors.category_id)}
          helperText={errors.category_id?.message ?? 'Auto-generated UUID for this document category.'}
          disabled
          fullWidth
        />
        <input type="hidden" {...register('category_id')} />

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <FormControl fullWidth>
            <InputLabel id="doc-type">Document Type</InputLabel>
            <Select
              labelId="doc-type"
              label="Document Type"
              value={values.document_type}
              onChange={(event) =>
                setValue('document_type', event.target.value as FormValues['document_type'], { shouldValidate: true })
              }
            >
              {DOCUMENT_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel id="doc-format">Output Format</InputLabel>
            <Select
              labelId="doc-format"
              label="Output Format"
              value={values.output_format}
              onChange={(event) =>
                setValue('output_format', event.target.value as FormValues['output_format'], { shouldValidate: true })
              }
            >
              {OUTPUT_FORMAT_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <FormControl fullWidth error={Boolean(errors.business_module)}>
            <InputLabel id="doc-business-module">Business Module</InputLabel>
            <Select
              labelId="doc-business-module"
              label="Business Module"
              value={values.business_module}
              onChange={(event) =>
                setValue('business_module', event.target.value as FormValues['business_module'], {
                  shouldValidate: true,
                })
              }
            >
              {BUSINESS_MODULE_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>{errors.business_module?.message}</FormHelperText>
          </FormControl>

          <FormControl fullWidth error={Boolean(errors.product)}>
            <InputLabel id="doc-product-module">Product Module</InputLabel>
            <Select
              labelId="doc-product-module"
              multiple
              label="Product Module"
              value={values.product}
              input={<OutlinedInput label="Product Module" />}
              onChange={(event) =>
                setValue('product', event.target.value as FormValues['product'], {
                  shouldValidate: true,
                })
              }
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {PRODUCT_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  <Checkbox checked={values.product?.includes(option) ?? false} />
                  <ListItemText primary={option} />
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>{errors.product?.message}</FormHelperText>
          </FormControl>
        </Stack>

        <FormControl fullWidth>
          <InputLabel id="doc-status">Status</InputLabel>
          <Select
            labelId="doc-status"
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

        <TextField
          label="Description"
          {...register('description')}
          multiline
          minRows={3}
          fullWidth
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
