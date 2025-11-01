<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLogsStore } from '../stores/logs';
import { useAppStore } from '../stores/app';

const logsStore = useLogsStore();
const appStore = useAppStore();

const expandedLogIds = ref<Set<string>>(new Set());

const filteredLogs = computed(() => {
  if (appStore.domain) {
    return logsStore.getLogsByDomain(appStore.domain);
  }
  return logsStore.logs;
});

const toggleLog = (logId: string) => {
  if (expandedLogIds.value.has(logId)) {
    expandedLogIds.value.delete(logId);
  } else {
    expandedLogIds.value.add(logId);
  }
};

const isExpanded = (logId: string) => {
  return expandedLogIds.value.has(logId);
};

const formatTime = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
};

const formatDuration = (ms: number) => {
  if (ms < 1000) {
    return `${ms.toFixed(0)}ms`;
  }
  return `${(ms / 1000).toFixed(2)}s`;
};

const getToolIcon = (tool: string) => {
  switch (tool.toLowerCase()) {
    case 'dig':
      return '🔍';
    case 'curl':
      return '🌐';
    case 'whois':
      return '📋';
    case 'openssl':
      return '🔒';
    default:
      return '⚙️';
  }
};

const getStatusClass = (exitCode: number) => {
  return exitCode === 0 ? 'status-pass' : 'status-fail';
};

const clearLogs = () => {
  if (confirm('Are you sure you want to clear all logs?')) {
    logsStore.clearLogs();
    expandedLogIds.value.clear();
  }
};

const copyCommand = (log: any) => {
  const fullCommand = `${log.tool} ${log.args.join(' ')}`;
  navigator.clipboard.writeText(fullCommand);
};

const copyOutput = (output: string) => {
  navigator.clipboard.writeText(output);
};
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-white mb-1">Command Logs</h1>
          <p class="text-sm text-[#858585]">
            View all executed commands and their outputs
            <span v-if="appStore.domain" class="text-blue-400">
              (filtered for {{ appStore.domain }})
            </span>
          </p>
        </div>
        <button
          v-if="logsStore.logs.length > 0"
          @click="clearLogs"
          class="px-4 py-2 bg-red-600/10 hover:bg-red-600/20 border border-red-600/30 text-red-400 text-sm font-medium rounded-lg transition-colors"
        >
          Clear Logs
        </button>
      </div>

      <!-- Empty state -->
      <div
        v-if="filteredLogs.length === 0"
        class="flex flex-col items-center justify-center py-20"
      >
        <svg
          class="w-16 h-16 text-[#3e3e42] mb-4"
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
        <h2 class="text-xl font-semibold text-[#858585] mb-2">No logs yet</h2>
        <p class="text-sm text-[#858585]">
          Commands executed by the application will appear here
        </p>
      </div>

      <!-- Logs accordion -->
      <div v-else class="space-y-2">
        <div
          v-for="log in filteredLogs"
          :key="log.id"
          class="bg-[#252526] border border-[#3e3e42] rounded-lg overflow-hidden transition-all"
        >
          <!-- Accordion header -->
          <button
            @click="toggleLog(log.id)"
            class="w-full px-4 py-3 flex items-center justify-between hover:bg-[#2d2d30] transition-colors"
          >
            <div class="flex items-center gap-3 flex-1 text-left">
              <!-- Tool icon -->
              <span class="text-2xl">{{ getToolIcon(log.tool) }}</span>

              <!-- Command info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-sm font-semibold text-white">{{ log.tool }}</span>
                  <span
                    :class="['text-xs px-2 py-0.5 rounded', getStatusClass(log.exitCode)]"
                  >
                    {{ log.exitCode === 0 ? 'SUCCESS' : 'FAILED' }}
                  </span>
                  <span class="text-xs text-[#858585]">
                    {{ formatDuration(log.duration) }}
                  </span>
                </div>
                <code
                  class="text-xs text-[#858585] font-mono truncate block"
                  :title="log.args.join(' ')"
                >
                  {{ log.args.join(' ') }}
                </code>
              </div>

              <!-- Timestamp -->
              <span class="text-xs text-[#858585] flex-shrink-0">
                {{ formatTime(log.timestamp) }}
              </span>

              <!-- Expand icon -->
              <svg
                :class="[
                  'w-5 h-5 text-[#858585] transition-transform',
                  isExpanded(log.id) ? 'rotate-180' : '',
                ]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </button>

          <!-- Accordion content -->
          <div v-if="isExpanded(log.id)" class="border-t border-[#3e3e42]">
            <!-- Command section -->
            <div class="px-4 py-3 bg-[#1e1e1e]">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-xs font-semibold text-[#858585] uppercase">Command</h4>
                <button
                  @click="copyCommand(log)"
                  class="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                  title="Copy command"
                >
                  Copy
                </button>
              </div>
              <code
                class="block text-sm text-[#cccccc] font-mono bg-[#252526] px-3 py-2 rounded border border-[#3e3e42]"
              >
                {{ log.tool }} {{ log.args.join(' ') }}
              </code>
            </div>

            <!-- Output section -->
            <div class="px-4 py-3">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-xs font-semibold text-[#858585] uppercase">Output</h4>
                <button
                  @click="copyOutput(log.output)"
                  class="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                  title="Copy output"
                >
                  Copy
                </button>
              </div>
              <pre
                class="text-xs text-[#cccccc] font-mono bg-[#1e1e1e] px-3 py-2 rounded border border-[#3e3e42] overflow-x-auto whitespace-pre-wrap break-words max-h-96 overflow-y-auto"
                >{{ log.output || '(empty)' }}</pre
              >
            </div>

            <!-- Metadata section -->
            <div class="px-4 py-3 bg-[#1e1e1e] border-t border-[#3e3e42]">
              <h4 class="text-xs font-semibold text-[#858585] uppercase mb-2">Metadata</h4>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <span class="text-[#858585]">Exit Code:</span>
                  <span :class="['ml-1 font-medium', getStatusClass(log.exitCode)]">
                    {{ log.exitCode }}
                  </span>
                </div>
                <div>
                  <span class="text-[#858585]">Duration:</span>
                  <span class="ml-1 text-white">{{ formatDuration(log.duration) }}</span>
                </div>
                <div>
                  <span class="text-[#858585]">Time:</span>
                  <span class="ml-1 text-white">{{ formatTime(log.timestamp) }}</span>
                </div>
                <div v-if="log.domain">
                  <span class="text-[#858585]">Domain:</span>
                  <span class="ml-1 text-white">{{ log.domain }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.status-pass {
  color: #4ec9b0;
}

.status-fail {
  color: #f48771;
}
</style>
