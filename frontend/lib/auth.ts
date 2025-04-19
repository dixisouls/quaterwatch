import type { User, AuthToken } from "@/types";

const TOKEN_KEY = "qw_token";
const USER_KEY = "qw_user";

export function saveSession(auth: AuthToken): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, auth.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(auth.user));
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
