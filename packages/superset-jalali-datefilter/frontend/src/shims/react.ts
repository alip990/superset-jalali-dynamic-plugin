/** Host React, either a module namespace or a default export (M0-2). */

const host = (window as unknown as Record<string, unknown>)['__superset__/react'] as
  | { default?: typeof import('react'); createElement?: unknown }
  | undefined;
const React = (host && host.default) ?? host;

if (!React || typeof (React as { createElement?: unknown }).createElement !== 'function') {
  throw new Error('jalali-datefilter: shared module react is missing');
}

export default React;
export const useState = (React as typeof import('react')).useState;
export const useEffect = (React as typeof import('react')).useEffect;
export const useLayoutEffect = (React as typeof import('react')).useLayoutEffect;
export const useMemo = (React as typeof import('react')).useMemo;
export const useRef = (React as typeof import('react')).useRef;
export const useCallback = (React as typeof import('react')).useCallback;
