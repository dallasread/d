import { defineStore } from 'pinia';
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import type { HttpResponse } from '../models/http';

export const useHttpStore = defineStore('http', () => {
  const httpResponse = ref<HttpResponse | null>(null);
  const httpsResponse = ref<HttpResponse | null>(null);
  const wwwHttpResponse = ref<HttpResponse | null>(null);
  const wwwHttpsResponse = ref<HttpResponse | null>(null);
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  const fetchHttp = async (domain: string) => {
    loading.value = true;
    error.value = null;

    try {
      // Check if domain already has www
      const isWww = domain.startsWith('www.');
      const wwwDomain = isWww ? domain : `www.${domain}`;
      const apexDomain = isWww ? domain.substring(4) : domain;

      // Fetch apex domain (HTTP and HTTPS) and www subdomain (HTTP and HTTPS)
      const [http, https, wwwHttp, wwwHttps] = await Promise.all([
        invoke<HttpResponse>('fetch_http', { url: `http://${apexDomain}` }).catch(() => null),
        invoke<HttpResponse>('fetch_http', { url: `https://${apexDomain}` }).catch(() => null),
        invoke<HttpResponse>('fetch_http', { url: `http://${wwwDomain}` }).catch(() => null),
        invoke<HttpResponse>('fetch_http', { url: `https://${wwwDomain}` }).catch(() => null),
      ]);

      httpResponse.value = http;
      httpsResponse.value = https;
      wwwHttpResponse.value = wwwHttp;
      wwwHttpsResponse.value = wwwHttps;
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
    wwwHttpResponse.value = null;
    wwwHttpsResponse.value = null;
    error.value = null;
  };

  return {
    httpResponse,
    httpsResponse,
    wwwHttpResponse,
    wwwHttpsResponse,
    loading,
    error,
    fetchHttp,
    clear,
  };
});
