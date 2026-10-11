import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import { g2j, j2g, monthLength, NOWRUZ, parseJalali } from '../src/jalali';

const fixture = JSON.parse(
  readFileSync(join(dirname(fileURLToPath(import.meta.url)), 'fixtures/days.json'), 'utf8'),
) as Array<{ g: string; jy: number; jm: number; jd: number }>;

function div(a: number, b: number): number {
  return Math.trunc(a / b);
}

function mod(a: number, b: number): number {
  return a - div(a, b) * b;
}

/** Inline port of the public jalaali-js conversion, used only as a parity check. */
function jalaaliToGregorian(jy: number, jm: number, jd: number): string {
  const breaks = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];
  const gy = jy + 621;
  let leapJ = -14;
  let jp = breaks[0];
  let jump = 0;
  for (let i = 1; i < breaks.length; i += 1) {
    const jmBreak = breaks[i];
    jump = jmBreak - jp;
    if (jy < jmBreak) break;
    leapJ += div(jump, 33) * 8 + div(mod(jump, 33), 4);
    jp = jmBreak;
  }
  let n = jy - jp;
  leapJ += div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
  if (mod(jump, 33) === 4 && jump - n === 4) leapJ += 1;
  const leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
  const march = 20 + leapJ - leapG;

  function g2d(year: number, month: number, day: number): number {
    let days = div((year + div(month - 8, 6) + 100100) * 1461, 4)
      + div(153 * mod(month + 9, 12) + 2, 5)
      + day - 34840408;
    days = days - div(div(year + 100100 + div(month - 8, 6), 100) * 3, 4) + 752;
    return days;
  }

  function d2g(jdn: number): string {
    let j = 4 * jdn + 139361631;
    j += div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
    const i = div(mod(j, 1461), 4) * 5 + 308;
    const day = div(mod(i, 153), 5) + 1;
    const month = mod(div(i, 153), 12) + 1;
    const year = div(j, 1461) - 100100 + div(8 - month, 6);
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${year}-${pad(month)}-${pad(day)}`;
  }

  const jdn = g2d(gy, 3, march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
  return d2g(jdn);
}

describe('jalali table parity', () => {
  it('matches the Python fixture', () => {
    expect(fixture.length).toBeGreaterThan(10000);
    for (const row of fixture) {
      expect(g2j(row.g)).toEqual([row.jy, row.jm, row.jd]);
      expect(j2g(row.jy, row.jm, row.jd)).toBe(row.g);
    }
  });

  it('agrees with jalaali-js on 1 Farvardin for 1350..1551', () => {
    for (let year = 1350; year <= 1551; year += 1) {
      expect(jalaaliToGregorian(year, 1, 1)).toBe(NOWRUZ[year]);
    }
  });

  it('accepts the 1403 leap day and rejects 1404/12/30', () => {
    expect(monthLength(1403, 12)).toBe(30);
    expect(j2g(1403, 12, 30)).toBe('2025-03-20');
    expect(monthLength(1404, 12)).toBe(29);
    expect(() => j2g(1404, 12, 30)).toThrow(/invalid date/);
  });

  it('parses Persian and Arabic digits', () => {
    expect(parseJalali('۱۴۰۳/۰۷/۰۱')).toEqual([1403, 7, 1]);
    expect(parseJalali('١٤٠٣-٠٧-٠١')).toEqual([1403, 7, 1]);
    expect(j2g(1403, 7, 1)).toBe('2024-09-22');
  });
});
