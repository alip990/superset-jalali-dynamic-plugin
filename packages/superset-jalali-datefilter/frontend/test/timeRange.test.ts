import { describe, expect, it } from 'vitest';

import { PRESETS, rollingPresetForStoredValue } from '../src/presets';
import { formatAbsolute, inclusiveEnd, parseAbsolute } from '../src/timeRange';

describe('time range strings', () => {
  it('emits a half-open absolute range and parses it back', () => {
    const value = formatAbsolute('2024-09-22', '2024-10-21');
    expect(value).toBe('2024-09-22T00:00:00 : 2024-10-22T00:00:00');
    const parsed = parseAbsolute(value);
    expect(parsed).toEqual({ start: '2024-09-22', endExclusive: '2024-10-22' });
    expect(inclusiveEnd(parsed!.endExclusive)).toBe('2024-10-21');
    expect(parseAbsolute('2024-09-22 : 2024-10-22')?.endExclusive).toBe('2024-10-22');
  });

  it('round-trips every preset', () => {
    const today = '2024-10-01';
    for (const preset of PRESETS) {
      const value = preset.value(today);
      if (preset.rolling) {
        expect(rollingPresetForStoredValue(value)?.id).toBe(preset.id);
        expect(parseAbsolute(value)).toBeNull();
      } else {
        const parsed = parseAbsolute(value);
        expect(parsed, preset.id).not.toBeNull();
        expect(formatAbsolute(parsed!.start, inclusiveEnd(parsed!.endExclusive))).toBe(value);
      }
    }
  });

  it('stores Mehr 1403 as the Gregorian half-open month', () => {
    const month = PRESETS.find(preset => preset.id === 'thisMonth')!;
    expect(month.value('2024-09-22')).toBe('2024-09-22T00:00:00 : 2024-10-22T00:00:00');
  });

  it('keeps rolling preset text stable', () => {
    expect(PRESETS.find(preset => preset.id === 'last7')!.value()).toBe(
      'DATEADD(DATETIME("today"), -6, day) : DATEADD(DATETIME("today"), 1, day)',
    );
    expect(PRESETS.find(preset => preset.id === 'today')!.value()).toBe(
      'today : DATEADD(DATETIME("today"), 1, day)',
    );
    expect(PRESETS.find(preset => preset.id === 'yesterday')!.value()).toBe(
      'DATEADD(DATETIME("today"), -1, day) : today',
    );
  });
});
