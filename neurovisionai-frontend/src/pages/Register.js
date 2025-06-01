import { useState, useEffect } from 'react';
import { Container, TextField, Typography, Button, Box, Link } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import './Home.css'; // Réutilisation des styles
import Footer from '../components/Footer';
import AnimatedLogo from '../components/AnimatedLogo';

export default function Register() {
  const [animate, setAnimate] = useState(false);
  const [form, setForm] = useState({
    nom: '',
    prenom: '',
    email: '',
    username: '',
    password: ''
  });

  const navigate = useNavigate();

  useEffect(() => {
    setTimeout(() => setAnimate(true), 300);
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:5000/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const data = await response.json();
    if (response.ok) {
      alert('Inscription réussie ! Vous pouvez vous connecter.');
      navigate('/login');
    } else {
      alert(data.message || 'Erreur lors de l’inscription');
    }
  };

  return (
    <>
      <Box
        sx={{
          position: 'relative',
          backgroundImage: 'url(/irm2.jpeg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.7)',
            zIndex: 0
          }
        }}
      >
        {/* Logo animé en haut à droite */}
        <Box sx={{ position: 'absolute', top: 20, right: 20, zIndex: 1 }}>
          {animate && <AnimatedLogo />}
        </Box>

        {/* Formulaire dans bloc blanc */}
        <Container maxWidth="sm" sx={{ zIndex: 1 }}>
          <Box className="section-box" sx={{ textAlign: 'center' }}>
            <Typography variant="h5" mb={3}>Inscription</Typography>
            <Box component="form" onSubmit={handleSubmit}>
              <TextField label="Nom" name="nom" fullWidth margin="normal" onChange={handleChange} required sx={{ backgroundColor: 'white' }} />
              <TextField label="Prénom" name="prenom" fullWidth margin="normal" onChange={handleChange} required sx={{ backgroundColor: 'white' }} />
              <TextField label="Email" name="email" fullWidth margin="normal" type="email" onChange={handleChange} required sx={{ backgroundColor: 'white' }} />
              <TextField label="Nom d'utilisateur" name="username" fullWidth margin="normal" onChange={handleChange} required sx={{ backgroundColor: 'white' }} />
              <TextField label="Mot de passe" name="password" type="password" fullWidth margin="normal" onChange={handleChange} required sx={{ backgroundColor: 'white' }} />
              <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>
                S'inscrire
              </Button>
            </Box>
            <Box mt={2}>
              <Typography variant="body2" sx={{ color: 'black' }}>
                Déjà inscrit ?{' '}
                <Link href="/login" underline="hover" color="primary">
                  Se connecter
                </Link>
              </Typography>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Pied de page global */}
      <Footer />
    </>
  );
}
