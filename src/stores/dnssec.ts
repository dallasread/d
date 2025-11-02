import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import type { DnssecValidation } from '../models/dns';

export const useDnssecStore = defineStore('dnssec', () => {
  const validation = ref<DnssecValidation | null>(null);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const fetchDnssec = async (domain: string) => {
    loading.value = true;
    error.value = null;

    try {
      const result = await invoke<DnssecValidation>('validate_dnssec', { domain });
      validation.value = result;
    } catch (e) {
      error.value = e as string;
      validation.value = null;
    } finally {
      loading.value = false;
    }
  };

  const reset = () => {
    validation.value = null;
    loading.value = false;
    error.value = null;
  };

  return {
    validation,
    loading,
    error,
    fetchDnssec,
    reset,
  };
});
