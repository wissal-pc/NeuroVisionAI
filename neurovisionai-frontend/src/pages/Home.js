import { Container, Typography, Box, Slide } from '@mui/material';
import { useEffect, useState } from 'react';
import './Home.css';
import Footer from '../components/Footer';
import AnimatedLogo from '../components/AnimatedLogo';
export default function Home() {
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    setTimeout(() => setAnimate(true), 300);
  }, []);

  return (
    <>
      <Box
        sx={{
          position: 'relative',
          backgroundImage: 'url(/irm1.jpeg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          minHeight: '100vh',
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
        {animate && (
          <AnimatedLogo />
        )}

        <Container sx={{ textAlign: 'center', pt: 4, position: 'relative', zIndex: 1 }} maxWidth="md">
          {/* <Slide direction="down" in={animate} timeout={800}>
            <img src="/logo.png" alt="NeuroVisionAI" className="logo" width={180} />
          </Slide> */}

          <Typography variant="h4" mt={3} fontWeight="bold" color="primary">
            Bienvenue sur NeuroVisionAI
          </Typography>
          <Typography variant="body1" mt={1} fontStyle="italic">
            Plateforme de segmentation de tumeurs cérébrales par intelligence artificielle.
          </Typography>

          {/* Instructions */}
          <Box className="section-box">
            <Typography variant="h5" fontWeight="bold">Instructions</Typography>
            <Typography mt={1}><strong>1.</strong> Connectez-vous avec vos identifiants ou créez un compte sécurisé.</Typography>
            <Typography><strong>2.</strong> Importez les images IRM du patient (format .nii ou .png accepté).</Typography>
            <Typography><strong>3.</strong> Lancez l’analyse automatique pour détecter et segmenter une éventuelle tumeur.</Typography>
            <Typography><strong>4.</strong> Consultez les résultats incluant le volume tumoral, la localisation, et le score Dice.</Typography>
            <Typography><strong>5.</strong> Fournissez un retour médical pour améliorer le système d’IA.</Typography>
            <Typography><strong>6.</strong> Générez et téléchargez un rapport PDF personnalisé.</Typography>
          </Box>

          {/* À propos */}
          <Box className="section-box">
            <Typography variant="h5" fontWeight="bold">À propos</Typography>
            <Typography mt={1}>
              NeuroVisionAI est une application web développée pour assister les professionnels de santé dans la détection et la segmentation de tumeurs cérébrales à partir d’IRM. 
              Grâce à l’intelligence artificielle, elle permet une analyse rapide, fiable et automatisée des examens, tout en offrant une interface intuitive pour le suivi et la génération de rapports médicaux.
            </Typography>
          </Box>

          {/* Contact */}
          <Box className="section-box" id="contact">
            <Typography variant="h5" fontWeight="bold">Contact</Typography>
            <Typography>Contact us with wissal.kallah@neurovisionai.com or kawtar.lameghaizi@neurovisionai.com</Typography>
          </Box>
        </Container>
      </Box>

      {/*  Footer en dehors du bloc voilé */}
      <Footer />
    </>
  );
}
