<script setup lang="ts">
/**
 * DNSSEC Validation Chain Visualization Component
 *
 * Displays the complete DNSSEC chain of trust from root zone down to the target domain.
 * Shows DNSKEY, DS, and RRSIG records at each level with visual arrows connecting
 * parent DS records to child DNSKEY records, and DNSKEY to RRSIG signatures.
 *
 * DNSSEC Chain Structure:
 * - Root zone (.): Contains root DNSKEYs and DS records pointing to TLD
 * - TLD zone (e.g., io.): Contains TLD DNSKEYs and DS records pointing to domain
 * - Domain zone (e.g., meat.io.): Contains domain DNSKEYs and RRSIG signatures
 *
 * Record Types:
 * - DNSKEY: Public keys used to verify DNS records (KSK = Key Signing Key, ZSK = Zone Signing Key)
 * - DS (Delegation Signer): Hash of child zone's DNSKEY, stored in parent zone
 * - RRSIG: Cryptographic signature proving record authenticity
 *
 * Key Tags:
 * - Unique identifiers for keys, used to match DS → DNSKEY and DNSKEY → RRSIG
 * - NOT the same as flags (256 = ZSK, 257 = KSK)
 * - Extracted from dig +multi output comments (e.g., "; key id = 5116")
 */
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { useAppStore } from '../stores/app';
import { useDnssecStore } from '../stores/dnssec';
import PanelLoading from './PanelLoading.vue';
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/solid';

const appStore = useAppStore();
const dnssecStore = useDnssecStore();

/**
 * DNSSEC Validation Status Color Mapping
 *
 * Maps validation status to visual colors:
 * - SECURE: Domain has valid DNSSEC chain (DS records match DNSKEYs)
 * - INSECURE: Domain not signed with DNSSEC (no DNSKEYs or DS records)
 * - BOGUS: DNSSEC chain broken (DS key tags don't match DNSKEY key tags)
 * - INDETERMINATE: Unable to determine status (query failures)
 */
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

/**
 * Status Icon Component Mapping
 * Maps validation status to HeroIcons components for visual indicators
 */
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

/**
 * Key Tag Color Assignment
 *
 * Assigns rotating colors to key tags for visual distinction.
 * Key tags are unique identifiers for DNSSEC keys (e.g., 5116, 55759).
 * Using modulo ensures consistent colors for the same key tag across the page.
 *
 * Example: If key_tag = 5116, color = colors[5116 % 4] = colors[0] = yellow
 */
const getKeytagColor = (keytag: number) => {
  const colors = ['text-yellow-400', 'text-red-400', 'text-blue-400', 'text-green-400'];
  return colors[keytag % colors.length];
};

/**
 * Record Type Color Map (Currently Unused)
 *
 * Note: Record types now use dim bold gray instead of colors.
 * Kept for potential future use.
 */
const getRecordTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    DNSKEY: 'text-cyan-400',
    DS: 'text-yellow-400',
    RRSIG: 'text-purple-400',
  };
  return colorMap[type] || 'text-blue-400';
};

/**
 * Zone Label Formatter
 *
 * Formats zone names with trailing dots (FQDN notation):
 * - Root zone: "." → ". (root zone)"
 * - TLD: "io" → "io. (zone)"
 * - Domain: "meat.io" → "meat.io. (zone)"
 *
 * Trailing dots indicate fully qualified domain names in DNS.
 */
const getZoneLabel = (zoneName: string) => {
  if (zoneName === '.') return '. (root zone)';
  return `${zoneName}. (zone)`;
};

/**
 * DS Record Validation Helper
 *
 * Checks if a DS record's key tag matches any DNSKEY in the child zone.
 * This is the core of DNSSEC chain validation:
 * - Parent zone DS record contains key_tag pointing to child zone DNSKEY
 * - If key tags match, the chain link is valid
 * - If no match, the chain is broken (BOGUS status)
 *
 * Example: DS in "io." zone with key_tag=5116 should match DNSKEY in "meat.io." zone with key_tag=5116
 *
 * Note: Currently unused as checkmarks were removed, but kept for potential future validation indicators.
 */
const dsMatchesChild = (dsKeytag: number, childZone: any) => {
  if (!childZone || !childZone.dnskey_records) return false;
  return childZone.dnskey_records.some((key: any) => key.key_tag === dsKeytag);
};

/**
 * Child Zone Lookup Helper
 *
 * Given a zone index in the chain, returns the next zone (child).
 * Used for DS → DNSKEY matching across parent/child zones.
 *
 * Example chain: [root(0), io(1), meat.io(2)]
 * - getChildZone(0) returns io (zone 1)
 * - getChildZone(1) returns meat.io (zone 2)
 * - getChildZone(2) returns null (no child)
 */
