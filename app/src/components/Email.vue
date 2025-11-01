<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useEmailStore } from '../stores/email';

const appStore = useAppStore();
const emailStore = useEmailStore();

const hasDomain = computed(() => !!appStore.domain);
</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Email Configuration</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view email configuration</p>
      </div>

      <!-- Coming Soon / Mock Display -->
      <div v-else class="space-y-6">
        <!-- Terminal-style display showing what the panel will look like -->
        <div class="bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg p-6 font-mono text-sm">
          <!-- Title -->
          <div class="mb-6">
            <span class="text-cyan-400 font-bold text-base"
              >Email Configuration for {{ appStore.domain }}</span
            >
            <div class="text-yellow-400 font-bold text-base mt-2">Security Score: 75/100</div>
          </div>

          <div class="space-y-6">
            <!-- Email Provider -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">Email Provider:</div>
              <div class="ml-4 text-gray-400">Unknown / Self-hosted</div>
            </div>

            <!-- MX Records -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">MX Records:</div>
              <div class="ml-4 space-y-3">
                <div>
                  <div class="text-gray-300">
                    Priority 10: <span class="text-white">in1-smtp.messagingengine.com</span>
                  </div>
                  <div class="ml-4 text-gray-400 text-xs">103.168.172.222</div>
                  <div class="ml-4 text-gray-400 text-xs">103.168.172.218</div>
                </div>
                <div>
                  <div class="text-gray-300">
                    Priority 20: <span class="text-white">in2-smtp.messagingengine.com</span>
                  </div>
                  <div class="ml-4 text-gray-400 text-xs">202.12.124.216</div>
                  <div class="ml-4 text-gray-400 text-xs">202.12.124.217</div>
                </div>
              </div>
            </div>

            <!-- SPF -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">SPF (Sender Policy Framework):</div>
              <div class="ml-4 space-y-1">
                <div class="text-gray-300">
                  Record:
                  <span class="text-white">v=spf1 include:spf.messagingengine.com ~all</span>
                </div>
                <div class="text-gray-300">
                  Policy: <span class="text-green-400">✓ Strict (~all)</span>
                </div>
                <div class="ml-4 text-gray-400">Rejects unauthorized senders (recommended)</div>
                <div class="text-gray-300">Mechanisms: <span class="text-white">2</span></div>
              </div>
            </div>

            <!-- DKIM -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">DKIM (DomainKeys Identified Mail):</div>
              <div class="ml-4 space-y-1">
                <div class="text-yellow-400">○ No DKIM records found</div>
                <div class="ml-4 text-gray-400 text-xs">
                  Checked selectors: default, google, k1, s1, s2, selector1, selector2
                </div>
                <div class="ml-4 text-gray-400 text-xs">
                  Note: DKIM selector names are provider-specific
                </div>
              </div>
            </div>

            <!-- DMARC -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">
                DMARC (Domain-based Message Authentication):
              </div>
              <div class="ml-4 space-y-1">
                <div class="text-gray-300">
                  Record:
                  <span class="text-white"
                    >v=DMARC1; p=quarantine; rua=mailto:postmaster@{{ appStore.domain }};
                    ruf=mailto:postmaster@mea...</span
                  >
                </div>
                <div class="text-gray-300">
                  Policy: <span class="text-yellow-400">quarantine</span>
                </div>
                <div class="text-gray-300">
                  DKIM Alignment: <span class="text-white">strict</span>
                </div>
                <div class="text-gray-300">
                  SPF Alignment: <span class="text-white">strict</span>
                </div>
                <div class="text-gray-300">
                  Aggregate Reports:
                  <span class="text-white">postmaster@{{ appStore.domain }}</span>
                </div>
                <div class="text-gray-300">
                  Forensic Reports: <span class="text-white">postmaster@{{ appStore.domain }}</span>
                </div>
              </div>
            </div>

            <!-- Configuration Status -->
            <div class="mb-6">
              <div class="text-yellow-400 font-bold mb-2">Configuration Status:</div>
              <div class="ml-4 space-y-1">
                <div class="text-yellow-400">○ DKIM not found – message signing not verified</div>
                <div class="text-green-400">✓ Core authentication configured</div>
                <div class="text-yellow-400">○ Consider adding DKIM for enhanced security</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Coming Soon Notice -->
        <div class="panel bg-blue-900/20 border-blue-800">
          <h3 class="text-lg font-semibold text-blue-400 mb-2">🚧 Coming Soon</h3>
          <p class="text-sm text-blue-300 mb-2">
            Email configuration analysis is currently under development. The display above shows an
            example of what this panel will look like.
          </p>
          <p class="text-xs text-blue-300/80">
            This panel will check MX records, SPF, DKIM (common selectors), and DMARC records to
            provide a security score and configuration recommendations.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
