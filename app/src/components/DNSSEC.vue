<script setup lang="ts">
import { computed, ref, onMounted, nextTick, watch, onUnmounted } from 'vue';
import { useAppStore } from '../stores/app';
import { useDnssecStore } from '../stores/dnssec';
import PanelLoading from './PanelLoading.vue';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CheckIcon,
  ArrowRightIcon,
} from '@heroicons/vue/24/solid';

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

// Get the child zone name for DS record label
const getChildZoneName = (index: number) => {
  const child = getChildZone(index);
  return child ? child.zone_name : null;
};

// DNSSEC sub-queries for loading state
const dnssecSubQueries = computed(() => [
  { name: 'Root Zone (.) DNSKEY', status: 'loading' as const },
  { name: 'TLD DS Records', status: 'loading' as const },
  { name: 'TLD DNSKEY', status: 'loading' as const },
  { name: 'Domain DS Records', status: 'loading' as const },
  { name: 'Domain DNSKEY', status: 'loading' as const },
]);

// Arrow paths for linking DS to DNSKEY records
const arrowPaths = ref<Array<{ d: string; color: string }>>([]);

// Calculate arrow paths between DS records and matching DNSKEYs
const calculateArrows = () => {
  arrowPaths.value = [];

  if (!dnssecStore.validation || !dnssecStore.validation.chain) return;

  const validation = dnssecStore.validation;

  // Wait for DOM to render
  nextTick(() => {
    // Iterate through each zone (except the last one which has no children)
    for (let zoneIndex = 0; zoneIndex < validation.chain.length - 1; zoneIndex++) {
      const parentZone = validation.chain[zoneIndex];
      const childZone = validation.chain[zoneIndex + 1];

      if (!parentZone.ds_records || !childZone.dnskey_records) continue;

      // For each DS record in the parent zone
      parentZone.ds_records.forEach((ds, dsIndex) => {
        // Find matching DNSKEY in child zone by key_tag
        const matchingDnskeyIndex = childZone.dnskey_records.findIndex(
          (key) => key.key_tag === ds.key_tag
        );

        if (matchingDnskeyIndex === -1) return;

        // Get DOM elements
        const dsElement = document.getElementById(
          `ds-zone${zoneIndex}-keytag${ds.key_tag}-index${dsIndex}`
        );
        const dnskeyElement = document.getElementById(
          `dnskey-zone${zoneIndex + 1}-keytag${ds.key_tag}-index${matchingDnskeyIndex}`
        );

        if (!dsElement || !dnskeyElement) return;

        // Get the container for relative positioning
        const container = dsElement.closest('.panel');
        if (!container) return;

        const containerRect = container.getBoundingClientRect();
        const dsRect = dsElement.getBoundingClientRect();
        const dnskeyRect = dnskeyElement.getBoundingClientRect();

        // Calculate start and end points (right side of DS, left side of DNSKEY)
        const x1 = dsRect.right - containerRect.left;
        const y1 = dsRect.top + dsRect.height / 2 - containerRect.top;
        const x2 = dnskeyRect.left - containerRect.left - 10;
        const y2 = dnskeyRect.top + dnskeyRect.height / 2 - containerRect.top;

        // Create a hand-drawn style curved path with slight randomness
        const dx = x2 - x1;
        const curve = Math.abs(dx) * 0.3;

        // Add slight randomness for hand-drawn effect
        const wobble1 = Math.random() * 4 - 2;
        const wobble2 = Math.random() * 4 - 2;

        const path = `M ${x1} ${y1} C ${x1 + curve} ${y1 + wobble1}, ${x2 - curve} ${y2 + wobble2}, ${x2} ${y2}`;

        // Use orange color for arrows
        arrowPaths.value.push({ d: path, color: '#fb923c' });
      });
    }
  });
};

// Watch for changes in validation data
watch(() => dnssecStore.validation, calculateArrows, { deep: true });

onMounted(() => {
  calculateArrows();
  // Recalculate on window resize
  window.addEventListener('resize', calculateArrows);
});

onUnmounted(() => {
  window.removeEventListener('resize', calculateArrows);
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

          <div v-else class="space-y-3 relative">
            <!-- SVG overlay for drawing arrows -->
            <svg
              class="absolute inset-0 pointer-events-none"
              style="width: 100%; height: 100%; z-index: 10"
            >
              <defs>
                <marker
                  id="arrowhead-orange"
                  markerWidth="10"
                  markerHeight="10"
                  refX="9"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill="#fb923c" />
                </marker>
              </defs>
              <!-- Draw arrows between DS and DNSKEY records -->
              <path
                v-for="(arrow, idx) in arrowPaths"
                :key="idx"
                :d="arrow.d"
                :stroke="arrow.color"
                stroke-width="2"
                fill="none"
                marker-end="url(#arrowhead-orange)"
                opacity="0.7"
              />
            </svg>
            <div
              v-for="(zone, index) in dnssecStore.validation.chain"
              :key="index"
              class="relative"
            >
              <!-- Zone Header -->
              <div class="mb-2">
                <div class="flex-1">
                  <h3 class="font-semibold text-cyan-400 mb-2">
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
                        :id="`dnskey-zone${index}-keytag${dnskey.key_tag}-index${keyIndex}`"
                        class="font-mono text-xs text-[#cccccc] flex items-start gap-2"
                      >
                        <CheckIcon class="w-3 h-3 text-green-400 flex-shrink-0 mt-0.5" />
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
                      <!-- DS Records Header -->
                      <div
                        v-if="getChildZoneName(index)"
                        class="text-xs text-[#858585] mb-1 flex items-center gap-1"
                      >
                        <ArrowRightIcon class="w-3 h-3" />
                        <span>DS records for child zone: {{ getChildZoneName(index) }}</span>
                      </div>
                      <div
                        v-for="(ds, dsIndex) in zone.ds_records"
                        :key="dsIndex"
                        :id="`ds-zone${index}-keytag${ds.key_tag}-index${dsIndex}`"
                        class="font-mono text-xs flex items-start gap-2"
                        :class="
                          dsMatchesChild(ds.key_tag, getChildZone(index))
                            ? 'text-green-400'
                            : 'text-[#cccccc]'
                        "
                      >
                        <span class="flex-shrink-0 flex items-center gap-0.5 mt-0.5">
                          <ArrowRightIcon
                            v-if="dsMatchesChild(ds.key_tag, getChildZone(index))"
                            class="w-3 h-3"
                          />
                          <CheckIcon class="w-3 h-3" />
                        </span>
                        <span class="flex-1 break-all">
                          DS KEYTAG=<span :class="getKeytagColor(ds.key_tag)">{{
                            ds.key_tag
                          }}</span>
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

                    <!-- RRSIG indicator -->
                    <div v-if="zone.rrsig_records && zone.rrsig_records.length > 0" class="mt-2">
                      <div class="font-mono text-xs text-gray-400">
                        RRSIG records found; zone records are signed
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
