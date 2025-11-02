<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { useAppStore } from '../stores/app';
import { useDnssecStore } from '../stores/dnssec';
import PanelLoading from './PanelLoading.vue';
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/solid';

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

const statusIconComponent = computed(() => {
  if (!dnssecStore.validation) return null;

  switch (dnssecStore.validation.status) {
    case 'SECURE':
      return CheckCircleIcon;
    case 'INSECURE':
      return ExclamationTriangleIcon;
    case 'BOGUS':
      return XCircleIcon;
    default:
      return null;
  }
});

// Cycle through colors for different keytags
const getKeytagColor = (keytag: number) => {
  const colors = ['text-yellow-400', 'text-red-400', 'text-blue-400', 'text-green-400'];
  return colors[keytag % colors.length];
};

// Color for DNSSEC record types
const getRecordTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    DNSKEY: 'text-cyan-400',
    DS: 'text-yellow-400',
    RRSIG: 'text-purple-400',
  };
  return colorMap[type] || 'text-blue-400';
};

const getZoneLabel = (zoneName: string) => {
  if (zoneName === '.') return '. (root zone)';
  return `${zoneName}. (zone)`;
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

// DNSSEC sub-queries for loading state
const dnssecSubQueries = computed(() => [
  { name: 'Root Zone (.) DNSKEY', status: 'loading' as const },
  { name: 'TLD DS Records', status: 'loading' as const },
  { name: 'TLD DNSKEY', status: 'loading' as const },
  { name: 'Domain DS Records', status: 'loading' as const },
  { name: 'Domain DNSKEY', status: 'loading' as const },
]);

// Arrow connections linking DS records to matching DNSKEY records and DNSKEY to RRSIG
interface ArrowConnection {
  path: string;
  color: string;
  startY: number;
  endY: number;
}

const arrowConnections = ref<ArrowConnection[]>([]);

// Calculate arrow paths between DS records and their matching DNSKEY records
// Visual style: vertical lines on the left with horizontal arrows pointing to records
// Example:  |->  DS record
//           |
//           |->  DNSKEY record
const calculateArrowPaths = () => {
  arrowConnections.value = [];

  if (!dnssecStore.validation?.chain) return;

  nextTick(() => {
    setTimeout(() => {
      const chain = dnssecStore.validation!.chain;

      // Iterate through each zone (parent) that has DS records
      for (let parentIndex = 0; parentIndex < chain.length - 1; parentIndex++) {
        const parentZone = chain[parentIndex];
        const childZone = chain[parentIndex + 1];

        if (!parentZone.ds_records?.length || !childZone.dnskey_records?.length) continue;

        // For each DS record in parent zone
        parentZone.ds_records.forEach((ds, dsIndex) => {
          // Find matching DNSKEY in child zone by key_tag
          const matchingDnskeyIndex = childZone.dnskey_records.findIndex(
            (dnskey) => dnskey.key_tag === ds.key_tag
          );

          if (matchingDnskeyIndex === -1) return;

          // Get DOM elements
          const dsEl = document.getElementById(
            `ds-zone${parentIndex}-keytag${ds.key_tag}-idx${dsIndex}`
          );
          const dnskeyEl = document.getElementById(
            `dnskey-zone${parentIndex + 1}-keytag${ds.key_tag}-idx${matchingDnskeyIndex}`
          );

          if (!dsEl || !dnskeyEl) return;

          const container = document.querySelector('.dnssec-chain-container');
          if (!container) return;

          const containerRect = container.getBoundingClientRect();
          const dsRect = dsEl.getBoundingClientRect();
          const dnskeyRect = dnskeyEl.getBoundingClientRect();

          // Fixed X position on the left side (20px from container left)
          const leftX = 20;

          // Start point: DS record center
          const y1 = dsRect.top + dsRect.height / 2 - containerRect.top;

          // End point: DNSKEY record center
          const y2 = dnskeyRect.top + dnskeyRect.height / 2 - containerRect.top;

          // Horizontal arrow length
          const arrowLength = 20;

          // Add more pronounced randomness for hand-drawn effect
          const wobble = () => (Math.random() - 0.5) * 6;
          const wobbleSmall = () => (Math.random() - 0.5) * 3;

          const w1 = wobble();
          const w2 = wobble();
          const w3 = wobble();
          const w4 = wobbleSmall();
          const w5 = wobbleSmall();

          // Create one continuous flowing arc from DS through vertical to DNSKEY
          // Using cubic bezier for smooth S-curve with no sharp corners
          const path = `
            M ${leftX + w4} ${y1 + w5}
            C ${leftX + 15 + w2} ${y1 + w1}, ${leftX + 15 + w3} ${y1 + wobble()}, ${leftX + arrowLength} ${y1 + wobbleSmall()}
            M ${leftX + wobbleSmall()} ${y1 + wobbleSmall()}
            C ${leftX + 8 + w4} ${y1 + 20 + w1}, ${leftX + 8 + w5} ${y2 - 20 + w2}, ${leftX + wobbleSmall()} ${y2 + wobbleSmall()}
            M ${leftX + w4} ${y2 + w5}
            C ${leftX + 15 + w3} ${y2 + w1}, ${leftX + 15 + w2} ${y2 + wobble()}, ${leftX + arrowLength} ${y2 + wobbleSmall()}
          `
            .trim()
            .replace(/\s+/g, ' ');

          arrowConnections.value.push({
            path,
            color: '#858585', // dim gray (matches app theme)
            startY: y1,
            endY: y2,
          });
        });
      }

      // Add arrows from DNSKEY to RRSIG in target zone
      const targetZone = chain[chain.length - 1];
      if (targetZone.dnskey_records?.length && targetZone.rrsig_records?.length) {
        targetZone.dnskey_records.forEach((dnskey, dnskeyIndex) => {
          // Find matching RRSIG by key_tag
          const matchingRrsigIndex = targetZone.rrsig_records.findIndex(
            (rrsig) => rrsig.key_tag === dnskey.key_tag
          );

          if (matchingRrsigIndex === -1) return;

          const dnskeyEl = document.getElementById(
            `dnskey-zone${chain.length - 1}-keytag${dnskey.key_tag}-idx${dnskeyIndex}`
          );
          const rrsigEl = document.getElementById(
            `rrsig-zone${chain.length - 1}-keytag${dnskey.key_tag}-idx${matchingRrsigIndex}`
          );

          if (!dnskeyEl || !rrsigEl) return;

          const container = document.querySelector('.dnssec-chain-container');
          if (!container) return;

          const containerRect = container.getBoundingClientRect();
          const dnskeyRect = dnskeyEl.getBoundingClientRect();
          const rrsigRect = rrsigEl.getBoundingClientRect();

          const leftX = 20;
          const y1 = dnskeyRect.top + dnskeyRect.height / 2 - containerRect.top;
          const y2 = rrsigRect.top + rrsigRect.height / 2 - containerRect.top;
          const arrowLength = 20;

          const wobble = () => (Math.random() - 0.5) * 6;
          const wobbleSmall = () => (Math.random() - 0.5) * 3;

          const w1 = wobble();
          const w2 = wobble();
          const w3 = wobble();
          const w4 = wobbleSmall();
          const w5 = wobbleSmall();

          const path = `
            M ${leftX + w4} ${y1 + w5}
            C ${leftX + 15 + w2} ${y1 + w1}, ${leftX + 15 + w3} ${y1 + wobble()}, ${leftX + arrowLength} ${y1 + wobbleSmall()}
            M ${leftX + wobbleSmall()} ${y1 + wobbleSmall()}
            C ${leftX + 8 + w4} ${y1 + 20 + w1}, ${leftX + 8 + w5} ${y2 - 20 + w2}, ${leftX + wobbleSmall()} ${y2 + wobbleSmall()}
            M ${leftX + w4} ${y2 + w5}
            C ${leftX + 15 + w3} ${y2 + w1}, ${leftX + 15 + w2} ${y2 + wobble()}, ${leftX + arrowLength} ${y2 + wobbleSmall()}
          `
            .trim()
            .replace(/\s+/g, ' ');

          arrowConnections.value.push({
            path,
            color: '#858585',
            startY: y1,
            endY: y2,
          });
        });
      }
    }, 100);
  });
};

// Watch for validation changes
watch(() => dnssecStore.validation, calculateArrowPaths, { deep: true });

onMounted(() => {
  calculateArrowPaths();
  window.addEventListener('resize', calculateArrowPaths);
});

onUnmounted(() => {
  window.removeEventListener('resize', calculateArrowPaths);
});
</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6 text-white">DNSSEC Validation</h1>

      <!-- Loading State -->
      <PanelLoading
        v-if="dnssecStore.loading"
        title="DNSSEC Validation"
        :sub-queries="dnssecSubQueries"
      />

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
              <component v-if="statusIconComponent" :is="statusIconComponent" class="w-5 h-5" />
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
        <div class="panel relative">
          <h2 class="text-xl font-semibold mb-4 text-white">Trust Chain</h2>

          <div v-if="dnssecStore.validation.chain.length === 0" class="text-[#858585]">
            No DNSSEC chain data available
          </div>

          <div v-else class="space-y-3 relative dnssec-chain-container pl-12">
            <!-- SVG overlay for arrow connections -->
            <svg
              class="absolute inset-0 pointer-events-none overflow-visible"
              style="width: 100%; height: 100%; z-index: 5"
            >
              <defs>
                <marker
                  id="arrowhead-orange"
                  markerWidth="6"
                  markerHeight="6"
                  refX="5"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 6 3, 0 6" fill="#fb923c" />
                </marker>
              </defs>
              <g v-for="(arrow, idx) in arrowConnections" :key="idx">
                <!-- Main path (vertical and horizontal lines) -->
                <path
                  :d="arrow.path"
                  :stroke="arrow.color"
                  stroke-width="2"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <!-- Arrowheads with hand-drawn curved ( shape -->
                <path
                  :d="`M ${40 + Math.random() * 2 - 1},${arrow.startY - 8 + Math.random() * 2 - 1} Q ${50 + Math.random() * 3 - 1.5},${arrow.startY - 4 + Math.random() * 2 - 1} ${56 + Math.random() * 2 - 1},${arrow.startY + Math.random() * 2 - 1} Q ${50 + Math.random() * 3 - 1.5},${arrow.startY + 4 + Math.random() * 2 - 1} ${40 + Math.random() * 2 - 1},${arrow.startY + 8 + Math.random() * 2 - 1}`"
                  :fill="arrow.color"
                />
                <path
                  :d="`M ${40 + Math.random() * 2 - 1},${arrow.endY - 8 + Math.random() * 2 - 1} Q ${50 + Math.random() * 3 - 1.5},${arrow.endY - 4 + Math.random() * 2 - 1} ${56 + Math.random() * 2 - 1},${arrow.endY + Math.random() * 2 - 1} Q ${50 + Math.random() * 3 - 1.5},${arrow.endY + 4 + Math.random() * 2 - 1} ${40 + Math.random() * 2 - 1},${arrow.endY + 8 + Math.random() * 2 - 1}`"
                  :fill="arrow.color"
                />
              </g>
            </svg>

            <div v-for="(zone, index) in dnssecStore.validation.chain" :key="index">
              <!-- Zone Header -->
              <div class="mb-2">
                <div class="flex-1">
                  <h3 class="font-semibold text-white mb-2">
                    {{ getZoneLabel(zone.zone_name) }}
                  </h3>

                  <div class="border border-[#3e3e42] rounded p-3 bg-[#1a1a1a]">
                    <!-- No DNSSEC records message -->
                    <div
                      v-if="
                        (!zone.dnskey_records || zone.dnskey_records.length === 0) &&
                        (!zone.ds_records || zone.ds_records.length === 0) &&
                        (!zone.rrsig_records || zone.rrsig_records.length === 0)
                      "
                      class="font-mono text-xs text-[#858585]"
                    >
                      No DNSSEC records found for this zone
                    </div>

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
                        <span
                          :id="`dnskey-zone${index}-keytag${dnskey.key_tag}-idx${keyIndex}`"
                          class="flex-1 break-all"
                        >
                          <span class="font-semibold text-[#858585]">DNSKEY</span> KEYTAG=<span
                            :class="getKeytagColor(dnskey.key_tag)"
                            >{{ dnskey.key_tag }}</span
                          >
                          ALGO={{ dnskey.algorithm }} TYPE=<span
                            :class="dnskey.flags === 257 ? 'text-blue-400' : 'text-cyan-400'"
                            >{{ dnskey.flags === 257 ? 'KSK' : 'ZSK' }}</span
                          >
                          PUBKEY={{ dnskey.public_key.substring(0, 100) }}...
                        </span>
                      </div>
                    </div>

                    <!-- DS Records -->
                    <div
                      v-if="zone.ds_records && zone.ds_records.length > 0"
                      class="space-y-1 mt-3 pt-3 -mx-3 -mb-3 px-3 pb-3 bg-[#0d0d0d] border-t border-[#2a2a2a]"
                    >
                      <div
                        v-for="(ds, dsIndex) in zone.ds_records"
                        :key="dsIndex"
                        class="font-mono text-xs text-[#cccccc] flex items-start gap-2"
                      >
                        <span
                          :id="`ds-zone${index}-keytag${ds.key_tag}-idx${dsIndex}`"
                          class="flex-1 break-all"
                        >
                          <span class="font-semibold text-[#858585]">DS</span> KEYTAG=<span
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
                      <div class="font-mono text-xs text-red-400">
                        No DS records found – chain is broken
                      </div>
                    </div>

                    <!-- RRSIG Records (show details only for target zone) -->
                    <!-- Target zone: dark bg as bottom of card -->
                    <div
                      v-if="
                        zone.rrsig_records &&
                        zone.rrsig_records.length > 0 &&
                        zone.zone_name === appStore.domain
                      "
                      class="space-y-1 mt-3 pt-3 -mx-3 -mb-3 px-3 pb-3 bg-[#0d0d0d] border-t border-[#2a2a2a]"
                    >
                      <div
                        v-for="(rrsig, rrsigIndex) in zone.rrsig_records"
                        :key="rrsigIndex"
                        class="font-mono text-xs text-[#cccccc] flex items-start gap-2"
                      >
                        <span
                          :id="`rrsig-zone${index}-keytag${rrsig.key_tag}-idx${rrsigIndex}`"
                          class="flex-1 break-all"
                        >
                          <span class="font-semibold text-[#858585]">RRSIG</span> TYPE={{
                            rrsig.type_covered
                          }}
                          KEYTAG=<span :class="getKeytagColor(rrsig.key_tag)">{{
                            rrsig.key_tag
                          }}</span>
                          ALGO={{ rrsig.algorithm }} SIGNER={{ rrsig.signer_name }} EXPIRES={{
                            rrsig.signature_expiration
                          }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
