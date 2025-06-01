import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <AppBar position="static" sx={{ backgroundColor: '#003366' }}>
      <Toolbar>
        <img src="/logo.png" alt="logo" width={40} height={40} style={{ marginRight: 10 }} />
        <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
          NeuroVisionAI
        </Typography>
        <Box>
          <Button color="inherit" component={Link} to="/">Accueil</Button>
          {/* <Button color="inherit" component="a" href="#contact">Contact</Button> */}
          <Button
            color="inherit"
            onClick={() => {
              const contactSection = document.getElementById('contact');
              if (contactSection) {
                contactSection.scrollIntoView({ behavior: 'smooth' });
              }
            }}
          >
            Contact
          </Button>

          <Button color="inherit" component={Link} to="/login">Se connecter</Button>
          <Button color="inherit" component={Link} to="/register">S'inscrire</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
