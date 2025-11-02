export interface CertificateSubject {
  common_name?: string;
  organization?: string;
  organizational_unit?: string;
  locality?: string;
  state?: string;
  country?: string;
}

export interface CertificateInfo {
  subject: CertificateSubject;
  issuer: CertificateSubject;
  serial_number: string;
  version: number;
  not_before: string;
  not_after: string;
  subject_alternative_names: string[];
  public_key_algorithm: string;
  public_key_size?: number;
  signature_algorithm: string;
  fingerprint_sha256: string;
}

export interface CertificateChain {
  certificates: CertificateInfo[];
  is_valid: boolean;
  validation_errors: string[];
}

export interface TlsInfo {
  host: string;
  port: number;
  certificate_chain: CertificateChain;
  raw_output?: string;
}
