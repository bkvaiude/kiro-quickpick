import { ReactNode } from 'react';
import { useAuthContext } from './AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Protected route component that redirects to login if not authenticated
 */
export const ProtectedRoute = ({ 
  children, 
  fallback = <div>Please log in to access this page</div> 
}: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuthContext();
  
  // Show loading state
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  // Show fallback if not authenticated
  if (!isAuthenticated) {
    return <>{fallback}</>;
  }
  
  // Show children if authenticated
  return <>{children}</>;
};