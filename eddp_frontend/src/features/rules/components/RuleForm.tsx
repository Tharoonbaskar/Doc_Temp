import { zodResolver } from '@hookform/resolvers/zod';
import { Box, Button, Checkbox, FormControl, FormControlLabel, InputLabel, MenuItem, Select, Stack, TextField } from '@mui/material';
import { useEffect, useMemo } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';

import { STATUS_OPTIONS } from '../../shared/constants';
import type { RulePayload } from '../types';

const RULE_TYPE_OPTIONS = ['VALIDATION', 'TRANSFORMATION', 'ELIGIBILITY', 'CALCULATION', 'ROUTING'] as const;

const ruleSchema = z.object({
  code: z.string().min(3, 'Code must be at least 3 characters.'),
  rule_group_id: z.string().uuid('Rule Group ID must be a valid UUID.'),
  name: z.string().min(2, 'Name is required.'),
  description: z.string(),
  expression: z.string().min(1, 'Expression is required.'),
  rule_type: z.enum(RULE_TYPE_OPTIONS),
  execution_order: z.number().int().min(1, 'Execution order must be > 0'),
  is_active: z.boolean(),
  status: z.enum(STATUS_OPTIONS),
});

type FormValues = z.infer<typeof ruleSchema>;

type Props = {
  initialValue?: RulePayload;
  existingCodes?: string[];
  submitLabel: string;
  onSubmit: (payload: RulePayload) => Promise<void>;
};

const defaultValue: RulePayload = {
  code: '',
  rule_group_id: '',
  name: '',
  description: '',
  expression: '',
  rule_type: 'VALIDATION',
  execution_order: 1,
  is_active: true,
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

const generateRuleCode = (name: string, existingCodes: string[]): string => {
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

export function RuleForm({ initialValue, existingCodes = [], submitLabel, onSubmit }: Props) {
  const generatedRuleGroupId = useMemo(() => initialValue?.rule_group_id || buildUuid(), [initialValue?.rule_group_id]);

  const defaultValues = useMemo<FormValues>(
    () => ({
      ...(initialValue ?? defaultValue),
      rule_group_id: generatedRuleGroupId,
    }),
    [generatedRuleGroupId, initialValue],
  );

  const {
    register,
    handleSubmit,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(ruleSchema),
    defaultValues,
  });

  const values = useWatch<FormValues>({ control });

  useEffect(() => {
    register('rule_type');
    register('status');
    register('is_active');
    register('execution_order');
  }, [register]);

  useEffect(() => {
    if (initialValue) {
      return;
    }

    const nextCode = generateRuleCode(values.name ?? '', existingCodes);
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
          label="Rule Group ID"
          value={values.rule_group_id}
          error={Boolean(errors.rule_group_id)}
          helperText={errors.rule_group_id?.message ?? 'Auto-generated UUID for this rule group.'}
          disabled
          fullWidth
        />
        <input type="hidden" {...register('rule_group_id')} />

        <FormControl fullWidth>
          <InputLabel id="rule-type">Rule Type</InputLabel>
          <Select
            labelId="rule-type"
            label="Rule Type"
            value={values.rule_type}
            onChange={(event) => setValue('rule_type', event.target.value as FormValues['rule_type'], { shouldValidate: true })}
          >
            {RULE_TYPE_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          label="Expression"
          {...register('expression')}
          error={Boolean(errors.expression)}
          helperText={errors.expression?.message}
          multiline
          minRows={3}
          fullWidth
        />

        <TextField
          label="Execution Order"
          type="number"
          value={values.execution_order}
          onChange={(event) => setValue('execution_order', Number(event.target.value || 1), { shouldValidate: true })}
          fullWidth
        />

        <FormControl fullWidth>
          <InputLabel id="rule-status">Status</InputLabel>
          <Select
            labelId="rule-status"
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
          label="Active Rule"
        />

        <Button type="submit" variant="contained" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : submitLabel}
        </Button>
      </Stack>
    </Box>
  );
}
