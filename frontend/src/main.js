import { createApp } from 'vue';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import App from './App.vue';
import router from './router.js';
import './style.css';

gsap.registerPlugin(ScrollTrigger);

createApp(App).use(router).mount('#app');
