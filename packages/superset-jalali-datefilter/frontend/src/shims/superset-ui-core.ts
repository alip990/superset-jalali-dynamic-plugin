/** Host @superset-ui/core singleton. getExtensionsRegistry is not a copy. */

type Registry = {
  get: (key: string) => unknown;
  set: (key: string, value: unknown) => void;
};

const host = (window as unknown as Record<string, unknown>)['__superset__/@superset-ui/core'] as
  | { default?: { getExtensionsRegistry?: () => Registry; NO_TIME_RANGE?: string }; getExtensionsRegistry?: () => Registry; NO_TIME_RANGE?: string }
  | undefined;
const core = (host && host.default) ?? host;

if (!core || typeof core.getExtensionsRegistry !== 'function') {
  throw new Error('jalali-datefilter: shared module @superset-ui/core is missing');
}

const getRegistry = core.getExtensionsRegistry.bind(core);
const noTimeRange = core.NO_TIME_RANGE ?? 'No filter';

export function getExtensionsRegistry(): Registry {
  return getRegistry();
}

export const NO_TIME_RANGE: string = noTimeRange;
