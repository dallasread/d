<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useWhoisStore } from '../stores/whois';
import PanelLoading from './PanelLoading.vue';

const appStore = useAppStore();
const whoisStore = useWhoisStore();

const hasDomain = computed(() => !!appStore.domain);

// Enhanced date parsing that handles multiple WHOIS date formats
const parseWhoisDate = (dateStr: string | undefined): Date | null => {
  if (!dateStr) return null;

  // Trim whitespace
  const trimmed = dateStr.trim();
  if (!trimmed) return null;

  try {
    // Month name mapping for various formats
    const monthNames: Record<string, number> = {
      jan: 0, january: 0,
      feb: 1, february: 1,
      mar: 2, march: 2,
      apr: 3, april: 3,
      may: 4,
      jun: 5, june: 5,
      jul: 6, july: 6,
      aug: 7, august: 7,
      sep: 8, september: 8,
      oct: 9, october: 9,
      nov: 10, november: 10,
      dec: 11, december: 11,
    };

    // Format 1: ISO 8601 with timezone - "2024-11-02T18:42:00Z" or "2024-11-02T18:42:00.000Z"
    let match = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z?$/i);
    if (match) {
      const [, year, month, day, hour, minute, second] = match;
      return new Date(Date.UTC(+year, +month - 1, +day, +hour, +minute, +second));
    }

    // Format 2: ISO date with space separator - "2024-11-02 18:42:00"
    match = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$/);
    if (match) {
      const [, year, month, day, hour, minute, second] = match;
      return new Date(+year, +month - 1, +day, +hour, +minute, +second);
    }

    // Format 3: ISO date only - "2024-11-02"
    match = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (match) {
      const [, year, month, day] = match;
      return new Date(+year, +month - 1, +day);
    }

    // Format 4: DD-MMM-YYYY - "02-Nov-2024" or "02-nov-2024"
    match = trimmed.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
    if (match) {
      const [, day, monthStr, year] = match;
      const month = monthNames[monthStr.toLowerCase()];
      if (month !== undefined) {
        return new Date(+year, month, +day);
      }
    }

    // Format 5: DD-MMM-YYYY HH:MM:SS - "02-Nov-2024 18:42:00"
    match = trimmed.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})\s+(\d{2}):(\d{2}):(\d{2})$/);
    if (match) {
      const [, day, monthStr, year, hour, minute, second] = match;
      const month = monthNames[monthStr.toLowerCase()];
      if (month !== undefined) {
        return new Date(+year, month, +day, +hour, +minute, +second);
      }
    }

    // Format 6: YYYY/MM/DD - "2024/11/02"
    match = trimmed.match(/^(\d{4})\/(\d{2})\/(\d{2})$/);
    if (match) {
      const [, year, month, day] = match;
      return new Date(+year, +month - 1, +day);
    }

    // Format 7: DD/MM/YYYY - "02/11/2024"
    match = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (match) {
      const [, day, month, year] = match;
      return new Date(+year, +month - 1, +day);
    }

    // Format 8: MM/DD/YYYY - US format "11/02/2024"
    // Note: This is ambiguous with DD/MM/YYYY, so we try both and see which makes sense
    match = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (match) {
      const [, first, second, year] = match;
      // If first number > 12, it must be day (DD/MM/YYYY)
      if (+first > 12) {
        return new Date(+year, +second - 1, +first);
      }
      // If second number > 12, it must be day (MM/DD/YYYY)
      if (+second > 12) {
        return new Date(+year, +first - 1, +second);
      }
      // Ambiguous - default to DD/MM/YYYY (international standard)
      return new Date(+year, +second - 1, +first);
    }

    // Format 9: DD.MM.YYYY - "02.11.2024" (European format)
    match = trimmed.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
    if (match) {
      const [, day, month, year] = match;
      return new Date(+year, +month - 1, +day);
    }

    // Format 10: YYYYMMDD - "20241102"
    match = trimmed.match(/^(\d{4})(\d{2})(\d{2})$/);
    if (match) {
      const [, year, month, day] = match;
      return new Date(+year, +month - 1, +day);
    }

    // Format 11: DD Month YYYY - "02 November 2024" or "2 Nov 2024"
    match = trimmed.match(/^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$/);
    if (match) {
      const [, day, monthStr, year] = match;
      const month = monthNames[monthStr.toLowerCase()];
      if (month !== undefined) {
        return new Date(+year, month, +day);
      }
    }

    // Format 12: Month DD, YYYY - "November 02, 2024" or "Nov 2, 2024"
    match = trimmed.match(/^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$/);
    if (match) {
      const [, monthStr, day, year] = match;
      const month = monthNames[monthStr.toLowerCase()];
      if (month !== undefined) {
        return new Date(+year, month, +day);
      }
    }

    // Format 13: RFC 2822 / RFC 822 - "Sat, 02 Nov 2024 18:42:00 GMT"
    match = trimmed.match(/^[A-Za-z]{3},?\s+(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})\s+(?:GMT|UTC|[+-]\d{4})$/);
    if (match) {
      const [, day, monthStr, year, hour, minute, second] = match;
      const month = monthNames[monthStr.toLowerCase()];
      if (month !== undefined) {
        return new Date(Date.UTC(+year, month, +day, +hour, +minute, +second));
      }
    }

    // Last resort: Try native Date parsing
    const nativeDate = new Date(trimmed);
    if (!isNaN(nativeDate.getTime())) {
      return nativeDate;
    }

    return null;
  } catch (e) {
    console.error('Error parsing WHOIS date:', dateStr, e);
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
