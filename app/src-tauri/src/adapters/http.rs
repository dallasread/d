use crate::models::http::{HttpResponse, HttpRedirect};
use std::process::Command;
use std::collections::HashMap;
use std::time::Instant;

pub struct HttpAdapter;

impl HttpAdapter {
    pub fn new() -> Self {
        HttpAdapter
    }

    pub async fn fetch(&self, url: &str) -> Result<HttpResponse, String> {
        if !self.is_curl_available() {
            return Err("curl command not found. Please install curl.".to_string());
        }

        let start = Instant::now();

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

        let response_time = start.elapsed().as_secs_f64();

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("curl command failed: {}", stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        self.parse_curl_output(&stdout, url, response_time)
    }

    fn parse_curl_output(&self, output: &str, original_url: &str, response_time: f64) -> Result<HttpResponse, String> {
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
        Command::new("curl")
            .arg("--version")
            .output()
            .is_ok()
    }
}
