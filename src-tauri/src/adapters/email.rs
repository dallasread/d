use crate::models::command_log::CommandLog;
use regex::Regex;
use std::process::Command;
use std::time::Instant;
use tauri::{AppHandle, Emitter};

pub struct EmailAdapter {
    app_handle: Option<AppHandle>,
}

impl EmailAdapter {
    pub fn new() -> Self {
        EmailAdapter { app_handle: None }
    }

    pub fn with_app_handle(app_handle: AppHandle) -> Self {
        EmailAdapter {
            app_handle: Some(app_handle),
        }
    }

    fn emit_log(&self, log: CommandLog) {
        if let Some(handle) = &self.app_handle {
            let _ = handle.emit("command-log", log);
        }
    }

    fn is_dig_available(&self) -> bool {
        Command::new("dig").arg("-v").output().is_ok()
    }

    /// Query MX records for a domain
    pub async fn query_mx(&self, domain: &str) -> Result<Vec<MxRecord>, String> {
        let start = Instant::now();

        if !self.is_dig_available() {
            return Err("dig command not found".to_string());
        }

        let args = vec![domain.to_string(), "MX".to_string(), "+short".to_string()];

        let output = Command::new("dig")
            .arg(domain)
            .arg("MX")
            .arg("+short")
            .output()
            .map_err(|e| format!("Failed to execute dig: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();
        let exit_code = output.status.code().unwrap_or(-1);
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        let log_output = if !stdout.is_empty() {
            stdout.clone()
        } else {
            stderr.clone()
        };

        self.emit_log(CommandLog::new(
            "dig".to_string(),
            args,
            log_output,
            exit_code,
            query_time * 1000.0,
            Some(domain.to_string()),
        ));

        if !output.status.success() {
            return Err(format!("dig command failed: {}", stderr));
        }

        Ok(self.parse_mx_records_from_output(&stdout))
    }

    /// Parse MX records from existing DNS records (reuse existing queries)
    pub fn parse_mx_records(
        &self,
        domain: &str,
        existing_records: &[String],
    ) -> Result<Vec<MxRecord>, String> {
        let mut records = Vec::new();

        for record in existing_records {
            let parts: Vec<&str> = record.split_whitespace().collect();
            if parts.len() >= 2 {
                if let Ok(priority) = parts[0].parse::<u16>() {
                    let hostname = parts[1].trim_end_matches('.').to_string();
                    records.push(MxRecord {
                        priority,
                        hostname,
                        ips: Vec::new(),
                    });
                }
            }
        }

        Ok(records)
    }

    fn parse_mx_records_from_output(&self, output: &str) -> Vec<MxRecord> {
        let mut records = Vec::new();

        for line in output.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }

            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 {
                if let Ok(priority) = parts[0].parse::<u16>() {
                    let hostname = parts[1].trim_end_matches('.').to_string();
                    records.push(MxRecord {
                        priority,
                        hostname,
                        ips: Vec::new(), // Will be populated separately if needed
                    });
                }
            }
        }

        records
    }

