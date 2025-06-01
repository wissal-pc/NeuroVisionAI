import { Container, Typography } from '@mui/material';
export default function Contact() {
  return (
    <Container sx={{ mt: 6 }}>
      <Typography variant="h5">Contact</Typography>
      <Typography>Email : contact@neurovisionai.com</Typography>
      <Typography>Adresse : Hôpital IA, Paris</Typography>
    </Container>
  );
}
