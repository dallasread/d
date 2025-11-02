import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useDNSStore } from './dns';
import { useDnssecStore } from './dnssec';
import { useWhoisStore } from './whois';
import { useCertificateStore } from './certificate';
import { useHttpStore } from './http';
import { useEmailStore } from './email';
import { useLogsStore } from './logs';

export interface AppState {
  domain: string;
  loading: boolean;
  error: string | null;
}

export const useAppStore = defineStore('app', () => {
  // State
  const domain = ref<string>('');
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);
  const currentTheme = ref<string>('dark');

  // Actions
  const setDomain = (newDomain: string) => {
    // Clear all stores when domain changes
    if (domain.value !== newDomain) {
      const dnsStore = useDNSStore();
      const dnssecStore = useDnssecStore();
      const whoisStore = useWhoisStore();
      const certificateStore = useCertificateStore();
      const httpStore = useHttpStore();
      const emailStore = useEmailStore();
      const logsStore = useLogsStore();

      // Clear data from all stores
      dnsStore.clearDNSData();
      dnsStore.clearCache();
      dnssecStore.reset();
      whoisStore.clear();
      certificateStore.clear();
      httpStore.clear();
      emailStore.clear();
      logsStore.clearLogs();
    }

    domain.value = newDomain;
  };

  const setLoading = (isLoading: boolean) => {
    loading.value = isLoading;
  };

  const setError = (errorMessage: string | null) => {
    error.value = errorMessage;
  };

  const setTheme = (theme: string) => {
    currentTheme.value = theme;
    localStorage.setItem('theme', theme);
  };

  const loadTheme = () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      currentTheme.value = savedTheme;
    }
  };

  return {
    domain,
    loading,
    error,
    currentTheme,
    setDomain,
    setLoading,
    setError,
    setTheme,
    loadTheme,
  };
});
