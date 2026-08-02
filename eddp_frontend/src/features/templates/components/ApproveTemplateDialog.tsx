import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from '@mui/material';
import { useState } from 'react';

import type { ApproveTemplatePayload } from '../types';

type ApproveTemplateDialogProps = {
  open: boolean;
  onClose: () => void;
  onApprove: (payload: ApproveTemplatePayload) => void;
  templateName: string;
};

export function ApproveTemplateDialog({ open, onClose, onApprove, templateName }: ApproveTemplateDialogProps) {
  const [effectiveDate, setEffectiveDate] = useState<string>(
    new Date().toISOString().slice(0, 16)
  );
  const [reviewComments, setReviewComments] = useState('');

  const handleApprove = () => {
    if (!effectiveDate) return;
    
    onApprove({
      effective_date: new Date(effectiveDate).toISOString(),
      review_comments: reviewComments || undefined,
    });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Approve Template</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ pt: 2 }}>
          <TextField
            label="Template Name"
            value={templateName}
            disabled
            fullWidth
          />
          
          <TextField
            label="Effective Date"
            type="datetime-local"
            value={effectiveDate}
            onChange={(e) => setEffectiveDate(e.target.value)}
            fullWidth
            required
            helperText="Template will become active on this date"
            InputLabelProps={{ shrink: true }}
          />
          
          <TextField
            label="Review Comments"
            value={reviewComments}
            onChange={(e) => setReviewComments(e.target.value)}
            multiline
            rows={4}
            fullWidth
            placeholder="Add optional comments about the approval..."
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button 
          onClick={handleApprove}
          variant="contained" 
          color="success"
          disabled={!effectiveDate}
        >
          Approve
        </Button>
      </DialogActions>
    </Dialog>
  );
}
