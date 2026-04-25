<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { gsap } from 'gsap';

const router = useRouter();
const route = useRoute();
const demoUrl = import.meta.env.VITE_DEMO_URL;
const scrolled = ref(false);
const open = ref(false);
const navRef = ref(null);
const menuRef = ref(null);

const links = [
  { to: '/', label: 'Home' },
  { to: '/services', label: 'Services' },
  { to: '/cases', label: 'Case Studies' },
  { to: '/contact', label: 'Contact' },
];

const onScroll = () => { scrolled.value = window.scrollY > 12; };

const go = (to) => {
  open.value = false;
  router.push(to);
};

watch(open, async (v) => {
  document.body.style.overflow = v ? 'hidden' : '';
  if (!v) return;
  await nextTick();
  if (!menuRef.value) return;
  gsap.set(menuRef.value, { clearProps: 'all' });
  gsap.fromTo(
    menuRef.value,
    { y: -10, opacity: 0 },
    { y: 0, opacity: 1, duration: 0.3, ease: 'power3.out', clearProps: 'all' }
  );
  const items = menuRef.value.querySelectorAll('.m-link');
  gsap.fromTo(
    items,
    { y: 12, opacity: 0 },
    { y: 0, opacity: 1, duration: 0.45, ease: 'power3.out', stagger: 0.05, delay: 0.08, clearProps: 'all' }
  );
});

watch(() => route.path, () => { open.value = false; });

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true });
  gsap.from(navRef.value, { y: -24, opacity: 0, duration: 0.8, ease: 'power3.out', clearProps: 'all' });
});
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll);
  document.body.style.overflow = '';
});
</script>

<template>
  <nav ref="navRef" :class="['nav', { scrolled, open }]">
    <button class="logo" @click="go('/')">Sentinel</button>

    <div class="links desktop-only">
      <button
        v-for="l in links"
        :key="l.to"
        :class="['link', { active: route.path === l.to }]"
        @click="go(l.to)"
      >
        {{ l.label }}
      </button>
    </div>

    <div class="cta desktop-only">
      <a
        v-if="demoUrl"
        class="demo-link"
        :href="demoUrl"
        target="_blank"
        rel="noopener"
      >Demo</a>
      <span class="api">API</span>
      <div class="sep" />
      <button class="get btn-press" @click="go('/contact')">Get access</button>
    </div>

    <button
      class="burger mobile-only"
      :aria-expanded="open"
      aria-label="Toggle menu"
      @click="open = !open"
    >
      <span :class="{ on: open }" />
      <span :class="{ on: open }" />
    </button>
  </nav>

  <div
    v-if="open"
    ref="menuRef"
    class="mobile-menu mobile-only"
    @click.self="open = false"
  >
    <div class="menu-inner">
      <button
        v-for="l in links"
        :key="l.to"
        :class="['m-link', { active: route.path === l.to }]"
        @click="go(l.to)"
      >
        {{ l.label }}
      </button>
      <button class="m-cta btn-press" @click="go('/contact')">Get access</button>
    </div>
  </div>
</template>

<style scoped>
.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 200;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 48px; height: var(--nav-height);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid transparent;
  transition: border-color 200ms ease, background 200ms ease;
}
.nav.scrolled,
.nav.open {
  background: rgba(255, 255, 255, 0.98);
  border-bottom-color: rgba(0, 0, 0, 0.07);
}

.logo {
  background: none; border: none; padding: 0;
  font-family: var(--font-display); font-size: 20px;
  color: #000; letter-spacing: -0.2px;
}

.links { display: flex; align-items: center; gap: 0; }
.link {
  background: none; border: none; padding: 6px 12px;
  font-size: 14px; font-weight: 500; letter-spacing: 0.1px;
  color: var(--color-fg-muted);
  border-radius: 6px;
  transition: color 150ms ease, background 150ms ease;
  position: relative;
}
.link:hover { color: #000; }
.link.active { color: #000; }
.link.active::after {
  content: ''; position: absolute; left: 12px; right: 12px; bottom: 2px;
  height: 1.5px; background: #000; border-radius: 2px;
}

.cta { display: flex; gap: 8px; align-items: center; }
.demo-link {
  font-size: 13px; font-weight: 600; color: #000;
  background: #f5f2ef; border: 1px solid rgba(0, 0, 0, 0.12);
  padding: 6px 14px; border-radius: 9999px;
  text-decoration: none; margin-right: 4px;
  letter-spacing: 0.1px;
}
.demo-link:hover { background: #ece8e3; text-decoration: none; color: #000; }
.api { font-size: 13px; color: var(--color-fg-muted); letter-spacing: 0.1px; }
.sep { width: 1px; height: 16px; background: rgba(0, 0, 0, 0.1); }
.get {
  font-size: 13px; font-weight: 600; color: #fff; background: #000;
  border: none; padding: 7px 16px; border-radius: 9999px;
  letter-spacing: 0.1px;
}
.get:hover { opacity: 0.85; }

.burger {
  width: 40px; height: 40px; border: none; background: transparent;
  position: relative; padding: 0; cursor: pointer; flex-shrink: 0;
}
.burger span {
  position: absolute; left: 10px; right: 10px; height: 1.5px;
  background: #000; border-radius: 2px;
  transition: transform 220ms ease, top 220ms ease;
}
.burger span:nth-child(1) { top: 16px; }
.burger span:nth-child(2) { top: 22px; }
.burger span.on:nth-child(1) { top: 19px; transform: rotate(45deg); }
.burger span.on:nth-child(2) { top: 19px; transform: rotate(-45deg); }

/* Default: desktop shows desktop-only, hides mobile-only */
.mobile-only { display: none; }
.desktop-only { display: flex; }

.mobile-menu {
  position: fixed;
  top: var(--nav-height);
  left: 0; right: 0; bottom: 0;
  z-index: 199;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  overflow-y: auto;
}
.menu-inner {
  padding: 16px 20px 32px;
  display: flex; flex-direction: column; gap: 2px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.07);
}
.m-link {
  background: none; border: none; text-align: left;
  padding: 16px 6px; font-size: 18px; font-weight: 500;
  color: #000; letter-spacing: 0.1px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.m-link.active { font-weight: 600; }
.m-cta {
  margin-top: 16px; background: #000; color: #fff;
  border-radius: 9999px; padding: 14px 18px; border: none;
  text-align: center; font-weight: 600; font-size: 15px;
}

@media (max-width: 900px) {
  .nav { padding: 0 20px; }
  .desktop-only { display: none; }
  .mobile-only { display: flex; }
  .burger { display: block; }
}
</style>
