<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';

const appStore = useAppStore();

const hasDomain = computed(() => !!appStore.domain);
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Empty state when no domain -->
      <div v-if="!hasDomain" class="flex flex-col items-center justify-center py-20">
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
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <h2 class="text-xl font-semibold text-[#858585] mb-2">Enter a domain to begin</h2>
        <p class="text-sm text-[#858585]">Use the search bar above to analyze a domain</p>
      </div>

      <!-- Dashboard content when domain is set -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Registration Card (full height left) -->
        <div class="card lg:row-span-2">
          <h2 class="text-xl font-semibold mb-3">Registration</h2>
          <p class="text-[#858585]">Domain registration information will appear here</p>
        </div>

        <!-- DNS Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">DNS</h2>
          <p class="text-[#858585]">DNS records summary</p>
        </div>

        <!-- Email Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">Email</h2>
          <p class="text-[#858585]">Email security status</p>
        </div>

        <!-- DNSSEC Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">DNSSEC</h2>
          <p class="text-[#858585]">DNSSEC validation</p>
        </div>

        <!-- Certificate Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">Certificate</h2>
          <p class="text-[#858585]">SSL/TLS certificate info</p>
        </div>

        <!-- HTTP Card -->
        <div class="card lg:col-span-2">
          <h2 class="text-xl font-semibold mb-3">HTTP/HTTPS</h2>
          <p class="text-[#858585]">HTTP connectivity status</p>
        </div>
      </div>
    </div>
  </div>
</template>