    /// Query SPF record for a domain
    pub async fn query_spf(&self, domain: &str) -> Result<Option<SpfRecord>, String> {
        let start = Instant::now();

        if !self.is_dig_available() {
            return Err("dig command not found".to_string());
        }

        let args = vec![domain.to_string(), "TXT".to_string(), "+short".to_string()];

        let output = Command::new("dig")
            .arg(domain)
            .arg("TXT")
            .arg("+short")
            .output()
            .map_err(|e| format!("Failed to execute dig: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();
        let exit_code = output.status.code().unwrap_or(-1);
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        let log_output = if !stdout.is_empty() {
            stdout.clone()
        } else {
            stderr.clone()
        };

        self.emit_log(CommandLog::new(
            "dig".to_string(),
            args,
            log_output,
            exit_code,
            query_time * 1000.0,
            Some(domain.to_string()),
        ));

        if !output.status.success() {
            return Err(format!("dig command failed: {}", stderr));
        }

        Ok(self.parse_spf_record(&stdout))
    }

    /// Parse SPF record from existing TXT records (reuse existing queries)
    pub fn parse_spf_from_txt(
        &self,
        domain: &str,
        existing_txt_records: &[String],
    ) -> Result<Option<SpfRecord>, String> {
        for record in existing_txt_records {
            let line = record.trim().trim_matches('"');
            if line.starts_with("v=spf1") {
                let mechanisms = line.split_whitespace().count() - 1;
                let policy = if line.contains("~all") {
                    "softfail".to_string()
                } else if line.contains("-all") {
                    "fail".to_string()
                } else if line.contains("?all") {
                    "neutral".to_string()
                } else if line.contains("+all") {
                    "pass".to_string()
                } else {
                    "unknown".to_string()
                };

                return Ok(Some(SpfRecord {
                    record: line.to_string(),
                    policy,
                    mechanisms,
                    is_valid: true,
                }));
            }
        }
        Ok(None)
    }

    fn parse_spf_record(&self, output: &str) -> Option<SpfRecord> {
        for line in output.lines() {
            let line = line.trim().trim_matches('"');
            if line.starts_with("v=spf1") {
                let mechanisms = line.split_whitespace().count() - 1; // Subtract "v=spf1"
                let policy = if line.contains("~all") {
                    "softfail".to_string()
                } else if line.contains("-all") {
                    "fail".to_string()
                } else if line.contains("?all") {
                    "neutral".to_string()
                } else if line.contains("+all") {
                    "pass".to_string()
                } else {
                    "unknown".to_string()
                };

                return Some(SpfRecord {
                    record: line.to_string(),
                    policy,
                    mechanisms,
                    is_valid: true,
                });
            }
        }
        None
    }

    /// Query DKIM record for a domain with common selectors
    pub async fn query_dkim(&self, domain: &str) -> Result<Vec<DkimRecord>, String> {
        let common_selectors = vec![
            "default",
            "google",
            "k1",
            "s1",
            "s2",
            "selector1",
            "selector2",
            "dkim",
            "mail",
        ];

        let mut records = Vec::new();

        for selector in common_selectors {
            let dkim_domain = format!("{}._domainkey.{}", selector, domain);

            if let Ok(Some(record)) = self.query_dkim_selector(&dkim_domain, selector).await {
                records.push(record);
            }
        }

        Ok(records)
    }

    async fn query_dkim_selector(
        &self,
        dkim_domain: &str,
        selector: &str,
    ) -> Result<Option<DkimRecord>, String> {
        let start = Instant::now();

        if !self.is_dig_available() {
            return Err("dig command not found".to_string());
        }

        let args = vec![
            dkim_domain.to_string(),
            "TXT".to_string(),
            "+short".to_string(),
        ];

        let output = Command::new("dig")
            .arg(dkim_domain)
            .arg("TXT")
            .arg("+short")
            .output()
            .map_err(|e| format!("Failed to execute dig: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();
        let exit_code = output.status.code().unwrap_or(-1);
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();

        // Only log if we find a record
        if !stdout.trim().is_empty() {
            self.emit_log(CommandLog::new(
                "dig".to_string(),
                args,
                stdout.clone(),
                exit_code,
                query_time * 1000.0,
                Some(dkim_domain.to_string()),
            ));
        }

        if !output.status.success() || stdout.trim().is_empty() {
            return Ok(None);
        }

        Ok(self.parse_dkim_record(&stdout, selector))
    }

    fn parse_dkim_record(&self, output: &str, selector: &str) -> Option<DkimRecord> {
        let combined = output.lines().collect::<Vec<_>>().join("");
        let record = combined.trim().trim_matches('"');

        if record.contains("v=DKIM1") || record.contains("p=") {
            return Some(DkimRecord {
                selector: selector.to_string(),
                record: Some(record.to_string()),
                is_valid: true,
            });
        }

        None
    }

    /// Query DMARC record for a domain
    pub async fn query_dmarc(&self, domain: &str) -> Result<Option<DmarcRecord>, String> {
        let dmarc_domain = format!("_dmarc.{}", domain);
        let start = Instant::now();

        if !self.is_dig_available() {
            return Err("dig command not found".to_string());
        }

        let args = vec![
            dmarc_domain.clone(),
            "TXT".to_string(),
            "+short".to_string(),
        ];

        let output = Command::new("dig")
            .arg(&dmarc_domain)
            .arg("TXT")
            .arg("+short")
            .output()
            .map_err(|e| format!("Failed to execute dig: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();
        let exit_code = output.status.code().unwrap_or(-1);
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        let log_output = if !stdout.is_empty() {
            stdout.clone()
        } else {
            stderr.clone()
        };

        self.emit_log(CommandLog::new(
            "dig".to_string(),
            args,
            log_output,
            exit_code,
            query_time * 1000.0,
            Some(dmarc_domain),
        ));

        if !output.status.success() {
            return Err(format!("dig command failed: {}", stderr));
        }

        Ok(self.parse_dmarc_record(&stdout))
    }

    fn parse_dmarc_record(&self, output: &str) -> Option<DmarcRecord> {
        let combined = output.lines().collect::<Vec<_>>().join("");
        let record = combined.trim().trim_matches('"');

        if !record.starts_with("v=DMARC1") {
            return None;
        }

        let policy_re = Regex::new(r"p=([^;]+)").ok()?;
        let aspf_re = Regex::new(r"aspf=([^;]+)").ok()?;
        let adkim_re = Regex::new(r"adkim=([^;]+)").ok()?;
        let rua_re = Regex::new(r"rua=([^;]+)").ok()?;
        let ruf_re = Regex::new(r"ruf=([^;]+)").ok()?;

        let policy = policy_re
            .captures(record)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .unwrap_or_else(|| "none".to_string());

        let spf_alignment = aspf_re
            .captures(record)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .unwrap_or_else(|| "r".to_string());

        let dkim_alignment = adkim_re
            .captures(record)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .unwrap_or_else(|| "r".to_string());

        let aggregate_reports = rua_re
            .captures(record)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .unwrap_or_else(|| "".to_string());

        let forensic_reports = ruf_re
            .captures(record)
            .and_then(|c| c.get(1))
            .map(|m| m.as_str().to_string())
            .unwrap_or_else(|| "".to_string());

        Some(DmarcRecord {
            record: record.to_string(),
            policy,
            dkim_alignment,
            spf_alignment,
            aggregate_reports,
            forensic_reports,
            is_valid: true,
        })
    }
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct MxRecord {
    pub priority: u16,
    pub hostname: String,
    pub ips: Vec<String>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SpfRecord {
    pub record: String,
    pub policy: String,
    pub mechanisms: usize,
    pub is_valid: bool,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DkimRecord {
    pub selector: String,
    pub record: Option<String>,
    pub is_valid: bool,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DmarcRecord {
    pub record: String,
    pub policy: String,
    pub dkim_alignment: String,
    pub spf_alignment: String,
    pub aggregate_reports: String,
    pub forensic_reports: String,
    pub is_valid: bool,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EmailConfig {
    pub mx_records: Vec<MxRecord>,
    pub spf_record: Option<SpfRecord>,
    pub dkim_records: Vec<DkimRecord>,
    pub dmarc_record: Option<DmarcRecord>,
    pub security_score: u8,
}
