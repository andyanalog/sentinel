import { onMounted, onBeforeUnmount } from 'vue';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

/**
 * useReveal — fade/slide `.reveal` elements within `rootRef` into view on scroll.
 * Stagger + slight y translate. Idempotent: created ScrollTriggers are killed on unmount.
 */
export function useReveal(rootRef, opts = {}) {
  const { selector = '.reveal', y = 20, stagger = 0.08, duration = 0.85 } = opts;
  const triggers = [];

  onMounted(() => {
    if (!rootRef.value) return;
    const items = rootRef.value.querySelectorAll(selector);
    items.forEach((el, i) => {
      const tween = gsap.fromTo(
        el,
        { opacity: 0, y },
        {
          opacity: 1,
          y: 0,
          duration,
          ease: 'power3.out',
          delay: (i % 6) * stagger,
          scrollTrigger: {
            trigger: el,
            start: 'top 85%',
            toggleActions: 'play none none none',
          },
        }
      );
      if (tween.scrollTrigger) triggers.push(tween.scrollTrigger);
    });
    ScrollTrigger.refresh();
  });

  onBeforeUnmount(() => {
    triggers.forEach((t) => t.kill());
  });
}

/**
 * splitChars — turns a string into char spans for hero animation.
 */
export function splitChars(text) {
  return Array.from(text).map((ch) => ({
    char: ch === ' ' ? '\u00a0' : ch,
    isSpace: ch === ' ',
  }));
}
