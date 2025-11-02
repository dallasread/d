<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useCertificateStore } from '../stores/certificate';
import PanelLoading from './PanelLoading.vue';

const appStore = useAppStore();
const certStore = useCertificateStore();

const hasDomain = computed(() => !!appStore.domain);

const leafCert = computed(() => certStore.tlsInfo?.certificate_chain.certificates[0]);

const daysUntilExpiry = computed(() => {
  if (!leafCert.value || !leafCert.value.not_after) return null;
  try {
    const expiryDate = new Date(leafCert.value.not_after);
    if (isNaN(expiryDate.getTime())) return null;
    const now = new Date();
    const days = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return days;
  } catch (e) {
    console.error('Error calculating days until expiry:', e);
    return null;
  }
});

const isExpired = computed(() => {
  if (!leafCert.value || !leafCert.value.not_after) return false;
  try {
    const expiryDate = new Date(leafCert.value.not_after);
    if (isNaN(expiryDate.getTime())) return false;
    return expiryDate < new Date();
  } catch (e) {
    console.error('Error checking expiration:', e);
    return false;
  }
});

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A';
  try {
    // OpenSSL outputs dates in format like "Jan  1 00:00:00 2024 GMT"
    // Try to parse it directly first
    let date = new Date(dateString);

    // If that fails, try to clean up the format
    if (isNaN(date.getTime())) {
      // Remove extra spaces and GMT
      const cleaned = dateString.replace(/\s+/g, ' ').replace(' GMT', '').trim();
      date = new Date(cleaned);
    }

    if (isNaN(date.getTime())) {
      console.warn('Could not parse date:', dateString);
      return dateString; // Return the original string if we can't parse it
    }

    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
  } catch (e) {
    console.error('Error formatting date:', e, 'for dateString:', dateString);
    return dateString; // Return original string on error
  }
};

const getStatusText = computed(() => {
  if (isExpired.value) return 'Expired';
  if (daysUntilExpiry.value !== null) {
    return `Valid (${daysUntilExpiry.value} days remaining)`;
  }
  return 'Unknown';
});

const getStatusClass = computed(() => {
  if (isExpired.value) return 'text-red-400';
  if (daysUntilExpiry.value !== null && daysUntilExpiry.value > 30) return 'text-green-400';
  if (daysUntilExpiry.value !== null && daysUntilExpiry.value > 0) return 'text-yellow-400';
  return 'text-gray-400';
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

      <!-- Certificate Info - Terminal Style -->
      <div v-else-if="leafCert" class="space-y-6">
        <div class="bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg p-6 font-mono text-sm">
          <!-- Title -->
          <div class="mb-6">
            <span class="text-cyan-400 font-bold text-base"
              >SSL/TLS Certificate for {{ appStore.domain }}</span
            >
          </div>

          <div class="space-y-6">
            <!-- Certificate Details -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">Certificate Details:</div>
              <div class="ml-4 space-y-1">
                <div class="text-gray-300">
                  Subject:
                  <span class="text-white">{{ leafCert.subject.common_name || 'N/A' }}</span>
                </div>
                <div class="text-gray-300">
                  Issuer:
                  <span class="text-white">{{
                    leafCert.issuer.organization || leafCert.issuer.common_name || 'N/A'
                  }}</span>
                </div>
                <div class="text-gray-300">
                  Valid From: <span class="text-white">{{ formatDate(leafCert.not_before) }}</span>
                </div>
                <div class="text-gray-300">
                  Valid Until: <span class="text-white">{{ formatDate(leafCert.not_after) }}</span>
                </div>
                <div class="text-gray-300">
                  Status: <span :class="getStatusClass">{{ getStatusText }}</span>
                </div>
              </div>
            </div>

            <!-- Public Key -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">Public Key:</div>
              <div class="ml-4 space-y-1">
                <div class="text-gray-300">
                  Algorithm: <span class="text-white">{{ leafCert.public_key_algorithm }}</span>
                </div>
                <div v-if="leafCert.public_key_size" class="text-gray-300">
                  Size: <span class="text-white">{{ leafCert.public_key_size }} bits</span>
                </div>
              </div>
            </div>

            <!-- Subject Alternative Names -->
            <div
              v-if="
                leafCert.subject_alternative_names && leafCert.subject_alternative_names.length > 0
              "
              class="mb-6"
            >
              <div class="text-yellow-400 font-bold mb-2">Subject Alternative Names:</div>
              <div class="ml-4 space-y-1">
                <div
                  v-for="(san, index) in leafCert.subject_alternative_names"
                  :key="index"
                  class="text-gray-300"
                >
                  • <span class="text-white">{{ san }}</span>
                </div>
              </div>
            </div>

            <!-- Certificate Chain -->
            <div v-if="certStore.tlsInfo" class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">Certificate Chain:</div>
              <div class="ml-4 space-y-1">
                <div class="text-gray-300">
                  Chain Length:
                  <span class="text-white">{{
                    certStore.tlsInfo.certificate_chain.certificates.length
                  }}</span>
                </div>
                <div class="text-gray-300">
                  Valid:
                  <span
                    :class="
                      certStore.tlsInfo.certificate_chain.is_valid
                        ? 'text-green-400'
                        : 'text-red-400'
                    "
                  >
                    {{ certStore.tlsInfo.certificate_chain.is_valid ? 'Yes' : 'No' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Security Features -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">Security Features:</div>
              <div class="ml-4 space-y-1">
                <div class="text-gray-300">
                  OCSP Stapling: <span class="text-gray-400">No</span>
                </div>
                <div class="text-gray-300">
                  Self-Signed:
                  <span
                    :class="
                      leafCert.issuer.common_name === leafCert.subject.common_name
                        ? 'text-red-400'
                        : 'text-green-400'
                    "
                  >
                    {{
                      leafCert.issuer.common_name === leafCert.subject.common_name ? 'Yes' : 'No'
                    }}
                  </span>
                </div>
              </div>
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
