<script setup lang="ts">
import { computed } from 'vue';
import type { HttpRedirect } from '../models/http';

const props = defineProps<{
  redirects: HttpRedirect[];
  finalUrl: string;
  finalStatusCode: number;
  responseTime: number;
}>();

const getStatusBadgeClass = (status: number) => {
  if (status >= 200 && status < 300) return 'bg-green-500/20 text-green-400 border-green-500/30';
  if (status >= 300 && status < 400)
    return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  if (status >= 400 && status < 500) return 'bg-red-500/20 text-red-400 border-red-500/30';
  if (status >= 500) return 'bg-red-500/20 text-red-400 border-red-500/30';
  return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
};

// Calculate final destination's individual response time
// Total time minus all redirect hop times
const finalDestinationTime = computed(() => {
  const redirectsTime = props.redirects.reduce((sum, redirect) => sum + redirect.response_time, 0);
  return Math.max(0, props.responseTime - redirectsTime);
});

// Open logs slideout
const openLogs = () => {
  window.dispatchEvent(new CustomEvent('app:toggle-logs'));
};
</script>

<template>
  <div class="-mx-4 -mb-4">
    <!-- Hops -->
    <div
      v-for="(redirect, index) in redirects"
      :key="index"
      class="bg-[#2d2d30] px-4 py-3 flex items-center gap-4 cursor-pointer hover:bg-[#323236] transition-colors"
      :class="{ 'border-b border-[#3e3e42]': index < redirects.length - 1 }"
      @click="openLogs"
      :title="`Click to view logs`"
    >
      <span
        :class="[
          'px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0',
          getStatusBadgeClass(redirect.status_code),
        ]"
      >
        {{ redirect.status_code }}
      </span>
      <span class="text-sm text-white font-mono break-all flex-1">
        {{ redirect.from_url }}
      </span>
      <span class="text-xs text-[#858585] flex-shrink-0">
        {{ Math.round(redirect.response_time * 1000) }}ms
      </span>
    </div>

    <!-- Final Destination -->
    <div class="bg-[#0d0d0d] border-t border-[#2a2a2a]">
      <div
        class="px-4 py-3 flex items-center gap-4 cursor-pointer hover:bg-[#1a1a1a] transition-colors"
        @click="openLogs"
        :title="`Click to view logs`"
      >
        <span
          :class="[
            'px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0',
            getStatusBadgeClass(finalStatusCode),
          ]"
        >
          {{ finalStatusCode }}
        </span>
        <span class="text-sm text-white font-mono break-all flex-1">
          {{ finalUrl }}
        </span>
        <span class="text-xs text-[#858585] flex-shrink-0">
          {{ Math.round(finalDestinationTime * 1000) }}ms
        </span>
      </div>
    </div>
  </div>
</template>
