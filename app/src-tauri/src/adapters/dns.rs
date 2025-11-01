use crate::models::dns::{DnsRecord, DnsResponse};
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

    // Query authoritative nameservers directly
    pub async fn query_authoritative(
        &self,
        domain: &str,
        record_type: &str,
        nameserver: Option<&str>,
    ) -> Result<DnsResponse, String> {
        let start = Instant::now();

        if !self.is_dig_available() {
            return Err("dig command not found. Please install BIND tools.".to_string());
        }

        let mut cmd = Command::new("dig");
        cmd.arg("+noall").arg("+answer").arg("+dnssec"); // Request DNSSEC records

        // If nameserver specified, query it directly
        if let Some(ns) = nameserver {
            cmd.arg(format!("@{}", ns));
        }

        cmd.arg(record_type).arg(domain);

        let output = cmd
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
            resolver: nameserver.unwrap_or("system").to_string(),
            raw_output: Some(stdout.to_string()),
        })
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
