use crate::models::command_log::CommandLog;
use crate::models::whois::WhoisInfo;
use regex::Regex;
use std::process::Command;
use std::time::Instant;
use tauri::{AppHandle, Emitter};

pub struct WhoisAdapter {
    app_handle: Option<AppHandle>,
}

impl WhoisAdapter {
    pub fn new() -> Self {
        WhoisAdapter { app_handle: None }
    }

    pub fn with_app_handle(app_handle: AppHandle) -> Self {
        WhoisAdapter {
            app_handle: Some(app_handle),
        }
    }

    fn emit_log(&self, log: CommandLog) {
        if let Some(handle) = &self.app_handle {
            let _ = handle.emit("command-log", log);
        }
    }

    pub async fn lookup(&self, domain: &str) -> Result<WhoisInfo, String> {
        let start = Instant::now();
        if !self.is_whois_available() {
            return Err("whois command not found. Please install whois.".to_string());
        }

        // Determine the appropriate WHOIS server based on TLD
        let whois_server = self.get_whois_server(domain);

        let mut args = vec![];
        let mut cmd = Command::new("whois");

        if let Some(server) = whois_server {
            args.push("-h".to_string());
            args.push(server.clone());
            cmd.arg("-h").arg(server);
        }

        args.push(domain.to_string());
        cmd.arg(domain);

        let output = cmd
            .output()
            .map_err(|e| format!("Failed to execute whois: {}", e))?;

        let query_time = start.elapsed().as_secs_f64();
        let exit_code = output.status.code().unwrap_or(-1);

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        // Emit command log
        let log_output = if !stdout.is_empty() {
            stdout.clone()
        } else {
            stderr.clone()
        };

        self.emit_log(CommandLog::new(
            "whois".to_string(),
            args,
            log_output,
            exit_code,
            query_time * 1000.0, // Convert to milliseconds
            Some(domain.to_string()),
        ));

        if !output.status.success() {
            return Err(format!("whois command failed: {}", stderr));
        }

        let whois_info = self.parse_whois_output(&stdout, domain)?;

        Ok(whois_info)
    }

    fn parse_whois_output(&self, output: &str, domain: &str) -> Result<WhoisInfo, String> {
        let registrar = self.extract_field(output, &["Registrar:", "registrar:"]);
        let creation_date =
            self.extract_field(output, &["Creation Date:", "Created Date:", "created:"]);
        let expiration_date =
            self.extract_field(output, &["Expiration Date:", "Expiry Date:", "expires:"]);
        let updated_date =
            self.extract_field(output, &["Updated Date:", "Last Updated:", "last-update:"]);
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

    fn get_whois_server(&self, domain: &str) -> Option<String> {
        // Extract TLD from domain
        let tld = domain.split('.').last()?.to_lowercase();

        // Map common TLDs to their WHOIS servers
        let server = match tld.as_str() {
            "com" | "net" => "whois.verisign-grs.com",
            "org" => "whois.pir.org",
            "io" => "whois.nic.io",
            "uk" => "whois.nic.uk",
            "de" => "whois.denic.de",
            "fr" => "whois.nic.fr",
            "nl" => "whois.domain-registry.nl",
            "eu" => "whois.eu",
            "au" => "whois.auda.org.au",
            "ca" => "whois.cira.ca",
            "jp" => "whois.jprs.jp",
            "cn" => "whois.cnnic.cn",
            "in" => "whois.registry.in",
            "br" => "whois.registro.br",
            "mx" => "whois.mx",
            "ru" => "whois.tcinet.ru",
            "us" => "whois.nic.us",
            "info" => "whois.afilias.net",
            "biz" => "whois.biz",
            "me" => "whois.nic.me",
            "tv" => "whois.nic.tv",
            "cc" => "whois.nic.cc",
            "name" => "whois.nic.name",
            "co" => "whois.nic.co",
            "app" => "whois.nic.google",
            "dev" => "whois.nic.google",
            _ => return None, // Let whois command auto-detect for unknown TLDs
        };

        Some(server.to_string())
    }

    fn is_whois_available(&self) -> bool {
        Command::new("whois").arg("--version").output().is_ok()
    }
}
