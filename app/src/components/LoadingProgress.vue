<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useDNSStore } from '../stores/dns';
import { useDnssecStore } from '../stores/dnssec';
import { useCertificateStore } from '../stores/certificate';
import { useWhoisStore } from '../stores/whois';
import { useHttpStore } from '../stores/http';

const appStore = useAppStore();
const dnsStore = useDNSStore();
const dnssecStore = useDnssecStore();
const certStore = useCertificateStore();
const whoisStore = useWhoisStore();
const httpStore = useHttpStore();

interface QueryStatus {
  name: string;
  loading: boolean;
  error: string | null;
  completed: boolean;
}

const queries = computed<QueryStatus[]>(() => [
  {
    name: 'DNS Records',
    loading: dnsStore.loading,
    error: dnsStore.error,
    completed: !dnsStore.loading && !dnsStore.error && dnsStore.aRecords.length > 0,
  },
  {
    name: 'DNSSEC Validation',
    loading: dnssecStore.loading,
    error: dnssecStore.error,
    completed: !dnssecStore.loading && !dnssecStore.error && dnssecStore.validation !== null,
  },
  {
    name: 'SSL Certificate',
    loading: certStore.loading,
    error: certStore.error,
    completed: !certStore.loading && !certStore.error && certStore.certificate !== null,
  },
  {
    name: 'WHOIS Registration',
    loading: whoisStore.loading,
    error: whoisStore.error,
    completed: !whoisStore.loading && !whoisStore.error && whoisStore.whois !== null,
  },
  {
    name: 'HTTP/HTTPS',
    loading: httpStore.loading,
    error: httpStore.error,
    completed: !httpStore.loading && !httpStore.error && httpStore.http !== null,
  },
]);

const getStatusIcon = (query: QueryStatus) => {
  if (query.completed) return '✓';
  if (query.error) return '✗';
  if (query.loading) return '●';
  return '○';
};

const getStatusColor = (query: QueryStatus) => {
  if (query.completed) return 'text-green-400';
  if (query.error) return 'text-red-400';
  if (query.loading) return 'text-blue-400';
  return 'text-gray-400';
};
</script>

<template>
  <div
    v-if="appStore.loading"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
  >
    <div class="bg-[#1e1e1e] border border-[#3e3e42] rounded-lg p-6 max-w-md w-full mx-4">
      <div class="flex items-center gap-3 mb-6">
        <svg
          class="animate-spin h-5 w-5 text-blue-500"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <h2 class="text-xl font-semibold text-white">Analyzing {{ appStore.domain }}</h2>
      </div>

      <div class="space-y-2">
        <div
          v-for="query in queries"
          :key="query.name"
          class="flex items-center gap-3 py-2"
        >
          <span
            :class="[
              'text-lg font-mono flex-shrink-0 w-6 text-center',
              getStatusColor(query),
              query.loading && 'animate-pulse'
            ]"
          >
            {{ getStatusIcon(query) }}
          </span>
          <span class="flex-1 text-[#cccccc]">{{ query.name }}</span>
          <span v-if="query.loading" class="text-xs text-[#858585]">querying...</span>
          <span v-else-if="query.error" class="text-xs text-red-400">failed</span>
          <span v-else-if="query.completed" class="text-xs text-green-400">done</span>
        </div>
      </div>

      <div class="mt-6 pt-4 border-t border-[#3e3e42]">
        <p class="text-xs text-[#858585] text-center">
          DNSSEC validation may take 10-15 seconds
        </p>
      </div>
    </div>
  </div>
</template>
