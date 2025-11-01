<script setup lang="ts">
import { useAppStore } from '../stores/app';

const emit = defineEmits<{
  click: [];
}>();

const appStore = useAppStore();
</script>

<template>
  <button
    @click="emit('click')"
    :disabled="!appStore.domain || appStore.loading"
    class="fixed bottom-6 right-24 flex items-center gap-2 px-4 py-3 bg-[#252526] hover:bg-[#2d2d30] border border-[#3e3e42] rounded-lg shadow-lg transition-colors group z-30 disabled:opacity-50 disabled:cursor-not-allowed"
    title="Refresh domain data"
  >
    <svg
      class="w-4 h-4 text-[#858585] group-hover:text-white transition-colors"
      :class="{ 'animate-spin': appStore.loading }"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
    <span class="text-sm font-medium text-[#858585] group-hover:text-white transition-colors">
      Refresh
    </span>
    <kbd
      class="hidden md:inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
    >
      R
    </kbd>
  </button>
</template>
