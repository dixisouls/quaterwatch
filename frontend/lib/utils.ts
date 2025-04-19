import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatQuarter(quarter: string, year: number): string {
  return `${quarter} ${year}`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function sentimentLabel(score: number | null): string {
  if (score === null) return "Neutral";
  if (score >= 0.25) return "Positive";
  if (score <= -0.25) return "Negative";
  return "Neutral";
}

export function sentimentColor(score: number | null): string {
  if (score === null) return "neutral";
  if (score >= 0.25) return "positive";
  if (score <= -0.25) return "negative";
  return "neutral";
}

export function confidenceLabel(score: number | null): string {
  if (score === null) return "N/A";
  if (score >= 7) return "High";
  if (score >= 4) return "Moderate";
  return "Low";
}

export function priceChange(
  from: number | null,
  to: number | null
): number | null {
  if (from === null || to === null || from === 0) return null;
  return ((to - from) / from) * 100;
}

export function formatPercent(value: number | null): string {
  if (value === null) return "N/A";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatPrice(value: number | null): string {
  if (value === null) return "N/A";
  return `$${value.toFixed(2)}`;
}
