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
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
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

    // Left/Right arrow keys for panel navigation
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      const currentPath = router.currentRoute.value.path;
      const currentIndex = routes.findIndex((r) => r.path === currentPath);

      if (currentIndex !== -1) {
        let nextIndex: number;
        if (event.key === 'ArrowLeft') {
          // Go to previous panel (wrap around to last if at first)
          nextIndex = currentIndex === 0 ? routes.length - 1 : currentIndex - 1;
        } else {
          // Go to next panel (wrap around to first if at last)
          nextIndex = currentIndex === routes.length - 1 ? 0 : currentIndex + 1;
        }
        router.push(routes[nextIndex].path);
        console.log(`Navigating to ${routes[nextIndex].name}`);
      }
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

    // L for logs slideout
    if (event.key.toLowerCase() === 'l') {
      event.preventDefault();
      console.log('Toggle logs slideout');
      window.dispatchEvent(new CustomEvent('app:toggle-logs'));
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
