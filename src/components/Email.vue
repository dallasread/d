<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '../stores/app';
import { useEmailStore } from '../stores/email';
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon } from '@heroicons/vue/24/solid';

const appStore = useAppStore();
// @ts-expect-error - Reserved for future email functionality
const emailStore = useEmailStore();

const hasDomain = computed(() => !!appStore.domain);

// Mock data for demonstration - will be replaced with real data from emailStore
const mockEmailData = computed(() => {
  if (!appStore.domain) return null;

  return {
    securityScore: 75,
    provider: 'Unknown / Self-hosted',
    mxRecords: [
      {
        priority: 10,
        hostname: 'in1-smtp.messagingengine.com',
        ips: ['103.168.172.222', '103.168.172.218'],
      },
      {
        priority: 20,
        hostname: 'in2-smtp.messagingengine.com',
        ips: ['202.12.124.216', '202.12.124.217'],
      },
    ],
    spf: {
      record: 'v=spf1 include:spf.messagingengine.com ~all',
      policy: '~all',
      mechanisms: 2,
      valid: true,
    },
    dkim: {
      found: false,
      checkedSelectors: ['default', 'google', 'k1', 's1', 's2', 'selector1', 'selector2'],
    },
    dmarc: {
      record: `v=DMARC1; p=quarantine; rua=mailto:postmaster@${appStore.domain}; ruf=mailto:postmaster@${appStore.domain}`,
      policy: 'quarantine',
      dkimAlignment: 'strict',
      spfAlignment: 'strict',
      aggregateReports: `postmaster@${appStore.domain}`,
      forensicReports: `postmaster@${appStore.domain}`,
    },
  };
});

const diagnostics = computed(() => {
  const data = mockEmailData.value;
  if (!data) return { issues: [], warnings: [], successes: [] };

  const issues = [];
  const warnings = [];
  const successes = [];

  // MX Records
  if (data.mxRecords.length === 0) {
    issues.push('No MX records found - email delivery will fail');
  } else {
    successes.push(`${data.mxRecords.length} MX record(s) configured for email delivery`);
  }

  // SPF
  if (!data.spf.valid) {
    issues.push('SPF record is invalid or missing');
  } else {
    successes.push('SPF configured - helps prevent email spoofing');
  }

  // DKIM
  if (!data.dkim.found) {
    warnings.push('DKIM not found - message signing not verified');
  } else {
    successes.push('DKIM configured - emails are cryptographically signed');
  }

  // DMARC
  if (!data.dmarc.record) {
    warnings.push('DMARC not configured - limited email authentication enforcement');
  } else if (data.dmarc.policy === 'none') {
    warnings.push('DMARC policy set to "none" - not enforcing authentication');
  } else {
    successes.push(`DMARC configured with "${data.dmarc.policy}" policy`);
  }

  return { issues, warnings, successes };
});

const getScoreColor = (score: number) => {
  if (score >= 90) return 'text-green-400';
  if (score >= 70) return 'text-yellow-400';
  return 'text-red-400';
};
</script>

