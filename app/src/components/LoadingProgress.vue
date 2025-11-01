<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAppStore } from '../stores/app';
import { useDNSStore } from '../stores/dns';
import { useDnssecStore } from '../stores/dnssec';
import { useCertificateStore } from '../stores/certificate';
import { useWhoisStore } from '../stores/whois';
import { useHttpStore } from '../stores/http';
import { CheckIcon, XMarkIcon } from '@heroicons/vue/24/solid';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';

const appStore = useAppStore();
const dnsStore = useDNSStore();
const dnssecStore = useDnssecStore();
const certStore = useCertificateStore();
const whoisStore = useWhoisStore();
const httpStore = useHttpStore();

interface SubQuery {
  name: string;
  status: 'pending' | 'loading' | 'completed' | 'failed';
}

interface QueryStatus {
  name: string;
  loading: boolean;
  error: string | null;
  completed: boolean;
  subQueries?: SubQuery[];
}

const queries = computed<QueryStatus[]>(() => {
  // DNS sub-queries
  const dnsSubQueries: SubQuery[] = [
    {
      name: 'A Records',
      status: dnsStore.loading ? 'loading' : dnsStore.aRecords ? 'completed' : 'pending',
    },
    {
      name: 'AAAA Records',
      status: dnsStore.loading ? 'loading' : dnsStore.aaaaRecords ? 'completed' : 'pending',
    },
    {
      name: 'MX Records',
      status: dnsStore.loading ? 'loading' : dnsStore.mxRecords ? 'completed' : 'pending',
    },
    {
      name: 'TXT Records',
      status: dnsStore.loading ? 'loading' : dnsStore.txtRecords ? 'completed' : 'pending',
    },
    {
      name: 'NS Records',
      status: dnsStore.loading ? 'loading' : dnsStore.nsRecords ? 'completed' : 'pending',
    },
  ];

  // DNSSEC sub-queries - show the chain levels
  const dnssecSubQueries: SubQuery[] = dnssecStore.loading
    ? [
        { name: 'Root Zone (.) DNSKEY', status: 'loading' },
        { name: 'TLD DS Records', status: 'loading' },
        { name: 'TLD DNSKEY', status: 'loading' },
        { name: 'Domain DS Records', status: 'loading' },
        { name: 'Domain DNSKEY', status: 'loading' },
      ]
    : dnssecStore.validation
      ? [
          { name: 'Root Zone (.) DNSKEY', status: 'completed' },
          { name: 'TLD DS Records', status: 'completed' },
          { name: 'TLD DNSKEY', status: 'completed' },
          { name: 'Domain DS Records', status: 'completed' },
          { name: 'Domain DNSKEY', status: 'completed' },
        ]
      : [];

  // HTTP sub-queries
  const httpSubQueries: SubQuery[] = [
    {
      name: 'HTTP (port 80)',
      status: httpStore.loading ? 'loading' : httpStore.http ? 'completed' : 'pending',
    },
    {
      name: 'HTTPS (port 443)',
      status: httpStore.loading ? 'loading' : httpStore.https ? 'completed' : 'pending',
    },
  ];

  return [
    {
      name: 'DNS Records',
      loading: dnsStore.loading,
      error: dnsStore.error,
      completed: !dnsStore.loading && !dnsStore.error && dnsStore.aRecords !== null,
      subQueries: dnsSubQueries,
    },
    {
      name: 'DNSSEC Validation',
      loading: dnssecStore.loading,
      error: dnssecStore.error,
      completed: !dnssecStore.loading && !dnssecStore.error && dnssecStore.validation !== null,
      subQueries: dnssecSubQueries,
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
      subQueries: httpSubQueries,
    },
  ];
});

const getStatusIconComponent = (query: QueryStatus) => {
  if (query.completed) return CheckIcon;
  if (query.error) return XMarkIcon;
  if (query.loading) return ArrowPathIcon;
  return null;
};

const getStatusColor = (query: QueryStatus) => {
  if (query.completed) return 'text-green-400';
  if (query.error) return 'text-red-400';
  if (query.loading) return 'text-blue-400';
  return 'text-gray-400';
};

const getSubQueryIconComponent = (status: string) => {
  if (status === 'completed') return CheckIcon;
  if (status === 'failed') return XMarkIcon;
  if (status === 'loading') return ArrowPathIcon;
  return null;
};

const getSubQueryColor = (status: string) => {
  if (status === 'completed') return 'text-green-400';
  if (status === 'failed') return 'text-red-400';
  if (status === 'loading') return 'text-blue-400';
  return 'text-gray-500';
};

const expanded = ref<Set<string>>(new Set(['DNSSEC Validation'])); // Expand DNSSEC by default

const toggleExpand = (queryName: string) => {
  if (expanded.value.has(queryName)) {
    expanded.value.delete(queryName);
  } else {
    expanded.value.add(queryName);
  }
};
</script>

<template>
  <div
    v-if="appStore.loading"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
  >
    <div
      class="bg-[#1e1e1e] border border-[#3e3e42] rounded-lg p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto"
    >
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

      <div class="space-y-1">
        <div v-for="query in queries" :key="query.name" class="border border-[#3e3e42] rounded">
          <!-- Main query -->
          <div
            class="flex items-center gap-3 py-2 px-3 hover:bg-[#252526] transition-colors"
            :class="query.subQueries && 'cursor-pointer'"
            @click="query.subQueries && toggleExpand(query.name)"
          >
            <component
              :is="getStatusIconComponent(query)"
              v-if="getStatusIconComponent(query)"
              :class="[
                'w-5 h-5 flex-shrink-0',
                getStatusColor(query),
                query.loading && 'animate-spin',
              ]"
            />
            <span class="flex-1 text-[#cccccc] font-medium">{{ query.name }}</span>

            <!-- Expand/collapse arrow -->
            <span v-if="query.subQueries" class="text-[#858585] text-xs mr-2">
              {{ expanded.has(query.name) ? '▼' : '▶' }}
            </span>

            <span v-if="query.loading" class="text-xs text-[#858585]">querying...</span>
            <span v-else-if="query.error" class="text-xs text-red-400">failed</span>
            <span v-else-if="query.completed" class="text-xs text-green-400">done</span>
          </div>

          <!-- Sub-queries (collapsible) -->
          <div
            v-if="query.subQueries && expanded.has(query.name)"
            class="px-3 pb-2 space-y-1 bg-[#1a1a1a] border-t border-[#3e3e42]"
          >
            <div
              v-for="subQuery in query.subQueries"
              :key="subQuery.name"
              class="flex items-center gap-3 py-1.5 pl-6"
            >
              <component
                :is="getSubQueryIconComponent(subQuery.status)"
                v-if="getSubQueryIconComponent(subQuery.status)"
                :class="[
                  'w-4 h-4 flex-shrink-0',
                  getSubQueryColor(subQuery.status),
                  subQuery.status === 'loading' && 'animate-spin',
                ]"
              />
              <span class="flex-1 text-sm text-[#999]">{{ subQuery.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
