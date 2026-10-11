/** Milestone 0 probe. Registers a red button in place of the date picker. */

export {};

const reactHost = (window as unknown as Record<string, { default?: { createElement?: (...args: unknown[]) => unknown } } & { createElement?: (...args: unknown[]) => unknown }>)['__superset__/react'];
const React = reactHost?.default ?? reactHost;
if (!React?.createElement) {
  throw new Error('jalali-datefilter: shared module react is missing');
}

const coreHost = (window as unknown as Record<string, { default?: { getExtensionsRegistry?: () => { get: (k: string) => unknown; set: (k: string, v: unknown) => void } }; getExtensionsRegistry?: () => { get: (k: string) => unknown; set: (k: string, v: unknown) => void } }>)['__superset__/@superset-ui/core'];
const core = coreHost?.default ?? coreHost;
if (typeof core?.getExtensionsRegistry !== 'function') {
  throw new Error('jalali-datefilter: shared module @superset-ui/core is missing');
}

function shape(value: unknown) {
  const record = value && typeof value === 'object' ? value as Record<string, unknown> : null;
  return {
    type: typeof value,
    hasDefault: Boolean(record && 'default' in record),
    keys: record ? Object.keys(record).slice(0, 40) : [],
  };
}

console.info('M0-2 __superset__/react', shape(reactHost));
console.info('M0-2 __superset__/@superset-ui/core', shape(coreHost));

function Hello(props: { value?: string; onChange: (value: string) => void }) {
  return React.createElement!(
    'button',
    {
      type: 'button',
      id: 'jdf-hello',
      'data-testid': 'jdf-hello',
      style: {
        background: 'red',
        color: 'white',
        border: 0,
        padding: '8px 12px',
        cursor: 'pointer',
        font: 'inherit',
      },
      onClick: () => props.onChange('2024-09-22T00:00:00 : 2024-10-22T00:00:00'),
    },
    `HELLO ${props.value ?? ''}`,
  );
}

const registry = core.getExtensionsRegistry!();
if (!registry.get('filter.dateFilterControl')) {
  registry.set('filter.dateFilterControl', Hello);
}

(window as unknown as { __JALALI_DATEFILTER__?: unknown }).__JALALI_DATEFILTER__ = {
  version: 'm0-hello',
  registered: true,
  mode: 'hello',
};
