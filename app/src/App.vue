<script setup lang="ts">
import { onMounted } from 'vue';
import { RouterView } from 'vue-router';
import { useAppStore } from './stores/app';
import Navigation from './components/Navigation.vue';

const appStore = useAppStore();

onMounted(() => {
  appStore.loadTheme();
});
</script>

<template>
  <div class="app-container min-h-screen">
    <Navigation />
    <main class="pt-0">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
}
</style>
