import { createContext } from "react";

export const AUTH_LOGOUT_EVENT = "auth:logout";

export function getTokenExpiration(token) {
  if (typeof token !== "string") return null;

  const parts = token.split(".");
  if (parts.length !== 3 || parts.some((part) => !part)) return null;

  try {
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const decoded = atob(payload.padEnd(Math.ceil(payload.length / 4) * 4, "="));
    const bytes = Uint8Array.from(decoded, (character) => character.charCodeAt(0));
    const claims = JSON.parse(new TextDecoder().decode(bytes));

    return Number.isFinite(claims.exp) && claims.exp > 0
      ? claims.exp * 1000
      : null;
  } catch {
    return null;
  }
}

export function isTokenValid(token) {
  const expiration = getTokenExpiration(token);
  return expiration !== null && expiration > Date.now();
}

export const AuthContext = createContext(null);
