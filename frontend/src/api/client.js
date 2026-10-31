import axios from "axios";
import {
    AUTH_LOGOUT_EVENT,
    AUTH_TOKEN_REFRESH_EVENT,
} from "../context/auth-context";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const client = axios.create({ baseURL, withCredentials: true });
let refreshInFlight = null;

function clearStoredAuth() {
    localStorage.removeItem("token");
}

export function refreshAccessToken() {
    if (refreshInFlight) return refreshInFlight;
    refreshInFlight = axios.post(`${baseURL}/auth/refresh`, {}, { withCredentials: true })
        .then(({ data }) => {
            localStorage.setItem("token", data.access_token);
            window.dispatchEvent(new CustomEvent(AUTH_TOKEN_REFRESH_EVENT, { detail: data.access_token }));
            return data.access_token;
        })
        .finally(() => { refreshInFlight = null; });
    return refreshInFlight;
}

client.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

client.interceptors.response.use(
    (response) => response,
    async (error) => {
        const config = error.config;
        const authPath = /\/auth\/(login|register|refresh|logout)(?:\?|$)/.test(config?.url || "");
        if (error.response?.status !== 401 || authPath || !config || config._authRetry) {
            return Promise.reject(error);
        }

        config._authRetry = true;
        try {
            const accessToken = await refreshAccessToken();
            config.headers.Authorization = `Bearer ${accessToken}`;
            return client(config);
        } catch {
            clearStoredAuth();
            window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT));
            return Promise.reject(error);
        }
    },
);

export default client;
