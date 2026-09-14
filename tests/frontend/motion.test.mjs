import test from "node:test";
import assert from "node:assert/strict";
import { createMotion } from "../../frontend/js/motion.js";

function preference(matches = false) {
  const listeners = new Set();
  return {
    matches,
    addEventListener: (_, callback) => listeners.add(callback),
    removeEventListener: (_, callback) => listeners.delete(callback),
    change(value) {
      this.matches = value;
      for (const callback of listeners) callback();
    },
    get listenerCount() { return listeners.size; },
  };
}

function element(withAnimation = true) {
  const animations = [];
  const node = {
    animations, style: {}, attributes: {}, removed: false,
    setAttribute(name, value) { this.attributes[name] = value; },
    remove() { this.removed = true; },
  };
  if (withAnimation) node.animate = (frames, options) => {
    let resolve, reject;
    const animation = {
      frames, options, cancelled: false,
      finished: new Promise((yes, no) => { resolve = yes; reject = no; }),
      finish() { resolve(); },
      cancel() { this.cancelled = true; reject(new Error("cancelled")); },
    };
    animations.push(animation);
    return animation;
  };
  return node;
}

test("Rapid navigation cancels the old animation without losing the current one", async () => {
  const media = preference();
  const motion = createMotion(media);
  const screen = element();
  const first = motion.navigate(screen);
  const second = motion.navigate(screen, "back");
  assert.equal(first.cancelled, true);
  assert.equal(second.cancelled, false);
  await Promise.resolve(); // The old rejection must not remove the newer animation.
  media.change(true);
  assert.equal(second.cancelled, true);
  assert.equal(screen.removed, false);
  motion.destroy();
  assert.equal(media.listenerCount, 0);
});

test("Reduced motion and missing animation support keep navigation and dismissal usable", () => {
  for (const [reduce, support] of [[true, true], [false, false]]) {
    const motion = createMotion(preference(reduce));
    const screen = element(support);
    assert.equal(motion.navigate(screen), null);
    assert.equal(screen.removed, false);
    motion.dismiss(screen);
    assert.equal(screen.inert, true);
    assert.equal(screen.removed, true);
    assert.equal(screen.animations.length, 0);
    motion.destroy();
  }
});

test("Closing dialogs stop intercepting input immediately and are removed after completion", async () => {
  const motion = createMotion(preference());
  const dialog = element();
  motion.dismiss(dialog);
  assert.equal(dialog.inert, true);
  assert.equal(dialog.attributes["aria-hidden"], "true");
  assert.equal(dialog.style.pointerEvents, "none");
  assert.equal(dialog.removed, false);
  dialog.animations[0].finish();
  await Promise.resolve();
  assert.equal(dialog.removed, true);
  motion.destroy();
});

test("Interrupted dialog exits cannot leave a blocking overlay or remove a replacement", async () => {
  const media = preference();
  const motion = createMotion(media);
  const oldDialog = element(), replacement = element();
  motion.dismiss(oldDialog);
  media.change(true);
  await Promise.resolve();
  assert.equal(oldDialog.removed, true);
  assert.equal(replacement.removed, false);
  motion.destroy();
});
