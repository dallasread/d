<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useDNSStore } from '../stores/dns';
import { useCertificateStore } from '../stores/certificate';
import { useWhoisStore } from '../stores/whois';
import { useHttpStore } from '../stores/http';

const isOpen = ref(false);
const showRaw = ref(false); // false = JSON, true = raw output

const route = useRoute();
const dnsStore = useDNSStore();
const certStore = useCertificateStore();
const whoisStore = useWhoisStore();
const httpStore = useHttpStore();

const currentPanel = computed(() => {
  const path = route.path;
  if (path === '/') return 'Dashboard';
  if (path === '/registration') return 'Registration';
  if (path === '/dns') return 'DNS';
  if (path === '/dnssec') return 'DNSSEC';
  if (path === '/certificate') return 'Certificate';
  if (path === '/http') return 'HTTP';
  if (path === '/email') return 'Email';
  return 'Unknown';
});

const jsonData = computed(() => {
  const path = route.path;
  if (path === '/dns') {
    return {
      a_records: dnsStore.aRecords,
      aaaa_records: dnsStore.aaaaRecords,
      mx_records: dnsStore.mxRecords,
      txt_records: dnsStore.txtRecords,
      ns_records: dnsStore.nsRecords,
    };
  }
  if (path === '/registration') return whoisStore.whoisInfo;
  if (path === '/certificate') return certStore.tlsInfo;
  if (path === '/http') {
    return {
      https: httpStore.httpsResponse,
      http: httpStore.httpResponse,
    };
  }
  return null;
});

const rawOutput = computed(() => {
  const path = route.path;
  if (path === '/dns') {
    return [
      dnsStore.aRecords?.raw_output,
      dnsStore.aaaaRecords?.raw_output,
      dnsStore.mxRecords?.raw_output,
      dnsStore.txtRecords?.raw_output,
      dnsStore.nsRecords?.raw_output,
    ]
      .filter(Boolean)
      .join('\n\n---\n\n');
  }
  if (path === '/registration') return whoisStore.whoisInfo?.raw_output;
  if (path === '/certificate') return certStore.tlsInfo?.raw_output;
  if (path === '/http') {
    return [httpStore.httpsResponse?.raw_output, httpStore.httpResponse?.raw_output]
      .filter(Boolean)
      .join('\n\n---\n\n');
  }
  return null;
});

const displayData = computed(() => {
  if (showRaw.value) {
    return rawOutput.value || 'No raw output available';
  }
  return JSON.stringify(jsonData.value, null, 2) || 'No data available';
});

const open = () => {
  isOpen.value = true;
  showRaw.value = false;
};

const close = () => {
  isOpen.value = false;
};

const toggleView = () => {
  showRaw.value = !showRaw.value;
};

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(displayData.value);
    console.log('Copied to clipboard');
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};

const handleShowRawData = () => {
  open();
};

const handleCloseModals = () => {
  close();
};

onMounted(() => {
  window.addEventListener('app:show-raw-data', handleShowRawData);
  window.addEventListener('app:close-modals', handleCloseModals);
});

onUnmounted(() => {
  window.removeEventListener('app:show-raw-data', handleShowRawData);
  window.removeEventListener('app:close-modals', handleCloseModals);
});

defineExpose({ open, close });
</script>

<template>
  <!-- Modal Overlay -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      leave-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="close"
      >
        <!-- Modal Content -->
        <div class="bg-[#1e1e1e] border border-[#3e3e42] rounded-lg w-full max-w-5xl max-h-[90vh] flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between p-4 border-b border-[#3e3e42]">
            <div>
              <h2 class="text-xl font-semibold">{{ currentPanel }} - Raw Data</h2>
              <p class="text-sm text-[#858585]">
                Press <kbd class="px-2 py-1 bg-[#3e3e42] rounded text-xs">T</kbd> to toggle view,
                <kbd class="px-2 py-1 bg-[#3e3e42] rounded text-xs">ESC</kbd> to close
              </p>
            </div>
            <button
              @click="close"
              class="p-2 hover:bg-[#3e3e42] rounded transition-colors"
              aria-label="Close"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Toolbar -->
          <div class="flex items-center gap-2 p-3 border-b border-[#3e3e42] bg-[#252526]">
            <button
              @click="toggleView"
              class="px-3 py-1.5 text-sm rounded transition-colors"
              :class="!showRaw ? 'bg-blue-600 text-white' : 'bg-[#3e3e42] hover:bg-[#4e4e52]'"
            >
              JSON
            </button>
            <button
              @click="toggleView"
              class="px-3 py-1.5 text-sm rounded transition-colors"
              :class="showRaw ? 'bg-blue-600 text-white' : 'bg-[#3e3e42] hover:bg-[#4e4e52]'"
            >
              Raw Output
            </button>
            <div class="flex-1"></div>
            <button
              @click="copyToClipboard"
              class="px-3 py-1.5 text-sm bg-[#3e3e42] hover:bg-[#4e4e52] rounded transition-colors flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-auto p-4">
            <pre class="text-xs font-mono text-[#cccccc] whitespace-pre-wrap">{{ displayData }}</pre>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
