import { useEffect, useState } from 'react';
import { Container, Typography, Box, Button } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import Footer from '../components/Footer';
import AnimatedLogo from '../components/AnimatedLogo';
import './Home.css';

export default function FollowUpPage() {
  const [data, setData] = useState(null);
  const [animate, setAnimate] = useState(false);
  const { id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    setTimeout(() => setAnimate(true), 300);

    axios.get(`http://localhost:5000/api/follow_up/${id}`, { withCredentials: true })
      .then(res => setData(res.data))
      .catch(err => {
        if (err.response?.status === 401) {
          alert("Session expirée. Veuillez vous reconnecter.");
          navigate('/login');
        } else {
          console.error("Erreur récupération suivi", err);
        }
      });
  }, [id, navigate]);

  if (!data) return <Typography>Chargement...</Typography>;

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
          <Box className="section-box" sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h4" color="primary" gutterBottom fontWeight="bold">Suivi Patient</Typography>

            <Typography variant="h6" mt={2} color="primary" fontWeight="bold">Informations Patient</Typography>
            <Typography><strong>Nom et Prénom :</strong> {data.nom} {data.prenom}</Typography>
            <Typography><strong>ID du patient :</strong> {data.patient_id}</Typography>

            <Typography variant="h6" mt={3} color="primary" fontWeight="bold">Plan de Suivi</Typography>
            <Typography><strong>Prochain examen :</strong> {data.next_exam}</Typography>
            <Typography><strong>Recommandations :</strong> {data.recommendations}</Typography>
            <Button
              variant="contained"
              color="primary"
              sx={{ mt: 3 }}
              onClick={() => {
                // window.open(`http://localhost:5000/download_report/${patientId}`, '_blank');
                window.open(`http://localhost:5000/generate_and_download/${data.patient_id}`, '_blank');

              }}
            >
              Télécharger le rapport PDF
            </Button>

            <Box mt={4} display="flex" gap={2}>
              <Button
                variant="contained"
                color="primary"
                onClick={() => {
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                  navigate('/analyse');
                }}
              >
                Nouvelle analyse
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={() => {
                  localStorage.removeItem('auth');
                  navigate('/');
                }}
              >
                Déconnexion
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      <Footer />
    </>
  );
}
