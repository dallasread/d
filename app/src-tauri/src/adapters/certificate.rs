use crate::models::certificate::{CertificateInfo, CertificateSubject, CertificateChain, TlsInfo};
use std::process::Command;
use regex::Regex;

pub struct CertificateAdapter;

impl CertificateAdapter {
    pub fn new() -> Self {
        CertificateAdapter
    }

    pub async fn get_certificate_info(&self, host: &str, port: u16) -> Result<TlsInfo, String> {
        if !self.is_openssl_available() {
            return Err("openssl command not found. Please install OpenSSL.".to_string());
        }

        // Get certificate chain using openssl s_client
        let output = Command::new("sh")
            .arg("-c")
            .arg(format!(
                "echo Q | openssl s_client -connect {}:{} -showcerts 2>/dev/null",
                host, port
            ))
            .output()
            .map_err(|e| format!("Failed to execute openssl: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let certificates = self.parse_certificate_chain(&stdout)?;

        Ok(TlsInfo {
            host: host.to_string(),
            port,
            certificate_chain: CertificateChain {
                certificates,
                is_valid: true,
                validation_errors: vec![],
            },
            raw_output: Some(stdout.to_string()),
        })
    }

    fn parse_certificate_chain(&self, output: &str) -> Result<Vec<CertificateInfo>, String> {
        let mut certificates = Vec::new();

        // Extract PEM certificates
        let cert_regex = Regex::new(r"-----BEGIN CERTIFICATE-----\n(.*?)\n-----END CERTIFICATE-----")
            .unwrap();

        for cap in cert_regex.captures_iter(output) {
            let pem = format!("-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----", &cap[1]);

            if let Ok(cert_info) = self.parse_single_certificate(&pem) {
                certificates.push(cert_info);
            }
        }

        if certificates.is_empty() {
            return Err("No certificates found in chain".to_string());
        }

        Ok(certificates)
    }

    fn parse_single_certificate(&self, pem: &str) -> Result<CertificateInfo, String> {
        // Save PEM to temp file and parse with openssl
        let output = Command::new("sh")
            .arg("-c")
            .arg(format!("echo '{}' | openssl x509 -text -noout", pem))
            .output()
            .map_err(|e| format!("Failed to parse certificate: {}", e))?;

        let text = String::from_utf8_lossy(&output.stdout);

        // Parse certificate fields
        let subject = self.parse_subject(&text, "Subject:");
        let issuer = self.parse_subject(&text, "Issuer:");
        let serial = self.extract_field(&text, "Serial Number:");
        let not_before = self.extract_field(&text, "Not Before:");
        let not_after = self.extract_field(&text, "Not After:");

        Ok(CertificateInfo {
            subject,
            issuer,
            serial_number: serial.unwrap_or_default(),
            version: 3,
            not_before: not_before.unwrap_or_default(),
            not_after: not_after.unwrap_or_default(),
            subject_alternative_names: vec![],
            public_key_algorithm: "RSA".to_string(),
            public_key_size: Some(2048),
            signature_algorithm: "SHA256withRSA".to_string(),
            fingerprint_sha256: String::new(),
        })
    }

    fn parse_subject(&self, text: &str, prefix: &str) -> CertificateSubject {
        if let Some(line) = text.lines().find(|l| l.contains(prefix)) {
            let parts: Vec<&str> = line.split(prefix).collect();
            if parts.len() > 1 {
                return self.parse_subject_fields(parts[1]);
            }
        }

        CertificateSubject {
            common_name: None,
            organization: None,
            organizational_unit: None,
            locality: None,
            state: None,
            country: None,
        }
    }

    fn parse_subject_fields(&self, subject_str: &str) -> CertificateSubject {
        let mut subject = CertificateSubject {
            common_name: None,
            organization: None,
            organizational_unit: None,
            locality: None,
            state: None,
            country: None,
        };

        for part in subject_str.split(',') {
            let kv: Vec<&str> = part.trim().splitn(2, '=').collect();
            if kv.len() == 2 {
                let key = kv[0].trim();
                let value = kv[1].trim().to_string();

                match key {
                    "CN" => subject.common_name = Some(value),
                    "O" => subject.organization = Some(value),
                    "OU" => subject.organizational_unit = Some(value),
                    "L" => subject.locality = Some(value),
                    "ST" => subject.state = Some(value),
                    "C" => subject.country = Some(value),
                    _ => {}
                }
            }
        }

        subject
    }

    fn extract_field(&self, text: &str, field: &str) -> Option<String> {
        text.lines()
            .find(|l| l.contains(field))
            .and_then(|l| l.split(':').nth(1))
            .map(|s| s.trim().to_string())
    }

    fn is_openssl_available(&self) -> bool {
        Command::new("openssl")
            .arg("version")
            .output()
            .is_ok()
    }
}
