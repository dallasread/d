<script setup lang="ts">
import type { HttpResponse } from '../models/http';
import RedirectChain from './RedirectChain.vue';

defineProps<{
  response: HttpResponse;
  icon: string;
}>();
</script>

<template>
  <div class="panel p-0 overflow-hidden">
    <div class="pb-4 flex items-center justify-between">
      <h3 class="text-lg font-semibold flex items-center gap-2">
        <span class="text-2xl">{{ icon }}</span>
        <span>{{ response.url }}</span>
      </h3>
      <span class="text-sm text-[#858585] flex-shrink-0">
        {{ Math.round(response.response_time * 1000) }}ms
      </span>
    </div>

    <!-- Redirect Chain -->
    <RedirectChain
      :redirects="response.redirects || []"
      :final-url="response.final_url"
      :final-status-code="response.status_code"
      :response-time="response.response_time"
    />
  </div>
</template>
