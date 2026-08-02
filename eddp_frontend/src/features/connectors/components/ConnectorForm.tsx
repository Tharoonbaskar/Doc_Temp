import { zodResolver } from '@hookform/resolvers/zod';
import { Box, Button, Checkbox, FormControl, FormControlLabel, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material';
import { useEffect } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';

import { STATUS_OPTIONS } from '../../shared/constants';
import type { ConnectorPayload } from '../types';

const CONNECTOR_TYPE_OPTIONS = ['DATABASE', 'API', 'FILE', 'QUEUE', 'WEBHOOK'] as const;

const connectorSchema = z.object({
  code: z.string().min(3, 'Code must be at least 3 characters.'),
  name: z.string().min(2, 'Name is required.'),
  connector_type: z.enum(CONNECTOR_TYPE_OPTIONS),
  description: z.string(),
  host: z.string(),
  port: z.union([z.number().int().positive(), z.null()]),
  database_name: z.string(),
  username: z.string(),
  password: z.string().optional(),
  api_base_url: z.string(),
  timeout: z.number().int().positive('Timeout must be > 0'),
  retry_count: z.number().int().min(0, 'Retry count cannot be negative'),
  is_active: z.boolean(),
  status: z.enum(STATUS_OPTIONS),
});

type FormValues = z.infer<typeof connectorSchema>;

type Props = {
  initialValue?: ConnectorPayload;
  existingCodes?: string[];
  submitLabel: string;
  onSubmit: (payload: ConnectorPayload) => Promise<void>;
};

const defaultValue: ConnectorPayload = {
  code: '',
  name: '',
  connector_type: 'API',
  description: '',
  host: '',
  port: null,
  database_name: '',
  username: '',
  password: '',
  api_base_url: '',
  timeout: 30,
  retry_count: 3,
  is_active: true,
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

const generateConnectorCode = (name: string, existingCodes: string[]): string => {
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

export function ConnectorForm({ initialValue, existingCodes = [], submitLabel, onSubmit }: Props) {
  const {
    register,
    handleSubmit,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(connectorSchema),
    defaultValues: initialValue ?? defaultValue,
  });

  const values = useWatch<FormValues>({ control });

  useEffect(() => {
    register('connector_type');
    register('status');
    register('is_active');
  }, [register]);

  useEffect(() => {
    if (initialValue) {
      return;
    }

    const nextCode = generateConnectorCode(values.name ?? '', existingCodes);
    setValue('code', nextCode, { shouldValidate: true, shouldDirty: false });
  }, [existingCodes, initialValue, setValue, values.name]);

  return (
    <Box
      component="form"
      onSubmit={handleSubmit(async (payload) => {
        await onSubmit(payload);
      })}
      noValidate
    >
      <Stack spacing={2}>
        <TextField label="Name" {...register('name')} error={Boolean(errors.name)} helperText={errors.name?.message} fullWidth />

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

        <FormControl fullWidth>
          <InputLabel id="connector-type">Connector Type</InputLabel>
          <Select
            labelId="connector-type"
            label="Connector Type"
            value={values.connector_type}
            onChange={(event) => setValue('connector_type', event.target.value as FormValues['connector_type'], { shouldValidate: true })}
          >
            {CONNECTOR_TYPE_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField label="Host" {...register('host')} fullWidth />
          <TextField
            label="Port"
            type="number"
            value={values.port ?? ''}
            onChange={(event) => {
              const next = event.target.value.trim();
              setValue('port', next ? Number(next) : null);
            }}
            fullWidth
          />
        </Stack>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField label="Database Name" {...register('database_name')} fullWidth />
          <TextField label="API Base URL" {...register('api_base_url')} fullWidth />
        </Stack>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField label="Username" {...register('username')} fullWidth />
          <TextField label="Password" type="password" {...register('password')} fullWidth />
        </Stack>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            label="Timeout"
            type="number"
            value={values.timeout}
            onChange={(event) => setValue('timeout', Number(event.target.value || 0))}
            fullWidth
          />
          <TextField
            label="Retry Count"
            type="number"
            value={values.retry_count}
            onChange={(event) => setValue('retry_count', Number(event.target.value || 0))}
            fullWidth
          />
        </Stack>

        <FormControl fullWidth>
          <InputLabel id="conn-status">Status</InputLabel>
          <Select
            labelId="conn-status"
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

        <TextField label="Description" {...register('description')} multiline minRows={3} fullWidth />

        <FormControlLabel
          control={<Checkbox checked={values.is_active} onChange={(event) => setValue('is_active', event.target.checked, { shouldValidate: true })} />}
          label="Active Connector"
        />

        <Button type="submit" variant="contained" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : submitLabel}
        </Button>
      </Stack>
    </Box>
  );
}
