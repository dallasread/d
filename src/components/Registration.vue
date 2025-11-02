<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useWhoisStore } from '../stores/whois';
import PanelLoading from './PanelLoading.vue';

const appStore = useAppStore();
const whoisStore = useWhoisStore();

const hasDomain = computed(() => !!appStore.domain);

// Enhanced date parsing that handles multiple formats
const parseWhoisDate = (dateStr: string | undefined): Date | null => {
  if (!dateStr) return null;

  try {
    // Try parsing as ISO date first
    let date = new Date(dateStr);
    if (!isNaN(date.getTime())) return date;

    // Try common WHOIS date formats
    // Format: "2024-11-02T18:42:00Z" or "2024-11-02 18:42:00"
    const isoMatch = dateStr.match(/(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2}):(\d{2})/);
    if (isoMatch) {
      date = new Date(dateStr.replace(' ', 'T'));
      if (!isNaN(date.getTime())) return date;
    }

    // Format: "02-Nov-2024"
    const shortMatch = dateStr.match(/(\d{2})-([A-Za-z]{3})-(\d{4})/);
    if (shortMatch) {
      date = new Date(dateStr);
      if (!isNaN(date.getTime())) return date;
    }

    // Format: "2024/11/02"
    const slashMatch = dateStr.match(/(\d{4})\/(\d{2})\/(\d{2})/);
    if (slashMatch) {
      date = new Date(dateStr.replace(/\//g, '-'));
      if (!isNaN(date.getTime())) return date;
    }

    return null;
  } catch (e) {
    console.error('Error parsing date:', dateStr, e);
    return null;
  }
};

const formatDate = (date: Date | null): string => {
  if (!date) return 'N/A';

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const expirationDate = computed(() => {
  const date = parseWhoisDate(whoisStore.whoisInfo?.expiration_date);
  return formatDate(date);
});

const creationDate = computed(() => {
  const date = parseWhoisDate(whoisStore.whoisInfo?.creation_date);
  return formatDate(date);
});

const updatedDate = computed(() => {
  const date = parseWhoisDate(whoisStore.whoisInfo?.updated_date);
  return formatDate(date);
});

const daysUntilExpiry = computed(() => {
  const expiryDate = parseWhoisDate(whoisStore.whoisInfo?.expiration_date);
  if (!expiryDate) return null;

  const now = new Date();
  const days = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return days;
});

const expiryStatusClass = computed(() => {
  if (daysUntilExpiry.value === null) return 'text-[#858585]';
  if (daysUntilExpiry.value > 90) return 'text-green-400';
  if (daysUntilExpiry.value > 30) return 'text-yellow-400';
  return 'text-red-400';
});</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Domain Registration</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view registration information</p>
      </div>

      <!-- Loading state -->
      <PanelLoading v-if="hasDomain && whoisStore.loading" title="WHOIS Registration" />

      <!-- Error Display -->
      <div v-else-if="hasDomain && whoisStore.error" class="panel bg-red-900/20 border-red-800">
        <h3 class="text-lg font-semibold text-red-400 mb-2">Failed to fetch WHOIS data</h3>
        <p class="text-sm text-red-300">{{ whoisStore.error }}</p>
      </div>

      <!-- Registration Info - Single Card -->
      <div v-else-if="hasDomain && whoisStore.whoisInfo" class="panel">
        <h2 class="text-xl font-semibold mb-6">Domain Registration Information</h2>

        <!-- Registrar and Status Row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6 pb-6 border-b border-[#3e3e42]">
          <!-- Registrar -->
          <div>
            <p class="text-xs text-[#858585] mb-1">Registrar</p>
            <p class="text-lg font-semibold">{{ whoisStore.whoisInfo.registrar || 'N/A' }}</p>
          </div>

          <!-- Domain Status -->
          <div v-if="whoisStore.whoisInfo.status.length > 0">
            <p class="text-xs text-[#858585] mb-2">
              Status
              <span class="text-blue-400 ml-1">({{ whoisStore.whoisInfo.status.length }})</span>
            </p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(status, index) in whoisStore.whoisInfo.status"
                :key="index"
                class="px-3 py-1.5 bg-[#2d2d30] border border-[#3e3e42] text-sm rounded-md"
              >
                {{ status }}
              </span>
            </div>
          </div>
        </div>

        <!-- Nameservers -->
        <div class="mb-6 pb-6 border-b border-[#3e3e42]">
          <h3 class="text-sm font-semibold text-[#858585] mb-4">
            NAMESERVERS
            <span class="text-blue-400 ml-1">({{ whoisStore.whoisInfo.nameservers.length }})</span>
          </h3>
          <div v-if="whoisStore.whoisInfo.nameservers.length > 0">
            <ul class="space-y-2">
              <li
                v-for="(ns, index) in whoisStore.whoisInfo.nameservers"
                :key="index"
                class="flex items-center gap-2"
              >
                <span class="text-blue-400 text-xs">▸</span>
                <span class="font-mono text-sm">{{ ns }}</span>
              </li>
            </ul>
          </div>
          <p v-else class="text-[#858585] text-sm">No nameservers found</p>
        </div>

        <!-- Important Dates -->
        <div>
          <h3 class="text-sm font-semibold text-[#858585] mb-4">IMPORTANT DATES</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p class="text-xs text-[#858585] mb-1">Created</p>
              <p class="font-medium">{{ creationDate }}</p>
            </div>
            <div>
              <p class="text-xs text-[#858585] mb-1">Last Updated</p>
              <p class="font-medium">{{ updatedDate }}</p>
            </div>
            <div>
              <p class="text-xs text-[#858585] mb-1">Expires</p>
              <p class="font-medium">{{ expirationDate }}</p>
              <p v-if="daysUntilExpiry !== null" :class="['text-sm mt-1 font-semibold', expiryStatusClass]">
                {{ daysUntilExpiry > 0 ? `${daysUntilExpiry} days remaining` : 'Expired' }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
