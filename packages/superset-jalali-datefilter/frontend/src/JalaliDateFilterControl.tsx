import React, { useMemo, useRef, useState } from 'react';

import Calendar from './Calendar';
import {
  compareJDate,
  formatJalali,
  isoFromJDate,
  JDate,
  jDateFromIso,
  parseJalali,
  tehranTodayIso,
  toPersianDigits,
} from './jalali';
import Popover from './Popover';
import { PRESETS, presetForStoredValue, rollingPresetForStoredValue } from './presets';
import { ensureStyles } from './styles';
import { STR } from './strings';
import { formatAbsolute, formatTrigger, inclusiveEnd, NO_FILTER, parseAbsolute } from './timeRange';

export type DateFilterControlProps = {
  value?: string;
  name?: string;
  onChange: (value: string) => void;
  onOpenPopover?: () => void;
  onClosePopover?: () => void;
  isOverflowingFilterBar?: boolean;
};

type Tab = 'presets' | 'custom' | 'advanced' | 'none';

function formatField(day: JDate | null): string {
  if (!day) return '';
  return toPersianDigits(formatJalali(day.y, day.m, day.d));
}

function readField(text: string): JDate {
  const [y, m, d] = parseJalali(text);
  return { y, m, d };
}

export default function JalaliDateFilterControl(props: DateFilterControlProps) {
  const { value, name, onChange, onOpenPopover, onClosePopover, isOverflowingFilterBar = false } = props;
  const trigger = useRef<HTMLButtonElement | null>(null);
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>('presets');
  const [presetId, setPresetId] = useState<string | null>(null);
  const [start, setStart] = useState<JDate | null>(null);
  const [end, setEnd] = useState<JDate | null>(null);
  const [fromText, setFromText] = useState('');
  const [toText, setToText] = useState('');
  const [visible, setVisible] = useState<JDate>({ y: 1403, m: 7, d: 1 });
  const [advanced, setAdvanced] = useState('');
  const [error, setError] = useState('');

  const today = useMemo(() => jDateFromIso(tehranTodayIso()), [open]);
  const label = formatTrigger(value, stored => rollingPresetForStoredValue(stored)?.label
    ?? presetForStoredValue(stored)?.label);

  function close() {
    setOpen(false);
    onClosePopover?.();
    trigger.current?.focus();
  }

  function openPopover() {
    ensureStyles();
    const stored = value || NO_FILTER;
    const rolling = rollingPresetForStoredValue(stored);
    const matched = presetForStoredValue(stored);
    const absolute = parseAbsolute(stored);
    setError('');
    if (!stored || stored === NO_FILTER) {
      setTab('none');
      setPresetId(null);
      setStart(null);
      setEnd(null);
    } else if (rolling || (matched && matched.rolling)) {
      setTab('presets');
      setPresetId((rolling ?? matched)!.id);
    } else if (absolute) {
      setTab('custom');
      setPresetId(matched && !matched.rolling ? matched.id : null);
      try {
        const nextStart = jDateFromIso(absolute.start);
        const nextEnd = jDateFromIso(inclusiveEnd(absolute.endExclusive));
        setStart(nextStart);
        setEnd(nextEnd);
        setFromText(formatField(nextStart));
        setToText(formatField(nextEnd));
        setVisible({ y: nextStart.y, m: nextStart.m, d: 1 });
      } catch {
        setTab('advanced');
        setAdvanced(stored);
      }
    } else {
      setTab('advanced');
      setAdvanced(stored);
      setPresetId(null);
    }
    if (!absolute) setVisible({ y: today.y, m: today.m, d: 1 });
    setOpen(true);
    onOpenPopover?.();
  }

  function pick(day: JDate) {
    setError('');
    if (!start || (start && end)) {
      setStart(day);
      setEnd(null);
      setFromText(formatField(day));
      setToText('');
      return;
    }
    if (compareJDate(day, start) < 0) {
      setEnd(start);
      setStart(day);
      setFromText(formatField(day));
      setToText(formatField(start));
      return;
    }
    setEnd(day);
    setToText(formatField(day));
  }

  function syncText(which: 'from' | 'to', text: string) {
    if (which === 'from') setFromText(text);
    else setToText(text);
    if (!text.trim()) return;
    try {
      const day = readField(text);
      setError('');
      if (which === 'from') {
        setStart(day);
        setVisible({ y: day.y, m: day.m, d: 1 });
      } else setEnd(day);
    } catch {
      setError(STR.errorInvalid);
    }
  }

  function apply() {
    if (tab === 'none') {
      onChange(NO_FILTER);
      close();
      return;
    }
    if (tab === 'presets') {
      const preset = PRESETS.find(item => item.id === presetId);
      if (!preset) {
        setError(STR.errorInvalid);
        return;
      }
      onChange(preset.value());
      close();
      return;
    }
    if (tab === 'advanced') {
      if (!advanced.trim()) {
        setError(STR.errorInvalid);
        return;
      }
      onChange(advanced.trim());
      close();
      return;
    }
    try {
      const nextStart = fromText.trim() ? readField(fromText) : start;
      const nextEnd = toText.trim() ? readField(toText) : end;
      if (!nextStart || !nextEnd) {
        setError(STR.errorInvalid);
        return;
      }
      if (compareJDate(nextEnd, nextStart) < 0) {
        setError(STR.errorOrder);
        return;
      }
      onChange(formatAbsolute(isoFromJDate(nextStart), isoFromJDate(nextEnd)));
      close();
    } catch (err) {
      const message = err instanceof Error && err.message.includes('outside')
        ? STR.errorRange
        : STR.errorInvalid;
      setError(message);
    }
  }

  ensureStyles();
  const shown = label;
  return (
    <div className="jdf-control" data-name={name || 'time_range'}>
      <button
        ref={trigger}
        type="button"
        className="jdf-trigger"
        data-testid="jdf-trigger"
        title={value && value !== shown ? value : undefined}
        onClick={() => (open ? close() : openPopover())}
      >
        {shown}
      </button>
      <Popover open={open} anchor={trigger.current} overflow={isOverflowingFilterBar} onClose={close}>
        <div className="jdf-tabs" role="tablist">
          {([
            ['presets', STR.presets],
            ['custom', STR.custom],
            ['advanced', STR.advanced],
            ['none', STR.noFilter],
          ] as Array<[Tab, string]>).map(([id, text]) => (
            <button
              key={id}
              type="button"
              className="jdf-tab"
              role="tab"
              data-testid={`jdf-tab-${id}`}
              aria-selected={tab === id}
              onClick={() => { setTab(id); setError(''); }}
            >
              {text}
            </button>
          ))}
        </div>
        {tab === 'presets' && (
          <div>
            <div className="jdf-presets">
              {PRESETS.map(preset => (
                <button
                  key={preset.id}
                  type="button"
                  className="jdf-preset"
                  data-testid={`jdf-preset-${preset.id}`}
                  aria-pressed={presetId === preset.id}
                  onClick={() => setPresetId(preset.id)}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <p className="jdf-hint">{STR.hintRolling}</p>
          </div>
        )}
        {tab === 'custom' && (
          <div>
            <Calendar
              visible={visible}
              onVisible={setVisible}
              start={start}
              end={end}
              today={today}
              onPick={pick}
            />
            <div className="jdf-fields">
              <label>
                {STR.from}
                <input
                  data-testid="jdf-from"
                  value={fromText}
                  onChange={event => syncText('from', event.target.value)}
                />
              </label>
              <label>
                {STR.to}
                <input
                  data-testid="jdf-to"
                  value={toText}
                  onChange={event => syncText('to', event.target.value)}
                />
              </label>
            </div>
          </div>
        )}
        {tab === 'advanced' && (
          <div className="jdf-advanced">
            <label htmlFor="jdf-advanced-input">{STR.advancedLabel}</label>
            <textarea
              id="jdf-advanced-input"
              data-testid="jdf-advanced"
              value={advanced}
              onChange={event => setAdvanced(event.target.value)}
            />
          </div>
        )}
        {tab === 'none' && <p className="jdf-none">{STR.noFilter}</p>}
        {error && <p className="jdf-error" data-testid="jdf-error">{error}</p>}
        <div className="jdf-actions">
          <button type="button" onClick={close}>{STR.cancel}</button>
          <button type="button" className="jdf-apply" data-testid="jdf-apply" onClick={apply}>
            {STR.apply}
          </button>
        </div>
      </Popover>
    </div>
  );
}
