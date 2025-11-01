use crate::models::whois::WhoisInfo;
use std::process::Command;
use regex::Regex;

pub struct WhoisAdapter;

impl WhoisAdapter {
    pub fn new() -> Self {
        WhoisAdapter
    }

    pub async fn lookup(&self, domain: &str) -> Result<WhoisInfo, String> {
        if !self.is_whois_available() {
            return Err("whois command not found. Please install whois.".to_string());
        }

        let output = Command::new("whois")
            .arg(domain)
            .output()
            .map_err(|e| format!("Failed to execute whois: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("whois command failed: {}", stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let whois_info = self.parse_whois_output(&stdout, domain)?;

        Ok(whois_info)
    }

    fn parse_whois_output(&self, output: &str, domain: &str) -> Result<WhoisInfo, String> {
        let registrar = self.extract_field(output, &["Registrar:", "registrar:"]);
        let creation_date = self.extract_field(output, &["Creation Date:", "Created Date:", "created:"]);
        let expiration_date = self.extract_field(output, &["Expiration Date:", "Expiry Date:", "expires:"]);
        let updated_date = self.extract_field(output, &["Updated Date:", "Last Updated:", "last-update:"]);
        let dnssec = self.extract_field(output, &["DNSSEC:", "dnssec:"]);

        let nameservers = self.extract_nameservers(output);
        let status = self.extract_status(output);

        Ok(WhoisInfo {
            domain: domain.to_string(),
            registrar,
            creation_date,
            expiration_date,
            updated_date,
            nameservers,
            status,
            dnssec,
            raw_output: output.to_string(),
        })
    }

    fn extract_field(&self, text: &str, patterns: &[&str]) -> Option<String> {
        for pattern in patterns {
            if let Some(line) = text.lines().find(|l| l.contains(pattern)) {
                if let Some(value) = line.split(':').nth(1) {
                    return Some(value.trim().to_string());
                }
            }
        }
        None
    }

    fn extract_nameservers(&self, text: &str) -> Vec<String> {
        let ns_regex = Regex::new(r"(?i)name server:\s*(\S+)").unwrap();

        ns_regex
            .captures_iter(text)
            .filter_map(|cap| cap.get(1).map(|m| m.as_str().to_lowercase()))
            .collect()
    }

    fn extract_status(&self, text: &str) -> Vec<String> {
        let status_regex = Regex::new(r"(?i)(?:domain )?status:\s*(\S+)").unwrap();

        status_regex
            .captures_iter(text)
            .filter_map(|cap| cap.get(1).map(|m| m.as_str().to_string()))
            .collect()
    }

    fn is_whois_available(&self) -> bool {
        Command::new("whois")
            .arg("--version")
            .output()
            .is_ok()
    }
}
