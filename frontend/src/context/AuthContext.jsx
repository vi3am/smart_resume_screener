import { useCallback, useEffect, useState } from "react";
import client, { refreshAccessToken } from "../api/client";
import {
    AUTH_LOGOUT_EVENT,
    AUTH_TOKEN_REFRESH_EVENT,
    AuthContext,
    getTokenExpiration,
    isTokenValid,
} from "./auth-context";

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => {
        const storedToken = localStorage.getItem("token");
        return isTokenValid(storedToken) ? storedToken : null;
    });

    const login = useCallback((newToken) => {
        if (!isTokenValid(newToken)) {
            throw new Error("Cannot store an invalid access token");
        }
        localStorage.setItem("token", newToken);
        setToken(newToken);
    }, []);

    const logout = useCallback(() => {
        void client.post("/auth/logout", {}, { withCredentials: true }).catch(() => {});
        localStorage.removeItem("token");
        setToken(null);
    }, []);

    useEffect(() => {
        if (!token) {
            if (localStorage.getItem("token")) refreshAccessToken().catch(logout);
            return undefined;
        }

        const expiration = getTokenExpiration(token);
        if (expiration === null) return undefined;
        const delay = Math.max(expiration - Date.now() - 60_000, 0);
        const timeoutId = window.setTimeout(() => refreshAccessToken().catch(logout), delay);
        return () => window.clearTimeout(timeoutId);
    }, [token, logout]);

    useEffect(() => {
        const handleStorage = (event) => {
            if (event.key !== "token") return;
            if (isTokenValid(event.newValue)) {
                setToken(event.newValue);
            } else {
                setToken(null);
            }
        };
        const handleTokenRefresh = (event) => {
            if (isTokenValid(event.detail)) setToken(event.detail);
        };

        window.addEventListener("storage", handleStorage);
        window.addEventListener(AUTH_LOGOUT_EVENT, logout);
        window.addEventListener(AUTH_TOKEN_REFRESH_EVENT, handleTokenRefresh);
        return () => {
            window.removeEventListener("storage", handleStorage);
            window.removeEventListener(AUTH_LOGOUT_EVENT, logout);
            window.removeEventListener(AUTH_TOKEN_REFRESH_EVENT, handleTokenRefresh);
        };
    }, [logout]);

    return (
        <AuthContext.Provider value={{ token, login, logout, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    );
}