const getChildZone = (index: number) => {
  if (!dnssecStore.validation || !dnssecStore.validation.chain) return null;
  return index < dnssecStore.validation.chain.length - 1
    ? dnssecStore.validation.chain[index + 1]
    : null;
};

/**
 * Loading State Sub-Queries
 *
 * Displayed during DNSSEC validation to show progress.
 * Each query fetches a different piece of the DNSSEC chain.
 */
const dnssecSubQueries = computed(() => [
  { name: 'Root Zone (.) DNSKEY', status: 'loading' as const },
  { name: 'TLD DS Records', status: 'loading' as const },
  { name: 'TLD DNSKEY', status: 'loading' as const },
  { name: 'Domain DS Records', status: 'loading' as const },
  { name: 'Domain DNSKEY', status: 'loading' as const },
]);

/**
 * Arrow Connection Interface
 *
 * Represents a visual arrow connecting related DNSSEC records.
 * Arrows connect:
 * 1. DS records in parent zone → matching DNSKEY records in child zone
 * 2. DNSKEY records → matching RRSIG records (in target zone only)
 *
 * Properties:
 * - path: SVG path data (hand-drawn style with bezier curves)
 * - color: Arrow stroke/fill color (dim gray #858585)
 * - startY: Y position of arrow start (DS or DNSKEY record)
 * - endY: Y position of arrow end (DNSKEY or RRSIG record)
 */
interface ArrowConnection {
  path: string;
  color: string;
  startY: number;
  endY: number;
}

/**
 * Arrow Connections Array
 *
 * Reactive array storing all arrow paths to be rendered in SVG overlay.
 * Recalculated whenever the DNSSEC validation data changes.
 */
const arrowConnections = ref<ArrowConnection[]>([]);

/**
 * Calculate Arrow Paths for DNSSEC Chain Visualization
 *
 * Draws hand-drawn style arrows connecting related DNSSEC records:
 * 1. DS records (parent zone) → DNSKEY records (child zone) with matching key_tag
 * 2. DNSKEY records → RRSIG records (target zone only) with matching key_tag
 *
 * Visual Style:
 * - Arrows on left side of cards (20px from container edge)
 * - Vertical line connecting records with horizontal arrows pointing to each
 * - Hand-drawn appearance using cubic bezier curves with randomized wobble
 * - Curved arrowheads shaped like "(" instead of sharp triangles
 *
 * Example ASCII representation:
 *   |->  DS record (key_tag=5116)
 *   |
 *   |->  DNSKEY record (key_tag=5116)
 *   |
 *   |->  RRSIG record (key_tag=5116)
 *
 * Technical Details:
 * - Uses DOM element positioning via getBoundingClientRect()
 * - Requires unique IDs on record elements for targeting
 * - Runs after nextTick + 100ms timeout to ensure DOM is fully rendered
 * - Recalculates on window resize and validation data changes
 */
