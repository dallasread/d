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
  if (status >= 200 && status < 300) return 'text-green-400';
  if (status >= 300 && status < 400) return 'text-yellow-400';
  if (status >= 400 && status < 500) return 'text-red-400';
  if (status >= 500) return 'text-red-400';
  return 'text-[#858585]';
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
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">HTTP/HTTPS Status</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view HTTP/HTTPS status</p>
      </div>

      <!-- Loading state -->
      <PanelLoading v-if="httpStore.loading" title="HTTP/HTTPS" :sub-queries="httpSubQueries" />

      <!-- HTTP/HTTPS Terminal-Style Display -->
      <div v-else-if="httpStore.httpResponse || httpStore.httpsResponse">
        <div class="terminal-output">
          <!-- Title -->
          <div class="terminal-title">HTTP/HTTPS Status for {{ appStore.domain }}</div>
          <div class="terminal-subtitle">Using: HTTP data from state</div>
          <div class="terminal-spacer"></div>

          <!-- Apex Domain HTTP -->
          <div v-if="httpStore.httpResponse" class="mb-8">
            <div class="mb-2">
              <span class="text-white font-bold">Apex Domain:</span>
            </div>
            <div class="mb-2">
              <span class="text-yellow-400 font-bold">HTTP://{{ appStore.domain }}</span>
            </div>
            <div class="ml-4 space-y-1">
              <div>
                <span :class="['font-bold', getStatusClass(httpStore.httpResponse.status_code)]"
                  >✓ Status: {{ httpStore.httpResponse.status_code }}
                  {{ getStatusMessage(httpStore.httpResponse.status_code) }}</span
                >
              </div>
              <div class="text-[#cccccc]">
                Response Time: {{ Math.round(httpStore.httpResponse.response_time * 1000) }}ms
              </div>

              <!-- Redirect Chain for HTTP -->
              <div v-if="httpStore.httpResponse.redirects.length > 0" class="mt-3">
                <div class="text-[#cccccc]">
                  Redirect Chain ({{ httpStore.httpResponse.redirects.length }} hop(s)):
                </div>
                <div class="ml-2 space-y-1 mt-1">
                  <div v-for="(redirect, index) in httpStore.httpResponse.redirects" :key="index">
                    <span :class="['font-bold', getStatusClass(redirect.status_code)]"
                      >{{ index + 1 }}. {{ redirect.status_code }}</span
                    >
                    <span class="text-[#cccccc]"> {{ redirect.from_url }}</span>
                    <div class="ml-5 text-[#cccccc]">→ {{ redirect.to_url }}</div>
                  </div>
                  <div class="text-green-400 mt-1">
                    Final: {{ httpStore.httpResponse.final_url }} ({{
                      httpStore.httpResponse.status_code
                    }})
                  </div>
                </div>
              </div>

              <!-- Important Headers -->
              <div v-if="httpStore.httpResponse.headers" class="mt-3 space-y-0.5 text-[#cccccc]">
                <div v-if="httpStore.httpResponse.headers['server']">
                  Server: {{ httpStore.httpResponse.headers['server'] }}
                </div>
                <div v-if="httpStore.httpResponse.headers['content-type']">
                  Content-Type: {{ httpStore.httpResponse.headers['content-type'] }}
                </div>
                <div v-if="httpStore.httpResponse.headers['content-length']">
                  Content-Length: {{ httpStore.httpResponse.headers['content-length'] }} bytes
                </div>
              </div>
            </div>
          </div>

          <!-- Apex Domain HTTPS -->
          <div v-if="httpStore.httpsResponse" class="mb-8">
            <div class="mb-2">
              <span class="text-yellow-400 font-bold">HTTPS://{{ appStore.domain }}</span>
            </div>
            <div class="ml-4 space-y-1">
              <div>
                <span :class="['font-bold', getStatusClass(httpStore.httpsResponse.status_code)]"
                  >✓ Status: {{ httpStore.httpsResponse.status_code }}
                  {{ getStatusMessage(httpStore.httpsResponse.status_code) }}</span
                >
              </div>
              <div class="text-[#cccccc]">
                Response Time: {{ Math.round(httpStore.httpsResponse.response_time * 1000) }}ms
              </div>

              <!-- Redirect Chain for HTTPS -->
              <div v-if="httpStore.httpsResponse.redirects.length > 0" class="mt-3">
                <div class="text-[#cccccc]">
                  Redirect Chain ({{ httpStore.httpsResponse.redirects.length }} hop(s)):
                </div>
                <div class="ml-2 space-y-1 mt-1">
                  <div v-for="(redirect, index) in httpStore.httpsResponse.redirects" :key="index">
                    <span :class="['font-bold', getStatusClass(redirect.status_code)]"
                      >{{ index + 1 }}. {{ redirect.status_code }}</span
                    >
                    <span class="text-[#cccccc]"> {{ redirect.from_url }}</span>
                    <div class="ml-5 text-[#cccccc]">→ {{ redirect.to_url }}</div>
                  </div>
                  <div class="text-green-400 mt-1">
                    Final: {{ httpStore.httpsResponse.final_url }} ({{
                      httpStore.httpsResponse.status_code
                    }})
                  </div>
                </div>
              </div>

              <!-- Important Headers -->
              <div v-if="httpStore.httpsResponse.headers" class="mt-3 space-y-0.5 text-[#cccccc]">
                <div v-if="httpStore.httpsResponse.headers['server']">
                  Server: {{ httpStore.httpsResponse.headers['server'] }}
                </div>
                <div v-if="httpStore.httpsResponse.headers['content-type']">
                  Content-Type: {{ httpStore.httpsResponse.headers['content-type'] }}
                </div>
                <div v-if="httpStore.httpsResponse.headers['content-length']">
                  Content-Length: {{ httpStore.httpsResponse.headers['content-length'] }} bytes
                </div>
              </div>
            </div>
          </div>

          <!-- WWW Subdomain Section -->
          <div v-if="httpStore.wwwHttpResponse || httpStore.wwwHttpsResponse" class="mb-8">
            <div class="mb-2">
              <span class="text-white font-bold">WWW Subdomain:</span>
            </div>

            <!-- WWW HTTP -->
            <div v-if="httpStore.wwwHttpResponse" class="mb-4">
              <div class="mb-2">
                <span class="text-yellow-400 font-bold">HTTP://www.{{ appStore.domain }}</span>
              </div>
              <div class="ml-4 space-y-1">
                <div>
                  <span
                    :class="['font-bold', getStatusClass(httpStore.wwwHttpResponse.status_code)]"
                    >✓ Status: {{ httpStore.wwwHttpResponse.status_code }}
                    {{ getStatusMessage(httpStore.wwwHttpResponse.status_code) }}</span
                  >
                </div>
                <div class="text-[#cccccc]">
                  Response Time: {{ Math.round(httpStore.wwwHttpResponse.response_time * 1000) }}ms
                </div>

                <!-- Redirect Chain for WWW HTTP -->
                <div v-if="httpStore.wwwHttpResponse.redirects.length > 0" class="mt-3">
                  <div class="text-[#cccccc]">
                    Redirect Chain ({{ httpStore.wwwHttpResponse.redirects.length }} hop(s)):
                  </div>
                  <div class="ml-2 space-y-1 mt-1">
                    <div
                      v-for="(redirect, index) in httpStore.wwwHttpResponse.redirects"
                      :key="index"
                    >
                      <span :class="['font-bold', getStatusClass(redirect.status_code)]"
                        >{{ index + 1 }}. {{ redirect.status_code }}</span
                      >
                      <span class="text-[#cccccc]"> {{ redirect.from_url }}</span>
                      <div class="ml-5 text-[#cccccc]">→ {{ redirect.to_url }}</div>
                    </div>
                    <div class="text-green-400 mt-1">
                      Final: {{ httpStore.wwwHttpResponse.final_url }} ({{
                        httpStore.wwwHttpResponse.status_code
                      }})
                    </div>
                  </div>
                </div>

                <!-- Important Headers -->
                <div
                  v-if="httpStore.wwwHttpResponse.headers"
                  class="mt-3 space-y-0.5 text-[#cccccc]"
                >
                  <div v-if="httpStore.wwwHttpResponse.headers['server']">
                    Server: {{ httpStore.wwwHttpResponse.headers['server'] }}
                  </div>
                  <div v-if="httpStore.wwwHttpResponse.headers['content-type']">
                    Content-Type: {{ httpStore.wwwHttpResponse.headers['content-type'] }}
                  </div>
                  <div v-if="httpStore.wwwHttpResponse.headers['content-length']">
                    Content-Length: {{ httpStore.wwwHttpResponse.headers['content-length'] }} bytes
                  </div>
                </div>
              </div>
            </div>

            <!-- WWW HTTPS -->
            <div v-if="httpStore.wwwHttpsResponse">
              <div class="mb-2">
                <span class="text-yellow-400 font-bold">HTTPS://www.{{ appStore.domain }}</span>
              </div>
              <div class="ml-4 space-y-1">
                <div>
                  <span
                    :class="['font-bold', getStatusClass(httpStore.wwwHttpsResponse.status_code)]"
                    >✓ Status: {{ httpStore.wwwHttpsResponse.status_code }}
                    {{ getStatusMessage(httpStore.wwwHttpsResponse.status_code) }}</span
                  >
                </div>
                <div class="text-[#cccccc]">
                  Response Time: {{ Math.round(httpStore.wwwHttpsResponse.response_time * 1000) }}ms
                </div>

                <!-- Redirect Chain for WWW HTTPS -->
                <div v-if="httpStore.wwwHttpsResponse.redirects.length > 0" class="mt-3">
                  <div class="text-[#cccccc]">
                    Redirect Chain ({{ httpStore.wwwHttpsResponse.redirects.length }} hop(s)):
                  </div>
                  <div class="ml-2 space-y-1 mt-1">
                    <div
                      v-for="(redirect, index) in httpStore.wwwHttpsResponse.redirects"
                      :key="index"
                    >
                      <span :class="['font-bold', getStatusClass(redirect.status_code)]"
                        >{{ index + 1 }}. {{ redirect.status_code }}</span
                      >
                      <span class="text-[#cccccc]"> {{ redirect.from_url }}</span>
                      <div class="ml-5 text-[#cccccc]">→ {{ redirect.to_url }}</div>
                    </div>
                    <div class="text-green-400 mt-1">
                      Final: {{ httpStore.wwwHttpsResponse.final_url }} ({{
                        httpStore.wwwHttpsResponse.status_code
                      }})
                    </div>
                  </div>
                </div>

                <!-- Important Headers -->
                <div
                  v-if="httpStore.wwwHttpsResponse.headers"
                  class="mt-3 space-y-0.5 text-[#cccccc]"
                >
                  <div v-if="httpStore.wwwHttpsResponse.headers['server']">
                    Server: {{ httpStore.wwwHttpsResponse.headers['server'] }}
                  </div>
                  <div v-if="httpStore.wwwHttpsResponse.headers['content-type']">
                    Content-Type: {{ httpStore.wwwHttpsResponse.headers['content-type'] }}
                  </div>
                  <div v-if="httpStore.wwwHttpsResponse.headers['content-length']">
                    Content-Length: {{ httpStore.wwwHttpsResponse.headers['content-length'] }} bytes
                  </div>
                </div>
              </div>
            </div>
          </div>
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

<style scoped>
.terminal-output {
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 1.5rem;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #e0e0e0;
}

.terminal-title {
  color: #00ffff;
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.terminal-subtitle {
  color: #666;
  font-size: 0.75rem;
}

.terminal-spacer {
  margin-bottom: 1.5rem;
}

.terminal-section-title {
  color: #ffffff;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.terminal-url {
  color: #ffff00;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.terminal-content {
  margin-left: 2rem;
}

.terminal-line {
  margin-bottom: 0.25rem;
}

.status-pass {
  color: #4ec9b0;
}

.status-warn {
  color: #dcdcaa;
}

.status-fail {
  color: #f48771;
}
</style>
