import Credentials from '@auth/core/providers/credentials';
import { defineConfig } from 'auth-astro';
import axios from 'axios';

interface UserObj {
    access: string,
    refresh: string,
    user: {
        id: number,
        username: string,
        email: string,
        is_superuser: boolean
    }
}

export default defineConfig({
    providers: [
        Credentials({
            credentials: {
                email: {},
                password: {},
                username: {}
            },
            authorize: async (credentials) => {
                let backendUrl = import.meta.env.BACKEND_URL
                let { data } = await axios.post(`${backendUrl}/api/auth/login/`, credentials, {
                    validateStatus: (status) => {
                        return status === 200;
                    }
                })
                return data
            }
        })
    ],
    callbacks: {
        jwt: async ({ token, user }) => {
            if (user) {
                token.accessToken = user.access;
                token.refreshToken = user.refresh;
                token.user = user.user;
                token.exp = Date.now() + 16 * 3600 * 1000; // Set expiration to 16 hours from now
            }

            // Check if access token has expired
            if (Date.now() > token.exp) {
                try {
                    // Attempt to refresh the token
                    const backendUrl = import.meta.env.BACKEND_URL;
                    const response = await axios.post(`${backendUrl}/api/auth/token/refresh`, {
                        refresh: token.refreshToken
                    });

                    if (response.status === 200) {
                        token.accessToken = response.data.access;
                        // Optionally update refresh token if your backend provides a new one
                        // token.refreshToken = response.data.refresh;
                        token.exp = Date.now() + 16 * 3600 * 1000; // Reset expiration to 16 hours
                    } else {
                        // If refresh fails, you might want to force a re-login
                        return { ...token, error: "RefreshAccessTokenError" };
                    }
                } catch (error) {
                    console.error("Failed to refresh token", error);
                    return { ...token, error: "RefreshAccessTokenError" };
                }
            }

            return token;
        }
    }
});

declare module '@auth/core/types' {
    interface User extends UserObj { }
    interface JWT {
        accessToken?: string;
        refreshToken?: string;
        exp?: number;
        error?: string;
        user?: {
            id: number,
            username: string,
            email: string,
            is_superuser: boolean
        }
    }
}