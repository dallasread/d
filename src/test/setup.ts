// Vitest setup file
import { vi } from 'vitest';

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn(),
  emit: vi.fn(),
}));

// Mock window.__TAURI__
global.window = global.window || {};
(global.window as any).__TAURI__ = {
  invoke: vi.fn(),
};
