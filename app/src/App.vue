<script setup lang="ts">
import { onMounted } from 'vue';
import { RouterView } from 'vue-router';
import { useAppStore } from './stores/app';
import Navigation from './components/Navigation.vue';
import RawDataModal from './components/RawDataModal.vue';
import LoadingProgress from './components/LoadingProgress.vue';
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts';

const appStore = useAppStore();

// Enable keyboard shortcuts
useKeyboardShortcuts();

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
    <RawDataModal />
    <LoadingProgress />
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
}
</style>
