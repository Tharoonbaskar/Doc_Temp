import { createTheme, type PaletteMode, responsiveFontSizes } from '@mui/material/styles';

export const buildTheme = (mode: PaletteMode) => {
  const theme = createTheme({
    palette: {
      mode,
      primary: {
        main: '#0057A8',
      },
      secondary: {
        main: '#0C8B5F',
      },
      background: {
        default: mode === 'light' ? '#F4F6F8' : '#0E141B',
        paper: mode === 'light' ? '#FFFFFF' : '#16202A',
      },
    },
    shape: {
      borderRadius: 10,
    },
    typography: {
      fontFamily: [
        'Inter',
        'Segoe UI',
        'Roboto',
        'Helvetica Neue',
        'Arial',
        'sans-serif',
      ].join(','),
      h4: {
        fontWeight: 700,
      },
      h5: {
        fontWeight: 700,
      },
      subtitle1: {
        fontWeight: 600,
      },
    },
    components: {
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: 'none',
            borderBottom: mode === 'light' ? '1px solid #E5EAF1' : '1px solid #243140',
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: mode === 'light' ? '1px solid #E5EAF1' : '1px solid #243140',
          },
        },
      },
    },
  });

  return responsiveFontSizes(theme);
};
