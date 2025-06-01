import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import AnalysePage from './pages/AnalysePage'; 
import Navbar from './components/Navbar';
import Contact from './pages/Contact';
import ResultPage from './pages/ResultPage';
import FollowUpPage from './pages/FollowUpPage';

function App() {
  const isAuthenticated = localStorage.getItem("auth") === "true";

  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/result" element={<ResultPage />} />
        <Route path="/follow_up/:id" element={<FollowUpPage />} />
        <Route
          path="/analyse"
          element={isAuthenticated ? <AnalysePage /> : <Navigate to="/login" />}
        />
      </Routes>
    </Router>
  );
}

export default App;
