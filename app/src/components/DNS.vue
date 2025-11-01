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
      <PanelLoading v-if="dnsStore.loading" title="DNS Records" :sub-queries="dnsSubQueries" />

      <!-- DNS Records -->
      <div v-else class="space-y-6">
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
        <!-- A Records -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            A Records
            <span class="text-sm font-normal text-[#858585]">(IPv4)</span>
            <span v-if="dnsStore.aRecords" class="text-sm font-normal text-blue-400">
              {{ dnsStore.aRecords.records.length }}
            </span>
          </h2>
          <div v-if="dnsStore.aRecords && dnsStore.aRecords.records.length > 0">
            <table class="w-full text-sm">
              <thead class="border-b border-[#3e3e42]">
                <tr>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Name</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">TTL</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">IP Address</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(record, index) in dnsStore.aRecords.records"
                  :key="index"
                  class="border-b border-[#3e3e42]/50"
                >
                  <td class="py-2 px-3">{{ record.name }}</td>
                  <td class="py-2 px-3 text-[#858585]">{{ record.ttl }}</td>
                  <td class="py-2 px-3 font-mono text-blue-400">{{ record.value }}</td>
                </tr>
              </tbody>
            </table>
            <p class="text-xs text-[#858585] mt-2">
              Query time: {{ dnsStore.aRecords.query_time.toFixed(3) }}s
            </p>
          </div>
          <p v-else class="text-[#858585]">No A records found</p>
        </div>

        <!-- AAAA Records -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            AAAA Records
            <span class="text-sm font-normal text-[#858585]">(IPv6)</span>
            <span v-if="dnsStore.aaaaRecords" class="text-sm font-normal text-blue-400">
              {{ dnsStore.aaaaRecords.records.length }}
            </span>
          </h2>
          <div v-if="dnsStore.aaaaRecords && dnsStore.aaaaRecords.records.length > 0">
            <table class="w-full text-sm">
              <thead class="border-b border-[#3e3e42]">
                <tr>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Name</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">TTL</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">IP Address</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(record, index) in dnsStore.aaaaRecords.records"
                  :key="index"
                  class="border-b border-[#3e3e42]/50"
                >
                  <td class="py-2 px-3">{{ record.name }}</td>
                  <td class="py-2 px-3 text-[#858585]">{{ record.ttl }}</td>
                  <td class="py-2 px-3 font-mono text-blue-400">{{ record.value }}</td>
                </tr>
              </tbody>
            </table>
            <p class="text-xs text-[#858585] mt-2">
              Query time: {{ dnsStore.aaaaRecords.query_time.toFixed(3) }}s
            </p>
          </div>
          <p v-else class="text-[#858585]">No AAAA records found</p>
        </div>

        <!-- MX Records -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            MX Records
            <span class="text-sm font-normal text-[#858585]">(Mail Exchange)</span>
            <span v-if="dnsStore.mxRecords" class="text-sm font-normal text-blue-400">
              {{ dnsStore.mxRecords.records.length }}
            </span>
          </h2>
          <div v-if="dnsStore.mxRecords && dnsStore.mxRecords.records.length > 0">
            <table class="w-full text-sm">
              <thead class="border-b border-[#3e3e42]">
                <tr>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Name</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">TTL</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Priority</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Mail Server</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(record, index) in dnsStore.mxRecords.records"
                  :key="index"
                  class="border-b border-[#3e3e42]/50"
                >
                  <td class="py-2 px-3">{{ record.name }}</td>
                  <td class="py-2 px-3 text-[#858585]">{{ record.ttl }}</td>
                  <td class="py-2 px-3 text-blue-400">{{ record.value.split(' ')[0] }}</td>
                  <td class="py-2 px-3 font-mono">
                    {{ record.value.split(' ')[1] || record.value }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p class="text-xs text-[#858585] mt-2">
              Query time: {{ dnsStore.mxRecords.query_time.toFixed(3) }}s
            </p>
          </div>
          <p v-else class="text-[#858585]">No MX records found</p>
        </div>

        <!-- NS Records -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            NS Records
            <span class="text-sm font-normal text-[#858585]">(Nameservers)</span>
            <span v-if="dnsStore.nsRecords" class="text-sm font-normal text-blue-400">
              {{ dnsStore.nsRecords.records.length }}
            </span>
          </h2>
          <div v-if="dnsStore.nsRecords && dnsStore.nsRecords.records.length > 0">
            <table class="w-full text-sm">
              <thead class="border-b border-[#3e3e42]">
                <tr>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Name</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">TTL</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Nameserver</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(record, index) in dnsStore.nsRecords.records"
                  :key="index"
                  class="border-b border-[#3e3e42]/50"
                >
                  <td class="py-2 px-3">{{ record.name }}</td>
                  <td class="py-2 px-3 text-[#858585]">{{ record.ttl }}</td>
                  <td class="py-2 px-3 font-mono text-blue-400">{{ record.value }}</td>
                </tr>
              </tbody>
            </table>
            <p class="text-xs text-[#858585] mt-2">
              Query time: {{ dnsStore.nsRecords.query_time.toFixed(3) }}s
            </p>
          </div>
          <p v-else class="text-[#858585]">No NS records found</p>
        </div>

        <!-- TXT Records -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            TXT Records
            <span class="text-sm font-normal text-[#858585]">(Text)</span>
            <span v-if="dnsStore.txtRecords" class="text-sm font-normal text-blue-400">
              {{ dnsStore.txtRecords.records.length }}
            </span>
          </h2>
          <div v-if="dnsStore.txtRecords && dnsStore.txtRecords.records.length > 0">
            <table class="w-full text-sm">
              <thead class="border-b border-[#3e3e42]">
                <tr>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Name</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">TTL</th>
                  <th class="text-left py-2 px-3 text-[#858585] font-medium">Value</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(record, index) in dnsStore.txtRecords.records"
                  :key="index"
                  class="border-b border-[#3e3e42]/50"
                >
                  <td class="py-2 px-3">{{ record.name }}</td>
                  <td class="py-2 px-3 text-[#858585]">{{ record.ttl }}</td>
                  <td class="py-2 px-3 font-mono text-sm break-all">{{ record.value }}</td>
                </tr>
              </tbody>
            </table>
            <p class="text-xs text-[#858585] mt-2">
              Query time: {{ dnsStore.txtRecords.query_time.toFixed(3) }}s
            </p>
          </div>
          <p v-else class="text-[#858585]">No TXT records found</p>
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
