import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useDNSStore } from './dns';
import type { DnsResponse, DnsRecord } from '../models/dns';

// Mock Tauri invoke
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

import { invoke } from '@tauri-apps/api/core';

describe('DNS Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('initializes with empty state', () => {
    const store = useDNSStore();

    expect(store.aRecords).toBeNull();
    expect(store.aaaaRecords).toBeNull();
    expect(store.mxRecords).toBeNull();
    expect(store.txtRecords).toBeNull();
    expect(store.nsRecords).toBeNull();
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
  });

  it('fetches DNS records successfully', async () => {
    const store = useDNSStore();

    const mockResponses: DnsResponse[] = [
      {
        records: [
          {
            name: 'example.com.',
            record_type: 'A',
            value: '93.184.216.34',
            ttl: 3600,
          } as DnsRecord,
        ],
        query_time: 0.123,
        resolver: 'system',
        raw_output: null,
      },
      {
        records: [
          {
            name: 'example.com.',
            record_type: 'MX',
            value: '10 mail.example.com.',
            ttl: 3600,
          } as DnsRecord,
        ],
        query_time: 0.145,
        resolver: 'system',
        raw_output: null,
      },
    ];

    vi.mocked(invoke).mockResolvedValue(mockResponses);

    await store.fetchDnsRecords('example.com');

    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    expect(store.aRecords).not.toBeNull();
    expect(store.aRecords?.records.length).toBe(1);
    expect(store.aRecords?.records[0].value).toBe('93.184.216.34');
  });

  it('handles errors during fetch', async () => {
    const store = useDNSStore();

    vi.mocked(invoke).mockRejectedValue('DNS query failed');

    await store.fetchDnsRecords('example.com');

    expect(store.loading).toBe(false);
    expect(store.error).toBe('DNS query failed');
  });

  it('caches DNS records', async () => {
    const store = useDNSStore();

    const mockResponses: DnsResponse[] = [
      {
        records: [
          {
            name: 'example.com.',
            record_type: 'A',
            value: '93.184.216.34',
            ttl: 3600,
          } as DnsRecord,
        ],
        query_time: 0.123,
        resolver: 'system',
        raw_output: null,
      },
    ];

    vi.mocked(invoke).mockResolvedValue(mockResponses);

    // First fetch
    await store.fetchDnsRecords('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);

    // Second fetch should use cache
    await store.fetchDnsRecords('example.com');
    expect(invoke).toHaveBeenCalledTimes(1); // Still only called once
  });

  it('clears cache', async () => {
    const store = useDNSStore();

    const mockResponses: DnsResponse[] = [
      {
        records: [
          {
            name: 'example.com.',
            record_type: 'A',
            value: '93.184.216.34',
            ttl: 3600,
          } as DnsRecord,
        ],
        query_time: 0.123,
        resolver: 'system',
        raw_output: null,
      },
    ];

    vi.mocked(invoke).mockResolvedValue(mockResponses);

    await store.fetchDnsRecords('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);

    store.clearCache();

    await store.fetchDnsRecords('example.com');
    expect(invoke).toHaveBeenCalledTimes(2); // Called again after cache clear
  });

  it('clears DNS data', () => {
    const store = useDNSStore();

    // Set some data
    store.setDNSData('A', {
      records: [
        {
          name: 'example.com.',
          record_type: 'A',
          value: '93.184.216.34',
          ttl: 3600,
        } as DnsRecord,
      ],
      query_time: 0.123,
      resolver: 'system',
      raw_output: null,
    });

    expect(store.aRecords).not.toBeNull();

    store.clearDNSData();

    expect(store.aRecords).toBeNull();
    expect(store.aaaaRecords).toBeNull();
    expect(store.error).toBeNull();
  });

  it('sets DNS data for different record types', () => {
    const store = useDNSStore();

    const aResponse: DnsResponse = {
      records: [
        {
          name: 'example.com.',
          record_type: 'A',
          value: '93.184.216.34',
          ttl: 3600,
        } as DnsRecord,
      ],
      query_time: 0.123,
      resolver: 'system',
      raw_output: null,
    };

    const mxResponse: DnsResponse = {
      records: [
        {
          name: 'example.com.',
          record_type: 'MX',
          value: '10 mail.example.com.',
          ttl: 3600,
        } as DnsRecord,
      ],
      query_time: 0.145,
      resolver: 'system',
      raw_output: null,
    };

    store.setDNSData('A', aResponse);
    store.setDNSData('MX', mxResponse);

    expect(store.aRecords).toEqual(aResponse);
    expect(store.mxRecords).toEqual(mxResponse);
  });

  it('handles multiple record types in response', async () => {
    const store = useDNSStore();

    const mockResponses: DnsResponse[] = [
      {
        records: [
          {
            name: 'example.com.',
            record_type: 'A',
            value: '93.184.216.34',
            ttl: 3600,
          } as DnsRecord,
        ],
        query_time: 0.123,
        resolver: 'system',
        raw_output: null,
      },
      {
        records: [
          {
            name: 'example.com.',
            record_type: 'AAAA',
            value: '2606:2800:220:1:248:1893:25c8:1946',
            ttl: 3600,
          } as DnsRecord,
        ],
        query_time: 0.134,
        resolver: 'system',
        raw_output: null,
      },
      {
        records: [
          {
            name: 'example.com.',
            record_type: 'NS',
            value: 'ns1.example.com.',
            ttl: 86400,
          } as DnsRecord,
        ],
        query_time: 0.145,
        resolver: 'system',
        raw_output: null,
      },
    ];

    vi.mocked(invoke).mockResolvedValue(mockResponses);

    await store.fetchDnsRecords('example.com');

    expect(store.aRecords).not.toBeNull();
    expect(store.aaaaRecords).not.toBeNull();
    expect(store.nsRecords).not.toBeNull();
  });
});
