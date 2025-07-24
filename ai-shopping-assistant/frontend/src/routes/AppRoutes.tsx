import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthContext } from "../auth/AuthContext";
import { Layout } from "../components/layout/Layout";
import { ProfilePage } from "../components/profile/ProfilePage";
import AppContent from "../components/AppContent";

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuthContext();
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppContent />} />
      <Route 
        path="/profile" 
        element={
          <ProtectedRoute>
            <Layout>
              <ProfilePage onBack={() => window.history.back()} />
            </Layout>
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
}