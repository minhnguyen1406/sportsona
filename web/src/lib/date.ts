/**
 * Date formatting helpers.
 *
 * Backend dates come as ISO date strings (YYYY-MM-DD or full ISO datetime).
 * We parse them with ``parseISO`` rather than ``new Date(s)`` because the
 * latter interprets ``"1997-09-30"`` as UTC midnight, which shifts to the
 * previous day in negative-UTC timezones — causing silent off-by-one bugs.
 *
 * date-fns is well-tested, tree-shakeable, and the de-facto standard for
 * date formatting in modern JS apps.
 */

import { format, parseISO } from 'date-fns';

/** Short format. e.g. ``2024-09-01`` → ``"Sep 1, 2024"``. */
export function formatDate(iso: string): string {
  return format(parseISO(iso), 'MMM d, yyyy');
}

/** Long format. e.g. ``2024-09-01`` → ``"September 1, 2024"``. */
export function formatLongDate(iso: string): string {
  return format(parseISO(iso), 'MMMM d, yyyy');
}

/** With weekday. e.g. ``2024-09-01`` → ``"Sunday, September 1, 2024"``. */
export function formatFullDate(iso: string): string {
  return format(parseISO(iso), 'EEEE, MMMM d, yyyy');
}

/**
 * Parse a backend timestamp as UTC. Backend DateTime columns are naive UTC
 * and serialize without an offset (``2026-09-13T02:15:00``); ``new Date``
 * would read that as *local* time, shifting it by the user's UTC offset.
 */
export function parseUTC(iso: string): Date {
  return new Date(/[Zz]$|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);
}
