import axios, { AxiosError } from "axios";
import type {
  AuthToken,
  JobStatusResponse,
  JobListItem,
  JobResults,
} from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT from localStorage on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("qw_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("qw_token");
      localStorage.removeItem("qw_user");
      window.location.href = "/auth/login";
    }
    return Promise.reject(err);
  }
);

export function getApiError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: string })?.detail;
    return detail ?? err.message ?? "An unexpected error occurred";
  }
  return "An unexpected error occurred";
}

// ── Auth ─────────────────────────────────────────────────────

export async function register(
  email: string,
  password: string,
  name?: string
): Promise<AuthToken> {
  const { data } = await api.post<AuthToken>("/api/auth/register", {
    email,
    password,
    name,
  });
  return data;
}

export async function login(
  email: string,
  password: string
): Promise<AuthToken> {
  const { data } = await api.post<AuthToken>("/api/auth/login", {
    email,
    password,
  });
  return data;
}

export async function googleAuth(code: string): Promise<AuthToken> {
  const { data } = await api.post<AuthToken>("/api/auth/google", { code });
  return data;
}

// ── Jobs ──────────────────────────────────────────────────────

export async function submitJob(
  ticker: string,
  quarter: string,
  year: number
): Promise<JobStatusResponse> {
  const { data } = await api.post<JobStatusResponse>("/api/jobs", {
    ticker,
    quarter,
    year,
  });
  return data;
}

export async function getJobStatus(
  jobId: string
): Promise<JobStatusResponse> {
  const { data } = await api.get<JobStatusResponse>(
    `/api/jobs/${jobId}/status`
  );
  return data;
}

export async function uploadTranscript(
  jobId: string,
  text: string
): Promise<JobStatusResponse> {
  const { data } = await api.put<JobStatusResponse>(
    `/api/jobs/${jobId}/transcript`,
    { text }
  );
  return data;
}

export async function getJobResults(jobId: string): Promise<JobResults> {
  const { data } = await api.get<JobResults>(`/api/jobs/${jobId}/results`);
  return data;
}

export async function listJobs(): Promise<JobListItem[]> {
  const { data } = await api.get<JobListItem[]>("/api/jobs");
  return data;
}

export default api;
