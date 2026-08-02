import RateReviewOutlinedIcon from '@mui/icons-material/RateReviewOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import {
  Alert,
  IconButton,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Stack,
  Typography,
  Tooltip,
  Chip,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { SearchBar } from '../components/forms/SearchBar';
import { PageHeader } from '../components/common/PageHeader';
import { DataTable } from '../components/tables/DataTable';
import { TEMPLATE_APPROVAL_ROUTES, TEMPLATE_ROUTES } from '../constants/appConstants';
import { useTemplates } from '../features/templates/hooks/useTemplates';
import type { TemplateItem, TemplateStatus } from '../features/templates/types';
import { applyListQuery } from '../features/shared/filtering';

const PAGE_SIZES = [10, 25, 50, 100];

type ApprovalRow = TemplateItem & {
  row_kind: 'TEMPLATE' | 'VERSION_REVIEW';
  source_template_id: string;
  review_version_number?: number;
};

export function TemplateApprovalsListPage() {
  const navigate = useNavigate();
  const query = useTemplates();
  
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0]);

  const isLoading = query.isLoading;
  const allTemplates = query.data ?? [];

  const approvalTemplates = useMemo<ApprovalRow[]>(() => {
    return allTemplates.flatMap((template) => {
      const rows: ApprovalRow[] = [];

      if (template.status === 'FOR_REVIEW' || template.status === 'APPROVED') {
        rows.push({
          ...template,
          row_kind: 'TEMPLATE',
          source_template_id: template.id,
        });
      }

      if (
        template.has_pending_draft &&
        template.pending_draft_version &&
        template.pending_draft_status === 'FOR_REVIEW'
      ) {
        rows.push({
          ...template,
          row_kind: 'VERSION_REVIEW',
          source_template_id: template.id,
          review_version_number: template.pending_draft_version,
          status: 'FOR_REVIEW',
          code: `${template.code}_V${template.pending_draft_version}`,
          name: `${template.name} (v${template.pending_draft_version}.0 In Review)`,
        });
      }

      return rows;
    });
  }, [allTemplates]);

  const paged = useMemo(() => {
    return applyListQuery(
      approvalTemplates,
      { search, status: '', page, pageSize },
      {
        statusSelector: (row: TemplateItem) => row.status,
        searchSelector: (row: ApprovalRow) => [row.code, row.name, row.category, row.template_type],
      }
    );
  }, [approvalTemplates, search, page, pageSize]);

  const totalPages = Math.ceil(paged.total / pageSize);

  return (
    <Stack spacing={3}>
      <PageHeader 
        title="Document Approvals" 
        subtitle="Review pending templates and view approval history"
      />

      {query.error && <Alert severity="error">Failed to load templates for approval.</Alert>}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
          <SearchBar
            placeholder="Search by code, name, category..."
            value={search}
            onChange={setSearch}
            sx={{ flex: 1 }}
          />

          <Stack direction="row" spacing={2} alignItems="center">
            <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
              Showing
            </Typography>
            <Select size="small" value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))}>
              {PAGE_SIZES.map((size) => (
                <MenuItem key={size} value={size}>
                  {size} / page
                </MenuItem>
              ))}
            </Select>
          </Stack>
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <DataTable
          rows={paged.rows}
          emptyMessage={isLoading ? 'Loading templates...' : 'No templates in approval workflow.'}
          columns={[
            { key: 'code', header: 'Code', render: (row: ApprovalRow) => row.code },
            { key: 'name', header: 'Name', render: (row: ApprovalRow) => row.name },
            { key: 'category', header: 'Category', render: (row: ApprovalRow) => row.category },
            { key: 'type', header: 'Template Type', render: (row: ApprovalRow) => row.template_type },
            { 
              key: 'status', 
              header: 'Status', 
              render: (row: ApprovalRow) => {
                const statusConfig: Partial<Record<TemplateStatus, { label: string; color: 'warning' | 'success' | 'default' }>> = {
                  FOR_REVIEW: { label: 'For Review', color: 'warning' },
                  APPROVED: { label: 'Approved', color: 'success' },
                };
                const config = statusConfig[row.status] || { label: row.status, color: 'default' as const };
                const label = row.row_kind === 'VERSION_REVIEW' ? 'In Review' : config.label;
                return <Chip label={label} color={config.color} size="small" />;
              }
            },
            { 
              key: 'version', 
              header: 'Version', 
              render: (row: ApprovalRow) => `v${row.review_version_number ?? row.current_version ?? 1}.0`
            },
            { 
              key: 'effective_date', 
              header: 'Effective Date', 
              render: (row: ApprovalRow) => {
                if (!row.effective_date) return '-';
                return new Date(row.effective_date).toLocaleDateString();
              }
            },
            { 
              key: 'approved_by', 
              header: 'Approved By', 
              render: (row: ApprovalRow) => row.approved_by_name || '-'
            },
            {
              key: 'actions',
              header: 'Actions',
              render: (row: ApprovalRow) => (
                <Stack direction="row" spacing={1}>
                  <Tooltip title="View">
                    <IconButton
                      onClick={() => {
                        if (row.row_kind === 'VERSION_REVIEW' && row.review_version_number) {
                          navigate(TEMPLATE_ROUTES.editVersion(row.source_template_id, row.review_version_number));
                          return;
                        }
                        navigate(TEMPLATE_APPROVAL_ROUTES.review(row.source_template_id));
                      }}
                    >
                      <VisibilityOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  {row.status === 'FOR_REVIEW' && row.row_kind === 'TEMPLATE' && (
                    <Tooltip title="Review & Approve">
                      <IconButton onClick={() => navigate(TEMPLATE_APPROVAL_ROUTES.review(row.source_template_id))} color="primary">
                        <RateReviewOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Stack>
              ),
            },
          ]}
        />

        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {paged.total} template(s) in approval workflow
          </Typography>
          <Pagination count={totalPages} page={page} onChange={(_, value) => setPage(value)} />
        </Stack>
      </Paper>
    </Stack>
  );
}
