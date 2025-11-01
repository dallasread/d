use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnsRecord {
    pub name: String,
    pub record_type: String,
    pub value: String,
    pub ttl: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnsResponse {
    pub records: Vec<DnsRecord>,
    pub query_time: f64,
    pub resolver: String,
    pub raw_output: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnskeyRecord {
    pub flags: u16,
    pub protocol: u8,
    pub algorithm: u8,
    pub public_key: String,
    pub key_tag: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DsRecord {
    pub key_tag: u16,
    pub algorithm: u8,
    pub digest_type: u8,
    pub digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RrsigRecord {
    pub type_covered: String,
    pub algorithm: u8,
    pub labels: u8,
    pub original_ttl: u32,
    pub signature_expiration: String,
    pub signature_inception: String,
    pub key_tag: u16,
    pub signer_name: String,
    pub signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZoneData {
    pub zone_name: String,
    pub dnskey_records: Vec<DnskeyRecord>,
    pub ds_records: Vec<DsRecord>,
    pub rrsig_records: Vec<RrsigRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnssecValidation {
    pub status: String, // SECURE, INSECURE, BOGUS, INDETERMINATE
    pub chain: Vec<ZoneData>,
    pub warnings: Vec<String>,
}
