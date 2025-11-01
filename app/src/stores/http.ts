import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import type { HttpResponse } from '../models/http';

export const useHttpStore = defineStore('http', () => {
  const httpResponse = ref<HttpResponse | null>(null);
  const httpsResponse = ref<HttpResponse | null>(null);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const fetchHttp = async (domain: string) => {
    loading.value = true;
    error.value = null;

    try {
      // Fetch both HTTP and HTTPS
      const [http, https] = await Promise.all([
        invoke<HttpResponse>('fetch_http', { url: `http://${domain}` }).catch(() => null),
        invoke<HttpResponse>('fetch_http', { url: `https://${domain}` }).catch(() => null),
      ]);

      httpResponse.value = http;
      httpsResponse.value = https;
    } catch (e) {
      error.value = e as string;
      console.error('Failed to fetch HTTP:', e);
    } finally {
      loading.value = false;
    }
  };

  const clear = () => {
    httpResponse.value = null;
    httpsResponse.value = null;
    error.value = null;
  };

  return {
    httpResponse,
    httpsResponse,
    loading,
    error,
    fetchHttp,
    clear,
  };
});
