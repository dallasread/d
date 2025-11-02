<script setup lang="ts">
import { computed } from 'vue';
import type { HttpRedirect } from '../models/http';
import { useLogsStore } from '../stores/logs';

const props = defineProps<{
  redirects: HttpRedirect[];
  finalUrl: string;
  finalStatusCode: number;
  responseTime: number;
}>();

const logsStore = useLogsStore();

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

// Open logs slideout with the most recent curl log for a given URL
const openLogForUrl = (url: string) => {
  console.log('Looking for curl log with URL:', url);

  // Find all curl logs
  const allCurlLogs = logsStore.logs.filter((log) => log.tool === 'curl');
  console.log('All curl logs:', allCurlLogs.map(l => ({ id: l.id, args: l.args })));

  // Find the most recent curl log for this exact URL (should be the last arg)
  const curlLogs = allCurlLogs.filter(
    (log) => log.args.length > 0 && log.args[log.args.length - 1] === url
  );

  console.log('Matching curl logs:', curlLogs.map(l => ({ id: l.id, args: l.args })));

  if (curlLogs.length > 0) {
    // Dispatch custom event to open logs with this log expanded
    window.dispatchEvent(
      new CustomEvent('app:open-logs', {
        detail: { logId: curlLogs[0].id },
      })
    );
  } else {
    // If exact match not found, just open the logs slideout
    console.log('No exact match found, opening logs slideout');
    window.dispatchEvent(new CustomEvent('app:toggle-logs'));
  }
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
      @click="openLogForUrl(redirect.from_url)"
      :title="`Click to view curl log for ${redirect.from_url}`"
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
        @click="openLogForUrl(finalUrl)"
        :title="`Click to view curl log for ${finalUrl}`"
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
