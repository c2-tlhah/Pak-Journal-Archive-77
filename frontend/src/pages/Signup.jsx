import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Signup = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to login page (which now handles both login and signup)
    navigate('/login');
  }, [navigate]);

  return null; // Component just redirects, no UI needed
};

export default Signup;
