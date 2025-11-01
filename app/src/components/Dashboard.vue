<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAppStore } from '../stores/app';
import { useDNSStore } from '../stores/dns';
import { useCertificateStore } from '../stores/certificate';
import { useWhoisStore } from '../stores/whois';
import { useHttpStore } from '../stores/http';
import { useDnssecStore } from '../stores/dnssec';

const router = useRouter();
const appStore = useAppStore();
const dnsStore = useDNSStore();
const certStore = useCertificateStore();
const whoisStore = useWhoisStore();
const httpStore = useHttpStore();
const dnssecStore = useDnssecStore();

const hasDomain = computed(() => !!appStore.domain);

// DNS counts
const aRecordCount = computed(() => dnsStore.aRecords?.records.length || 0);
const aaaaRecordCount = computed(() => dnsStore.aaaaRecords?.records.length || 0);
const mxRecordCount = computed(() => dnsStore.mxRecords?.records.length || 0);
const nsRecordCount = computed(() => dnsStore.nsRecords?.records.length || 0);

// Certificate info
const certInfo = computed(() => certStore.tlsInfo?.certificate_chain.certificates[0]);
const certDaysUntilExpiry = computed(() => {
  if (!certInfo.value || !certInfo.value.not_after) return null;
  try {
    const expiryDate = new Date(certInfo.value.not_after);
    if (isNaN(expiryDate.getTime())) return null;
    const now = new Date();
    const days = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return days;
  } catch (e) {
    console.error('Error parsing certificate date:', e);
    return null;
  }
});

