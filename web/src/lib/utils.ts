import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * shadcn-svelte's standard class-merging helper.
 * Combines clsx (conditional) with tailwind-merge (de-duplicates conflicting Tailwind classes).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
