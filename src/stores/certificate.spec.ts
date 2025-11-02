import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useCertificateStore } from './certificate';
import type { TlsInfo, CertificateSubject, CertificateInfo } from '../models/certificate';

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

import { invoke } from '@tauri-apps/api/core';

describe('Certificate Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('initializes with empty state', () => {
    const store = useCertificateStore();

    expect(store.tlsInfo).toBeNull();
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
  });

  it('fetches certificate information successfully', async () => {
    const store = useCertificateStore();

    const mockSubject: CertificateSubject = {
      common_name: 'example.com',
      organization: 'Example Inc',
      organizational_unit: null,
      locality: null,
      state: null,
      country: 'US',
    };

    const mockCert: CertificateInfo = {
      subject: mockSubject,
      issuer: {
        common_name: 'Example CA',
        organization: 'Example Inc',
        organizational_unit: null,
        locality: null,
        state: null,
        country: 'US',
      },
      serial_number: '123456',
      version: 3,
      not_before: '2024-01-01',
      not_after: '2025-01-01',
      subject_alternative_names: [],
      public_key_algorithm: 'RSA',
      public_key_size: 2048,
      signature_algorithm: 'SHA256withRSA',
      fingerprint_sha256: '',
    };

    const mockTlsInfo: TlsInfo = {
      host: 'example.com',
      port: 443,
      certificate_chain: {
        certificates: [mockCert],
        is_valid: true,
        validation_errors: [],
      },
      raw_output: null,
    };

    vi.mocked(invoke).mockResolvedValue(mockTlsInfo);

    await store.fetchCertificate('example.com');

    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    expect(store.tlsInfo).toEqual(mockTlsInfo);
    expect(invoke).toHaveBeenCalledWith('get_certificate', { host: 'example.com', port: 443 });
  });

  it('fetches certificate with custom port', async () => {
    const store = useCertificateStore();

    const mockTlsInfo: TlsInfo = {
      host: 'example.com',
      port: 8443,
      certificate_chain: {
        certificates: [],
        is_valid: true,
        validation_errors: [],
      },
      raw_output: null,
    };

    vi.mocked(invoke).mockResolvedValue(mockTlsInfo);

    await store.fetchCertificate('example.com', 8443);

    expect(invoke).toHaveBeenCalledWith('get_certificate', { host: 'example.com', port: 8443 });
  });

  it('handles errors during fetch', async () => {
    const store = useCertificateStore();

    vi.mocked(invoke).mockRejectedValue('Certificate fetch failed');

    await store.fetchCertificate('example.com');

    expect(store.loading).toBe(false);
    expect(store.error).toBe('Certificate fetch failed');
    expect(store.tlsInfo).toBeNull();
  });

  it('caches certificate information', async () => {
    const store = useCertificateStore();

    const mockTlsInfo: TlsInfo = {
      host: 'example.com',
      port: 443,
      certificate_chain: {
        certificates: [],
        is_valid: true,
        validation_errors: [],
      },
      raw_output: null,
    };

    vi.mocked(invoke).mockResolvedValue(mockTlsInfo);

    // First fetch
    await store.fetchCertificate('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);

    // Second fetch should use cache
    await store.fetchCertificate('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);
  });

  it('clears cache', async () => {
    const store = useCertificateStore();

    const mockTlsInfo: TlsInfo = {
      host: 'example.com',
      port: 443,
      certificate_chain: {
        certificates: [],
        is_valid: true,
        validation_errors: [],
      },
      raw_output: null,
    };

    vi.mocked(invoke).mockResolvedValue(mockTlsInfo);

    await store.fetchCertificate('example.com');
    expect(invoke).toHaveBeenCalledTimes(1);

    store.clearCache();

    await store.fetchCertificate('example.com');
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it('clears certificate data', () => {
    const store = useCertificateStore();

    store.tlsInfo = {
      host: 'example.com',
      port: 443,
      certificate_chain: {
        certificates: [],
        is_valid: true,
        validation_errors: [],
      },
      raw_output: null,
    };

    expect(store.tlsInfo).not.toBeNull();

    store.clearCertificateData();

    expect(store.tlsInfo).toBeNull();
    expect(store.error).toBeNull();
  });
});
