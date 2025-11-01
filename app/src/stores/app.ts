import { defineStore } from 'pinia';
import { ref } from 'vue';

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
