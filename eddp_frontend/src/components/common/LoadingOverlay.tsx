import { Backdrop, CircularProgress } from '@mui/material';

type Props = {
  open: boolean;
};

export function LoadingOverlay({ open }: Props) {
  return (
    <Backdrop open={open} sx={{ zIndex: (theme) => theme.zIndex.modal + 1 }}>
      <CircularProgress color="inherit" />
    </Backdrop>
  );
}
