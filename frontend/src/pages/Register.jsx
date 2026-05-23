import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { UserPlus, User, KeyRound, Mail } from 'lucide-react';

const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');   // ✅ added
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const { register } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await register(username, email, password);  // ✅ fixed
      alert("Registration successful ✅");
      navigate('/');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Registration failed. Try again.');
    }
  };

  return (
    <div className="flex bg-slate-900 min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <div className="w-full max-w-md bg-white/10 backdrop-blur-md rounded-2xl shadow-2xl p-8 border border-white/20">

        <div className="flex flex-col items-center mb-8">
          <div className="bg-indigo-600 p-3 rounded-full mb-4 shadow-lg shadow-indigo-600/50">
            <UserPlus className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white">Create Account</h2>
        </div>

        {error && (
          <div className="bg-rose-500/10 border border-rose-500 text-rose-400 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">

          {/* Username */}
          <div>
            <label className="text-white">Username</label>
            <div className="relative">
              <User className="absolute left-2 top-2 text-gray-400" />
              <input
                type="text"
                className="w-full pl-8 p-2 bg-gray-800 text-white rounded"
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Email (NEW) */}
          <div>
            <label className="text-white">Email</label>
            <div className="relative">
              <Mail className="absolute left-2 top-2 text-gray-400" />
              <input
                type="email"
                className="w-full pl-8 p-2 bg-gray-800 text-white rounded"
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="text-white">Password</label>
            <div className="relative">
              <KeyRound className="absolute left-2 top-2 text-gray-400" />
              <input
                type="password"
                className="w-full pl-8 p-2 bg-gray-800 text-white rounded"
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button className="w-full bg-indigo-600 p-2 rounded text-white">
            Register
          </button>
        </form>

        <p className="text-center text-gray-400 mt-4">
          Already have account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;