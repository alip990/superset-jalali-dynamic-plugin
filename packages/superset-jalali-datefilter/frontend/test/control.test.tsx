import React from 'react';
import { act } from 'react-dom/test-utils';
import { render, unmountComponentAtNode } from 'react-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import JalaliDateFilterControl from '../src/JalaliDateFilterControl';

let container: HTMLDivElement;

beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
});

afterEach(() => {
  unmountComponentAtNode(container);
  container.remove();
});

function renderControl(props: Partial<React.ComponentProps<typeof JalaliDateFilterControl>> = {}) {
  const onChange = vi.fn();
  act(() => {
    render(
      <JalaliDateFilterControl value="No filter" onChange={onChange} {...props} />,
      container,
    );
  });
  return onChange;
}

function click(selector: string) {
  const node = document.querySelector(selector) as HTMLElement;
  expect(node, selector).toBeTruthy();
  act(() => {
    node.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
}

describe('JalaliDateFilterControl', () => {
  it('picks an inclusive Mehr range and emits the half-open Gregorian string', () => {
    const onChange = renderControl();
    click('[data-testid="jdf-trigger"]');
    click('[data-testid="jdf-tab-custom"]');
    const year = document.querySelector('select[aria-label="سال"]') as HTMLSelectElement;
    const month = document.querySelector('select[aria-label="ماه"]') as HTMLSelectElement;
    act(() => {
      year.value = '1403';
      year.dispatchEvent(new Event('change', { bubbles: true }));
    });
    act(() => {
      month.value = '7';
      month.dispatchEvent(new Event('change', { bubbles: true }));
    });
    click('[data-date="1403-07-01"]');
    click('[data-date="1403-07-30"]');
    click('[data-testid="jdf-apply"]');
    expect(onChange).toHaveBeenCalledWith('2024-09-22T00:00:00 : 2024-10-22T00:00:00');
  });

  it('closes on Escape and returns no value', () => {
    const onChange = renderControl();
    click('[data-testid="jdf-trigger"]');
    expect(document.querySelector('[data-testid="jdf-popover"]')).toBeTruthy();
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(document.querySelector('[data-testid="jdf-popover"]')).toBeNull();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('opens a centred panel when the filter bar overflows', () => {
    renderControl({ isOverflowingFilterBar: true });
    click('[data-testid="jdf-trigger"]');
    expect(document.querySelector('[data-testid="jdf-popover"]')?.className).toContain('jdf-popover-center');
  });

  it('accepts Persian digits in the from/to fields', () => {
    const onChange = renderControl();
    click('[data-testid="jdf-trigger"]');
    click('[data-testid="jdf-tab-custom"]');
    const from = document.querySelector('[data-testid="jdf-from"]') as HTMLInputElement;
    const to = document.querySelector('[data-testid="jdf-to"]') as HTMLInputElement;
    act(() => {
      const set = (node: HTMLInputElement, value: string) => {
        const descriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
        descriptor?.set?.call(node, value);
        node.dispatchEvent(new Event('change', { bubbles: true }));
      };
      set(from, '۱۴۰۳/۰۷/۰۱');
      set(to, '۱۴۰۳/۰۷/۳۰');
    });
    click('[data-testid="jdf-apply"]');
    expect(onChange).toHaveBeenCalledWith('2024-09-22T00:00:00 : 2024-10-22T00:00:00');
  });
});
