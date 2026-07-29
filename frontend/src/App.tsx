import { Routes, Route, Navigate, useSearchParams } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "./contexts/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import CurriculumView from "./pages/CurriculumView";
import Quiz from "./pages/Quiz";
import Progress from "./pages/Progress";

export default function App() {
  const { user, logout } = useAuth();
  const [params] = useSearchParams();
  const switchAccount = params.get("switch") === "1";

  useEffect(() => {
    if (switchAccount) {
      logout();
    }
  }, [switchAccount, logout]);

  const showAuthedShell = Boolean(user) && !switchAccount;

  return (
    <div className="min-h-screen bg-gray-50">
      {showAuthedShell && <Navbar />}
      <Routes>
        <Route
          path="/login"
          element={showAuthedShell ? <Navigate to="/" replace /> : <Login />}
        />
        <Route
          path="/register"
          element={showAuthedShell ? <Navigate to="/" replace /> : <Register />}
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/curriculum/:id"
          element={
            <ProtectedRoute>
              <CurriculumView />
            </ProtectedRoute>
          }
        />
        <Route
          path="/quiz/:topicId"
          element={
            <ProtectedRoute>
              <Quiz />
            </ProtectedRoute>
          }
        />
        <Route
          path="/progress"
          element={
            <ProtectedRoute>
              <Progress />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
