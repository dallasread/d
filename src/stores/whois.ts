import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import type { WhoisInfo } from '../models/whois';

export const useWhoisStore = defineStore('whois', () => {
  const whoisInfo = ref<WhoisInfo | null>(null);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const fetchWhois = async (domain: string) => {
    loading.value = true;
    error.value = null;

    try {
      const result = await invoke<WhoisInfo>('lookup_whois', { domain });
      whoisInfo.value = result;
    } catch (e) {
      error.value = e as string;
      console.error('Failed to fetch WHOIS:', e);
    } finally {
      loading.value = false;
    }
  };

  const clear = () => {
    whoisInfo.value = null;
    error.value = null;
  };

  return {
    whoisInfo,
    loading,
    error,
    fetchWhois,
    clear,
  };
});
