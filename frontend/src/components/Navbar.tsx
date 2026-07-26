import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import AppBrand from "./AppBrand";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-gradient-to-r from-violet-950 via-indigo-950 to-slate-900 border-b border-white/10 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center gap-8">
            <Link to="/" className="hover:opacity-90 transition-opacity">
              <AppBrand variant="nav" />
            </Link>
            {user && (
              <div className="hidden sm:flex gap-6">
                <Link
                  to="/"
                  className="text-indigo-100 hover:text-amber-300 font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/progress"
                  className="text-indigo-100 hover:text-amber-300 font-medium transition-colors"
                >
                  Progress
                </Link>
              </div>
            )}
          </div>
          {user && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-indigo-100/80">Hi, {user.name}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-indigo-100 hover:text-amber-300 font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
