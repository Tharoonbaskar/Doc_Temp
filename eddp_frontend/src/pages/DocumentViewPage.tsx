import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { Alert, Button, Paper, Stack, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { DOCUMENT_ROUTES } from '../constants/appConstants';
import { useDocument } from '../features/documents/hooks/useDocuments';

export function DocumentViewPage() {
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const query = useDocument(id);

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (query.error) {
    return <Alert severity="error">Failed to load document details.</Alert>;
  }

  if (!query.data) {
    return <EmptyState title="Document not found" description="The requested document does not exist." />;
  }

  const row = query.data;
  const productValue = Array.isArray(row.product) ? row.product.join(', ') : row.product;

  return (
    <Stack spacing={3}>
      <PageHeader
        title={row.name}
        subtitle="Document details"
        actions={
          <Button variant="contained" startIcon={<EditOutlinedIcon />} onClick={() => navigate(DOCUMENT_ROUTES.edit(row.id))}>
            Edit
          </Button>
        }
      />

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={1}>
          <Typography><strong>Code:</strong> {row.code}</Typography>
          <Typography><strong>Status:</strong> {row.status}</Typography>
          <Typography><strong>Category ID:</strong> {row.category?.id ?? '-'}</Typography>
          <Typography><strong>Category:</strong> {row.category?.name ?? '-'}</Typography>
          <Typography><strong>Type:</strong> {row.document_type}</Typography>
          <Typography><strong>Output Format:</strong> {row.output_format}</Typography>
          <Typography><strong>Business Module:</strong> {row.business_module}</Typography>
          <Typography><strong>Product:</strong> {productValue}</Typography>
          <Typography><strong>Description:</strong> {row.description || '-'}</Typography>
        </Stack>
      </Paper>
    </Stack>
  );
}
