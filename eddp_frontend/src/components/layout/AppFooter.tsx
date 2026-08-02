import { Box, Typography } from '@mui/material';

export function AppFooter() {
  return (
    <Box component="footer" sx={{ mt: 'auto', py: 2 }}>
      <Typography variant="caption" color="text.secondary">
        Copyright {new Date().getFullYear()} EDDP Enterprise. All rights reserved.
      </Typography>
    </Box>
  );
}
