<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useDnssecStore } from '../stores/dnssec';

const appStore = useAppStore();
const dnssecStore = useDnssecStore();

const statusColor = computed(() => {
  if (!dnssecStore.validation) return 'gray';

  switch (dnssecStore.validation.status) {
    case 'SECURE':
      return 'green';
    case 'INSECURE':
      return 'yellow';
    case 'BOGUS':
      return 'red';
    default:
      return 'gray';
  }
});

const statusIcon = computed(() => {
  if (!dnssecStore.validation) return '○';

  switch (dnssecStore.validation.status) {
    case 'SECURE':
      return '✓';
    case 'INSECURE':
      return '△';
    case 'BOGUS':
      return '✗';
    default:
      return '○';
  }
});
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6 text-white">DNSSEC Validation</h1>

      <!-- Loading State -->
      <div v-if="dnssecStore.loading" class="panel">
        <div class="flex items-center gap-3">
          <svg
            class="animate-spin h-5 w-5 text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <p class="text-[#cccccc]">Validating DNSSEC chain...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="dnssecStore.error" class="panel border-red-500/30 bg-red-500/5">
        <div class="flex items-start gap-3">
          <span class="text-red-500 text-xl">⚠</span>
          <div>
            <h3 class="text-red-400 font-semibold mb-1">Validation Error</h3>
            <p class="text-[#cccccc]">{{ dnssecStore.error }}</p>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!appStore.domain" class="panel">
        <p class="text-[#858585]">Enter a domain to validate DNSSEC chain</p>
      </div>

      <!-- Validation Results -->
      <div v-else-if="dnssecStore.validation" class="space-y-6">
        <!-- Status Overview -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 text-white">Validation Status</h2>

          <div class="flex items-center gap-4 mb-4">
            <div
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm',
                statusColor === 'green' &&
                  'bg-green-500/10 text-green-400 border border-green-500/30',
                statusColor === 'yellow' &&
                  'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30',
                statusColor === 'red' && 'bg-red-500/10 text-red-400 border border-red-500/30',
                statusColor === 'gray' && 'bg-gray-500/10 text-gray-400 border border-gray-500/30',
              ]"
            >
              <span class="text-xl">{{ statusIcon }}</span>
              <span>{{ dnssecStore.validation.status }}</span>
            </div>

            <div class="text-[#858585] text-sm">
              <span v-if="dnssecStore.validation.status === 'SECURE'">
                DNSSEC is properly configured and validated
              </span>
              <span v-else-if="dnssecStore.validation.status === 'INSECURE'">
                DNSSEC is not enabled for this domain
              </span>
              <span v-else-if="dnssecStore.validation.status === 'BOGUS'">
                DNSSEC validation failed - potential security issue
              </span>
              <span v-else> Could not determine DNSSEC status </span>
            </div>
          </div>

          <!-- Warnings -->
          <div
            v-if="dnssecStore.validation.warnings.length > 0"
            class="mt-4 p-3 bg-yellow-500/5 border border-yellow-500/30 rounded-lg"
          >
            <h3 class="text-yellow-400 font-semibold mb-2 flex items-center gap-2">
              <span>⚠</span>
              <span>Warnings</span>
            </h3>
            <ul class="list-disc list-inside space-y-1">
              <li
                v-for="(warning, index) in dnssecStore.validation.warnings"
                :key="index"
                class="text-[#cccccc] text-sm"
              >
                {{ warning }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Chain Visualization -->
        <div class="panel">
          <h2 class="text-xl font-semibold mb-4 text-white">Trust Chain</h2>

          <div v-if="dnssecStore.validation.chain.length === 0" class="text-[#858585]">
            No DNSSEC chain data available
          </div>

          <div v-else class="space-y-4">
            <div
              v-for="(zone, index) in dnssecStore.validation.chain"
              :key="index"
              class="relative"
            >
              <!-- Zone Card -->
              <div class="bg-[#252526] border border-[#3e3e42] rounded-lg p-4">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="font-semibold text-white">{{ zone.zone || 'Root Zone' }}</h3>
                  <span
                    class="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded border border-blue-500/30"
                  >
                    Zone {{ index + 1 }} of {{ dnssecStore.validation.chain.length }}
                  </span>
                </div>

                <!-- DNSKEY Records -->
                <div v-if="zone.dnskey_records && zone.dnskey_records.length > 0" class="mb-3">
                  <h4 class="text-sm font-medium text-[#cccccc] mb-2">DNSKEY Records</h4>
                  <div class="space-y-2">
                    <div
                      v-for="(dnskey, keyIndex) in zone.dnskey_records"
                      :key="keyIndex"
                      class="bg-[#1e1e1e] border border-[#3e3e42] rounded p-3 text-sm"
                    >
                      <div class="grid grid-cols-2 gap-2">
                        <div>
                          <span class="text-[#858585]">Flags:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ dnskey.flags }}</span>
                        </div>
                        <div>
                          <span class="text-[#858585]">Protocol:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ dnskey.protocol }}</span>
                        </div>
                        <div>
                          <span class="text-[#858585]">Algorithm:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ dnskey.algorithm }}</span>
                        </div>
                        <div>
                          <span class="text-[#858585]">Key Tag:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ dnskey.key_tag }}</span>
                        </div>
                      </div>
                      <div class="mt-2">
                        <span class="text-[#858585]">Public Key:</span>
                        <p class="mt-1 text-[#cccccc] font-mono text-xs break-all">
                          {{ dnskey.public_key.substring(0, 64) }}...
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- DS Records -->
                <div v-if="zone.ds_records && zone.ds_records.length > 0">
                  <h4 class="text-sm font-medium text-[#cccccc] mb-2">DS Records</h4>
                  <div class="space-y-2">
                    <div
                      v-for="(ds, dsIndex) in zone.ds_records"
                      :key="dsIndex"
                      class="bg-[#1e1e1e] border border-[#3e3e42] rounded p-3 text-sm"
                    >
                      <div class="grid grid-cols-2 gap-2">
                        <div>
                          <span class="text-[#858585]">Key Tag:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ ds.key_tag }}</span>
                        </div>
                        <div>
                          <span class="text-[#858585]">Algorithm:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ ds.algorithm }}</span>
                        </div>
                        <div class="col-span-2">
                          <span class="text-[#858585]">Digest Type:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ ds.digest_type }}</span>
                        </div>
                      </div>
                      <div class="mt-2">
                        <span class="text-[#858585]">Digest:</span>
                        <p class="mt-1 text-[#cccccc] font-mono text-xs break-all">
                          {{ ds.digest }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- RRSIG Records -->
                <div v-if="zone.rrsig_records && zone.rrsig_records.length > 0" class="mt-3">
                  <h4 class="text-sm font-medium text-[#cccccc] mb-2">RRSIG Records</h4>
                  <div class="space-y-2">
                    <div
                      v-for="(rrsig, rrsigIndex) in zone.rrsig_records"
                      :key="rrsigIndex"
                      class="bg-[#1e1e1e] border border-[#3e3e42] rounded p-3 text-sm"
                    >
                      <div class="grid grid-cols-2 gap-2">
                        <div>
                          <span class="text-[#858585]">Type Covered:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{
                            rrsig.type_covered
                          }}</span>
                        </div>
                        <div>
                          <span class="text-[#858585]">Algorithm:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ rrsig.algorithm }}</span>
                        </div>
                        <div>
                          <span class="text-[#858585]">Key Tag:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ rrsig.key_tag }}</span>
                        </div>
                        <div>
                          <span class="text-[#858585]">Labels:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ rrsig.labels }}</span>
                        </div>
                        <div class="col-span-2">
                          <span class="text-[#858585]">Signer:</span>
                          <span class="ml-2 text-[#cccccc] font-mono">{{ rrsig.signer_name }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Arrow to next zone -->
              <div
                v-if="index < dnssecStore.validation.chain.length - 1"
                class="flex justify-center my-2"
              >
                <div class="text-[#858585] text-2xl">↓</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