<template>
  <div class="min-h-screen p-3 md:p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Email Configuration</h1>

      <!-- Empty state -->
      <div v-if="!hasDomain" class="panel">
        <p class="text-[#858585]">Enter a domain to view email configuration</p>
      </div>

      <!-- Email Configuration Display -->
      <div v-else-if="mockEmailData" class="space-y-6">
        <!-- Security Score Card -->
        <div class="panel">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-semibold">Email Security Score</h2>
            <span class="text-3xl font-bold" :class="getScoreColor(mockEmailData.securityScore)">
              {{ mockEmailData.securityScore }}/100
            </span>
          </div>
        </div>

        <!-- Diagnostic Summary -->
        <div
          class="panel"
          v-if="
            diagnostics.issues.length > 0 ||
            diagnostics.warnings.length > 0 ||
            diagnostics.successes.length > 0
          "
        >
          <h2 class="text-xl font-semibold mb-4">Email Health Check</h2>

          <!-- Issues -->
          <div v-if="diagnostics.issues.length > 0" class="space-y-2 mb-3">
            <div
              v-for="(issue, index) in diagnostics.issues"
              :key="`issue-${index}`"
              class="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded"
            >
              <XCircleIcon class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-red-300">{{ issue }}</span>
            </div>
          </div>

          <!-- Warnings -->
          <div v-if="diagnostics.warnings.length > 0" class="space-y-2 mb-3">
            <div
              v-for="(warning, index) in diagnostics.warnings"
              :key="`warning-${index}`"
              class="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded"
            >
              <ExclamationTriangleIcon class="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-yellow-300">{{ warning }}</span>
            </div>
          </div>

          <!-- Successes -->
          <div v-if="diagnostics.successes.length > 0" class="space-y-2">
            <div
              v-for="(success, index) in diagnostics.successes"
              :key="`success-${index}`"
              class="flex items-start gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded"
            >
              <CheckCircleIcon class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-green-300">{{ success }}</span>
            </div>
          </div>
        </div>

        <!-- MX Records Card -->
        <div class="panel">
          <h2 class="text-lg font-semibold mb-3 flex items-center gap-2">
            <span class="text-2xl">📧</span>
            MX Records
            <span class="text-sm font-normal text-blue-400">{{ mockEmailData.mxRecords.length }}</span>
          </h2>
          <div v-if="mockEmailData.mxRecords.length > 0" class="space-y-3">
            <div
              v-for="(mx, index) in mockEmailData.mxRecords"
              :key="index"
              class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]"
            >
              <div class="flex items-center gap-3 mb-2">
                <span class="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold">
                  Priority {{ mx.priority }}
                </span>
                <code class="text-sm font-mono">{{ mx.hostname }}</code>
              </div>
              <div class="ml-4 space-y-1">
                <div v-for="(ip, ipIndex) in mx.ips" :key="ipIndex" class="text-xs text-[#858585]">
                  {{ ip }}
                </div>
              </div>
            </div>
          </div>
          <p v-else class="text-[#858585] text-sm">No MX records found</p>
        </div>

        <!-- SPF Card -->
        <div class="panel">
          <h2 class="text-lg font-semibold mb-3 flex items-center gap-2">
            <span class="text-2xl">🛡️</span>
            SPF (Sender Policy Framework)
          </h2>
          <div class="space-y-3">
            <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
              <div class="text-xs text-[#858585] mb-1">Record</div>
              <code class="text-sm font-mono break-all">{{ mockEmailData.spf.record }}</code>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
                <div class="text-xs text-[#858585] mb-1">Policy</div>
                <span class="text-sm text-green-400 font-semibold">{{ mockEmailData.spf.policy }}</span>
              </div>
              <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
                <div class="text-xs text-[#858585] mb-1">Mechanisms</div>
                <span class="text-sm">{{ mockEmailData.spf.mechanisms }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- DKIM Card -->
        <div class="panel">
          <h2 class="text-lg font-semibold mb-3 flex items-center gap-2">
            <span class="text-2xl">🔑</span>
            DKIM (DomainKeys Identified Mail)
          </h2>
          <div v-if="!mockEmailData.dkim.found" class="space-y-3">
            <div class="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded">
              <ExclamationTriangleIcon class="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              <div>
                <div class="text-sm text-yellow-300 mb-1">No DKIM records found</div>
                <div class="text-xs text-[#858585]">
                  Checked selectors: {{ mockEmailData.dkim.checkedSelectors.join(', ') }}
                </div>
                <div class="text-xs text-[#858585] mt-1">
                  Note: DKIM selector names are provider-specific
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- DMARC Card -->
        <div class="panel">
          <h2 class="text-lg font-semibold mb-3 flex items-center gap-2">
            <span class="text-2xl">📋</span>
            DMARC (Domain-based Message Authentication)
          </h2>
          <div class="space-y-3">
            <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
              <div class="text-xs text-[#858585] mb-1">Record</div>
              <code class="text-sm font-mono break-all">{{ mockEmailData.dmarc.record }}</code>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
                <div class="text-xs text-[#858585] mb-1">Policy</div>
                <span class="text-sm text-yellow-400 font-semibold">{{ mockEmailData.dmarc.policy }}</span>
              </div>
              <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
                <div class="text-xs text-[#858585] mb-1">DKIM Alignment</div>
                <span class="text-sm">{{ mockEmailData.dmarc.dkimAlignment }}</span>
              </div>
              <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
                <div class="text-xs text-[#858585] mb-1">SPF Alignment</div>
                <span class="text-sm">{{ mockEmailData.dmarc.spfAlignment }}</span>
              </div>
              <div class="p-3 bg-[#2d2d30] rounded border border-[#3e3e42]">
                <div class="text-xs text-[#858585] mb-1">Aggregate Reports</div>
                <span class="text-sm break-all">{{ mockEmailData.dmarc.aggregateReports }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
