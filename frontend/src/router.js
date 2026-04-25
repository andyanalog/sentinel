import { createRouter, createWebHistory } from 'vue-router';
import Home from './pages/Home.vue';
import Services from './pages/Services.vue';
import Cases from './pages/Cases.vue';
import Contact from './pages/Contact.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/services', name: 'services', component: Services },
    { path: '/cases', name: 'cases', component: Cases },
    { path: '/contact', name: 'contact', component: Contact },
  ],
  scrollBehavior() {
    return { top: 0, behavior: 'instant' };
  },
});

export default router;
