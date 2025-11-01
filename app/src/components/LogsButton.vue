<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useLogsStore } from '../stores/logs';
import { useAppStore } from '../stores/app';

const emit = defineEmits<{
  click: [];
}>();

const route = useRoute();
const logsStore = useLogsStore();
const appStore = useAppStore();

// Map routes to relevant tools (same as LogsSlideout)
const routeToolMap: Record<string, string[]> = {
  '/': [], // Dashboard shows all
  '/registration': ['whois'],
  '/dns': ['dig'],
  '/dnssec': ['dig'],
  '/certificate': ['openssl'],
  '/http': ['curl'],
  '/email': ['dig'],
};

const logCount = computed(() => {
  let logs = logsStore.logs;

  // Filter by domain if set
  if (appStore.domain) {
    logs = logs.filter((log) => log.domain === appStore.domain);
  }

  // Filter by current route/panel
  const tools = routeToolMap[route.path];
  if (tools && tools.length > 0) {
    logs = logs.filter((log) => tools.includes(log.tool));
  }

  return logs.length;
});
</script>

<template>
  <button
    @click="emit('click')"
    class="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-3 bg-[#252526] hover:bg-[#2d2d30] border border-[#3e3e42] rounded-lg shadow-lg transition-colors group z-30"
    title="View command logs"
  >
    <svg
      class="w-5 h-5 text-[#858585] group-hover:text-white transition-colors"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
    <span class="text-sm font-medium text-[#858585] group-hover:text-white transition-colors">
      Logs
    </span>
    <kbd
      class="hidden md:inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
    >
      L
    </kbd>
    <span
      v-if="logCount > 0"
      class="px-2 py-0.5 bg-blue-600 text-white text-xs font-semibold rounded-full"
    >
      {{ logCount }}
    </span>
  </button>
</template>
