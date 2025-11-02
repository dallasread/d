use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CertificateInfo {
    pub subject: CertificateSubject,
    pub issuer: CertificateSubject,
    pub serial_number: String,
    pub version: i32,
    pub not_before: String,
    pub not_after: String,
    pub subject_alternative_names: Vec<String>,
    pub public_key_algorithm: String,
    pub public_key_size: Option<u32>,
    pub signature_algorithm: String,
    pub fingerprint_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CertificateSubject {
    pub common_name: Option<String>,
    pub organization: Option<String>,
    pub organizational_unit: Option<String>,
    pub locality: Option<String>,
    pub state: Option<String>,
    pub country: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CertificateChain {
    pub certificates: Vec<CertificateInfo>,
    pub is_valid: bool,
    pub validation_errors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TlsInfo {
    pub host: String,
    pub port: u16,
    pub certificate_chain: CertificateChain,
    pub raw_output: Option<String>,
}
