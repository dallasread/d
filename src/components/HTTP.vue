<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useHttpStore } from '../stores/http';
import PanelLoading from './PanelLoading.vue';
import HTTPResponse from './HTTPResponse.vue';

const appStore = useAppStore();
const httpStore = useHttpStore();

const hasDomain = computed(() => !!appStore.domain);

const httpSubQueries = computed(() => [
  { name: 'HTTP (port 80)', status: 'loading' as const },
  { name: 'HTTPS (port 443)', status: 'loading' as const },
]);

const getStatusBadgeClass = (status: number) => {
  if (status >= 200 && status < 300) return 'bg-green-500/20 text-green-400 border-green-500/30';
  if (status >= 300 && status < 400)
    return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  if (status >= 400 && status < 500) return 'bg-red-500/20 text-red-400 border-red-500/30';
  if (status >= 500) return 'bg-red-500/20 text-red-400 border-red-500/30';
  return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
};

const getStatusMessage = (status: number) => {
  const messages: Record<number, string> = {
    200: 'OK',
    201: 'Created',
    204: 'No Content',
    301: 'Moved Permanently',
    302: 'Found',
    304: 'Not Modified',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    500: 'Internal Server Error',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
  };
  return messages[status] || 'Unknown';
};
</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">HTTP/HTTPS Status</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view HTTP/HTTPS status</p>
      </div>

      <!-- Loading state -->
      <PanelLoading v-if="httpStore.loading" title="HTTP/HTTPS" :sub-queries="httpSubQueries" />

      <!-- HTTP/HTTPS Card Layout -->
      <div v-else-if="httpStore.httpResponse || httpStore.httpsResponse" class="space-y-6">
        <!-- Primary Domain Section -->
        <div class="space-y-4">
          <!-- HTTP Card -->
          <HTTPResponse v-if="httpStore.httpResponse" :response="httpStore.httpResponse" icon="🌐" />

          <!-- HTTPS Card -->
          <HTTPResponse v-if="httpStore.httpsResponse" :response="httpStore.httpsResponse" icon="🔒" />
        </div>

        <!-- WWW Subdomain Section -->
        <div
          v-if="(httpStore.wwwHttpResponse || httpStore.wwwHttpsResponse) && !appStore.domain?.startsWith('www.')"
          class="space-y-4 pt-6 border-t border-[#3e3e42]"
        >
          <!-- WWW HTTP Card -->
          <HTTPResponse v-if="httpStore.wwwHttpResponse" :response="httpStore.wwwHttpResponse" icon="🌐" />

          <!-- WWW HTTPS Card -->
          <HTTPResponse v-if="httpStore.wwwHttpsResponse" :response="httpStore.wwwHttpsResponse" icon="🔒" />
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="httpStore.error" class="panel bg-red-900/20 border-red-800">
        <h3 class="text-lg font-semibold text-red-400 mb-2">Error</h3>
        <p class="text-sm text-red-300">{{ httpStore.error }}</p>
      </div>

      <!-- No Data -->
      <div
        v-if="
          !httpStore.httpResponse && !httpStore.httpsResponse && !httpStore.loading && hasDomain
        "
        class="panel"
      >
        <p class="text-[#858585]">No HTTP/HTTPS data available</p>
      </div>
    </div>
  </div>
</template>
