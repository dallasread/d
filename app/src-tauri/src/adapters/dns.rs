use crate::models::dns::{DnsRecord, DnsResponse, DnskeyRecord, DsRecord, RrsigRecord};
use std::process::Command;
use std::time::Instant;

pub struct DnsAdapter;

impl DnsAdapter {
    pub fn new() -> Self {
        DnsAdapter
    }

    pub async fn query(&self, domain: &str, record_type: &str) -> Result<DnsResponse, String> {
        let start = Instant::now();

        // Check if dig is available
        if !self.is_dig_available() {
            return Err("dig command not found. Please install BIND tools.".to_string());
        }

        // Execute dig command
        let output = Command::new("dig")
            .arg("+noall")
            .arg("+answer")
            .arg(record_type)
            .arg(domain)
            .output()
            .map_err(|e| format!("Failed to execute dig: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("dig command failed: {}", stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let records = self.parse_dig_output(&stdout, record_type)?;

        Ok(DnsResponse {
            records,
            query_time,
            resolver: "system".to_string(),
            raw_output: Some(stdout.to_string()),
        })
    }

    pub async fn query_multiple(
        &self,
        domain: &str,
        record_types: Vec<&str>,
    ) -> Result<Vec<DnsResponse>, String> {
        let mut responses = Vec::new();

        for record_type in record_types {
            match self.query(domain, record_type).await {
                Ok(response) => responses.push(response),
                Err(e) => {
                    // Log error but continue with other queries
                    eprintln!("Error querying {} record: {}", record_type, e);
                }
            }
        }

        Ok(responses)
    }

    fn parse_dig_output(&self, output: &str, record_type: &str) -> Result<Vec<DnsRecord>, String> {
        let mut records = Vec::new();

        for line in output.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with(';') {
                continue;
            }

            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 5 {
                continue;
            }

            let name = parts[0].to_string();
            let ttl = parts[1].parse::<u32>().unwrap_or(0);
            let rr_type = parts[3].to_string();
            let value = parts[4..].join(" ");

            records.push(DnsRecord {
                name,
                record_type: rr_type,
                value,
                ttl,
            });
        }

        if records.is_empty() {
            return Err(format!("No {} records found", record_type));
        }

        Ok(records)
    }

    fn is_dig_available(&self) -> bool {
        Command::new("dig").arg("-v").output().is_ok()
    }

    // Get authoritative nameservers for a domain
    pub async fn get_nameservers(&self, domain: &str) -> Result<Vec<String>, String> {
        let response = self.query(domain, "NS").await?;
        Ok(response.records.iter().map(|r| r.value.clone()).collect())
    }

    // Query DNSKEY records from authoritative server
    pub async fn query_dnskey(&self, domain: &str) -> Result<DnsResponse, String> {
        let start = Instant::now();

        // First get the nameservers for this domain
        let nameservers = self.get_nameservers(domain).await?;

        if nameservers.is_empty() {
            return Err("No nameservers found for domain".to_string());
        }

        // Query the first authoritative nameserver
        let ns = &nameservers[0];

        if !self.is_dig_available() {
            return Err("dig command not found".to_string());
        }

        let mut cmd = Command::new("dig");
        cmd.arg("+noall")
            .arg("+answer")
            .arg("+dnssec")
            .arg(format!("@{}", ns))
            .arg("DNSKEY")
            .arg(domain);

        let output = cmd
            .output()
            .map_err(|e| format!("Failed to execute dig: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("dig command failed: {}", stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);

        // For DNSSEC queries, empty results are valid (means DNSSEC not enabled)
        let records = self
            .parse_dig_output(&stdout, "DNSKEY")
            .unwrap_or_else(|_| Vec::new());

        Ok(DnsResponse {
            records,
            query_time,
            resolver: ns.to_string(),
            raw_output: Some(stdout.to_string()),
        })
    }

    // Query DS records from parent zone's authoritative server
    pub async fn query_ds(&self, domain: &str) -> Result<DnsResponse, String> {
        let start = Instant::now();

        // Get parent domain
        let parts: Vec<&str> = domain.split('.').collect();
        if parts.len() < 2 {
            return Err("Invalid domain for DS query".to_string());
        }

        let parent_domain = parts[1..].join(".");
        let parent_ns = self.get_nameservers(&parent_domain).await?;

        if parent_ns.is_empty() {
            return Err("No parent nameservers found".to_string());
        }

        let ns = &parent_ns[0];

        if !self.is_dig_available() {
            return Err("dig command not found".to_string());
        }

        let mut cmd = Command::new("dig");
        cmd.arg("+noall")
            .arg("+answer")
            .arg("+dnssec")
            .arg("+time=2") // 2 second timeout
            .arg("+tries=1") // Only try once
            .arg(format!("@{}", ns))
            .arg("DS")
            .arg(domain);

        let output = cmd
            .output()
            .map_err(|e| format!("Failed to execute dig: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("dig command failed: {}", stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);

        // For DNSSEC queries, empty results are valid (means DNSSEC not enabled)
        let records = self
            .parse_dig_output(&stdout, "DS")
            .unwrap_or_else(|_| Vec::new());

        Ok(DnsResponse {
            records,
            query_time,
            resolver: ns.to_string(),
            raw_output: Some(stdout.to_string()),
        })
    }

    // Parse DNSKEY records from DNS records
    pub fn parse_dnskey_records(&self, records: &[DnsRecord]) -> Vec<DnskeyRecord> {
        records
            .iter()
            .filter(|r| r.record_type == "DNSKEY")
            .filter_map(|r| {
                // DNSKEY format: flags protocol algorithm public_key
                let parts: Vec<&str> = r.value.split_whitespace().collect();
                if parts.len() >= 4 {
                    let flags = parts[0].parse::<u16>().ok()?;
                    let protocol = parts[1].parse::<u8>().ok()?;
                    let algorithm = parts[2].parse::<u8>().ok()?;
                    let public_key = parts[3..].join(" ");

                    // Calculate key tag (simplified - just use flags for now)
                    let key_tag = flags; // In real implementation, calculate from public key

                    Some(DnskeyRecord {
                        flags,
                        protocol,
                        algorithm,
                        key_tag,
                        public_key,
                    })
                } else {
                    None
                }
            })
            .collect()
    }

    // Parse DS records from DNS records
    pub fn parse_ds_records(&self, records: &[DnsRecord]) -> Vec<DsRecord> {
        records
            .iter()
            .filter(|r| r.record_type == "DS")
            .filter_map(|r| {
                // DS format: key_tag algorithm digest_type digest
                let parts: Vec<&str> = r.value.split_whitespace().collect();
                if parts.len() >= 4 {
                    let key_tag = parts[0].parse::<u16>().ok()?;
                    let algorithm = parts[1].parse::<u8>().ok()?;
                    let digest_type = parts[2].parse::<u8>().ok()?;
                    let digest = parts[3..].join("");

                    Some(DsRecord {
                        key_tag,
                        algorithm,
                        digest_type,
                        digest,
                    })
                } else {
                    None
                }
            })
            .collect()
    }

    // Parse RRSIG records from DNS records
    pub fn parse_rrsig_records(&self, records: &[DnsRecord]) -> Vec<RrsigRecord> {
        records
            .iter()
            .filter(|r| r.record_type == "RRSIG")
            .filter_map(|r| {
                // RRSIG format: type_covered algorithm labels original_ttl expiration inception key_tag signer signature
                let parts: Vec<&str> = r.value.split_whitespace().collect();
                if parts.len() >= 9 {
                    Some(RrsigRecord {
                        type_covered: parts[0].to_string(),
                        algorithm: parts[1].parse::<u8>().ok()?,
                        labels: parts[2].parse::<u8>().ok()?,
                        original_ttl: parts[3].parse::<u32>().ok()?,
                        signature_expiration: parts[4].to_string(),
                        signature_inception: parts[5].to_string(),
                        key_tag: parts[6].parse::<u16>().ok()?,
                        signer_name: parts[7].to_string(),
                        signature: parts[8..].join(" "),
                    })
                } else {
                    None
                }
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_dns_query() {
        let adapter = DnsAdapter::new();
        let result = adapter.query("example.com", "A").await;
        assert!(result.is_ok());
    }
}
