use crate::models::command_log::CommandLog;
use crate::models::http::{HttpRedirect, HttpResponse};
use std::collections::HashMap;
use std::process::Command;
use std::time::Instant;
use tauri::{AppHandle, Emitter};

pub struct HttpAdapter {
    app_handle: Option<AppHandle>,
}

impl HttpAdapter {
    pub fn new() -> Self {
        HttpAdapter { app_handle: None }
    }

    pub fn with_app_handle(app_handle: AppHandle) -> Self {
        HttpAdapter {
            app_handle: Some(app_handle),
        }
    }

    fn emit_log(&self, log: CommandLog) {
        if let Some(handle) = &self.app_handle {
            let _ = handle.emit("command-log", log);
        }
    }

    pub async fn fetch(&self, url: &str) -> Result<HttpResponse, String> {
        let start = Instant::now();
        if !self.is_curl_available() {
            return Err("curl command not found. Please install curl.".to_string());
        }

        let args = vec![
            "-L".to_string(),
            "-I".to_string(),
            "-s".to_string(),
            "-S".to_string(),
            "-w".to_string(),
            "\\n__STATUS_CODE__:%{http_code}\\n__FINAL_URL__:%{url_effective}\\n__TIME__:%{time_total}".to_string(),
            url.to_string(),
        ];

        let output = Command::new("curl")
            .arg("-L") // Follow redirects
            .arg("-I") // Head request
            .arg("-s") // Silent
            .arg("-S") // Show errors
            .arg("-w")
            .arg("\\n__STATUS_CODE__:%{http_code}\\n__FINAL_URL__:%{url_effective}\\n__TIME__:%{time_total}")
            .arg(url)
            .output()
            .map_err(|e| format!("Failed to execute curl: {}", e))?;

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

        // Extract domain from URL for logging
        let domain = url
            .trim_start_matches("http://")
            .trim_start_matches("https://")
            .split('/')
            .next()
            .unwrap_or(url);

        self.emit_log(CommandLog::new(
            "curl".to_string(),
            args,
            log_output,
            exit_code,
            query_time * 1000.0, // Convert to milliseconds
            Some(domain.to_string()),
        ));

        if !output.status.success() {
            return Err(format!("curl command failed: {}", stderr));
        }

        self.parse_curl_output(&stdout, url, query_time)
    }

    fn parse_curl_output(
        &self,
        output: &str,
        original_url: &str,
        response_time: f64,
    ) -> Result<HttpResponse, String> {
        let mut status_code = 0;
        let mut final_url = original_url.to_string();
        let mut headers = HashMap::new();
        let mut redirects = Vec::new();

        // Extract status code and final URL from footer
        for line in output.lines() {
            if line.starts_with("__STATUS_CODE__:") {
                if let Some(code) = line.split(':').nth(1) {
                    status_code = code.trim().parse().unwrap_or(0);
                }
            } else if line.starts_with("__FINAL_URL__:") {
                if let Some(url) = line.split(':').nth(1) {
                    final_url = url.trim().to_string();
                }
            }
        }

        // Parse headers from HTTP response blocks
        let http_blocks: Vec<&str> = output.split("HTTP/").collect();

        for (i, block) in http_blocks.iter().enumerate() {
            if block.is_empty() {
                continue;
            }

            let lines: Vec<&str> = block.lines().collect();
            if lines.is_empty() {
                continue;
            }

            // Extract status from first line
            let first_line = lines[0];
            if let Some(status_str) = first_line.split_whitespace().nth(0) {
                if let Ok(code) = status_str.parse::<u16>() {
                    // Track redirects (3xx codes)
                    if code >= 300 && code < 400 && i < http_blocks.len() - 1 {
                        redirects.push(HttpRedirect {
                            from_url: original_url.to_string(),
                            to_url: final_url.clone(),
                            status_code: code,
                        });
                    }
                }
            }

            // Parse headers from last block only
            if i == http_blocks.len() - 1 {
                for line in &lines[1..] {
                    if let Some(colon_pos) = line.find(':') {
                        let key = line[..colon_pos].trim().to_string();
                        let value = line[colon_pos + 1..].trim().to_string();
                        headers.insert(key, value);
                    }
                }
            }
        }

        Ok(HttpResponse {
            url: original_url.to_string(),
            status_code,
            final_url,
            redirects,
            headers,
            response_time,
            raw_output: Some(output.to_string()),
        })
    }

    fn is_curl_available(&self) -> bool {
        Command::new("curl").arg("--version").output().is_ok()
    }
}
