<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { RouterView } from 'vue-router';
import { useAppStore } from './stores/app';
import { useLogsStore } from './stores/logs';
import Navigation from './components/Navigation.vue';
import RawDataModal from './components/RawDataModal.vue';
import LogsButton from './components/LogsButton.vue';
import LogsSlideout from './components/LogsSlideout.vue';
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';

const appStore = useAppStore();
const logsStore = useLogsStore();

const isLogsOpen = ref(false);

let unlistenCommandLog: UnlistenFn | null = null;

// Enable keyboard shortcuts
useKeyboardShortcuts();

const toggleLogs = () => {
  isLogsOpen.value = !isLogsOpen.value;
};

const closeLogs = () => {
  isLogsOpen.value = false;
};

onMounted(async () => {
  appStore.loadTheme();

  // Listen for command logs from backend
  unlistenCommandLog = await listen('command-log', (event) => {
    logsStore.addLog(event.payload as any);
  });
});

onUnmounted(() => {
  if (unlistenCommandLog) {
    unlistenCommandLog();
  }
});
</script>

<template>
  <div class="app-container min-h-screen">
    <Navigation />
    <main class="pt-0">
      <RouterView />
    </main>
    <RawDataModal />

    <!-- Show logs button on all pages -->
    <LogsButton @click="toggleLogs" />

    <!-- Logs slideout -->
    <LogsSlideout :is-open="isLogsOpen" @close="closeLogs" />
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
}
</style>
