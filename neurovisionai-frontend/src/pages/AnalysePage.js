import { useState, useEffect, useRef } from 'react';
import { Container, TextField, Typography, Button, Box } from '@mui/material';
import Footer from '../components/Footer';
import AnimatedLogo from '../components/AnimatedLogo';
import './Home.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function AnalysePage() {
  const [animate, setAnimate] = useState(false);
  const [form, setForm] = useState({
    patient_lastname: '',
    patient_firstname: '',
    patient_id: '',
    patient_birthdate: '',
    antecedents: '',
    traitements: '',
    irm_date: '',
    file: null,
    ground_truth: null
  });

  const formRef = useRef();
  const navigate = useNavigate();

  useEffect(() => {
    setTimeout(() => setAnimate(true), 300);
  }, []);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setForm({ ...form, [name]: files ? files[0] : value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const data = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      if (value) data.append(key, value);
    });

    try {
      await axios.post('http://localhost:5000/upload', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });
      alert('Analyse envoyée avec succès !');
      navigate('/result');
    } catch (err) {
      alert("Erreur lors de l'envoi.");
      console.error(err);
    }
  };

  const handleReset = () => {
    setForm({
      patient_lastname: '',
      patient_firstname: '',
      patient_id: '',
      patient_birthdate: '',
      antecedents: '',
      traitements: '',
      irm_date: '',
      file: null,
      ground_truth: null
    });
    if (formRef.current) {
      formRef.current.reset();
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth');
    window.scrollTo(0, 0);
    navigate('/');
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
            <Typography variant="h5" mb={3}>Importer une image IRM</Typography>

            <Box component="form" onSubmit={handleSubmit} ref={formRef}>
              <TextField name="patient_lastname" label="Nom du patient" fullWidth margin="normal" onChange={handleChange} value={form.patient_lastname} required sx={{ backgroundColor: 'white' }} />
              <TextField name="patient_firstname" label="Prénom du patient" fullWidth margin="normal" onChange={handleChange} value={form.patient_firstname} required sx={{ backgroundColor: 'white' }} />
              <TextField name="patient_id" label="ID du patient" fullWidth margin="normal" onChange={handleChange} value={form.patient_id} required sx={{ backgroundColor: 'white' }} />
              <TextField name="patient_birthdate" label="Date de naissance" type="date" InputLabelProps={{ shrink: true }} fullWidth margin="normal" onChange={handleChange} value={form.patient_birthdate} required sx={{ backgroundColor: 'white' }} />
              <TextField name="antecedents" label="Antécédents médicaux" multiline rows={2} fullWidth margin="normal" onChange={handleChange} value={form.antecedents} sx={{ backgroundColor: 'white' }} />
              <TextField name="traitements" label="Traitements en cours" multiline rows={2} fullWidth margin="normal" onChange={handleChange} value={form.traitements} sx={{ backgroundColor: 'white' }} />
              <TextField name="irm_date" label="Date de l'IRM" type="date" InputLabelProps={{ shrink: true }} fullWidth margin="normal" onChange={handleChange} value={form.irm_date} required sx={{ backgroundColor: 'white' }} />

              <Typography align="left" mt={2} mb={1}>Fichier IRM :</Typography>
              <input type="file" name="file" accept=".nii,.gz,.png" onChange={handleChange} required style={{ marginBottom: 12 }} />

              <Typography align="left" mt={2} mb={1}>Masque réel (optionnel) :</Typography>
              <input type="file" name="ground_truth" accept=".nii,.gz,.png" onChange={handleChange} style={{ marginBottom: 20 }} />

              <Button variant="contained" color="primary" type="submit" fullWidth sx={{ mb: 1 }}>
                Analyser
              </Button>
              <Button variant="outlined" color="secondary" fullWidth onClick={handleReset}>
                Réinitialiser
              </Button>
              <Button variant="text" color="error" fullWidth sx={{ mt: 2 }} onClick={handleLogout}>
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