// WHOIS info
const registrar = computed(() => whoisStore.whoisInfo?.registrar || 'N/A');
const expirationDate = computed(() => {
  if (!whoisStore.whoisInfo?.expiration_date) return 'N/A';
  try {
    const date = new Date(whoisStore.whoisInfo.expiration_date);
    if (isNaN(date.getTime())) return 'N/A';
    return date.toLocaleDateString();
  } catch (e) {
    console.error('Error parsing expiration date:', e);
    return 'N/A';
  }
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

// Overall health calculation
const healthChecks = computed(() => {
  const checks = [];

  // DNS checks
  checks.push({
    name: 'DNS Resolution',
    status: aRecordCount.value > 0 || aaaaRecordCount.value > 0 ? 'pass' : 'fail',
    message:
      aRecordCount.value > 0 || aaaaRecordCount.value > 0
        ? 'Domain resolves correctly'
        : 'No A/AAAA records found',
  });

  let nsStatus: 'pass' | 'warn' | 'fail';
  let nsMessage: string;
  if (nsRecordCount.value >= 2) {
    nsStatus = 'pass';
    nsMessage = `${nsRecordCount.value} nameservers configured`;
  } else if (nsRecordCount.value > 0) {
    nsStatus = 'warn';
    nsMessage = 'Only 1 nameserver (recommend 2+)';
  } else {
    nsStatus = 'fail';
    nsMessage = 'No nameservers found';
  }

  checks.push({
    name: 'Nameservers',
    status: nsStatus,
    message: nsMessage,
  });

  // Certificate checks
  if (certDaysUntilExpiry.value !== null) {
    let certStatus: 'pass' | 'warn' | 'fail';
    let certMessage: string;
    if (certDaysUntilExpiry.value > 30) {
      certStatus = 'pass';
      certMessage = `Valid for ${certDaysUntilExpiry.value} days`;
    } else if (certDaysUntilExpiry.value > 0) {
      certStatus = 'warn';
      certMessage = `Expires in ${certDaysUntilExpiry.value} days`;
    } else {
      certStatus = 'fail';
      certMessage = 'Certificate expired';
    }

    checks.push({
      name: 'SSL Certificate',
      status: certStatus,
      message: certMessage,
    });
  }

  // HTTPS checks
  if (httpsStatus.value > 0) {
    let httpsCheckStatus: 'pass' | 'warn' | 'fail';
    let httpsMessage: string;
    if (httpsStatus.value >= 200 && httpsStatus.value < 300) {
      httpsCheckStatus = 'pass';
      httpsMessage = `Responding with ${httpsStatus.value}`;
    } else if (httpsStatus.value >= 300 && httpsStatus.value < 400) {
      httpsCheckStatus = 'warn';
      httpsMessage = `Redirecting (${httpsStatus.value})`;
    } else {
      httpsCheckStatus = 'fail';
      httpsMessage = `Error ${httpsStatus.value}`;
    }

    checks.push({
      name: 'HTTPS',
      status: httpsCheckStatus,
      message: httpsMessage,
    });
  }

  // Email checks
  checks.push({
    name: 'Email (MX)',
    status: mxRecordCount.value > 0 ? 'pass' : 'warn',
    message:
      mxRecordCount.value > 0
        ? `${mxRecordCount.value} MX record(s) configured`
        : 'No MX records found',
  });

  // WHOIS/Registration checks
  if (whoisStore.whoisInfo) {
    const expirationDate = whoisStore.whoisInfo.expiration_date
      ? new Date(whoisStore.whoisInfo.expiration_date)
      : null;
    if (expirationDate && !isNaN(expirationDate.getTime())) {
      const daysUntilExpiry = Math.floor(
        (expirationDate.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
      );
      let regStatus: 'pass' | 'warn' | 'fail';
      let regMessage: string;
      if (daysUntilExpiry > 90) {
        regStatus = 'pass';
        regMessage = `Expires in ${daysUntilExpiry} days`;
      } else if (daysUntilExpiry > 30) {
        regStatus = 'warn';
        regMessage = `Expires in ${daysUntilExpiry} days`;
      } else if (daysUntilExpiry > 0) {
        regStatus = 'fail';
        regMessage = `Expires soon (${daysUntilExpiry} days)`;
      } else {
        regStatus = 'fail';
        regMessage = 'Domain expired';
      }
      checks.push({
        name: 'Registration',
        status: regStatus,
        message: regMessage,
      });
    }
  }

  // DNSSEC checks
  if (dnssecStore.validation) {
    let dnssecStatus: 'pass' | 'warn' | 'fail';
    let dnssecMessage: string;
    if (dnssecStore.validation.status === 'SECURE') {
      dnssecStatus = 'pass';
      dnssecMessage = 'DNSSEC validated';
    } else if (dnssecStore.validation.status === 'INSECURE') {
      dnssecStatus = 'warn';
      dnssecMessage = 'DNSSEC not configured';
    } else if (dnssecStore.validation.status === 'BOGUS') {
      dnssecStatus = 'fail';
      dnssecMessage = 'DNSSEC validation failed';
    } else {
      dnssecStatus = 'warn';
      dnssecMessage = 'DNSSEC status unknown';
    }
    checks.push({
      name: 'DNSSEC',
      status: dnssecStatus,
      message: dnssecMessage,
    });
  }

  // WWW subdomain check
  if (httpStore.wwwHttpsResponse && httpStore.apexHttpsResponse) {
    const wwwWorks =
      httpStore.wwwHttpsResponse.status_code >= 200 && httpStore.wwwHttpsResponse.status_code < 400;
    const apexWorks =
      httpStore.apexHttpsResponse.status_code >= 200 &&
      httpStore.apexHttpsResponse.status_code < 400;

    if (wwwWorks && apexWorks) {
      checks.push({
        name: 'WWW Subdomain',
        status: 'pass',
        message: 'Both apex and www accessible',
      });
    } else if (wwwWorks || apexWorks) {
      checks.push({
        name: 'WWW Subdomain',
        status: 'warn',
        message: wwwWorks ? 'Only www accessible' : 'Only apex accessible',
      });
    } else {
      checks.push({
        name: 'WWW Subdomain',
        status: 'fail',
        message: 'Neither apex nor www accessible',
      });
    }
  }

  return checks;
});

const overallHealth = computed(() => {
  const total = healthChecks.value.length;
  const passed = healthChecks.value.filter((c) => c.status === 'pass').length;
  const warnings = healthChecks.value.filter((c) => c.status === 'warn').length;
  const failed = healthChecks.value.filter((c) => c.status === 'fail').length;

  const percentage = Math.round((passed / total) * 100);

  let status: 'healthy' | 'warning' | 'critical';
  if (failed > 0) {
    status = 'critical';
  } else if (warnings > 0) {
    status = 'warning';
  } else {
    status = 'healthy';
  }

  return {
    percentage,
    status,
    passed,
    warnings,
    failed,
    total,
  };
});
</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
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
      <div v-else class="space-y-4">
        <!-- Overall Health Card -->
        <div
          class="card p-6"
          :class="{
            'border-l-4 border-l-green-500': overallHealth.status === 'healthy',
            'border-l-4 border-l-yellow-500': overallHealth.status === 'warning',
            'border-l-4 border-l-red-500': overallHealth.status === 'critical',
          }"
        >
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 class="text-2xl font-bold mb-1">Overall Health</h2>
              <p class="text-sm text-[#858585]">{{ appStore.domain }}</p>
            </div>
            <div class="text-right">
              <div
                class="text-4xl font-bold"
                :class="{
                  'text-green-500': overallHealth.status === 'healthy',
                  'text-yellow-500': overallHealth.status === 'warning',
                  'text-red-500': overallHealth.status === 'critical',
                }"
              >
                {{ overallHealth.percentage }}%
              </div>
              <p
                class="text-xs uppercase font-semibold tracking-wide mt-1"
                :class="{
                  'text-green-500': overallHealth.status === 'healthy',
                  'text-yellow-500': overallHealth.status === 'warning',
                  'text-red-500': overallHealth.status === 'critical',
                }"
              >
                {{ overallHealth.status }}
              </p>
            </div>
          </div>

          <!-- Health checks summary -->
          <div class="flex gap-6 mb-4 text-sm">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-green-500"></span>
              <span class="text-[#858585]">{{ overallHealth.passed }} Passed</span>
            </div>
            <div v-if="overallHealth.warnings > 0" class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
              <span class="text-[#858585]">{{ overallHealth.warnings }} Warnings</span>
            </div>
            <div v-if="overallHealth.failed > 0" class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-red-500"></span>
              <span class="text-[#858585]">{{ overallHealth.failed }} Failed</span>
            </div>
          </div>

          <!-- Individual checks -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div
              v-for="check in healthChecks"
              :key="check.name"
              class="flex items-start gap-2 p-3 rounded bg-[#252526]"
            >
              <span
                class="text-lg flex-shrink-0 mt-0.5"
                :class="{
                  'text-green-500': check.status === 'pass',
                  'text-yellow-500': check.status === 'warn',
                  'text-red-500': check.status === 'fail',
                }"
              >
                {{ check.status === 'pass' ? '✓' : check.status === 'warn' ? '⚠' : '✗' }}
              </span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium">{{ check.name }}</p>
                <p class="text-xs text-[#858585] mt-0.5">{{ check.message }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Existing cards grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <!-- 1. Registration Card -->
          <div
            class="card cursor-pointer hover:border-blue-500/50 transition-colors"
            @click="router.push('/registration')"
          >
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-xl font-semibold">Registration</h2>
              <kbd
                class="inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
              >
                2
              </kbd>
            </div>
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

          <!-- 2. DNS Card -->
          <div
            class="card cursor-pointer hover:border-blue-500/50 transition-colors"
            @click="router.push('/dns')"
          >
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-xl font-semibold">DNS</h2>
              <kbd
                class="inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
              >
                3
              </kbd>
            </div>
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

          <!-- 3. DNSSEC Card -->
          <div
            class="card cursor-pointer hover:border-blue-500/50 transition-colors"
            @click="router.push('/dnssec')"
          >
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-xl font-semibold">DNSSEC</h2>
              <kbd
                class="inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
              >
                4
              </kbd>
            </div>
            <div class="text-sm">
              <p class="text-[#858585]">DNSSEC validation status</p>
              <p class="text-xs text-[#858585] mt-2">Coming soon</p>
            </div>
          </div>

          <!-- Certificate Card -->
          <div
            class="card cursor-pointer hover:border-blue-500/50 transition-colors"
            @click="router.push('/certificate')"
          >
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-xl font-semibold">Certificate</h2>
              <kbd
                class="inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
              >
                5
              </kbd>
            </div>
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
          <div
            class="card cursor-pointer hover:border-blue-500/50 transition-colors"
            @click="router.push('/http')"
          >
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-xl font-semibold">HTTP/HTTPS</h2>
              <kbd
                class="inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
              >
                6
              </kbd>
            </div>
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

          <!-- 5. Certificate Card -->
          <div
            class="card cursor-pointer hover:border-blue-500/50 transition-colors"
            @click="router.push('/certificate')"
          >
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-xl font-semibold">Certificate</h2>
              <kbd
                class="inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
              >
                5
              </kbd>
            </div>
            <div v-if="certStore.loading" class="space-y-2">
              <div class="h-3 bg-[#3e3e42] rounded animate-pulse"></div>
              <div class="h-3 bg-[#3e3e42] rounded animate-pulse w-3/4"></div>
            </div>
            <div v-else-if="leafCert" class="space-y-2 text-sm">
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

          <!-- 6. Email Card -->
          <div
            class="card cursor-pointer hover:border-blue-500/50 transition-colors"
            @click="router.push('/email')"
          >
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-xl font-semibold">Email</h2>
              <kbd
                class="inline-flex items-center justify-center w-5 h-5 text-[11px] font-medium rounded border bg-[#3e3e42] border-[#5a5a5f] text-[#b0b0b0]"
              >
                7
              </kbd>
            </div>
            <div class="text-sm">
              <p class="text-[#858585]">Email security configuration</p>
              <p class="text-xs text-[#858585] mt-2">Coming soon</p>
            </div>
          </div>
        </div>
        <!-- End existing cards grid -->
      </div>
    </div>
  </div>
</template>
