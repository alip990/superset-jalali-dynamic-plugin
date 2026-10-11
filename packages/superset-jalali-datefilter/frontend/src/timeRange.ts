/** Superset time-range strings. Absolute ranges are half-open; the UI is inclusive. */

import { addDays, g2j, j2g, toPersianDigits } from './jalali';
import { STR } from './strings';

export const NO_FILTER = 'No filter';

const ABSOLUTE = /^(\d{4}-\d{2}-\d{2})(?:T00:00:00)?\s*:\s*(\d{4}-\d{2}-\d{2})(?:T00:00:00)?$/;

export type ParsedRange =
  | { kind: 'none' }
  | { kind: 'preset'; id: string }
  | { kind: 'absolute'; start: string; endExclusive: string }
  | { kind: 'advanced'; raw: string };

export function formatAbsolute(startIso: string, endInclusiveIso: string): string {
  const endExclusive = addDays(endInclusiveIso, 1);
  return `${startIso}T00:00:00 : ${endExclusive}T00:00:00`;
}

export function parseAbsolute(value: string): { start: string; endExclusive: string } | null {
  const match = value.trim().match(ABSOLUTE);
  if (!match) return null;
  return { start: match[1], endExclusive: match[2] };
}

export function inclusiveEnd(endExclusiveIso: string): string {
  return addDays(endExclusiveIso, -1);
}

export function formatTrigger(value: string | undefined, presetLabel: (id: string) => string | undefined): string {
  if (!value || value === NO_FILTER) return STR.noFilter;
  const preset = presetLabel(value);
  if (preset) return preset;
  const absolute = parseAbsolute(value);
  if (!absolute) return value;
  try {
    const [sy, sm, sd] = g2j(absolute.start);
    const [ey, em, ed] = g2j(inclusiveEnd(absolute.endExclusive));
    const pad = (n: number) => String(n).padStart(2, '0');
    const start = toPersianDigits(`${sy}/${pad(sm)}/${pad(sd)}`);
    const end = toPersianDigits(`${ey}/${pad(em)}/${pad(ed)}`);
    return `${start} تا ${end}`;
  } catch {
    return value;
  }
}

export function jalaliDayToIso(jy: number, jm: number, jd: number): string {
  return j2g(jy, jm, jd);
}
