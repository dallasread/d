import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface DNSRecord {
  name: string;
  type: string;
  value: string;
  ttl: number;
}

export interface DNSResponse {
  records: DNSRecord[];
  query_time: number;
  resolver: string;
}

export const useDNSStore = defineStore('dns', () => {
  // State
  const aRecords = ref<DNSResponse | null>(null);
  const aaaaRecords = ref<DNSResponse | null>(null);
  const mxRecords = ref<DNSResponse | null>(null);
  const txtRecords = ref<DNSResponse | null>(null);
  const nsRecords = ref<DNSResponse | null>(null);
  const loading = ref<boolean>(false);

  // Actions
  const setDNSData = (type: string, data: DNSResponse) => {
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
  };

  return {
    aRecords,
    aaaaRecords,
    mxRecords,
    txtRecords,
    nsRecords,
    loading,
    setDNSData,
    clearDNSData,
  };
});
