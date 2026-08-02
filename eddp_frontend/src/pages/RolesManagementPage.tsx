import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import {
  Alert,
  Button,
  IconButton,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';

import { ConfirmDialog } from '../components/dialogs/ConfirmDialog';
import { SearchBar } from '../components/forms/SearchBar';
import { PageHeader } from '../components/common/PageHeader';
import { DataTable } from '../components/tables/DataTable';
import { useCreateRole, useDeleteRole, useRoles, useUpdateRole } from '../features/admin/hooks/useAdmin';
import { STATUS_OPTIONS } from '../features/shared/constants';
import { applyListQuery } from '../features/shared/filtering';
import { makeCode } from '../features/shared/utils';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { setPage, setPageSize, setSearch, setStatus } from '../store/slices/rolesSlice';

export function RolesManagementPage() {
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.roles.query);
  const { data = [], isLoading, error } = useRoles();
  const createMutation = useCreateRole();
  const updateMutation = useUpdateRole();
  const deleteMutation = useDeleteRole();

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingId, setEditingId] = useState('');
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setRoleStatus] = useState<'ACTIVE' | 'INACTIVE' | 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'>('ACTIVE');
  const [pendingDeleteId, setPendingDeleteId] = useState('');
  const [pendingDeleteName, setPendingDeleteName] = useState('');

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.code, row.name, row.description],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  const openCreate = () => {
    setEditingId('');
    setName('');
    setDescription('');
    setCode('');
    setRoleStatus('ACTIVE');
    setEditorOpen(true);
  };

  const openEdit = (id: string) => {
    const row = data.find((item) => item.id === id);
    if (!row) {
      return;
    }
    setEditingId(row.id);
    setCode(row.code);
    setName(row.name);
    setDescription(row.description ?? '');
    setRoleStatus(row.status);
    setEditorOpen(true);
  };

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Role Management"
        subtitle="Manage enterprise roles and role lifecycle for administration."
        actions={
          <Button variant="contained" startIcon={<AddOutlinedIcon />} onClick={openCreate}>
            New Role
          </Button>
        }
      />

      {error ? <Alert severity="error">Failed to load roles.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={query.search}
            onChange={(value) => dispatch(setSearch(value))}
            placeholder="Search code, name, description"
          />
          <Select
            size="small"
            value={query.status}
            onChange={(event) => dispatch(setStatus(event.target.value as typeof query.status))}
            displayEmpty
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            {STATUS_OPTIONS.map((item) => (
              <MenuItem key={item} value={item}>
                {item}
              </MenuItem>
            ))}
          </Select>
          <Select
            size="small"
            value={String(query.pageSize)}
            onChange={(event) => dispatch(setPageSize(Number(event.target.value)))}
            sx={{ minWidth: 120 }}
          >
            {[10, 20, 50].map((size) => (
              <MenuItem key={size} value={String(size)}>
                {size} / page
              </MenuItem>
            ))}
          </Select>
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <DataTable
          rows={paged.rows}
          emptyMessage={isLoading ? 'Loading roles...' : 'No roles found.'}
          columns={[
            { key: 'code', header: 'Code', render: (row) => row.code },
            { key: 'name', header: 'Role Name', render: (row) => row.name },
            { key: 'description', header: 'Description', render: (row) => row.description || '-' },
            { key: 'status', header: 'Status', render: (row) => row.status },
            {
              key: 'actions',
              header: 'Actions',
              render: (row) => (
                <Stack direction="row" spacing={1}>
                  <IconButton onClick={() => openEdit(row.id)}>
                    <EditOutlinedIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    onClick={() => {
                      setPendingDeleteId(row.id);
                      setPendingDeleteName(row.name);
                    }}
                  >
                    <DeleteOutlineOutlinedIcon fontSize="small" />
                  </IconButton>
                </Stack>
              ),
            },
          ]}
        />

        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {paged.total} record(s)
          </Typography>
          <Pagination page={query.page} count={pageCount} onChange={(_, page) => dispatch(setPage(page))} color="primary" />
        </Stack>
      </Paper>

      <ConfirmDialog
        open={editorOpen}
        title={editingId ? 'Edit Role' : 'Create Role'}
        description=""
        onCancel={() => setEditorOpen(false)}
        onConfirm={async () => {
          if (!name.trim()) {
            dispatch(enqueueNotification({ severity: 'error', message: 'Role name is required.' }));
            return;
          }

          const payload = {
            code: code.trim() || makeCode('ROLE', name),
            name: name.trim(),
            description: description.trim(),
            status,
          } as const;

          if (editingId) {
            await updateMutation.mutateAsync({ id: editingId, payload });
            dispatch(enqueueNotification({ severity: 'success', message: 'Role updated.' }));
          } else {
            await createMutation.mutateAsync(payload);
            dispatch(enqueueNotification({ severity: 'success', message: 'Role created.' }));
          }
          setEditorOpen(false);
        }}
      />

      {editorOpen ? (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack spacing={2}>
            <TextField label="Code" value={code} onChange={(event) => setCode(event.target.value)} fullWidth />
            <TextField label="Name" value={name} onChange={(event) => setName(event.target.value)} fullWidth />
            <TextField
              label="Description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              fullWidth
              multiline
              minRows={3}
            />
            <Select
              size="small"
              value={status}
              onChange={(event) => setRoleStatus(event.target.value as typeof status)}
              sx={{ minWidth: 180 }}
            >
              {STATUS_OPTIONS.map((item) => (
                <MenuItem key={item} value={item}>
                  {item}
                </MenuItem>
              ))}
            </Select>
          </Stack>
        </Paper>
      ) : null}

      <ConfirmDialog
        open={Boolean(pendingDeleteId)}
        title="Delete Role"
        description={`Delete ${pendingDeleteName || 'this role'}?`}
        onCancel={() => {
          setPendingDeleteId('');
          setPendingDeleteName('');
        }}
        onConfirm={async () => {
          if (!pendingDeleteId) {
            return;
          }
          await deleteMutation.mutateAsync(pendingDeleteId);
          dispatch(enqueueNotification({ severity: 'success', message: 'Role deleted.' }));
          setPendingDeleteId('');
          setPendingDeleteName('');
        }}
      />
    </Stack>
  );
}
