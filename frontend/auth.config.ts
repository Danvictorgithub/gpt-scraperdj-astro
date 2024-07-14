import type { APIRoute } from 'astro';
import { defineConfig } from 'auth-astro';
import Credentials from '@auth/core/providers/credentials';
import { SignInError } from '@auth/core/errors';
import type { JWT } from '@auth/core/jwt';
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
                username: { label: "Username", type: "text" },
                password: { label: "Password", type: "password" }
            },
            async authorize(credentials) {
                const backendUrl = import.meta.env.BACKEND_URL
                if (!backendUrl) {
                    throw new Error("Backend URL is not set")
                }
                const res = await fetch(`${backendUrl}/api/auth/login/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(credentials)
                })
                if (res.status == 200) {
                    const data: UserObj = await res.json()
                    if (data.user.is_superuser)
                        return data as any;
                    else
                        return null
                }
                else {
                    return null
                }
            }
        })
    ],
    callbacks: {
        jwt: async ({ token, user }) => {
            if (user) {
                // This is the initial sign in
                token.access = user.access;
                token.refresh = user.refresh;
                token.user = user.user;
                // Set an expiration time for the access token (e.g., 5 minutes)
                token.exp = Math.floor(Date.now() / 1000) + 16 * 60 * 60;
            } else if (Date.now() < (token.exp ?? 0) * 1000) {
                // Token hasn't expired yet, return it as is
                return token;
            } else {
                // Token has expired, try to refresh it
                return refreshAccessToken(token);
            }
            return token;
        },
        session: async ({ token, session }) => {
            session.user = token.user as any;
            session.access = token.access as string;
            session.error = token.error as string
            return session;
        },
    },
    pages: {
        signIn: '/auth/signin',
        signOut: '/logout',
        error: '/auth/signin?errorMessage=Invalid Credentials&'
    },
    events: {
    }
}
);

async function refreshAccessToken(token: JWT) {
    try {
        const backendUrl = import.meta.env.BACKEND_URL;
        if (!backendUrl) {
            throw new Error("Backend URL is not set");
        }

        const response = await fetch(`${backendUrl}/api/token/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                refresh: token.refresh,
            }),
        });

        const refreshedTokens = await response.json();

        if (!response.ok) {
            throw refreshedTokens;
        }

        return {
            ...token,
            accessToken: refreshedTokens.access,
            exp: Math.floor(Date.now() / 1000) + 5 * 60, // 5 minutes
        };
    } catch (error) {
        console.error('Error refreshing access token:', error);
        return {
            ...token,
            error: "RefreshAccessTokenError",
        };
    }
}
declare module '@auth/core/types' {
    interface User {
        access: string;
        refresh: string;
        user: UserObj
    }

    interface JWT {
        access?: string;
        refresh?: string;
        exp?: number;
        error?: string;
        user?: User;
    }

    interface Session {
        user?: User;
        access?: string;
        error?: string;
    }
}
