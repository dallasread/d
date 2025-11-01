import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import type { DnsResponse } from '../models/dns';

export const useDNSStore = defineStore('dns', () => {
  // State
  const aRecords = ref<DnsResponse | null>(null);
  const aaaaRecords = ref<DnsResponse | null>(null);
  const mxRecords = ref<DnsResponse | null>(null);
  const txtRecords = ref<DnsResponse | null>(null);
  const nsRecords = ref<DnsResponse | null>(null);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  // Actions
  const fetchDnsRecords = async (domain: string) => {
    loading.value = true;
    error.value = null;

    try {
      const recordTypes = ['A', 'AAAA', 'MX', 'TXT', 'NS'];
      const responses = await invoke<DnsResponse[]>('query_dns_multiple', {
        domain,
        recordTypes,
      });

      // Map responses to individual record types
      responses.forEach((response) => {
        if (response.records.length > 0) {
          const recordType = response.records[0].record_type;
          setDNSData(recordType, response);
        }
      });
    } catch (e) {
      error.value = e as string;
      console.error('Failed to fetch DNS records:', e);
    } finally {
      loading.value = false;
    }
  };

  const setDNSData = (type: string, data: DnsResponse) => {
    switch (type) {
      case 'A':
        aRecords.value = data;
        break;
      case 'AAAA':
        aaaaRecords.value = data;
        break;
      case 'MX':
        mxRecords.value = data;
        break;
      case 'TXT':
        txtRecords.value = data;
        break;
      case 'NS':
        nsRecords.value = data;
        break;
    }
  };

  const clearDNSData = () => {
    aRecords.value = null;
    aaaaRecords.value = null;
    mxRecords.value = null;
    txtRecords.value = null;
    nsRecords.value = null;
    error.value = null;
  };

  return {
    aRecords,
    aaaaRecords,
    mxRecords,
    txtRecords,
    nsRecords,
    loading,
    error,
    fetchDnsRecords,
    setDNSData,
    clearDNSData,
  };
});
