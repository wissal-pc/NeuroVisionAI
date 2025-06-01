import { Box, Typography } from '@mui/material';

export default function Footer() {
  return (
    <Box sx={{ backgroundColor: '#003366', color: '#fff', py: 2, textAlign: 'center' }}>
      <Typography variant="body2">
        © {new Date().getFullYear()} NeuroVisionAI. Tous droits réservés.
      </Typography>
    </Box>
  );
}
