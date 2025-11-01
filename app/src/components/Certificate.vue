<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useCertificateStore } from '../stores/certificate';

const appStore = useAppStore();
const certStore = useCertificateStore();

const hasDomain = computed(() => !!appStore.domain);

const leafCert = computed(() => certStore.tlsInfo?.certificate_chain.certificates[0]);

const daysUntilExpiry = computed(() => {
  if (!leafCert.value) return null;
  const expiryDate = new Date(leafCert.value.not_after);
  const now = new Date();
  const days = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return days;
});

const expiryStatusClass = computed(() => {
  if (daysUntilExpiry.value === null) return 'text-[#858585]';
  if (daysUntilExpiry.value > 30) return 'status-pass';
  if (daysUntilExpiry.value > 0) return 'status-warn';
  return 'status-fail';
});

const isExpired = computed(() => {
  if (!leafCert.value) return false;
  return new Date(leafCert.value.not_after) < new Date();
});

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">SSL/TLS Certificate</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view certificate information</p>
      </div>

      <!-- Loading state -->
      <div v-else-if="certStore.loading" class="panel">
        <div class="space-y-4">
          <div class="h-6 bg-[#3e3e42] rounded animate-pulse"></div>
          <div class="h-4 bg-[#3e3e42] rounded animate-pulse w-3/4"></div>
          <div class="h-4 bg-[#3e3e42] rounded animate-pulse w-1/2"></div>
        </div>
      </div>

      <!-- Certificate Info -->
      <div v-else-if="leafCert" class="space-y-6">
        <!-- Certificate Overview -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Certificate Overview</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p class="text-sm text-[#858585]">Issued To (Common Name)</p>
              <p class="text-lg font-medium">{{ leafCert.subject.common_name || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Issued By (Organization)</p>
              <p class="text-lg font-medium">
                {{ leafCert.issuer.organization || leafCert.issuer.common_name || 'N/A' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Validity Period -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Validity Period</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p class="text-sm text-[#858585]">Valid From</p>
              <p class="font-medium">{{ formatDate(leafCert.not_before) }}</p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Valid Until</p>
              <p class="font-medium">{{ formatDate(leafCert.not_after) }}</p>
            </div>
            <div>
              <p class="text-sm text-[#858585]">Status</p>
              <p :class="['font-medium', expiryStatusClass]">
                <span v-if="isExpired" class="status-fail">✗ Expired</span>
                <span v-else-if="daysUntilExpiry !== null">
                  {{ daysUntilExpiry > 30 ? '✓' : '⚠' }} {{ daysUntilExpiry }} days remaining
                </span>
              </p>
            </div>
          </div>
        </div>

        <!-- Subject Details -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Subject Details</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div v-if="leafCert.subject.organization">
              <p class="text-[#858585]">Organization (O)</p>
              <p>{{ leafCert.subject.organization }}</p>
            </div>
            <div v-if="leafCert.subject.organizational_unit">
              <p class="text-[#858585]">Organizational Unit (OU)</p>
              <p>{{ leafCert.subject.organizational_unit }}</p>
            </div>
            <div v-if="leafCert.subject.locality">
              <p class="text-[#858585]">Locality (L)</p>
              <p>{{ leafCert.subject.locality }}</p>
            </div>
            <div v-if="leafCert.subject.state">
              <p class="text-[#858585]">State (ST)</p>
              <p>{{ leafCert.subject.state }}</p>
            </div>
            <div v-if="leafCert.subject.country">
              <p class="text-[#858585]">Country (C)</p>
              <p>{{ leafCert.subject.country }}</p>
            </div>
          </div>
        </div>

        <!-- Issuer Details -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Issuer Details</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div v-if="leafCert.issuer.common_name">
              <p class="text-[#858585]">Common Name (CN)</p>
              <p>{{ leafCert.issuer.common_name }}</p>
            </div>
            <div v-if="leafCert.issuer.organization">
              <p class="text-[#858585]">Organization (O)</p>
              <p>{{ leafCert.issuer.organization }}</p>
            </div>
            <div v-if="leafCert.issuer.country">
              <p class="text-[#858585]">Country (C)</p>
              <p>{{ leafCert.issuer.country }}</p>
            </div>
          </div>
        </div>

        <!-- Subject Alternative Names -->
        <div v-if="leafCert.subject_alternative_names.length > 0" class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            Subject Alternative Names (SANs)
            <span class="text-sm font-normal text-blue-400">{{
              leafCert.subject_alternative_names.length
            }}</span>
          </h2>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(san, index) in leafCert.subject_alternative_names"
              :key="index"
              class="px-3 py-1 bg-[#3e3e42] text-sm rounded-md font-mono"
            >
              {{ san }}
            </span>
          </div>
        </div>

        <!-- Technical Details -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4">Technical Details</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div>
              <p class="text-[#858585]">Serial Number</p>
              <p class="font-mono text-xs break-all">{{ leafCert.serial_number }}</p>
            </div>
            <div>
              <p class="text-[#858585]">Version</p>
              <p>{{ leafCert.version }}</p>
            </div>
            <div>
              <p class="text-[#858585]">Public Key Algorithm</p>
              <p>{{ leafCert.public_key_algorithm }}</p>
            </div>
            <div v-if="leafCert.public_key_size">
              <p class="text-[#858585]">Public Key Size</p>
              <p>{{ leafCert.public_key_size }} bits</p>
            </div>
            <div>
              <p class="text-[#858585]">Signature Algorithm</p>
              <p>{{ leafCert.signature_algorithm }}</p>
            </div>
            <div>
              <p class="text-[#858585]">Fingerprint (SHA256)</p>
              <p class="font-mono text-xs break-all">{{ leafCert.fingerprint_sha256 || 'N/A' }}</p>
            </div>
          </div>
        </div>

        <!-- Certificate Chain -->
        <div v-if="certStore.tlsInfo" class="panel">
          <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
            Certificate Chain
            <span class="text-sm font-normal text-blue-400">
              {{ certStore.tlsInfo.certificate_chain.certificates.length }} certificate(s)
            </span>
          </h2>
          <div class="space-y-3">
            <div
              v-for="(cert, index) in certStore.tlsInfo.certificate_chain.certificates"
              :key="index"
              class="p-3 bg-[#1e1e1e] rounded border border-[#3e3e42]"
            >
              <div class="flex items-start justify-between">
                <div>
                  <p class="font-medium">{{ cert.subject.common_name || 'Unknown' }}</p>
                  <p class="text-xs text-[#858585]">
                    Issued by:
                    {{ cert.issuer.common_name || cert.issuer.organization || 'Unknown' }}
                  </p>
                </div>
                <span class="text-xs px-2 py-1 bg-[#3e3e42] rounded">
                  {{
                    index === 0
                      ? 'Leaf'
                      : index === certStore.tlsInfo.certificate_chain.certificates.length - 1
                        ? 'Root'
                        : 'Intermediate'
                  }}
                </span>
              </div>
            </div>
          </div>
          <div class="mt-4">
            <p class="text-sm">
              <span class="text-[#858585]">Chain Valid:</span>
              <span
                :class="
                  certStore.tlsInfo.certificate_chain.is_valid ? 'status-pass' : 'status-fail'
                "
              >
                {{ certStore.tlsInfo.certificate_chain.is_valid ? '✓ Yes' : '✗ No' }}
              </span>
            </p>
            <div
              v-if="certStore.tlsInfo.certificate_chain.validation_errors.length > 0"
              class="mt-2"
            >
              <p class="text-sm text-[#858585]">Validation Errors:</p>
              <ul class="text-sm text-red-400 list-disc list-inside">
                <li
                  v-for="(error, index) in certStore.tlsInfo.certificate_chain.validation_errors"
                  :key="index"
                >
                  {{ error }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Error Display -->
        <div v-if="certStore.error" class="panel bg-red-900/20 border-red-800">
          <h3 class="text-lg font-semibold text-red-400 mb-2">Error</h3>
          <p class="text-sm text-red-300">{{ certStore.error }}</p>
        </div>
      </div>

      <!-- No Data -->
      <div v-else class="panel">
        <p class="text-[#858585]">No certificate data available</p>
      </div>
    </div>
  </div>
</template>
