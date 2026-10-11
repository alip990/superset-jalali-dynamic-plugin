import React, { useEffect, useLayoutEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

type PopoverProps = {
  open: boolean;
  anchor: HTMLElement | null;
  overflow: boolean;
  onClose: () => void;
  children: React.ReactNode;
};

export default function Popover(props: PopoverProps) {
  const { open, anchor, overflow, onClose, children } = props;
  const panel = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    const node = panel.current;
    if (!open || !node || overflow || !anchor) return;
    const rect = anchor.getBoundingClientRect();
    const width = node.offsetWidth;
    const height = node.offsetHeight;
    let left = rect.right - width;
    let top = rect.bottom + 4;
    left = Math.max(8, Math.min(left, window.innerWidth - width - 8));
    if (top + height > window.innerHeight - 8) top = Math.max(8, rect.top - height - 4);
    node.style.top = `${top}px`;
    node.style.left = `${left}px`;
  }, [open, anchor, overflow, children]);

  useEffect(() => {
    if (!open) return undefined;
    function onPointer(event: MouseEvent) {
      const target = event.target as Node | null;
      if (!target) return;
      if (panel.current?.contains(target) || anchor?.contains(target)) return;
      onClose();
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    }
    document.addEventListener('mousedown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onPointer);
      document.removeEventListener('keydown', onKey);
    };
  }, [open, anchor, onClose]);

  if (!open) return null;
  return createPortal(
    <div
      ref={panel}
      className={overflow ? 'jdf-popover jdf-popover-center' : 'jdf-popover'}
      role="dialog"
      aria-label="انتخاب تاریخ"
      data-testid="jdf-popover"
      dir="rtl"
    >
      {children}
    </div>,
    document.body,
  );
}
