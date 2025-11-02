<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useCertificateStore } from '../stores/certificate';
import PanelLoading from './PanelLoading.vue';

const appStore = useAppStore();
const certStore = useCertificateStore();

const hasDomain = computed(() => !!appStore.domain);

const leafCert = computed(() => certStore.tlsInfo?.certificate_chain.certificates[0]);

const parseDate = (dateString: string | undefined): Date | null => {
  if (!dateString) return null;

  try {
    // Try parsing directly
    let date = new Date(dateString);

    // If that fails, clean up the format and try again
    if (isNaN(date.getTime())) {
      const cleaned = dateString.replace(/\s+/g, ' ').replace(' GMT', '').trim();
      date = new Date(cleaned);
    }

    return isNaN(date.getTime()) ? null : date;
  } catch (e) {
    console.error('Error parsing date:', dateString, e);
    return null;
  }
};

const daysUntilExpiry = computed(() => {
  if (!leafCert.value) {
    console.log('No leaf certificate');
    return null;
  }

  if (!leafCert.value.not_after) {
    console.warn('Leaf cert missing not_after date');
    return null;
  }

  console.log('Parsing not_after date:', leafCert.value.not_after);
  const expiryDate = parseDate(leafCert.value.not_after);

  if (!expiryDate) {
    console.warn('Could not parse expiry date:', leafCert.value.not_after);
    return null;
  }

  const now = new Date();
  const days = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  console.log('Calculated days until expiry:', days);
  return days;
});

const isExpired = computed(() => {
  const days = daysUntilExpiry.value;
  if (days === null) return false;
  return days < 0;
});

