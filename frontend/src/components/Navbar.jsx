import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { LogOut, Home, Key, UserPlus, RefreshCw, Activity, ShieldCheck } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <ShieldCheck className="h-8 w-8 text-indigo-400" />
              <span className="text-xl font-bold text-white tracking-wide">True<span className="text-indigo-400">Sight</span> AI</span>
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link to="/" className="text-slate-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2">
                  <Home className="w-4 h-4" /> Analyse
                </Link>
                <Link to="/dashboard" className="text-slate-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2">
                  <Activity className="w-4 h-4" /> Dashboard
                </Link>
                <div className="w-px h-6 bg-slate-700 mx-2"></div>
                <span className="text-slate-400 text-sm">Hello, <span className="text-white font-medium">{user.username}</span></span>
                <button
                  onClick={handleLogout}
                  className="ml-4 text-red-400 hover:text-red-300 hover:bg-slate-800 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" /> Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-slate-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2">
                  <Key className="w-4 h-4" /> Login
                </Link>
                <Link to="/register" className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors shadow-lg shadow-indigo-600/30 flex items-center gap-2">
                  <UserPlus className="w-4 h-4" /> Register
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
