import { useState, useEffect } from 'react';
import { useAuthContext } from '../../auth/AuthContext';
import { useAuth0 } from '@auth0/auth0-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Button } from '../ui/button';
import { ArrowLeft, User, Mail, Calendar, Shield, Clock, Key } from 'lucide-react';
import { decodeJWT, formatTimestamp, isTokenExpired, getTimeUntilExpiry } from '../../utils/jwtUtils';
import type { DecodedToken } from '../../utils/jwtUtils';

interface ProfilePageProps {
  onBack?: () => void;
}

export function ProfilePage({ onBack }: ProfilePageProps) {
  const { user } = useAuthContext();
  const { getIdTokenClaims } = useAuth0();
  const [idToken, setIdToken] = useState<DecodedToken | null>(null);
  const [rawToken, setRawToken] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIdToken = async () => {
      try {
        const tokenClaims = await getIdTokenClaims();
        if (tokenClaims && tokenClaims.__raw) {
          setRawToken(tokenClaims.__raw);
          const decoded = decodeJWT(tokenClaims.__raw);
          setIdToken(decoded);
        }
      } catch (error) {
        console.error('Error fetching ID token:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchIdToken();
  }, [getIdTokenClaims]);

  if (!user) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-muted-foreground">Please log in to view your profile.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading profile...</p>
        </div>
      </div>
    );
  }

  // Get user initials for avatar fallback
  const getInitials = () => {
    if (user.name) {
      return user.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);
    }
    return user.email ? user.email[0].toUpperCase() : 'U';
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center mb-6">
        {onBack && (
          <Button variant="ghost" size="sm" onClick={onBack} className="mr-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        )}
        <h1 className="text-3xl font-bold">Profile</h1>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* User Information Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              User Information
            </CardTitle>
            <CardDescription>
              Basic information from your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src={user.picture} alt={user.name || 'User'} />
                <AvatarFallback className="text-lg">{getInitials()}</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-lg font-semibold">{user.name || 'No name provided'}</h3>
                <p className="text-muted-foreground flex items-center gap-1">
                  <Mail className="h-4 w-4" />
                  {user.email || 'No email provided'}
                </p>
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">User ID:</span>
                <code className="text-xs bg-muted px-2 py-1 rounded font-mono">
                  {user.sub || 'N/A'}
                </code>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Last Updated:</span>
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {user.updated_at ? new Date(user.updated_at).toLocaleDateString() : 'N/A'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Marketing Consent:</span>
                <Badge variant={user.marketingConsent ? 'default' : 'secondary'}>
                  {user.marketingConsent ? 'Granted' : 'Not granted'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}