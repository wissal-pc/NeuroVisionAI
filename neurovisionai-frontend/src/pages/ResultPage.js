import { useState, useEffect } from 'react';
import { Container, Typography, Box, Button, TextField, MenuItem } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import Footer from '../components/Footer';
import AnimatedLogo from '../components/AnimatedLogo';
import axios from 'axios';
import './Home.css';

export default function ResultPage() {
  const [animate, setAnimate] = useState(false);
  const [data, setData] = useState(null);
  const [feedback, setFeedback] = useState({
    seg_ok: '',
    confidence: '',
    commentaire: '',
    next_exam: '',
    recommendations: ''
  });

  const navigate = useNavigate();

  useEffect(() => {
    setTimeout(() => setAnimate(true), 300);

    axios.get('http://localhost:5000/api/latest_result', { withCredentials: true })
      .then(res => setData(res.data))
      .catch(err => {
        if (err.response && err.response.status === 401) {
          alert("Session expirée. Veuillez vous reconnecter.");
          navigate('/login');
        } else {
          console.error('Erreur récupération résultat', err);
        }
      });
  }, [navigate]);

  const handleChange = (e) => {
    setFeedback({ ...feedback, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/feedback', {
        patient_id: data.patient_id,
        ...feedback
      }, { withCredentials: true });
      navigate(`/follow_up/${data.patient_id}`);
    } catch (err) {
      console.error("Erreur feedback", err);
    }
  };

  const formatCentroid = (centroidStr) => {
    try {
      const [x, y, z] = centroidStr.replace(/[()]/g, '').split(',').map(c => c.trim());
      return `X: ${x} mm, Y: ${y} mm, Z: ${z} mm`;
    } catch (e) {
      return centroidStr;
    }
  };
  const formatDate = (rawDate) => {
  if (!rawDate) return '';
  const date = new Date(rawDate);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
};
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

        <Container maxWidth="md" sx={{ zIndex: 1 }}>
          <Box className="section-box" sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h4" mb={2} color="primary" align="center" fontWeight="bold" gutterBottom>Informations Patient</Typography>
            <Typography><strong>Nom et Prénom :</strong> {data.patient_lastname} {data.patient_firstname}</Typography>
            <Typography><strong>ID du patient :</strong> {data.patient_id}</Typography>
            {/* <Typography><strong>Date de naissance :</strong> {data.patient_birthdate} (Age : {data.patient_age} ans)</Typography> */}
            <Typography><strong>Date de naissance :</strong> {formatDate(data.patient_birthdate)} (Age : {data.patient_age} ans)</Typography>
            <Typography><strong>Antécédents :</strong> {data.antecedents}</Typography>
            <Typography><strong>Traitements :</strong> {data.traitements}</Typography>
            <Typography><strong>Médecin :</strong> {data.medecin}</Typography>
            <Typography><strong>Date de l'IRM :</strong> {formatDate(data.irm_date)}</Typography>
            <Typography variant="h4" mt={4} color="primary" align="center" fontWeight="bold" gutterBottom>Résultat de l’analyse</Typography>
            <Typography><strong>Volume tumoral :</strong> {data.volume} cm³</Typography>
            {/* <Typography><strong>Dimensions :</strong> {data.dimensions?.L} mm (L) × {data.dimensions?.H} mm (H) × {data.dimensions?.P} mm (P)</Typography> */}
            <Typography><strong>Score Dice :</strong> {data.dice || 'Non calculé'}</Typography>
            <Typography><strong>Centroïde :</strong> {formatCentroid(data.centroid)}</Typography>

            <Typography variant="h6" mt={4}>Image originale (IRM brute)</Typography>
            <img src={`http://localhost:5000/static/original.png`} alt="IRM Brute" width={250} />

            <Typography variant="h6" mt={4}>Masque de segmentation</Typography>
            <img src={`http://localhost:5000/static/result.png`} alt="IRM Segmentation" width={250} />

            {/* Feedback */}
            <Typography variant="h5" mt={5} mb={2}>Feedback Médical Complet</Typography>
            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                select
                fullWidth
                label="Segmentation correcte ?"
                name="seg_ok"
                value={feedback.seg_ok}
                onChange={handleChange}
                required
                sx={{ mb: 2 }}
              >
                <MenuItem value="">-- Sélectionner --</MenuItem>
                <MenuItem value="Oui">Oui</MenuItem>
                <MenuItem value="Non">Non</MenuItem>
                <MenuItem value="Partiellement">Partiellement</MenuItem>
              </TextField>

              <TextField
                label="Confiance (1-5)"
                type="number"
                inputProps={{ min: 1, max: 5 }}
                name="confidence"
                value={feedback.confidence}
                onChange={handleChange}
                fullWidth
                required
                sx={{ mb: 2 }}
              />

              <TextField
                label="Commentaires détaillés"
                name="commentaire"
                value={feedback.commentaire}
                onChange={handleChange}
                multiline
                rows={2}
                fullWidth
                required
                sx={{ mb: 2 }}
              />

              <TextField
                label="Prochain examen recommandé"
                name="next_exam"
                value={feedback.next_exam}
                onChange={handleChange}
                fullWidth
                sx={{ mb: 2 }}
              />

              <TextField
                label="Recommandations"
                name="recommendations"
                value={feedback.recommendations}
                onChange={handleChange}
                multiline
                rows={2}
                fullWidth
                sx={{ mb: 2 }}
              />

              <Button variant="contained" type="submit" color="primary" fullWidth>
                Soumettre le feedback complet
              </Button>
            </Box>

            <Box mt={3} display="flex" justifyContent="space-between">
              <Button variant="contained" color="primary" onClick={() => {
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                  navigate(-1);
                }}>
                Nouvelle analyse
              </Button>
              <Button variant="outlined" color="error" onClick={() => {
                localStorage.removeItem('auth');
                window.scrollTo(0, 0);
                navigate('/');
              }}>
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
