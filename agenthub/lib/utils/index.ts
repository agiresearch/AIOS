import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Generates a random 6-digit numeric ID
 * @returns string A 6-digit number as a string, padded with leading zeros if necessary
 */
export function generateSixDigitId(): number {
  // Generate a random number between 0 and 999999
  const randomNumber = Math.floor(Math.random() * 1000000);
  
  // Convert to string and pad with leading zeros if needed
  return parseInt(randomNumber.toString().padStart(6, '0'));
}
