import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useWhoisStore } from './whois';
import type { WhoisInfo } from '../models/whois';

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

import { invoke } from '@tauri-apps/api/core';

describe('WHOIS Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('initializes with empty state', () => {
    const store = useWhoisStore();

    expect(store.whoisInfo).toBeNull();
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
  });

  it('fetches WHOIS information successfully', async () => {
    const store = useWhoisStore();

    const mockWhois: WhoisInfo = {
      domain: 'example.com',
      registrar: 'Example Registrar Inc.',
      creation_date: '1995-08-14T04:00:00Z',
      expiration_date: '2025-08-13T04:00:00Z',
      updated_date: '2024-08-13T09:11:03Z',
      nameservers: ['ns1.example.com', 'ns2.example.com'],
      status: ['clientTransferProhibited'],
      dnssec: 'unsigned',
      raw_output: 'raw whois data',
    };

    vi.mocked(invoke).mockResolvedValue(mockWhois);

    await store.fetchWhoisInfo('example.com');

    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    expect(store.whoisInfo).toEqual(mockWhois);
    expect(invoke).toHaveBeenCalledWith('lookup_whois', { domain: 'example.com' });
  });

  it('handles errors during fetch', async () => {
    const store = useWhoisStore();

    vi.mocked(invoke).mockRejectedValue('WHOIS lookup failed');

    await store.fetchWhoisInfo('example.com');

    expect(store.loading).toBe(false);
    expect(store.error).toBe('WHOIS lookup failed');
    expect(store.whoisInfo).toBeNull();
  });

  it('caches WHOIS information', async () => {
    const store = useWhoisStore();

    const mockWhois: WhoisInfo = {
      domain: 'example.com',
      registrar: 'Example Registrar Inc.',
      creation_date: '1995-08-14T04:00:00Z',
      expiration_date: '2025-08-13T04:00:00Z',
      updated_date: '2024-08-13T09:11:03Z',
      nameservers: ['ns1.example.com'],
      status: ['ok'],
      dnssec: 'unsigned',
      raw_output: 'raw',
    };

    vi.mocked(invoke).mockResolvedValue(mockWhois);

    // First fetch
    await store.fetchWhoisInfo('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);

    // Second fetch should use cache
    await store.fetchWhoisInfo('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);
  });

  it('clears cache', async () => {
    const store = useWhoisStore();

    const mockWhois: WhoisInfo = {
      domain: 'example.com',
      registrar: 'Example Registrar Inc.',
      creation_date: '1995-08-14T04:00:00Z',
      expiration_date: '2025-08-13T04:00:00Z',
      updated_date: '2024-08-13T09:11:03Z',
      nameservers: [],
      status: [],
      dnssec: 'unsigned',
      raw_output: 'raw',
    };

    vi.mocked(invoke).mockResolvedValue(mockWhois);

    await store.fetchWhoisInfo('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);

    store.clearCache();

    await store.fetchWhoisInfo('example.com');
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it('clears WHOIS data', () => {
    const store = useWhoisStore();

    store.whoisInfo = {
      domain: 'example.com',
      registrar: 'Example Registrar Inc.',
      creation_date: '1995-08-14T04:00:00Z',
      expiration_date: '2025-08-13T04:00:00Z',
      updated_date: '2024-08-13T09:11:03Z',
      nameservers: [],
      status: [],
      dnssec: 'unsigned',
      raw_output: 'raw',
    };

    expect(store.whoisInfo).not.toBeNull();

    store.clearWhoisData();

    expect(store.whoisInfo).toBeNull();
    expect(store.error).toBeNull();
  });
});
