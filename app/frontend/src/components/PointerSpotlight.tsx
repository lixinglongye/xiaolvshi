import { useEffect } from 'react';

const BUTTON_SELECTOR =
  'button:not(:disabled), a.interactive-button, [role="button"]:not([aria-disabled="true"]), .quiet-button, .soft-button';

export default function PointerSpotlight() {
  useEffect(() => {
    const findButton = (target: EventTarget | null) => {
      if (!(target instanceof Element)) return null;
      return target.closest<HTMLElement>(BUTTON_SELECTOR);
    };

    const updatePointer = (event: PointerEvent) => {
      const button = findButton(event.target);
      if (!button) return;

      const rect = button.getBoundingClientRect();
      button.style.setProperty('--button-x', `${event.clientX - rect.left}px`);
      button.style.setProperty('--button-y', `${event.clientY - rect.top}px`);
      button.dataset.pointer = 'inside';
    };

    const clearPointer = (event: PointerEvent) => {
      const button = findButton(event.target);
      if (!button) return;

      const related = event.relatedTarget;
      if (related instanceof Node && button.contains(related)) return;

      button.dataset.pointer = 'idle';
    };

    window.addEventListener('pointermove', updatePointer, { passive: true });
    window.addEventListener('pointerover', updatePointer, { passive: true });
    window.addEventListener('pointerout', clearPointer, true);

    return () => {
      window.removeEventListener('pointermove', updatePointer);
      window.removeEventListener('pointerover', updatePointer);
      window.removeEventListener('pointerout', clearPointer, true);
    };
  }, []);

  return null;
}
