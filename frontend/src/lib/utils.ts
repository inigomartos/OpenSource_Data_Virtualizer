import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, currency = 'EUR'): string {
  if (Math.abs(value) >= 1_000_000) {
    return new Intl.NumberFormat('en', {
      style: 'currency',
      currency,
      maximumFractionDigits: 1,
    }).format(value / 1_000_000) + 'M';
  }
  if (Math.abs(value) >= 1_000) {
    return new Intl.NumberFormat('en', {
      style: 'currency',
      currency,
      maximumFractionDigits: 1,
    }).format(value / 1_000) + 'K';
  }
  return new Intl.NumberFormat('en', {
    style: 'currency',
    currency,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en').format(value);
}