const calculateArrowPaths = () => {
  // Clear existing arrows
  arrowConnections.value = [];

  if (!dnssecStore.validation?.chain) return;

  // Wait for DOM to fully render before calculating positions
  nextTick(() => {
    setTimeout(() => {
      const chain = dnssecStore.validation!.chain;

      // ========================================================================
      // PART 1: Draw arrows from DS records to matching DNSKEY records
      // ========================================================================
      // Iterate through parent/child zone pairs in the DNSSEC chain
      // Example: [root, io, meat.io] → pairs: (root→io), (io→meat.io)
      for (let parentIndex = 0; parentIndex < chain.length - 1; parentIndex++) {
        const parentZone = chain[parentIndex];
        const childZone = chain[parentIndex + 1];

        // Skip if either zone is missing required records
        if (!parentZone.ds_records?.length || !childZone.dnskey_records?.length) continue;

        // For each DS record in the parent zone
        parentZone.ds_records.forEach((ds, dsIndex) => {
          // Find the matching DNSKEY in child zone by key_tag
          // Example: DS with key_tag=5116 should match DNSKEY with key_tag=5116
          const matchingDnskeyIndex = childZone.dnskey_records.findIndex(
            (dnskey) => dnskey.key_tag === ds.key_tag
          );

          // Skip if no matching DNSKEY found (broken chain)
          if (matchingDnskeyIndex === -1) return;

          // Get DOM elements by their unique IDs
          // IDs are set on the <span> elements containing record text
          const dsEl = document.getElementById(
            `ds-zone${parentIndex}-keytag${ds.key_tag}-idx${dsIndex}`
          );
          const dnskeyEl = document.getElementById(
            `dnskey-zone${parentIndex + 1}-keytag${ds.key_tag}-idx${matchingDnskeyIndex}`
          );

          // Skip if elements not found in DOM (shouldn't happen)
          if (!dsEl || !dnskeyEl) return;

          // Get container for relative positioning
          const container = document.querySelector('.dnssec-chain-container');
          if (!container) return;

          // Calculate Y positions relative to container
          const containerRect = container.getBoundingClientRect();
          const dsRect = dsEl.getBoundingClientRect();
          const dnskeyRect = dnskeyEl.getBoundingClientRect();

          // Arrow positioning constants
          const leftX = 20; // Fixed X position from left edge
          const arrowLength = 20; // Horizontal arrow length

          // Calculate vertical center positions
          const y1 = dsRect.top + dsRect.height / 2 - containerRect.top; // DS record Y
          const y2 = dnskeyRect.top + dnskeyRect.height / 2 - containerRect.top; // DNSKEY record Y

          // Hand-drawn wobble effect
          // Adds random variation to create organic, hand-drawn appearance
          const wobble = () => (Math.random() - 0.5) * 6; // ±3px variation
          const wobbleSmall = () => (Math.random() - 0.5) * 3; // ±1.5px variation

          const w1 = wobble();
          const w2 = wobble();
          const w3 = wobble();
          const w4 = wobbleSmall();
          const w5 = wobbleSmall();

          // SVG Path Construction
          // Creates three segments:
          // 1. Horizontal arrow at DS record (pointing right)
          // 2. Vertical line connecting DS to DNSKEY
          // 3. Horizontal arrow at DNSKEY record (pointing right)
          //
          // Using cubic bezier curves (C command) for smooth, organic curves
          // M = moveto, C = cubic bezier curve
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

          // Add arrow to render queue
          arrowConnections.value.push({
            path,
            color: '#858585', // Dim gray matching app theme
            startY: y1,
            endY: y2,
          });
        });
      }

      // ========================================================================
      // PART 2: Draw arrows from DNSKEY to RRSIG in target zone only
      // ========================================================================
      // RRSIG records are only shown for the target domain (last zone in chain)
      // These signatures prove that the DNSKEY records are authentic
      const targetZone = chain[chain.length - 1];
      if (targetZone.dnskey_records?.length && targetZone.rrsig_records?.length) {
        targetZone.dnskey_records.forEach((dnskey, dnskeyIndex) => {
          // Find matching RRSIG signature by key_tag
          // RRSIG.key_tag indicates which DNSKEY was used to sign the record
          const matchingRrsigIndex = targetZone.rrsig_records.findIndex(
            (rrsig) => rrsig.key_tag === dnskey.key_tag
          );

          // Skip if no matching signature found
          if (matchingRrsigIndex === -1) return;

          // Get DOM elements for DNSKEY and RRSIG
          const dnskeyEl = document.getElementById(
            `dnskey-zone${chain.length - 1}-keytag${dnskey.key_tag}-idx${dnskeyIndex}`
          );
          const rrsigEl = document.getElementById(
            `rrsig-zone${chain.length - 1}-keytag${dnskey.key_tag}-idx${matchingRrsigIndex}`
          );

          if (!dnskeyEl || !rrsigEl) return;

          const container = document.querySelector('.dnssec-chain-container');
          if (!container) return;

          // Calculate positions
          const containerRect = container.getBoundingClientRect();
          const dnskeyRect = dnskeyEl.getBoundingClientRect();
          const rrsigRect = rrsigEl.getBoundingClientRect();

          // Arrow positioning (same as DS→DNSKEY arrows)
          const leftX = 20;
          const arrowLength = 20;
          const y1 = dnskeyRect.top + dnskeyRect.height / 2 - containerRect.top;
          const y2 = rrsigRect.top + rrsigRect.height / 2 - containerRect.top;

          // Hand-drawn wobble effect
          const wobble = () => (Math.random() - 0.5) * 6;
          const wobbleSmall = () => (Math.random() - 0.5) * 3;

          const w1 = wobble();
          const w2 = wobble();
          const w3 = wobble();
          const w4 = wobbleSmall();
          const w5 = wobbleSmall();

          // SVG path (same structure as DS→DNSKEY arrows)
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

          // Add DNSKEY→RRSIG arrow to render queue
          arrowConnections.value.push({
            path,
            color: '#858585',
            startY: y1,
            endY: y2,
          });
        });
      }
    }, 100); // 100ms timeout ensures DOM is fully rendered
  });
};

/**
 * Lifecycle Hooks and Watchers
 */

// Recalculate arrows whenever DNSSEC validation data changes
// Deep watch ensures nested changes (like new records) trigger recalculation
watch(() => dnssecStore.validation, calculateArrowPaths, { deep: true });

// Calculate arrows on component mount and set up resize listener
onMounted(() => {
  calculateArrowPaths();
  // Recalculate on window resize to maintain correct positioning
  window.addEventListener('resize', calculateArrowPaths);
});

// Clean up resize listener when component unmounts
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
