<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useDNSStore } from '../stores/dns';
import PanelLoading from './PanelLoading.vue';
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon } from '@heroicons/vue/24/solid';

const appStore = useAppStore();
const dnsStore = useDNSStore();

const hasDomain = computed(() => !!appStore.domain);

const dnsSubQueries = computed(() => [
  { name: 'A Records (IPv4)', status: 'loading' as const },
  { name: 'AAAA Records (IPv6)', status: 'loading' as const },
  { name: 'MX Records (Mail)', status: 'loading' as const },
  { name: 'TXT Records', status: 'loading' as const },
  { name: 'NS Records (Nameservers)', status: 'loading' as const },
]);

// Diagnostic insights
const diagnostics = computed(() => {
  const issues = [];
  const warnings = [];
  const successes = [];

  // Check for missing critical records
  if (
    dnsStore.aRecords &&
    dnsStore.aRecords.records.length === 0 &&
    dnsStore.aaaaRecords &&
    dnsStore.aaaaRecords.records.length === 0
  ) {
    issues.push('No A or AAAA records found - domain will not resolve');
  } else if (dnsStore.aRecords && dnsStore.aRecords.records.length > 0) {
    successes.push(`Domain resolves to ${dnsStore.aRecords.records.length} IPv4 address(es)`);
  }

  // Check nameserver configuration
  if (dnsStore.nsRecords) {
    if (dnsStore.nsRecords.records.length === 0) {
      issues.push('No NS records found - DNS delegation is broken');
    } else if (dnsStore.nsRecords.records.length === 1) {
      warnings.push('Only 1 nameserver configured - recommend at least 2 for redundancy');
    } else {
      successes.push(
        `${dnsStore.nsRecords.records.length} nameservers configured (good redundancy)`
      );
    }
  }

  // Check mail configuration
  if (dnsStore.mxRecords) {
    if (dnsStore.mxRecords.records.length === 0) {
      warnings.push('No MX records - email delivery may fail');
    } else {
      successes.push(`${dnsStore.mxRecords.records.length} MX record(s) configured for email`);
    }
  }

  // Check IPv6 support
  if (dnsStore.aaaaRecords && dnsStore.aaaaRecords.records.length === 0) {
    warnings.push('No IPv6 (AAAA) records - domain not accessible via IPv6');
  }

  return { issues, warnings, successes };
});

// Combine all DNS records into a single array with type information
const allRecords = computed(() => {
  const records: Array<{
    type: string;
    name: string;
    ttl: number;
    value: string;
    priority?: number;
  }> = [];

  // A Records
  if (dnsStore.aRecords?.records) {
    dnsStore.aRecords.records.forEach((record) => {
      records.push({
        type: 'A',
        name: record.name,
        ttl: record.ttl,
        value: record.value,
      });
    });
  }

  // AAAA Records
  if (dnsStore.aaaaRecords?.records) {
    dnsStore.aaaaRecords.records.forEach((record) => {
      records.push({
        type: 'AAAA',
        name: record.name,
        ttl: record.ttl,
        value: record.value,
      });
    });
  }

  // MX Records
  if (dnsStore.mxRecords?.records) {
    dnsStore.mxRecords.records.forEach((record) => {
      // MX records have format "priority hostname"
      const parts = record.value.split(' ');
      const priority = parts.length > 1 ? parseInt(parts[0]) : undefined;
      const hostname = parts.length > 1 ? parts.slice(1).join(' ') : record.value;

      records.push({
        type: 'MX',
        name: record.name,
        ttl: record.ttl,
        value: hostname,
        priority,
      });
    });
  }

  // NS Records
  if (dnsStore.nsRecords?.records) {
    dnsStore.nsRecords.records.forEach((record) => {
      records.push({
        type: 'NS',
        name: record.name,
        ttl: record.ttl,
        value: record.value,
      });
    });
  }

  // TXT Records
  if (dnsStore.txtRecords?.records) {
    dnsStore.txtRecords.records.forEach((record) => {
      records.push({
        type: 'TXT',
        name: record.name,
        ttl: record.ttl,
        value: record.value,
      });
    });
  }

  return records;
});

const getRecordTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    A: 'text-blue-400',
    AAAA: 'text-purple-400',
    MX: 'text-green-400',
    NS: 'text-yellow-400',
    TXT: 'text-cyan-400',
  };
  return colors[type] || 'text-gray-400';
};
</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">DNS Records</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view DNS records</p>
      </div>

      <!-- Loading state -->
      <PanelLoading v-if="hasDomain && dnsStore.loading" title="DNS Records" :sub-queries="dnsSubQueries" />

      <!-- DNS Records -->
      <div v-else-if="hasDomain" class="space-y-6">
        <!-- Diagnostic Summary -->
        <div
          class="panel"
          v-if="
            diagnostics.issues.length > 0 ||
            diagnostics.warnings.length > 0 ||
            diagnostics.successes.length > 0
          "
        >
          <h2 class="text-xl font-semibold mb-4">DNS Health Check</h2>

          <!-- Issues -->
          <div v-if="diagnostics.issues.length > 0" class="space-y-2 mb-3">
            <div
              v-for="(issue, index) in diagnostics.issues"
              :key="`issue-${index}`"
              class="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded"
            >
              <XCircleIcon class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-red-300">{{ issue }}</span>
            </div>
          </div>

          <!-- Warnings -->
          <div v-if="diagnostics.warnings.length > 0" class="space-y-2 mb-3">
            <div
              v-for="(warning, index) in diagnostics.warnings"
              :key="`warning-${index}`"
              class="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded"
            >
              <ExclamationTriangleIcon class="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-yellow-300">{{ warning }}</span>
            </div>
          </div>

          <!-- Successes -->
          <div v-if="diagnostics.successes.length > 0" class="space-y-2">
            <div
              v-for="(success, index) in diagnostics.successes"
              :key="`success-${index}`"
              class="flex items-start gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded"
            >
              <CheckCircleIcon class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-green-300">{{ success }}</span>
            </div>
          </div>
        </div>
        <!-- All DNS Records in Single Table -->
        <div class="panel py-4">
          <h2 class="text-lg font-semibold mb-3 flex items-center gap-2">
            DNS Records
            <span class="text-sm font-normal text-blue-400">{{ allRecords.length }}</span>
          </h2>
          <div v-if="allRecords.length > 0">
            <table class="w-full text-sm">
              <thead class="border-b border-[#3e3e42]">
                <tr>
                  <th class="text-left py-1.5 px-2 text-[#858585] font-medium text-sm">Type</th>
                  <th class="text-left py-1.5 px-2 text-[#858585] font-medium text-sm">Name</th>
                  <th class="text-left py-1.5 px-2 text-[#858585] font-medium text-sm">TTL</th>
                  <th class="text-left py-1.5 px-2 text-[#858585] font-medium text-sm">Priority</th>
                  <th class="text-left py-1.5 px-2 text-[#858585] font-medium text-sm">Value</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(record, index) in allRecords"
                  :key="index"
                  class="border-b border-[#3e3e42]/50"
                >
                  <td class="py-1.5 px-2">
                    <span
                      class="font-semibold text-xs px-2 py-0.5 rounded"
                      :class="getRecordTypeColor(record.type)"
                    >
                      {{ record.type }}
                    </span>
                  </td>
                  <td class="py-1.5 px-2 text-sm">{{ record.name }}</td>
                  <td class="py-1.5 px-2 text-[#858585] text-xs">{{ record.ttl }}</td>
                  <td class="py-1.5 px-2 text-blue-400 text-xs">
                    {{ record.priority !== undefined ? record.priority : '' }}
                  </td>
                  <td class="py-1.5 px-2 font-mono text-xs break-all">{{ record.value }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="text-[#858585]">No DNS records found</p>
        </div>

        <!-- Error Display -->
        <div v-if="dnsStore.error" class="panel bg-red-900/20 border-red-800">
          <h3 class="text-lg font-semibold text-red-400 mb-2">Error</h3>
          <p class="text-sm text-red-300">{{ dnsStore.error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
