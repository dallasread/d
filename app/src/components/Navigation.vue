<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAppStore } from '../stores/app';

const router = useRouter();
const route = useRoute();
const appStore = useAppStore();

const domainInput = ref('');

const tabs = [
  { name: 'Dashboard', path: '/', key: '0' },
  { name: 'Registration', path: '/registration', key: '1' },
  { name: 'DNS', path: '/dns', key: '2' },
  { name: 'DNSSEC', path: '/dnssec', key: '3' },
  { name: 'Certificate', path: '/certificate', key: '4' },
  { name: 'HTTP', path: '/http', key: '5' },
  { name: 'Email', path: '/email', key: '6' },
];

const isActiveTab = (path: string) => {
  return route.path === path;
};

const navigateToTab = (path: string) => {
  router.push(path);
};

const handleSearch = () => {
  if (domainInput.value.trim()) {
    appStore.setDomain(domainInput.value.trim());
    appStore.setLoading(true);
    // TODO: Trigger data fetch
    console.log('Fetching data for:', domainInput.value);

    // Simulate loading (remove this when real fetch is implemented)
    setTimeout(() => {
      appStore.setLoading(false);
    }, 2000);
  }
};

const handleKeypress = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    handleSearch();
  }
};
</script>

<template>
  <div class="sticky top-0 z-50 bg-[#1e1e1e] border-b border-[#3e3e42]">
    <!-- Top bar with branding and search -->
    <div class="w-full px-6 py-4">
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

        <!-- Current domain display -->
        <div v-if="appStore.domain && !appStore.loading" class="flex-shrink-0">
          <div class="px-3 py-1.5 bg-[#252526] border border-[#3e3e42] rounded-md">
            <p class="text-xs text-[#858585]">Current</p>
            <p class="text-sm font-medium text-white">{{ appStore.domain }}</p>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="appStore.loading" class="flex-shrink-0">
          <div
            class="flex items-center gap-2 px-3 py-2 bg-blue-600/10 border border-blue-600/30 rounded-md"
          >
            <svg
              class="animate-spin h-4 w-4 text-blue-500"
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
            <span class="text-sm text-blue-400">Analyzing...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation tabs -->
    <div class="w-full px-6">
      <nav class="flex gap-1 -mb-px max-w-full" aria-label="Tabs">
        <button
          v-for="tab in tabs"
          :key="tab.path"
          @click="navigateToTab(tab.path)"
          :class="[
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
            isActiveTab(tab.path)
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-[#858585] hover:text-[#cccccc] hover:border-[#3e3e42]',
          ]"
          :aria-current="isActiveTab(tab.path) ? 'page' : undefined"
        >
          <span>{{ tab.name }}</span>
          <span class="ml-2 text-xs opacity-60">{{ tab.key }}</span>
        </button>
      </nav>
    </div>
  </div>
</template>
