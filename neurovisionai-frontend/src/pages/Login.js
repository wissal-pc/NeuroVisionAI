import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, TextField, Button, Typography, Box } from '@mui/material';
import './Home.css';
import Footer from '../components/Footer';
import AnimatedLogo from '../components/AnimatedLogo';
import axios from 'axios';

export default function Login() {
  const [animate, setAnimate] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    setTimeout(() => setAnimate(true), 300);
  }, []);

  const handleLogin = async () => {
    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);

      const res = await axios.post("http://localhost:5000/login", formData, {
        withCredentials: true // 🔑 important pour stocker le cookie de session
      });

      if (res.data.success) {
        // localStorage.setItem("auth", "true");
        localStorage.setItem("auth", "true");
        navigate("/analyse");
      } else {
        alert(res.data.message || "Échec de la connexion");
      }
    } catch (err) {
      console.error("Erreur de connexion :", err);
      alert("Connexion échouée. Vérifie les identifiants.");
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
        <Box sx={{ position: 'absolute', top: 20, right: 20, zIndex: 1 }}>
          {animate && <AnimatedLogo />}
        </Box>

        <Container maxWidth="sm" sx={{ zIndex: 1 }}>
          <Box className="section-box" sx={{ textAlign: 'center' }}>
            <Typography variant="h5" mb={3}>Connexion Médecin</Typography>
            <TextField
              label="Nom d'utilisateur"
              variant="outlined"
              fullWidth
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              sx={{ mb: 2, backgroundColor: 'white' }}
            />
            <TextField
              label="Mot de passe"
              type="password"
              variant="outlined"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 3, backgroundColor: 'white' }}
            />
            <Button variant="contained" color="primary" fullWidth onClick={handleLogin} sx={{ mb: 2 }}>
              Se connecter
            </Button>
            <Typography variant="body2">
              <span>Pas encore de compte ? </span>
              <span
                onClick={() => navigate('/register')}
                style={{ color: '#3f51b5', cursor: 'pointer', textDecoration: 'underline' }}
              >
                Créer un compte
              </span>
            </Typography>
          </Box>
        </Container>
      </Box>

      <Footer />
    </>
  );
}
