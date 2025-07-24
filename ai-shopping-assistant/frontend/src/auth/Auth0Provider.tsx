import { Auth0Provider as Auth0ProviderBase } from '@auth0/auth0-react';
import type { ReactNode } from 'react';

// Auth0 configuration from environment variables
const domain = import.meta.env.VITE_AUTH0_DOMAIN || '';
const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID || '';
const redirectUri = import.meta.env.VITE_AUTH0_REDIRECT_URI || window.location.origin;
const audience = import.meta.env.VITE_AUTH0_AUDIENCE || '';

interface Auth0ProviderProps {
    children: ReactNode;
}

/**
 * Auth0 provider component that wraps the application
 * and provides authentication functionality
 */
export const CustomAuth0Provider = ({ children }: Auth0ProviderProps) => {
    // Handle redirect callback after authentication
    const onRedirectCallback = (appState: any) => {
        // If there's a saved return path, navigate to it
        const returnTo = localStorage.getItem('auth_return_to');
        if (returnTo) {
            localStorage.removeItem('auth_return_to');
            window.location.href = returnTo;
        }
    };

    return (
        <Auth0ProviderBase
            domain={domain}
            clientId={clientId}
            authorizationParams={{
                redirect_uri: redirectUri,
                audience: audience,
                scope: "openid profile email"
            }}
            onRedirectCallback={onRedirectCallback}
            cacheLocation="localstorage"
            // @ts-ignore
            openUrl={(url: string) => {
                console.log("🔍 ---- Authorize URL about to be called:", url);
                window.location.assign(url);
            }}
        >
            {children}
        </Auth0ProviderBase>
    );
};