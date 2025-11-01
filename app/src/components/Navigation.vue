<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAppStore } from '../stores/app';
import { useDNSStore } from '../stores/dns';
import { useDnssecStore } from '../stores/dnssec';
import { useCertificateStore } from '../stores/certificate';
import { useWhoisStore } from '../stores/whois';
import { useHttpStore } from '../stores/http';
import { useLogsStore } from '../stores/logs';

const router = useRouter();
const route = useRoute();
const appStore = useAppStore();
const dnsStore = useDNSStore();
const dnssecStore = useDnssecStore();
const certStore = useCertificateStore();
const whoisStore = useWhoisStore();
const httpStore = useHttpStore();
const logsStore = useLogsStore();

const domainInput = ref('');

const emit = defineEmits<{
  toggleLogs: [];
}>();

const tabs = [
  { name: 'Dashboard', path: '/', key: '1' },
  { name: 'Registration', path: '/registration', key: '2' },
  { name: 'DNS', path: '/dns', key: '3' },
  { name: 'DNSSEC', path: '/dnssec', key: '4' },
  { name: 'Certificate', path: '/certificate', key: '5' },
  { name: 'HTTP', path: '/http', key: '6' },
  { name: 'Email', path: '/email', key: '7' },
];

const isActiveTab = (path: string) => {
  return route.path === path;
};

const navigateToTab = (path: string) => {
  router.push(path);
};

const handleSearch = async () => {
  if (domainInput.value.trim()) {
    const domain = domainInput.value.trim().toLowerCase();

    // If domain changed, clear all caches and logs
    if (domain !== appStore.domain) {
      if (dnsStore.clearCache) dnsStore.clearCache();
      logsStore.clearLogs();
      // Clear other store caches as they're implemented
    }

    appStore.setDomain(domain);
    appStore.setLoading(true);
    appStore.setError(null);

    try {
      // Fetch all data in parallel
      await Promise.all([
        dnsStore.fetchDnsRecords(domain),
        dnssecStore.fetchDnssec(domain),
        certStore.fetchCertificate(domain),
        whoisStore.fetchWhois(domain),
        httpStore.fetchHttp(domain),
      ]);

      // Stay on current page - don't auto-navigate
    } catch (error) {
      console.error('Error fetching domain data:', error);
      appStore.setError('Failed to fetch domain data. Please try again.');
    } finally {
      appStore.setLoading(false);
    }
  }
};

const handleKeypress = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    handleSearch();
  }
};

const handleRefresh = () => {
  if (appStore.domain) {
    // Set domain input to current domain if not already set
    if (!domainInput.value) {
      domainInput.value = appStore.domain;
    }

    // Clear cache and logs on refresh
    if (dnsStore.clearCache) dnsStore.clearCache();
    logsStore.clearLogs();
    // Clear other store caches as they're implemented

    handleSearch();
  }
};

const toggleLogs = () => {
  emit('toggleLogs');
};

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
    logs = logs.filter((log) => {
      if (!tools.includes(log.tool)) {
        return false;
      }

      // Special filtering for email tab - only show MX and TXT queries
      if (route.path === '/email' && log.tool === 'dig') {
        const args = log.args.join(' ');
        return args.includes(' MX') || args.includes(' TXT');
      }

      // Special filtering for DNS tab - exclude DNSKEY and DS queries (those are DNSSEC)
      if (route.path === '/dns' && log.tool === 'dig') {
        const args = log.args.join(' ');
        return !args.includes(' DNSKEY') && !args.includes(' DS');
      }

      // Special filtering for DNSSEC tab - only show DNSKEY and DS queries
      if (route.path === '/dnssec' && log.tool === 'dig') {
        const args = log.args.join(' ');
        return args.includes(' DNSKEY') || args.includes(' DS');
      }

      return true;
    });
  }

  return logs.length;
});

onMounted(() => {
  window.addEventListener('app:refresh', handleRefresh);
});

onUnmounted(() => {
  window.removeEventListener('app:refresh', handleRefresh);
});
</script>

<template>
  <div class="fixed top-0 left-0 right-0 z-50 bg-[#1e1e1e] border-b border-[#3e3e42]">
    <!-- Top bar with branding and search -->
    <div class="w-full px-3 md:px-6 py-3 md:py-4">
      <div class="flex items-center gap-6 max-w-full">
        <!-- Branding -->
        <div class="flex-shrink-0">
          <h1 class="text-2xl font-bold text-white">D</h1>
        </div>

        <!-- Search bar -->
        <div class="flex-1">
          <div class="relative">
            <input
              v-model="domainInput"
              type="text"
              placeholder="Enter domain (e.g., example.com)"
              class="w-full px-4 py-2.5 bg-[#252526] border border-[#3e3e42] rounded-lg text-[#cccccc] placeholder-[#858585] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              :disabled="appStore.loading"
              @keypress="handleKeypress"
            />
            <button
              @click="handleSearch"
              :disabled="appStore.loading || !domainInput.trim()"
              class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-[#3e3e42] disabled:text-[#858585] text-white text-sm font-medium rounded transition-colors"
            >
              {{ appStore.loading ? 'Loading...' : 'Analyze' }}
            </button>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="flex items-center gap-2 flex-shrink-0">
          <!-- Refresh button -->
          <button
            @click="handleRefresh"
            :disabled="!appStore.domain || appStore.loading"
            class="flex items-center gap-2 px-3 py-2 bg-[#252526] hover:bg-[#2d2d30] border border-[#3e3e42] rounded-lg transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
            title="Refresh domain data"
          >
            <kbd
              class="hidden md:inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
            >
              R
            </kbd>
            <span
              class="text-sm font-medium text-[#858585] group-hover:text-white transition-colors"
            >
              Refresh
            </span>
          </button>

          <!-- Logs button -->
          <button
            @click="toggleLogs"
            class="flex items-center gap-2 px-3 py-2 bg-[#252526] hover:bg-[#2d2d30] border border-[#3e3e42] rounded-lg transition-colors group"
            title="View command logs"
          >
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
            <span
              class="hidden sm:inline text-sm font-medium text-[#858585] group-hover:text-white transition-colors"
            >
              Logs
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Navigation tabs -->
    <div class="w-full px-3 md:px-6 overflow-x-auto overflow-y-hidden">
      <nav class="flex gap-1 -mb-px" aria-label="Tabs">
        <button
          v-for="tab in tabs"
          :key="tab.path"
          @click="navigateToTab(tab.path)"
          :class="[
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 cursor-pointer whitespace-nowrap flex-shrink-0',
            isActiveTab(tab.path)
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-[#858585] hover:text-[#cccccc] hover:border-[#3e3e42]',
          ]"
          :aria-current="isActiveTab(tab.path) ? 'page' : undefined"
        >
          <kbd
            class="hidden md:inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border"
            :class="[
              isActiveTab(tab.path)
                ? 'bg-blue-500/15 border-blue-500/40 text-blue-300'
                : 'bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]',
            ]"
          >
            {{ tab.key }}
          </kbd>
          <span>{{ tab.name }}</span>
        </button>
      </nav>
    </div>
  </div>
</template>
