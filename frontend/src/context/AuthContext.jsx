import { useCallback, useEffect, useState } from "react";
import {
    AUTH_LOGOUT_EVENT,
    AuthContext,
    getTokenExpiration,
    isTokenValid,
} from "./auth-context";

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => {
        const storedToken = localStorage.getItem("token");
        if (isTokenValid(storedToken)) return storedToken;
        if (storedToken) localStorage.removeItem("token");
        return null;
    });

    const login = useCallback((newToken) => {
        if (!isTokenValid(newToken)) {
            throw new Error("Cannot store an invalid or expired access token");
        }
        localStorage.setItem("token", newToken);
        setToken(newToken);
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem("token");
        setToken(null);
    }, []);

    useEffect(() => {
        if (!token) return undefined;

        const expiration = getTokenExpiration(token);
        const timeoutId = window.setTimeout(
            logout,
            expiration === null ? 0 : Math.max(expiration - Date.now(), 0),
        );
        return () => window.clearTimeout(timeoutId);
    }, [token, logout]);

    useEffect(() => {
        const handleStorage = (event) => {
            if (event.key !== "token") return;
            if (isTokenValid(event.newValue)) {
                setToken(event.newValue);
            } else {
                if (event.newValue) localStorage.removeItem("token");
                setToken(null);
            }
        };

        window.addEventListener("storage", handleStorage);
        window.addEventListener(AUTH_LOGOUT_EVENT, logout);
        return () => {
            window.removeEventListener("storage", handleStorage);
            window.removeEventListener(AUTH_LOGOUT_EVENT, logout);
        };
    }, [logout]);

    return (
        <AuthContext.Provider value={{ token, login, logout, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    );
}