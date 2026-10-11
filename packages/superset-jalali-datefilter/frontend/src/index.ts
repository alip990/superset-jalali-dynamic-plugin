import { getExtensionsRegistry } from '@superset-ui/core';

import JalaliDateFilterControl from './JalaliDateFilterControl';

declare const __VERSION__: string;

const registry = getExtensionsRegistry();
if (!registry.get('filter.dateFilterControl')) {
  registry.set('filter.dateFilterControl', JalaliDateFilterControl);
}

(window as unknown as { __JALALI_DATEFILTER__?: unknown }).__JALALI_DATEFILTER__ = {
  version: __VERSION__,
  registered: true,
};
