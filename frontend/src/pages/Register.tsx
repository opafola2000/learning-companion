import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register, login } from "../api/auth";
import { useAuth } from "../contexts/AuthContext";
import AuthLayout from "../components/AuthLayout";
import { formatApiError } from "../utils/apiError";

const inputClass =
  "w-full px-4 py-2.5 border border-indigo-100 rounded-lg bg-indigo-50/40 focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none transition-shadow";

const buttonClass =
  "w-full bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 text-white py-2.5 rounded-lg font-medium hover:from-violet-700 hover:via-indigo-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-500/30";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setTokens, logout } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (password.length < 8) {
        setError("Password must be at least 8 characters.");
        return;
      }
      logout();
      await register(email, password, name);
      const data = await login(email, password);
      setTokens(data.access_token, data.refresh_token);
      navigate("/");
    } catch (err: unknown) {
      setError(formatApiError(err, "Registration failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout subtitle="Create your account to start learning">
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className={inputClass}
            placeholder="Your name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className={inputClass}
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className={inputClass}
            placeholder="At least 8 characters"
          />
        </div>

        <button type="submit" disabled={loading} className={buttonClass}>
          {loading ? "Creating account..." : "Create Account"}
        </button>

        <p className="text-center text-sm text-gray-500">
          Already have an account?{" "}
          <Link
            to="/login"
            className="text-violet-600 hover:text-indigo-700 hover:underline font-medium"
          >
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
