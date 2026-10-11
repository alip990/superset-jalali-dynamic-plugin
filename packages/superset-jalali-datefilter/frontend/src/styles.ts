/** Scoped rules, injected once. The filter bar font is inherited. */

const CSS = `
.jdf-trigger {
  appearance: none;
  width: 100%;
  min-height: 32px;
  padding: 4px 10px;
  border: 1px solid #c4b8a5;
  border-radius: 6px;
  background: #fffdf8;
  color: #2b241c;
  font: inherit;
  text-align: right;
  cursor: pointer;
}
.jdf-trigger:focus {
  outline: 2px solid #c47b2b;
  outline-offset: 1px;
}
.jdf-popover {
  position: fixed;
  z-index: 1100;
  width: min(420px, calc(100vw - 16px));
  max-height: min(560px, calc(100vh - 16px));
  overflow: auto;
  padding: 12px;
  border: 1px solid #e4d7c4;
  border-radius: 12px;
  background: #fffdf8;
  color: #2b241c;
  box-shadow: 0 16px 40px rgba(60, 40, 10, 0.18);
  font: inherit;
  direction: rtl;
}
.jdf-popover-center {
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(440px, calc(100vw - 24px));
}
.jdf-tabs, .jdf-presets, .jdf-nav, .jdf-actions, .jdf-fields {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.jdf-tabs { margin-bottom: 10px; }
.jdf-tab, .jdf-preset, .jdf-nav button, .jdf-actions button, .jdf-day {
  font: inherit;
  cursor: pointer;
}
.jdf-tab, .jdf-preset, .jdf-nav button {
  border: 1px solid transparent;
  background: transparent;
  color: inherit;
  border-radius: 999px;
  padding: 4px 10px;
}
.jdf-tab[aria-selected="true"], .jdf-preset[aria-pressed="true"] {
  background: #f4e2c4;
  border-color: #e0c28a;
}
.jdf-hint, .jdf-error, .jdf-advanced label {
  display: block;
  margin: 8px 0;
  font-size: 0.85em;
  line-height: 1.6;
}
.jdf-hint { color: #6d5c48; }
.jdf-error { color: #9c2f2f; }
.jdf-weekdays, .jdf-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.jdf-weekdays span, .jdf-day {
  text-align: center;
  padding: 6px 0;
}
.jdf-weekdays span { color: #6d5c48; font-size: 0.8em; }
.jdf-day {
  border: 0;
  background: transparent;
  border-radius: 8px;
  color: inherit;
}
.jdf-day:hover, .jdf-day:focus { background: #f6ecdc; outline: none; }
.jdf-day-friday { color: #9c2f2f; }
.jdf-day-today { box-shadow: inset 0 0 0 1px #c47b2b; }
.jdf-day-range { background: #f8ead3; border-radius: 0; }
.jdf-day-edge { background: #c47b2b; color: #fffdf8; }
.jdf-day-edge.jdf-day-friday { color: #fffdf8; }
.jdf-nav, .jdf-actions { justify-content: space-between; align-items: center; margin: 8px 0; }
.jdf-nav select, .jdf-fields input, .jdf-advanced textarea {
  font: inherit;
  border: 1px solid #c4b8a5;
  border-radius: 6px;
  background: white;
  color: inherit;
  padding: 4px 8px;
}
.jdf-fields { align-items: center; }
.jdf-fields input { width: 8.5em; }
.jdf-advanced textarea { width: 100%; min-height: 88px; resize: vertical; }
.jdf-actions button {
  border-radius: 8px;
  padding: 6px 14px;
  border: 1px solid #c4b8a5;
  background: white;
}
.jdf-apply { background: #2b241c !important; color: #fffdf8; border-color: #2b241c !important; }
.jdf-none { padding: 12px 0 4px; }
`;

let injected = false;

export function ensureStyles(): void {
  if (injected || typeof document === 'undefined') return;
  const node = document.createElement('style');
  node.dataset.jdf = '1';
  node.textContent = CSS;
  document.head.appendChild(node);
  injected = true;
}
