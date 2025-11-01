<script setup lang="ts">
interface SubQuery {
  name: string;
  status: 'pending' | 'loading' | 'completed' | 'failed';
}

interface Props {
  title: string;
  subQueries?: SubQuery[];
}

defineProps<Props>();

const getIcon = (status: string) => {
  if (status === 'completed') return '✓';
  if (status === 'failed') return '✗';
  if (status === 'loading') return '●';
  return '○';
};

const getColor = (status: string) => {
  if (status === 'completed') return 'text-green-400';
  if (status === 'failed') return 'text-red-400';
  if (status === 'loading') return 'text-blue-400';
  return 'text-gray-500';
};
</script>

<template>
  <div class="panel">
    <div class="flex items-center gap-3 mb-4">
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
      <h2 class="text-lg font-semibold text-white">Loading {{ title }}...</h2>
    </div>

    <div v-if="subQueries && subQueries.length > 0" class="space-y-2">
      <div
        v-for="subQuery in subQueries"
        :key="subQuery.name"
        class="flex items-center gap-3 py-2 border-l-2 border-[#3e3e42] pl-4"
      >
        <span
          :class="[
            'text-base font-mono flex-shrink-0 w-6 text-center',
            getColor(subQuery.status),
            subQuery.status === 'loading' && 'animate-pulse'
          ]"
        >
          {{ getIcon(subQuery.status) }}
        </span>
        <span class="flex-1 text-[#cccccc]">{{ subQuery.name }}</span>
        <span v-if="subQuery.status === 'loading'" class="text-xs text-[#858585]">querying...</span>
        <span v-else-if="subQuery.status === 'failed'" class="text-xs text-red-400">failed</span>
        <span v-else-if="subQuery.status === 'completed'" class="text-xs text-green-400">done</span>
      </div>
    </div>

    <div v-else class="text-[#858585]">
      <p>Querying data...</p>
    </div>
  </div>
</template>
