/** Jalali conversion. UTC date arithmetic only; the table is the one source. */

import { NOWRUZ } from './nowruz.generated';

export { NOWRUZ };

const DIGITS: Record<string, string> = {
  '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
  '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
  '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
  '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
};

const YEARS = Object.keys(NOWRUZ).map(Number).sort((a, b) => a - b);
export const MIN_YEAR = YEARS[0];
export const SENTINEL_YEAR = YEARS[YEARS.length - 1];
export const MAX_YEAR = SENTINEL_YEAR - 1;

const EPOCH: Record<number, number> = {};
YEARS.forEach(year => {
  EPOCH[year] = utc(NOWRUZ[year]);
});

export function utc(iso: string): number {
  const [year, month, day] = iso.split('-').map(Number);
  return Date.UTC(year, month - 1, day);
}

export function isoFromUtc(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

export function addDays(iso: string, days: number): string {
  const [year, month, day] = iso.split('-').map(Number);
  return isoFromUtc(Date.UTC(year, month - 1, day + days));
}

export function compareIso(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

export function monthLength(jy: number, jm: number): number {
  if (jy < MIN_YEAR || jy > MAX_YEAR) {
    throw new Error(`jalali-datefilter: year ${jy} is outside ${MIN_YEAR}..${MAX_YEAR}`);
  }
  if (jm < 1 || jm > 12) {
    throw new Error(`jalali-datefilter: invalid month ${jm}`);
  }
  if (jm <= 6) return 31;
  if (jm <= 11) return 30;
  return Math.round((EPOCH[jy + 1] - EPOCH[jy]) / 86400000) - 336;
}

export function g2j(iso: string): [number, number, number] {
  const ms = utc(iso);
  if (ms < EPOCH[MIN_YEAR] || ms >= EPOCH[SENTINEL_YEAR]) {
    throw new Error(`jalali-datefilter: ${iso} is outside the Jalali table`);
  }
  let lo = 0;
  let hi = YEARS.length - 2;
  while (lo < hi) {
    const mid = Math.floor((lo + hi + 1) / 2);
    if (EPOCH[YEARS[mid]] <= ms) lo = mid;
    else hi = mid - 1;
  }
  const jy = YEARS[lo];
  const doy = Math.round((ms - EPOCH[jy]) / 86400000);
  if (doy < 186) return [jy, Math.floor(doy / 31) + 1, (doy % 31) + 1];
  return [jy, Math.floor((doy - 186) / 30) + 7, ((doy - 186) % 30) + 1];
}

export function j2g(jy: number, jm: number, jd: number): string {
  const length = monthLength(jy, jm);
  if (jd < 1 || jd > length) {
    throw new Error(`jalali-datefilter: invalid date ${jy}/${jm}/${jd}`);
  }
  const doy = jm <= 6 ? (jm - 1) * 31 + (jd - 1) : 186 + (jm - 7) * 30 + (jd - 1);
  return isoFromUtc(EPOCH[jy] + doy * 86400000);
}

export function normalizeDigits(text: string): string {
  return text.replace(/[۰-۹٠-٩]/g, ch => DIGITS[ch] ?? ch);
}

export function parseJalali(text: string): [number, number, number] {
  const match = normalizeDigits(text.trim()).match(/^(\d{4})[-/](\d{2})[-/](\d{2})$/);
  if (!match) throw new Error(`jalali-datefilter: invalid Jalali date ${text}`);
  const jy = Number(match[1]);
  const jm = Number(match[2]);
  const jd = Number(match[3]);
  j2g(jy, jm, jd);
  return [jy, jm, jd];
}

export function formatJalali(jy: number, jm: number, jd: number, sep = '/'): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${jy}${sep}${pad(jm)}${sep}${pad(jd)}`;
}

export function toPersianDigits(text: string): string {
  return text.replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[Number(d)]);
}

export function tehranTodayIso(): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Tehran',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const pick = (type: string) => parts.find(part => part.type === type)?.value ?? '';
  return `${pick('year')}-${pick('month')}-${pick('day')}`;
}

/** Python Monday=0. This returns Saturday=0 … Friday=6 for a Gregorian ISO date. */
export function weekdaySat0(iso: string): number {
  const [year, month, day] = iso.split('-').map(Number);
  const dow = new Date(Date.UTC(year, month - 1, day)).getUTCDay();
  return (dow + 1) % 7;
}

export type JDate = { y: number; m: number; d: number };

export function jDateFromIso(iso: string): JDate {
  const [y, m, d] = g2j(iso);
  return { y, m, d };
}

export function isoFromJDate(value: JDate): string {
  return j2g(value.y, value.m, value.d);
}

export function compareJDate(left: JDate, right: JDate): number {
  return left.y - right.y || left.m - right.m || left.d - right.d;
}

export function addJalaliMonths(value: JDate, delta: number): JDate {
  const index = value.y * 12 + (value.m - 1) + delta;
  const y = Math.floor(index / 12);
  const m = (index % 12) + 1;
  const d = Math.min(value.d, monthLength(y, m));
  return { y, m, d };
}
