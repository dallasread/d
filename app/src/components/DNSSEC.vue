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

// Cycle through colors for different keytags
const getKeytagColor = (keytag: number) => {
  const colors = ['text-yellow-400', 'text-red-400', 'text-blue-400', 'text-green-400'];
  return colors[keytag % colors.length];
};

const getZoneLabel = (zoneName: string) => {
  if (zoneName === '.') return 'root zone';
  return `${zoneName} (zone)`;
};

// Check if a DS record key tag matches any DNSKEY in the child zone
const dsMatchesChild = (dsKeytag: number, childZone: any) => {
  if (!childZone || !childZone.dnskey_records) return false;
  return childZone.dnskey_records.some((key: any) => key.key_tag === dsKeytag);
};

// Get the child zone for a given zone index
const getChildZone = (index: number) => {
  if (!dnssecStore.validation || !dnssecStore.validation.chain) return null;
  return index < dnssecStore.validation.chain.length - 1
    ? dnssecStore.validation.chain[index + 1]
    : null;
};
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

          <div class="flex items-center gap-4">
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

          <div v-else class="space-y-3">
            <div
              v-for="(zone, index) in dnssecStore.validation.chain"
              :key="index"
              class="relative"
            >
              <!-- Zone Header with Tree Connection -->
              <div class="flex items-start gap-3 mb-2">
                <div class="flex flex-col items-center pt-1">
                  <!-- Vertical line from previous zone -->
                  <div v-if="index > 0" class="w-px h-3 bg-[#3e3e42]"></div>
                  <!-- Corner and horizontal line -->
                  <div class="flex items-center">
                    <div class="w-px h-3 bg-[#3e3e42]"></div>
                    <div class="w-3 h-px bg-[#3e3e42]"></div>
                  </div>
                  <!-- Vertical line to content -->
                  <div class="w-px flex-1 bg-[#3e3e42] min-h-[20px]"></div>
                </div>

                <div class="flex-1">
                  <h3 class="font-semibold text-cyan-400 mb-2">
                    {{ getZoneLabel(zone.zone_name) }}
                  </h3>

                  <div class="border border-[#3e3e42] rounded p-3 bg-[#1a1a1a]">
                    <!-- DNSKEY Records -->
                    <div
                      v-if="zone.dnskey_records && zone.dnskey_records.length > 0"
                      class="space-y-1 mb-2"
                    >
                      <div
                        v-for="(dnskey, keyIndex) in zone.dnskey_records"
                        :key="keyIndex"
                        class="font-mono text-xs text-[#cccccc] flex items-start gap-2"
                      >
                        <span class="text-green-400 flex-shrink-0">✓</span>
                        <span class="flex-1 break-all">
                          DNSKEY KEYTAG=<span :class="getKeytagColor(dnskey.key_tag)">{{
                            dnskey.key_tag
                          }}</span>
                          ALGO={{ dnskey.algorithm }} TYPE=<span
                            :class="dnskey.flags === 257 ? 'text-blue-400' : 'text-cyan-400'"
                            >{{ dnskey.flags === 257 ? 'KSK' : 'ZSK' }}</span
                          >
                          PUBKEY={{ dnskey.public_key.substring(0, 100) }}...
                        </span>
                      </div>
                    </div>

                    <!-- DS Records -->
                    <div v-if="zone.ds_records && zone.ds_records.length > 0" class="space-y-1">
                      <div
                        v-for="(ds, dsIndex) in zone.ds_records"
                        :key="dsIndex"
                        class="font-mono text-xs flex items-start gap-2"
                        :class="
                          dsMatchesChild(ds.key_tag, getChildZone(index))
                            ? 'text-green-400'
                            : 'text-[#cccccc]'
                        "
                      >
                        <span class="flex-shrink-0">
                          {{ dsMatchesChild(ds.key_tag, getChildZone(index)) ? '├─> ✓' : '✓' }}
                        </span>
                        <span class="flex-1 break-all">
                          DS&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;KEYTAG=<span
                            :class="getKeytagColor(ds.key_tag)"
                            >{{ ds.key_tag }}</span
                          >
                          ALGO={{ ds.algorithm }} HASH={{ ds.digest }}
                        </span>
                      </div>
                    </div>

                    <!-- No DS records warning (only for non-root zones with no child DS records) -->
                    <div
                      v-if="
                        zone.ds_records &&
                        zone.ds_records.length === 0 &&
                        zone.zone_name !== '.' &&
                        index < dnssecStore.validation.chain.length - 1
                      "
                      class="mt-2"
                    >
                      <div class="font-mono text-xs text-red-400 flex items-start gap-2">
                        <span class="flex-shrink-0">✗</span>
                        <span>No DS records found – chain is broken</span>
                      </div>
                    </div>

                    <!-- RRSIG indicator -->
                    <div v-if="zone.rrsig_records && zone.rrsig_records.length > 0" class="mt-2">
                      <div class="font-mono text-xs text-gray-400 flex items-start gap-2">
                        <span class="flex-shrink-0">○</span>
                        <span>RRSIG records found; zone records are signed</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Arrow to next zone (if not last) -->
              <div
                v-if="index < dnssecStore.validation.chain.length - 1"
                class="flex items-center gap-3 my-1 ml-3"
              >
                <div class="w-px h-3 bg-[#3e3e42]"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
