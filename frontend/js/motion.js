// Local kiosk timings, inspired by functional motion. No navigation waits on an effect.
export function createMotion(preference = matchMedia("(prefers-reduced-motion: reduce)")) {
  const running = new Map();
  const cancelAll = () => {
    for (const animation of running.values()) animation.cancel();
    running.clear();
  };
  preference.addEventListener?.("change", cancelAll);

  function play(element, frames, options) {
    running.get(element)?.cancel();
    running.delete(element);
    if (preference.matches || typeof element.animate !== "function") return null;
    const animation = element.animate(frames, options);
    running.set(element, animation);
    const clear = () => {
      if (running.get(element) === animation) running.delete(element);
    };
    animation.finished.then(clear, clear);
    return animation;
  }

  return {
    navigate(element, direction = "forward") {
      const reset = direction === "reset";
      const offset = reset ? 0 : direction === "back" ? -12 : 12;
      return play(element, [
        { opacity: 0.35, transform: `translateX(${offset}px)` },
        { opacity: 1, transform: "translateX(0)" },
      ], { duration: reset ? 160 : 280, easing: "cubic-bezier(.2,.75,.25,1)" });
    },
    dismiss(element) {
      if (!element) return;
      // Restore the underlying UI immediately; a fading dialog cannot receive input.
      element.inert = true;
      element.setAttribute("aria-hidden", "true");
      element.style.pointerEvents = "none";
      const animation = play(element, [{ opacity: 1 }, { opacity: 0 }], {
        duration: 140, easing: "ease-out",
      });
      if (animation) animation.finished.then(() => element.remove(), () => element.remove());
      else element.remove();
    },
    destroy() {
      cancelAll();
      preference.removeEventListener?.("change", cancelAll);
    },
  };
}
