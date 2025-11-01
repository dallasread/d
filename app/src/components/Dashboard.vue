<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useDNSStore } from '../stores/dns';
import { useCertificateStore } from '../stores/certificate';
import { useWhoisStore } from '../stores/whois';
import { useHttpStore } from '../stores/http';

const appStore = useAppStore();
const dnsStore = useDNSStore();
const certStore = useCertificateStore();
const whoisStore = useWhoisStore();
const httpStore = useHttpStore();

const hasDomain = computed(() => !!appStore.domain);

// DNS counts
const aRecordCount = computed(() => dnsStore.aRecords?.records.length || 0);
const aaaaRecordCount = computed(() => dnsStore.aaaaRecords?.records.length || 0);
const mxRecordCount = computed(() => dnsStore.mxRecords?.records.length || 0);
const nsRecordCount = computed(() => dnsStore.nsRecords?.records.length || 0);

// Certificate info
const certInfo = computed(() => certStore.tlsInfo?.certificate_chain.certificates[0]);
const certDaysUntilExpiry = computed(() => {
  if (!certInfo.value) return null;
  const expiryDate = new Date(certInfo.value.not_after);
  const now = new Date();
  const days = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return days;
});

// WHOIS info
const registrar = computed(() => whoisStore.whoisInfo?.registrar || 'N/A');
const expirationDate = computed(() => {
  if (!whoisStore.whoisInfo?.expiration_date) return 'N/A';
  return new Date(whoisStore.whoisInfo.expiration_date).toLocaleDateString();
});

// HTTP status
const httpsStatus = computed(() => httpStore.httpsResponse?.status_code || 0);
const httpResponseTime = computed(() => {
  if (!httpStore.httpsResponse) return 0;
  return Math.round(httpStore.httpsResponse.response_time * 1000);
});

// Status helpers
const getStatusClass = (value: number, goodThreshold: number) => {
  if (value === 0) return 'text-[#858585]';
  if (value >= goodThreshold) return 'status-pass';
  return 'status-warn';
};

const getCertStatusClass = (days: number | null) => {
  if (days === null) return 'text-[#858585]';
  if (days > 30) return 'status-pass';
  if (days > 0) return 'status-warn';
  return 'status-fail';
};

const getHttpStatusClass = (status: number) => {
  if (status === 0) return 'text-[#858585]';
  if (status >= 200 && status < 300) return 'status-pass';
  if (status >= 300 && status < 400) return 'status-warn';
  return 'status-fail';
};
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
          <h2 class="text-xl font-semibold mb-4">Registration</h2>
          <div v-if="whoisStore.loading" class="space-y-3">
            <div class="h-4 bg-[#3e3e42] rounded animate-pulse"></div>
            <div class="h-4 bg-[#3e3e42] rounded animate-pulse w-3/4"></div>
          </div>
          <div v-else-if="whoisStore.whoisInfo" class="space-y-3">
            <div>
              <p class="text-xs text-[#858585]">Registrar</p>
              <p class="text-sm font-medium">{{ registrar }}</p>
            </div>
            <div>
              <p class="text-xs text-[#858585]">Expires</p>
              <p class="text-sm font-medium">{{ expirationDate }}</p>
            </div>
            <div>
              <p class="text-xs text-[#858585]">Nameservers</p>
              <p class="text-sm font-medium">
                {{ whoisStore.whoisInfo.nameservers.length }} servers
              </p>
            </div>
            <div v-if="whoisStore.whoisInfo.dnssec">
              <p class="text-xs text-[#858585]">DNSSEC</p>
              <p class="text-sm font-medium">{{ whoisStore.whoisInfo.dnssec }}</p>
            </div>
          </div>
          <p v-else class="text-[#858585] text-sm">No registration data</p>
        </div>

        <!-- DNS Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">DNS</h2>
          <div v-if="dnsStore.loading" class="space-y-2">
            <div class="h-3 bg-[#3e3e42] rounded animate-pulse"></div>
            <div class="h-3 bg-[#3e3e42] rounded animate-pulse w-2/3"></div>
          </div>
          <div v-else class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-[#858585]">A Records:</span>
              <span :class="getStatusClass(aRecordCount, 1)">{{ aRecordCount }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-[#858585]">AAAA Records:</span>
              <span :class="getStatusClass(aaaaRecordCount, 1)">{{ aaaaRecordCount }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-[#858585]">MX Records:</span>
              <span :class="getStatusClass(mxRecordCount, 1)">{{ mxRecordCount }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-[#858585]">NS Records:</span>
              <span :class="getStatusClass(nsRecordCount, 2)">{{ nsRecordCount }}</span>
            </div>
          </div>
        </div>

        <!-- Email Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Email</h2>
          <div class="text-sm">
            <p class="text-[#858585]">Email security configuration</p>
            <p class="text-xs text-[#858585] mt-2">Coming soon</p>
          </div>
        </div>

        <!-- DNSSEC Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">DNSSEC</h2>
          <div class="text-sm">
            <p class="text-[#858585]">DNSSEC validation status</p>
            <p class="text-xs text-[#858585] mt-2">Coming soon</p>
          </div>
        </div>

        <!-- Certificate Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-4">Certificate</h2>
          <div v-if="certStore.loading" class="space-y-2">
            <div class="h-3 bg-[#3e3e42] rounded animate-pulse"></div>
            <div class="h-3 bg-[#3e3e42] rounded animate-pulse w-3/4"></div>
          </div>
          <div v-else-if="certInfo" class="space-y-2 text-sm">
            <div>
              <p class="text-xs text-[#858585]">Issued To</p>
              <p class="text-sm font-medium truncate">
                {{ certInfo.subject.common_name || 'N/A' }}
              </p>
            </div>
            <div>
              <p class="text-xs text-[#858585]">Issued By</p>
              <p class="text-sm font-medium truncate">
                {{ certInfo.issuer.organization || 'N/A' }}
              </p>
            </div>
            <div>
              <p class="text-xs text-[#858585]">Expires</p>
              <p :class="['text-sm font-medium', getCertStatusClass(certDaysUntilExpiry)]">
                {{ certDaysUntilExpiry !== null ? `${certDaysUntilExpiry} days` : 'N/A' }}
              </p>
            </div>
          </div>
          <p v-else class="text-[#858585] text-sm">No certificate data</p>
        </div>

        <!-- HTTP Card -->
        <div class="card lg:col-span-2">
          <h2 class="text-xl font-semibold mb-4">HTTP/HTTPS</h2>
          <div v-if="httpStore.loading" class="space-y-2">
            <div class="h-3 bg-[#3e3e42] rounded animate-pulse"></div>
            <div class="h-3 bg-[#3e3e42] rounded animate-pulse w-1/2"></div>
          </div>
          <div v-else-if="httpStore.httpsResponse" class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-[#858585]">HTTPS Status:</span>
              <span :class="getHttpStatusClass(httpsStatus)">{{ httpsStatus || 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-[#858585]">Response Time:</span>
              <span class="text-white">{{ httpResponseTime }}ms</span>
            </div>
            <div class="flex justify-between">
              <span class="text-[#858585]">Redirects:</span>
              <span class="text-white">{{ httpStore.httpsResponse.redirects.length }}</span>
            </div>
          </div>
          <p v-else class="text-[#858585] text-sm">No HTTP data</p>
        </div>
      </div>
    </div>
  </div>
</template>
