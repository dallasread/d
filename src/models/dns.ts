export interface DnsRecord {
  name: string;
  record_type: string;
  value: string;
  ttl: number;
}

export interface DnsResponse {
  records: DnsRecord[];
  query_time: number;
  resolver: string;
  raw_output?: string;
}

export interface DnskeyRecord {
  flags: number;
  protocol: number;
  algorithm: number;
  public_key: string;
  key_tag: number;
}

export interface DsRecord {
  key_tag: number;
  algorithm: number;
  digest_type: number;
  digest: string;
}

export interface RrsigRecord {
  type_covered: string;
  algorithm: number;
  labels: number;
  original_ttl: number;
  signature_expiration: string;
  signature_inception: string;
  key_tag: number;
  signer_name: string;
  signature: string;
}

export interface ZoneData {
  zone_name: string;
  dnskey_records: DnskeyRecord[];
  ds_records: DsRecord[];
  rrsig_records: RrsigRecord[];
}

export interface DnssecValidation {
  status: string; // SECURE, INSECURE, BOGUS, INDETERMINATE
  chain: ZoneData[];
  warnings: string[];
}
