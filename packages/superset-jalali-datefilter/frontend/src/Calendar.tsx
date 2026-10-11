import React, { useState } from 'react';

import {
  addDays,
  compareJDate,
  g2j,
  isoFromJDate,
  j2g,
  JDate,
  MAX_YEAR,
  MIN_YEAR,
  monthLength,
  toPersianDigits,
  weekdaySat0,
} from './jalali';
import { MONTHS, STR, WEEKDAY_INITIALS } from './strings';

export type CalendarProps = {
  visible: JDate;
  onVisible: (next: JDate) => void;
  start: JDate | null;
  end: JDate | null;
  today: JDate;
  onPick: (day: JDate) => void;
};

function pad(value: JDate): string {
  return `${value.y}-${String(value.m).padStart(2, '0')}-${String(value.d).padStart(2, '0')}`;
}

function shiftMonth(visible: JDate, delta: number): JDate {
  const index = visible.y * 12 + (visible.m - 1) + delta;
  const y = Math.floor(index / 12);
  const m = (index % 12) + 1;
  if (y < MIN_YEAR || y > MAX_YEAR) return visible;
  return { y, m, d: 1 };
}

export default function Calendar(props: CalendarProps) {
  const { visible, onVisible, start, end, today, onPick } = props;
  const [focused, setFocused] = useState<JDate>(start ?? { ...visible, d: 1 });
  const length = monthLength(visible.y, visible.m);
  const lead = weekdaySat0(j2g(visible.y, visible.m, 1));
  const cells: Array<JDate | null> = [
    ...Array.from({ length: lead }, () => null),
    ...Array.from({ length }, (_, index) => ({ y: visible.y, m: visible.m, d: index + 1 })),
  ];
  while (cells.length % 7 !== 0) cells.push(null);

  function move(day: JDate, delta: number) {
    const [y, m, d] = g2j(addDays(isoFromJDate(day), delta));
    const next = { y, m, d };
    setFocused(next);
    if (y !== visible.y || m !== visible.m) onVisible({ y, m, d: 1 });
  }

  function onKey(event: React.KeyboardEvent<HTMLButtonElement>, day: JDate) {
    const delta: Record<string, number> = {
      ArrowLeft: 1,
      ArrowRight: -1,
      ArrowUp: -7,
      ArrowDown: 7,
    };
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onPick(day);
      return;
    }
    if (delta[event.key] == null) return;
    event.preventDefault();
    try {
      move(day, delta[event.key]);
    } catch {
      /* stay inside the generated table */
    }
  }

  const years: number[] = [];
  for (let year = MIN_YEAR; year <= MAX_YEAR; year += 1) years.push(year);

  return (
    <div className="jdf-calendar">
      <div className="jdf-nav">
        <button type="button" onClick={() => onVisible(shiftMonth(visible, -1))}>
          {STR.prevMonth}
        </button>
        <span>
          <select
            aria-label="ماه"
            value={visible.m}
            onChange={event => onVisible({ y: visible.y, m: Number(event.target.value), d: 1 })}
          >
            {MONTHS.map((name, index) => (
              <option key={name} value={index + 1}>{name}</option>
            ))}
          </select>
          <select
            aria-label="سال"
            value={visible.y}
            onChange={event => onVisible({ y: Number(event.target.value), m: visible.m, d: 1 })}
          >
            {years.map(year => (
              <option key={year} value={year}>{toPersianDigits(String(year))}</option>
            ))}
          </select>
        </span>
        <button type="button" onClick={() => onVisible(shiftMonth(visible, 1))}>
          {STR.nextMonth}
        </button>
      </div>
      <div className="jdf-weekdays">
        {WEEKDAY_INITIALS.map(initial => <span key={initial}>{initial}</span>)}
      </div>
      <div className="jdf-grid" role="grid">
        {cells.map((day, index) => {
          if (!day) return <span key={`e-${index}`} />;
          const edge = (start && compareJDate(day, start) === 0) || (end && compareJDate(day, end) === 0);
          const inRange = start && end && compareJDate(day, start) > 0 && compareJDate(day, end) < 0;
          const friday = weekdaySat0(isoFromJDate(day)) === 6;
          const isToday = compareJDate(day, today) === 0;
          const isFocused = compareJDate(day, focused) === 0 && day.m === visible.m;
          const className = [
            'jdf-day',
            friday ? 'jdf-day-friday' : '',
            isToday ? 'jdf-day-today' : '',
            inRange ? 'jdf-day-range' : '',
            edge ? 'jdf-day-edge' : '',
          ].filter(Boolean).join(' ');
          return (
            <button
              key={pad(day)}
              type="button"
              className={className}
              data-date={pad(day)}
              tabIndex={isFocused ? 0 : -1}
              ref={node => {
                if (isFocused && node) node.focus();
              }}
              onClick={() => {
                setFocused(day);
                onPick(day);
              }}
              onKeyDown={event => onKey(event, day)}
            >
              {toPersianDigits(String(day.d))}
            </button>
          );
        })}
      </div>
    </div>
  );
}
