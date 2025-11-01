<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useHttpStore } from '../stores/http';
import PanelLoading from './PanelLoading.vue';

const appStore = useAppStore();
const httpStore = useHttpStore();

const hasDomain = computed(() => !!appStore.domain);

const httpSubQueries = computed(() => [
  { name: 'HTTP (port 80)', status: 'loading' as const },
  { name: 'HTTPS (port 443)', status: 'loading' as const },
]);

const getStatusClass = (status: number) => {
  if (status >= 200 && status < 300) return 'status-pass';
  if (status >= 300 && status < 400) return 'status-warn';
  if (status >= 400 && status < 500) return 'status-fail';
  if (status >= 500) return 'status-fail';
  return 'text-[#858585]';
};

const getStatusText = (status: number) => {
  if (status >= 200 && status < 300) return 'Success';
  if (status >= 300 && status < 400) return 'Redirect';
  if (status >= 400 && status < 500) return 'Client Error';
  if (status >= 500) return 'Server Error';
  return 'Unknown';
};
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">HTTP/HTTPS Status</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view HTTP/HTTPS status</p>
      </div>

      <!-- Loading state -->
      <PanelLoading v-if="httpStore.loading" title="HTTP/HTTPS" :sub-queries="httpSubQueries" />

      <!-- HTTP/HTTPS Info -->
      <div v-else class="space-y-6">
        <!-- HTTPS Response -->
        <div v-if="httpStore.httpsResponse" class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                clip-rule="evenodd"
              />
            </svg>
            HTTPS Response
          </h2>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <p class="text-sm text-[#858585]">Status Code</p>
              <p
                :class="['text-2xl font-bold', getStatusClass(httpStore.httpsResponse.status_code)]"
              >
                {{ httpStore.httpsResponse.status_code }}
              </p>
              <p class="text-xs text-[#858585]">
                {{ getStatusText(httpStore.httpsResponse.status_code) }}
              </p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Response Time</p>
              <p class="text-2xl font-bold">
                {{ Math.round(httpStore.httpsResponse.response_time * 1000) }}ms
              </p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Redirects</p>
              <p class="text-2xl font-bold">{{ httpStore.httpsResponse.redirects.length }}</p>
            </div>
          </div>

          <div class="space-y-3">
            <div>
              <p class="text-sm text-[#858585]">Original URL</p>
              <p class="font-mono text-sm break-all">{{ httpStore.httpsResponse.url }}</p>
            </div>
            <div v-if="httpStore.httpsResponse.final_url !== httpStore.httpsResponse.url">
              <p class="text-sm text-[#858585]">Final URL</p>
              <p class="font-mono text-sm break-all text-blue-400">
                {{ httpStore.httpsResponse.final_url }}
              </p>
            </div>
          </div>

          <!-- Redirect Chain -->
          <div v-if="httpStore.httpsResponse.redirects.length > 0" class="mt-6">
            <h3 class="text-lg font-semibold mb-3">Redirect Chain</h3>
            <div class="space-y-2">
              <div
                v-for="(redirect, index) in httpStore.httpsResponse.redirects"
                :key="index"
                class="flex items-start gap-3 p-3 bg-[#1e1e1e] rounded border border-[#3e3e42]"
              >
                <div class="flex-shrink-0 mt-1">
                  <span class="text-xs px-2 py-1 bg-[#3e3e42] rounded">{{ index + 1 }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <span
                      :class="['font-mono text-sm font-bold', getStatusClass(redirect.status_code)]"
                    >
                      {{ redirect.status_code }}
                    </span>
                    <span class="text-xs text-[#858585]">{{
                      getStatusText(redirect.status_code)
                    }}</span>
                  </div>
                  <p class="font-mono text-xs text-[#858585] break-all">
                    From: {{ redirect.from_url }}
                  </p>
                  <p class="font-mono text-xs text-blue-400 break-all">To: {{ redirect.to_url }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Response Headers -->
          <div v-if="Object.keys(httpStore.httpsResponse.headers).length > 0" class="mt-6">
            <h3 class="text-lg font-semibold mb-3">Response Headers</h3>
            <div class="bg-[#1e1e1e] rounded p-4 overflow-x-auto">
              <table class="w-full text-sm">
                <tbody>
                  <tr
                    v-for="(value, key) in httpStore.httpsResponse.headers"
                    :key="key"
                    class="border-b border-[#3e3e42]/50 last:border-0"
                  >
                    <td class="py-2 pr-4 text-[#858585] font-mono text-xs">{{ key }}:</td>
                    <td class="py-2 font-mono text-xs break-all">{{ value }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- HTTP Response (if different from HTTPS) -->
        <div v-if="httpStore.httpResponse" class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-[#858585]" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M10 1.944A11.954 11.954 0 012.166 5C2.056 5.649 2 6.319 2 7c0 5.225 3.34 9.67 8 11.317C14.66 16.67 18 12.225 18 7c0-.682-.057-1.35-.166-2.001A11.954 11.954 0 0110 1.944zM11 14a1 1 0 11-2 0 1 1 0 012 0zm0-7a1 1 0 10-2 0v3a1 1 0 102 0V7z"
                clip-rule="evenodd"
              />
            </svg>
            HTTP Response
            <span class="text-xs text-[#858585]">(Insecure)</span>
          </h2>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p class="text-sm text-[#858585]">Status Code</p>
              <p
                :class="['text-2xl font-bold', getStatusClass(httpStore.httpResponse.status_code)]"
              >
                {{ httpStore.httpResponse.status_code }}
              </p>
              <p class="text-xs text-[#858585]">
                {{ getStatusText(httpStore.httpResponse.status_code) }}
              </p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Response Time</p>
              <p class="text-2xl font-bold">
                {{ Math.round(httpStore.httpResponse.response_time * 1000) }}ms
              </p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Redirects</p>
              <p class="text-2xl font-bold">{{ httpStore.httpResponse.redirects.length }}</p>
            </div>
          </div>
        </div>

        <!-- No HTTPS -->
        <div
          v-if="!httpStore.httpsResponse && !httpStore.loading"
          class="panel bg-yellow-900/20 border-yellow-800"
        >
          <h3 class="text-lg font-semibold text-yellow-400 mb-2">⚠ No HTTPS</h3>
          <p class="text-sm text-yellow-300">This domain does not support HTTPS connections.</p>
        </div>

        <!-- Error Display -->
        <div v-if="httpStore.error" class="panel bg-red-900/20 border-red-800">
          <h3 class="text-lg font-semibold text-red-400 mb-2">Error</h3>
          <p class="text-sm text-red-300">{{ httpStore.error }}</p>
        </div>
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
