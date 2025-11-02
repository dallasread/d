import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { useDNSStore } from './dns';

export interface MxRecord {
  priority: number;
  hostname: string;
  ips: string[];
}

export interface SpfRecord {
  record: string;
  policy: string;
  mechanisms: number;
  isValid: boolean;
}

export interface DkimRecord {
  selector: string;
  record: string | null;
  isValid: boolean;
}

export interface DmarcRecord {
  record: string;
  policy: string;
  dkimAlignment: string;
  spfAlignment: string;
  aggregateReports: string;
  forensicReports: string;
  isValid: boolean;
}

export interface EmailConfig {
  mxRecords: MxRecord[];
  spfRecord: SpfRecord | null;
  dkimRecords: DkimRecord[];
  dmarcRecord: DmarcRecord | null;
  securityScore: number;
}

export const useEmailStore = defineStore('email', () => {
  const emailConfig = ref<EmailConfig | null>(null);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const fetchEmailConfig = async (domain: string) => {
    loading.value = true;
    error.value = null;

    try {
      // Get existing DNS records from DNS store to avoid duplicate queries
      const dnsStore = useDNSStore();

      // Extract MX and TXT records that are already fetched
      const existingMxRecords = dnsStore.mxRecords?.records?.map(record => record.value) || [];
      const existingTxtRecords = dnsStore.txtRecords?.records?.map(record => record.value) || [];

      const result = await invoke<EmailConfig>('fetch_email_config', {
        domain,
        existingMxRecords,
        existingTxtRecords
      });
      emailConfig.value = result;
    } catch (e) {
      error.value = e as string;
      console.error('Failed to fetch email config:', e);
    } finally {
      loading.value = false;
    }
  };

  const clear = () => {
    emailConfig.value = null;
    error.value = null;
  };

  return {
    emailConfig,
    loading,
    error,
    fetchEmailConfig,
    clear,
  };
});
