import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import type { TlsInfo } from '../models/certificate';

export const useCertificateStore = defineStore('certificate', () => {
  const tlsInfo = ref<TlsInfo | null>(null);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const fetchCertificate = async (host: string, port?: number) => {
    loading.value = true;
    error.value = null;

    console.log('Fetching certificate for:', host, 'port:', port || 443);

    try {
      const result = await invoke<TlsInfo>('get_certificate', {
        host,
        port: port || 443,
      });
      console.log('Certificate result:', result);
      tlsInfo.value = result;
    } catch (e) {
      error.value = e as string;
      console.error('Failed to fetch certificate:', e);
    } finally {
      loading.value = false;
    }
  };

  const clear = () => {
    tlsInfo.value = null;
    error.value = null;
  };

  return {
    tlsInfo,
    loading,
    error,
    fetchCertificate,
    clear,
  };
});
