import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

export function useKeyboardShortcuts() {
  const router = useRouter();

  const routes = [
    { key: '0', path: '/', name: 'Dashboard' },
    { key: '1', path: '/registration', name: 'Registration' },
    { key: '2', path: '/dns', name: 'DNS' },
    { key: '3', path: '/dnssec', name: 'DNSSEC' },
    { key: '4', path: '/certificate', name: 'Certificate' },
    { key: '5', path: '/http', name: 'HTTP' },
    { key: '6', path: '/email', name: 'Email' },
  ];

  const handleKeyDown = (event: KeyboardEvent) => {
    // Ignore if user is typing in an input
    if (
      event.target instanceof HTMLInputElement ||
      event.target instanceof HTMLTextAreaElement
    ) {
      return;
    }

    // Number keys 0-6 for navigation
    const route = routes.find((r) => r.key === event.key);
    if (route) {
      event.preventDefault();
      router.push(route.path);
      console.log(`Navigating to ${route.name}`);
      return;
    }

    // R for refresh
    if (event.key.toLowerCase() === 'r' && !event.metaKey && !event.ctrlKey) {
      event.preventDefault();
      console.log('Refresh triggered');
      // Emit custom event for refresh
      window.dispatchEvent(new CustomEvent('app:refresh'));
      return;
    }

    // L for logs/raw data
    if (event.key.toLowerCase() === 'l') {
      event.preventDefault();
      console.log('Show raw data modal');
      window.dispatchEvent(new CustomEvent('app:show-raw-data'));
      return;
    }

    // H for help
    if (event.key.toLowerCase() === 'h') {
      event.preventDefault();
      console.log('Show help');
      window.dispatchEvent(new CustomEvent('app:show-help'));
      return;
    }

    // ESC to close modals
    if (event.key === 'Escape') {
      window.dispatchEvent(new CustomEvent('app:close-modals'));
      return;
    }
  };

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown);
  });

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown);
  });

  return {
    routes,
  };
}
