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

  // Cache
  const cache = ref<
    Map<
      string,
      {
        aRecords: DnsResponse | null;
        aaaaRecords: DnsResponse | null;
        mxRecords: DnsResponse | null;
        txtRecords: DnsResponse | null;
        nsRecords: DnsResponse | null;
      }
    >
  >(new Map());
  const currentDomain = ref<string>('');

  // Actions
  const fetchDnsRecords = async (domain: string) => {
    // Check cache first
    if (cache.value.has(domain)) {
      const cached = cache.value.get(domain)!;
      aRecords.value = cached.aRecords;
      aaaaRecords.value = cached.aaaaRecords;
      mxRecords.value = cached.mxRecords;
      txtRecords.value = cached.txtRecords;
      nsRecords.value = cached.nsRecords;
      currentDomain.value = domain;
      return;
    }

    loading.value = true;
    error.value = null;
    currentDomain.value = domain;

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

      // Save to cache
      cache.value.set(domain, {
        aRecords: aRecords.value,
        aaaaRecords: aaaaRecords.value,
        mxRecords: mxRecords.value,
        txtRecords: txtRecords.value,
        nsRecords: nsRecords.value,
      });
    } catch (e) {
      error.value = e as string;
      console.error('Failed to fetch DNS records:', e);
    } finally {
      loading.value = false;
    }
  };

  const clearCache = () => {
    cache.value.clear();
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
    currentDomain,
    clearCache,
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
