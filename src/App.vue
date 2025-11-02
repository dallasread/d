<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { RouterView } from 'vue-router';
import { useAppStore } from './stores/app';
import { useLogsStore } from './stores/logs';
import Navigation from './components/Navigation.vue';
import RawDataModal from './components/RawDataModal.vue';
import LogsSlideout from './components/LogsSlideout.vue';
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';

const appStore = useAppStore();
const logsStore = useLogsStore();

const isLogsOpen = ref(false);
const expandLogId = ref<string | null>(null);

let unlistenCommandLog: UnlistenFn | null = null;

// Enable keyboard shortcuts
useKeyboardShortcuts();

const toggleLogs = () => {
  isLogsOpen.value = !isLogsOpen.value;
  if (!isLogsOpen.value) {
    expandLogId.value = null;
  }
};

const openLogsWithExpanded = (logId: string) => {
  expandLogId.value = logId;
  isLogsOpen.value = true;
};

const closeLogs = () => {
  isLogsOpen.value = false;
  expandLogId.value = null;
};

onMounted(async () => {
  appStore.loadTheme();

  // Listen for command logs from backend
  unlistenCommandLog = await listen('command-log', (event) => {
    logsStore.addLog(event.payload as any);
  });

  // Listen for keyboard shortcut to toggle logs
  window.addEventListener('app:toggle-logs', toggleLogs);

  // Listen for open logs with specific log expanded
  window.addEventListener('app:open-logs', ((event: CustomEvent) => {
    if (event.detail?.logId) {
      openLogsWithExpanded(event.detail.logId);
    }
  }) as EventListener);
});

onUnmounted(() => {
  if (unlistenCommandLog) {
    unlistenCommandLog();
  }
  window.removeEventListener('app:toggle-logs', toggleLogs);
  window.removeEventListener('app:open-logs', ((event: CustomEvent) => {
    if (event.detail?.logId) {
      openLogsWithExpanded(event.detail.logId);
    }
  }) as EventListener);
});
</script>

<template>
  <div class="app-container min-h-screen">
    <Navigation @toggle-logs="toggleLogs" />
    <main class="pt-[120px]">
      <RouterView />
    </main>
    <RawDataModal />

    <!-- Logs slideout -->
    <LogsSlideout :isOpen="isLogsOpen" :expandLogId="expandLogId" @close="closeLogs" />
  </div>
</template>

<style>
/* Global styles to prevent horizontal scroll */
html,
body {
  overflow-x: hidden;
  max-width: 100vw;
}
</style>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
  overflow-x: hidden;
}
</style>
