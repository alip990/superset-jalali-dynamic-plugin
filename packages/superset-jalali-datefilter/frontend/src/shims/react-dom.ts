/** Host react-dom. createPortal is the only surface the picker needs. */

const host = (window as unknown as Record<string, unknown>)['__superset__/react-dom'] as
  | { default?: { createPortal?: typeof import('react-dom').createPortal }; createPortal?: typeof import('react-dom').createPortal }
  | undefined;
const ReactDOM = (host && host.default) ?? host;

if (!ReactDOM || typeof ReactDOM.createPortal !== 'function') {
  throw new Error('jalali-datefilter: shared module react-dom is missing');
}

export const createPortal = ReactDOM.createPortal.bind(ReactDOM);
export default ReactDOM;
