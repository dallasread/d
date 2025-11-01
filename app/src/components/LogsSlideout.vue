<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useLogsStore } from '../stores/logs';
import { useAppStore } from '../stores/app';

const route = useRoute();
const logsStore = useLogsStore();
const appStore = useAppStore();

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

// Handle ESC key to close
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.isOpen) {
    emit('close');
  }
};

// Watch for isOpen changes to add/remove listener
watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    } else {
      window.removeEventListener('keydown', handleKeyDown);
    }
  }
);

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});

const expandedLogIds = ref<Set<string>>(new Set());

// Map routes to relevant tools
const routeToolMap: Record<string, string[]> = {
  '/': [], // Dashboard shows all
  '/registration': ['whois'],
  '/dns': ['dig'],
  '/dnssec': ['dig'],
  '/certificate': ['openssl'],
  '/http': ['curl'],
  '/email': ['dig'],
};

const filteredLogs = computed(() => {
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

  return logs;
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

const getStatus = (log: any): 'success' | 'fail' => {
  const tool = log.tool.toLowerCase();
  const exitCode = log.exitCode;
  const output = log.output || '';

  // Tool-specific success detection
  switch (tool) {
    case 'dig':
      // dig is successful if it got an answer or NOERROR status
      // Even with non-zero exit codes, dig can return valid data
      return output.includes('ANSWER SECTION') ||
        output.includes('status: NOERROR') ||
        output.includes('AUTHORITY SECTION')
        ? 'success'
        : 'fail';

    case 'openssl':
      // openssl s_client is successful if we got certificate data
      // It often returns non-zero exit codes even on success
      return output.includes('BEGIN CERTIFICATE') || output.includes('Verify return code: 0')
        ? 'success'
        : 'fail';

    case 'whois':
      // whois is successful if we got registrar/domain info
      return output.includes('Registrar:') ||
        output.includes('Domain Name:') ||
        output.includes('registrar:')
        ? 'success'
        : 'fail';

    case 'curl':
      // curl is successful with exit code 0
      return exitCode === 0 ? 'success' : 'fail';

    default:
      // Default: trust the exit code
      return exitCode === 0 ? 'success' : 'fail';
  }
};

const getStatusClass = (log: any) => {
  return getStatus(log) === 'success' ? 'status-pass' : 'status-fail';
};

const clearLogs = () => {
  logsStore.clearLogs();
  expandedLogIds.value.clear();
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
  <!-- Backdrop -->
  <Transition name="fade">
    <div v-if="isOpen" class="fixed inset-0 bg-black/50 z-40" @click="emit('close')"></div>
  </Transition>

  <!-- Slideout Panel -->
  <Transition name="slide">
    <div
      v-if="isOpen"
      class="fixed top-0 right-0 h-full w-full md:w-2/3 lg:w-1/2 bg-[#1e1e1e] shadow-2xl z-50 flex flex-col"
    >
      <!-- Header -->
      <div class="flex justify-between items-center p-6 border-b border-[#3e3e42]">
        <div>
          <h2 class="text-xl font-bold text-white mb-1">Command Logs</h2>
          <p class="text-sm text-[#858585]">
            <span v-if="route.path !== '/'">
              {{ route.path.substring(1).charAt(0).toUpperCase() + route.path.substring(2) }} panel
              logs
            </span>
            <span v-else>All executed commands</span>
            <span v-if="appStore.domain" class="text-blue-400"> for {{ appStore.domain }} </span>
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="emit('close')"
            class="p-2 hover:bg-[#3e3e42] rounded transition-colors"
            aria-label="Close logs"
          >
            <svg
              class="w-5 h-5 text-[#858585]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6">
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
          <h3 class="text-lg font-semibold text-[#858585] mb-2">No logs yet</h3>
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
              <div class="flex items-center gap-3 flex-1 text-left min-w-0">
                <!-- Tool icon -->
                <span class="text-2xl flex-shrink-0">{{ getToolIcon(log.tool) }}</span>

                <!-- Command info -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <code
                      class="text-sm text-white font-mono truncate flex-1 min-w-0"
                      :title="`${log.tool} ${log.args.join(' ')}`"
                    >
                      {{ log.tool }} {{ log.args.join(' ') }}
                    </code>
                    <span
                      :class="['text-xs px-2 py-0.5 rounded flex-shrink-0', getStatusClass(log)]"
                    >
                      {{ getStatus(log) === 'success' ? 'SUCCESS' : 'FAILED' }}
                    </span>
                  </div>
                </div>

                <!-- Duration and expand icon -->
                <div class="flex items-center gap-3 flex-shrink-0">
                  <span class="text-xs text-[#858585]">
                    {{ formatDuration(log.duration) }}
                  </span>
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
              </div>
            </button>

            <!-- Accordion content -->
            <Transition name="accordion">
              <div v-if="isExpanded(log.id)" class="border-t border-[#3e3e42] overflow-hidden">
                <!-- Output section -->
                <div class="px-4 py-3 bg-[#1e1e1e]">
                  <pre
                    class="text-xs text-[#cccccc] font-mono overflow-x-auto whitespace-pre-wrap break-words max-h-96 overflow-y-auto"
                    >{{ log.output || '(empty)' }}</pre
                  >
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.status-pass {
  color: #4ec9b0;
}

.status-fail {
  color: #f48771;
}

/* Fade transition for backdrop */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide transition for panel */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* Accordion transition for log expansion */
.accordion-enter-active {
  transition: max-height 0.2s ease;
}

.accordion-leave-active {
  transition: max-height 0.1s ease;
}

.accordion-enter-from,
.accordion-leave-to {
  max-height: 0;
}

.accordion-enter-to,
.accordion-leave-from {
  max-height: 500px;
}
</style>
