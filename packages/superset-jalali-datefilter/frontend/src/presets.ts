/** Rolling presets keep a Superset expression. Calendar presets freeze Asia/Tehran today. */

import { addDays, g2j, j2g, tehranTodayIso, weekdaySat0 } from './jalali';
import { STR } from './strings';
import { formatAbsolute } from './timeRange';

export type Preset = {
  id: string;
  label: string;
  rolling: boolean;
  value: (todayIso?: string) => string;
};

function day(todayIso?: string): string {
  return todayIso ?? tehranTodayIso();
}

function seasonIndex(month: number): number {
  return Math.floor((month - 1) / 3);
}

function seasonBounds(year: number, season: number): [string, string] {
  const startMonth = season * 3 + 1;
  const start = j2g(year, startMonth, 1);
  const endExclusive = season === 3 ? j2g(year + 1, 1, 1) : j2g(year, startMonth + 3, 1);
  return [start, addDays(endExclusive, -1)];
}

export const PRESETS: Preset[] = [
  {
    id: 'today',
    label: STR.today,
    rolling: true,
    value: () => 'today : DATEADD(DATETIME("today"), 1, day)',
  },
  {
    id: 'yesterday',
    label: STR.yesterday,
    rolling: true,
    value: () => 'DATEADD(DATETIME("today"), -1, day) : today',
  },
  {
    id: 'last7',
    label: STR.last7,
    rolling: true,
    value: () => 'DATEADD(DATETIME("today"), -6, day) : DATEADD(DATETIME("today"), 1, day)',
  },
  {
    id: 'last30',
    label: STR.last30,
    rolling: true,
    value: () => 'DATEADD(DATETIME("today"), -29, day) : DATEADD(DATETIME("today"), 1, day)',
  },
  {
    id: 'last90',
    label: STR.last90,
    rolling: true,
    value: () => 'DATEADD(DATETIME("today"), -89, day) : DATEADD(DATETIME("today"), 1, day)',
  },
  {
    id: 'thisWeek',
    label: STR.thisWeek,
    rolling: false,
    value: todayIso => {
      const current = day(todayIso);
      const start = addDays(current, -weekdaySat0(current));
      return formatAbsolute(start, addDays(start, 6));
    },
  },
  {
    id: 'thisMonth',
    label: STR.thisMonth,
    rolling: false,
    value: todayIso => {
      const [jy, jm] = g2j(day(todayIso));
      const endExclusive = jm === 12 ? j2g(jy + 1, 1, 1) : j2g(jy, jm + 1, 1);
      return formatAbsolute(j2g(jy, jm, 1), addDays(endExclusive, -1));
    },
  },
  {
    id: 'lastMonth',
    label: STR.lastMonth,
    rolling: false,
    value: todayIso => {
      const [jy, jm] = g2j(day(todayIso));
      const py = jm === 1 ? jy - 1 : jy;
      const pm = jm === 1 ? 12 : jm - 1;
      return formatAbsolute(j2g(py, pm, 1), addDays(j2g(jy, jm, 1), -1));
    },
  },
  {
    id: 'thisSeason',
    label: STR.thisSeason,
    rolling: false,
    value: todayIso => {
      const [jy, jm] = g2j(day(todayIso));
      const [start, end] = seasonBounds(jy, seasonIndex(jm));
      return formatAbsolute(start, end);
    },
  },
  {
    id: 'lastSeason',
    label: STR.lastSeason,
    rolling: false,
    value: todayIso => {
      const [jy, jm] = g2j(day(todayIso));
      const current = seasonIndex(jm);
      const year = current === 0 ? jy - 1 : jy;
      const season = current === 0 ? 3 : current - 1;
      const [start, end] = seasonBounds(year, season);
      return formatAbsolute(start, end);
    },
  },
  {
    id: 'thisYear',
    label: STR.thisYear,
    rolling: false,
    value: todayIso => {
      const [jy] = g2j(day(todayIso));
      return formatAbsolute(j2g(jy, 1, 1), addDays(j2g(jy + 1, 1, 1), -1));
    },
  },
  {
    id: 'lastYear',
    label: STR.lastYear,
    rolling: false,
    value: todayIso => {
      const [jy] = g2j(day(todayIso));
      return formatAbsolute(j2g(jy - 1, 1, 1), addDays(j2g(jy, 1, 1), -1));
    },
  },
];

export function presetById(id: string): Preset | undefined {
  return PRESETS.find(preset => preset.id === id);
}

export function presetForStoredValue(value: string, todayIso?: string): Preset | undefined {
  const trimmed = value.trim();
  return PRESETS.find(preset => preset.value(todayIso) === trimmed);
}

export function rollingPresetForStoredValue(value: string): Preset | undefined {
  const trimmed = value.trim();
  return PRESETS.find(preset => preset.rolling && preset.value() === trimmed);
}
