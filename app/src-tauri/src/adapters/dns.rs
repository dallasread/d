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

    pub async fn query_multiple(&self, domain: &str, record_types: Vec<&str>) -> Result<Vec<DnsResponse>, String> {
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
        Command::new("dig")
            .arg("-v")
            .output()
            .is_ok()
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
