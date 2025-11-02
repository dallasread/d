// Test helpers and utilities for frontend tests

import type { DnsResponse, DnsRecord } from '../models/dns';
import type { WhoisInfo } from '../models/whois';
import type { TlsInfo, CertificateInfo, CertificateSubject } from '../models/certificate';

/**
 * Create a mock DNS record
 */
export function createMockDnsRecord(overrides?: Partial<DnsRecord>): DnsRecord {
  return {
    name: 'example.com.',
    record_type: 'A',
    value: '93.184.216.34',
    ttl: 3600,
    ...overrides,
  };
}

/**
 * Create a mock DNS response
 */
export function createMockDnsResponse(overrides?: Partial<DnsResponse>): DnsResponse {
  return {
    records: [createMockDnsRecord()],
    query_time: 0.123,
    resolver: 'system',
    raw_output: null,
    ...overrides,
  };
}

/**
 * Create a mock WHOIS info
 */
export function createMockWhoisInfo(overrides?: Partial<WhoisInfo>): WhoisInfo {
  return {
    domain: 'example.com',
    registrar: 'Example Registrar Inc.',
    creation_date: '1995-08-14T04:00:00Z',
    expiration_date: '2025-08-13T04:00:00Z',
    updated_date: '2024-08-13T09:11:03Z',
    nameservers: ['ns1.example.com', 'ns2.example.com'],
    status: ['clientTransferProhibited'],
    dnssec: 'unsigned',
    raw_output: 'mock whois output',
    ...overrides,
  };
}

/**
 * Create a mock certificate subject
 */
export function createMockCertificateSubject(
  overrides?: Partial<CertificateSubject>
): CertificateSubject {
  return {
    common_name: 'example.com',
    organization: 'Example Inc',
    organizational_unit: null,
    locality: null,
    state: null,
    country: 'US',
    ...overrides,
  };
}

/**
 * Create a mock certificate info
 */
export function createMockCertificateInfo(
  overrides?: Partial<CertificateInfo>
): CertificateInfo {
  return {
    subject: createMockCertificateSubject(),
    issuer: createMockCertificateSubject({ common_name: 'Example CA' }),
    serial_number: '123456',
    version: 3,
    not_before: '2024-01-01T00:00:00Z',
    not_after: '2025-01-01T00:00:00Z',
    subject_alternative_names: [],
    public_key_algorithm: 'RSA',
    public_key_size: 2048,
    signature_algorithm: 'SHA256withRSA',
    fingerprint_sha256: 'abc123',
    ...overrides,
  };
}

/**
 * Create a mock TLS info
 */
export function createMockTlsInfo(overrides?: Partial<TlsInfo>): TlsInfo {
  return {
    host: 'example.com',
    port: 443,
    certificate_chain: {
      certificates: [createMockCertificateInfo()],
      is_valid: true,
      validation_errors: [],
    },
    raw_output: null,
    ...overrides,
  };
}

/**
 * Create multiple mock DNS records
 */
export function createMockDnsRecords(count: number, type: string): DnsRecord[] {
  return Array.from({ length: count }, (_, i) => ({
    name: 'example.com.',
    record_type: type,
    value: type === 'A' ? `93.184.216.${34 + i}` : `${type.toLowerCase()}${i + 1}.example.com.`,
    ttl: 3600,
  }));
}

/**
 * Wait for async operations to complete
 */
export function flushPromises(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

/**
 * Create a mock invoke response for testing
 */
export function mockInvokeResponse<T>(response: T): () => Promise<T> {
  return () => Promise.resolve(response);
}

/**
 * Create a mock invoke error for testing
 */
export function mockInvokeError(error: string): () => Promise<never> {
  return () => Promise.reject(error);
}