const formatDate = (dateString: string | undefined) => {
  if (!dateString) {
    console.warn('formatDate called with empty dateString');
    return 'N/A';
  }

  const date = parseDate(dateString);

  if (!date) {
    console.warn('Could not parse date for formatting:', dateString);
    return dateString; // Return the original string if we can't parse it
  }

  // Format as human-readable date
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

const getStatusText = computed(() => {
  // No certificate data
  if (!leafCert.value) return 'No Certificate';

  // Certificate exists but date couldn't be parsed
  if (daysUntilExpiry.value === null) {
    return 'Valid (Unable to determine expiry)';
  }

  // Certificate is expired
  if (isExpired.value) {
    const daysExpired = Math.abs(daysUntilExpiry.value);
    return `Expired (${daysExpired} days ago)`;
  }

  // Certificate is valid
  return `Valid (${daysUntilExpiry.value} days remaining)`;
});

const getStatusClass = computed(() => {
  // No certificate
  if (!leafCert.value) return 'text-gray-400';

  // Date parsing failed
  if (daysUntilExpiry.value === null) return 'text-yellow-400';

  // Expired
  if (isExpired.value) return 'text-red-400';

  // Expiring soon (30 days or less)
  if (daysUntilExpiry.value <= 30) return 'text-yellow-400';

  // Valid
  return 'text-green-400';
});
</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">SSL/TLS Certificate</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view certificate information</p>
      </div>

      <!-- Loading state -->
      <PanelLoading v-if="certStore.loading" title="SSL Certificate" />

      <!-- Certificate Info - Card Layout -->
      <div v-else-if="leafCert" class="space-y-6">
        <!-- Status Overview Card -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 text-white">Certificate Status</h2>
          <div class="flex items-center gap-4">
            <div
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm',
                isExpired && 'bg-red-500/10 text-red-400 border border-red-500/30',
                !isExpired &&
                  daysUntilExpiry !== null &&
                  daysUntilExpiry > 30 &&
                  'bg-green-500/10 text-green-400 border border-green-500/30',
                !isExpired &&
                  daysUntilExpiry !== null &&
                  daysUntilExpiry <= 30 &&
                  'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30',
              ]"
            >
              <span>{{ getStatusText }}</span>
            </div>
          </div>
        </div>

        <!-- Certificate Details Card -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 text-white">Certificate Details</h2>
          <div class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-[#858585] mb-1">Subject (Issued To)</p>
                <p class="text-base font-medium text-white">
                  {{ leafCert.subject.common_name || 'N/A' }}
                </p>
              </div>
              <div>
                <p class="text-sm text-[#858585] mb-1">Issuer (Certificate Authority)</p>
                <p class="text-base font-medium text-white">
                  {{ leafCert.issuer.organization || leafCert.issuer.common_name || 'N/A' }}
                </p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <p class="text-sm text-[#858585] mb-1">Valid From</p>
                <p class="text-base font-medium text-white">{{ formatDate(leafCert.not_before) }}</p>
              </div>
              <div>
                <p class="text-sm text-[#858585] mb-1">Valid Until</p>
                <p class="text-base font-medium" :class="getStatusClass">
                  {{ formatDate(leafCert.not_after) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Public Key Info Card -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 text-white">Public Key Information</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-[#858585] mb-1">Algorithm</p>
              <p class="text-base font-medium text-white">{{ leafCert.public_key_algorithm }}</p>
            </div>
            <div v-if="leafCert.public_key_size">
              <p class="text-sm text-[#858585] mb-1">Key Size</p>
              <p class="text-base font-medium text-white">{{ leafCert.public_key_size }} bits</p>
            </div>
          </div>
        </div>

        <!-- Subject Alternative Names Card -->
        <div
          v-if="leafCert.subject_alternative_names && leafCert.subject_alternative_names.length > 0"
          class="panel"
        >
          <h2 class="text-xl font-semibold mb-4 text-white flex items-center gap-2">
            Subject Alternative Names
            <span class="text-sm font-normal text-blue-400">{{
              leafCert.subject_alternative_names.length
            }}</span>
          </h2>
          <div class="border border-[#3e3e42] rounded p-3 bg-[#1a1a1a]">
            <div class="space-y-2">
              <div
                v-for="(san, index) in leafCert.subject_alternative_names"
                :key="index"
                class="font-mono text-sm text-[#cccccc] flex items-center gap-2"
              >
                <span class="text-blue-400">•</span>
                <span>{{ san }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Certificate Chain Card -->
        <div v-if="certStore.tlsInfo" class="panel">
          <h2 class="text-xl font-semibold mb-4 text-white">Certificate Chain</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-[#858585] mb-1">Chain Length</p>
              <p class="text-base font-medium text-white">
                {{ certStore.tlsInfo.certificate_chain.certificates.length }} certificate(s)
              </p>
            </div>
            <div>
              <p class="text-sm text-[#858585] mb-1">Chain Valid</p>
              <p
                class="text-base font-medium"
                :class="
                  certStore.tlsInfo.certificate_chain.is_valid ? 'text-green-400' : 'text-red-400'
                "
              >
                {{ certStore.tlsInfo.certificate_chain.is_valid ? 'Yes' : 'No' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Security Features Card -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 text-white">Security Features</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm text-[#858585]">Self-Signed Certificate</span>
              <span
                class="text-sm font-medium"
                :class="
                  leafCert.issuer.common_name === leafCert.subject.common_name
                    ? 'text-red-400'
                    : 'text-green-400'
                "
              >
                {{ leafCert.issuer.common_name === leafCert.subject.common_name ? 'Yes' : 'No' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="certStore.error" class="panel bg-red-900/20 border-red-800">
        <h3 class="text-lg font-semibold text-red-400 mb-2">Error</h3>
        <p class="text-sm text-red-300">{{ certStore.error }}</p>
      </div>

      <!-- No Data -->
      <div v-if="!leafCert && !certStore.loading && hasDomain && !certStore.error" class="panel">
        <p class="text-[#858585]">No certificate data available</p>
        <p class="text-xs text-[#666] mt-2">
          Debug: tlsInfo={{ certStore.tlsInfo }}, loading={{ certStore.loading }}, error={{
            certStore.error
          }}
        </p>
      </div>
    </div>
  </div>
</template>
