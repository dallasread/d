<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useWhoisStore } from '../stores/whois';
import PanelLoading from './PanelLoading.vue';
import { CheckIcon, XMarkIcon } from '@heroicons/vue/24/solid';

const appStore = useAppStore();
const whoisStore = useWhoisStore();

const hasDomain = computed(() => !!appStore.domain);

const expirationDate = computed(() => {
  if (!whoisStore.whoisInfo?.expiration_date) return 'N/A';
  return new Date(whoisStore.whoisInfo.expiration_date).toLocaleString();
});

const creationDate = computed(() => {
  if (!whoisStore.whoisInfo?.creation_date) return 'N/A';
  return new Date(whoisStore.whoisInfo.creation_date).toLocaleString();
});

const updatedDate = computed(() => {
  if (!whoisStore.whoisInfo?.updated_date) return 'N/A';
  return new Date(whoisStore.whoisInfo.updated_date).toLocaleString();
});

const daysUntilExpiry = computed(() => {
  if (!whoisStore.whoisInfo?.expiration_date) return null;
  const expiryDate = new Date(whoisStore.whoisInfo.expiration_date);
  const now = new Date();
  const days = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return days;
});

const expiryStatusClass = computed(() => {
  if (daysUntilExpiry.value === null) return 'text-[#858585]';
  if (daysUntilExpiry.value > 90) return 'status-pass';
  if (daysUntilExpiry.value > 30) return 'status-warn';
  return 'status-fail';
});
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Domain Registration</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view registration information</p>
      </div>

      <!-- Loading state -->
      <PanelLoading v-if="whoisStore.loading" title="WHOIS Registration" />

      <!-- Registration Info -->
      <div v-else-if="whoisStore.whoisInfo" class="space-y-6">
        <!-- Overview Card -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Overview</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-[#858585]">Domain</p>
              <p class="text-lg font-medium">{{ whoisStore.whoisInfo.domain }}</p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Registrar</p>
              <p class="text-lg font-medium">{{ whoisStore.whoisInfo.registrar || 'N/A' }}</p>
            </div>
          </div>
        </div>

        <!-- Dates Card -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Important Dates</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p class="text-sm text-[#858585]">Created</p>
              <p class="font-medium">{{ creationDate }}</p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Last Updated</p>
              <p class="font-medium">{{ updatedDate }}</p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Expires</p>
              <p class="font-medium">{{ expirationDate }}</p>
              <p v-if="daysUntilExpiry !== null" :class="['text-sm mt-1', expiryStatusClass]">
                {{ daysUntilExpiry > 0 ? `${daysUntilExpiry} days remaining` : 'Expired' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Nameservers Card -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            Nameservers
            <span class="text-sm font-normal text-blue-400">{{
              whoisStore.whoisInfo.nameservers.length
            }}</span>
          </h2>
          <div v-if="whoisStore.whoisInfo.nameservers.length > 0">
            <ul class="space-y-2">
              <li
                v-for="(ns, index) in whoisStore.whoisInfo.nameservers"
                :key="index"
                class="flex items-center gap-2"
              >
                <span class="text-blue-400">•</span>
                <span class="font-mono text-sm">{{ ns }}</span>
              </li>
            </ul>
          </div>
          <p v-else class="text-[#858585]">No nameservers found</p>
        </div>

        <!-- Status Codes Card -->
        <div v-if="whoisStore.whoisInfo.status.length > 0" class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            Domain Status
            <span class="text-sm font-normal text-blue-400">{{
              whoisStore.whoisInfo.status.length
            }}</span>
          </h2>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(status, index) in whoisStore.whoisInfo.status"
              :key="index"
              class="px-3 py-1 bg-[#3e3e42] text-sm rounded-md"
            >
              {{ status }}
            </span>
          </div>
        </div>

        <!-- DNSSEC Card -->
        <div v-if="whoisStore.whoisInfo.dnssec" class="panel">
          <h2 class="text-xl font-semibold mb-4">DNSSEC</h2>
          <div class="flex items-center gap-2">
            <CheckIcon
              v-if="whoisStore.whoisInfo.dnssec.toLowerCase().includes('signed')"
              class="w-5 h-5 status-pass"
            />
            <XMarkIcon v-else class="w-5 h-5 text-[#858585]" />
            <span class="font-medium">{{ whoisStore.whoisInfo.dnssec }}</span>
          </div>
        </div>

        <!-- Raw WHOIS Data -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Raw WHOIS Data</h2>
          <div class="bg-[#1e1e1e] rounded p-4 overflow-x-auto">
            <pre class="text-xs text-[#858585] font-mono whitespace-pre-wrap">{{
              whoisStore.whoisInfo.raw_output
            }}</pre>
          </div>
        </div>

        <!-- Error Display -->
        <div v-if="whoisStore.error" class="panel bg-red-900/20 border-red-800">
          <h3 class="text-lg font-semibold text-red-400 mb-2">Error</h3>
          <p class="text-sm text-red-300">{{ whoisStore.error }}</p>
        </div>
      </div>

      <!-- No Data -->
      <div v-else class="panel">
        <p class="text-[#858585]">No registration data available</p>
      </div>
    </div>
  </div>
</template>
