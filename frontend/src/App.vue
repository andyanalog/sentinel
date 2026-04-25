<script setup>
import Nav from './components/Nav.vue';
</script>

<template>
  <Nav />
  <main>
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </main>
</template>

<style scoped>
main { padding-top: var(--nav-height); }
</style>
