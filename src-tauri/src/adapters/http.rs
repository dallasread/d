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
        if !self.is_curl_available() {
            return Err("curl command not found. Please install curl.".to_string());
        }

        let mut redirects = Vec::new();
        let mut current_url = url.to_string();
        let mut total_time = 0.0;
        let max_redirects = 20;
        let mut redirect_count = 0;

        loop {
            if redirect_count >= max_redirects {
                return Err(format!("Too many redirects (max: {})", max_redirects));
            }

            let hop_start = Instant::now();

            let args = vec![
                "-I".to_string(),
                "-s".to_string(),
                "-S".to_string(),
                current_url.clone(),
            ];

            let output = Command::new("curl")
                .arg("-I") // Head request only
                .arg("-s") // Silent
                .arg("-S") // Show errors
                .arg(&current_url)
                .output()
                .map_err(|e| format!("Failed to execute curl: {}", e))?;

            let hop_time = hop_start.elapsed().as_secs_f64();
            total_time += hop_time;

            let exit_code = output.status.code().unwrap_or(-1);
            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();

            // Emit command log for this hop
            let log_output = if !stdout.is_empty() {
                stdout.clone()
            } else {
                stderr.clone()
            };

            let domain = current_url
                .trim_start_matches("http://")
                .trim_start_matches("https://")
                .split('/')
                .next()
                .unwrap_or(&current_url);

            self.emit_log(CommandLog::new(
                "curl".to_string(),
                args,
                log_output,
                exit_code,
                hop_time * 1000.0,
                Some(domain.to_string()),
            ));

            // Check for HTTP response
            let has_http_response = stdout.contains("HTTP/");
            if !output.status.success() && !has_http_response {
                return Err(format!("curl command failed: {}", stderr));
            }

            // Parse response
            let (status_code, headers) = self.parse_response_headers(&stdout)?;

            // Check if this is a redirect
            if status_code >= 300 && status_code < 400 {
                if let Some(location) = headers.get("location") {
                    let next_url =
                        if location.starts_with("http://") || location.starts_with("https://") {
                            location.clone()
                        } else if location.starts_with("/") {
                            // Relative URL - construct absolute URL
                            let base = if current_url.starts_with("https://") {
                                let rest = current_url.trim_start_matches("https://");
                                let domain = rest.split('/').next().unwrap_or("");
                                format!("https://{}", domain)
                            } else {
                                let rest = current_url.trim_start_matches("http://");
                                let domain = rest.split('/').next().unwrap_or("");
                                format!("http://{}", domain)
                            };
                            format!("{}{}", base, location)
                        } else {
                            // Relative to current path
                            let mut base = current_url
                                .rsplitn(2, '/')
                                .nth(1)
                                .unwrap_or(&current_url)
                                .to_string();
                            if !base.ends_with('/') {
                                base.push('/');
                            }
                            format!("{}{}", base, location)
                        };

                    redirects.push(HttpRedirect {
                        from_url: current_url.clone(),
                        to_url: next_url.clone(),
                        status_code,
                        response_time: hop_time,
                    });

                    current_url = next_url;
                    redirect_count += 1;
                } else {
                    // 3xx without Location header - treat as final response
                    return Ok(HttpResponse {
                        url: url.to_string(),
                        status_code,
                        final_url: current_url,
                        redirects,
                        headers,
                        response_time: total_time,
                        raw_output: Some(stdout),
                    });
                }
            } else {
                // Non-redirect response - we're done
                return Ok(HttpResponse {
                    url: url.to_string(),
                    status_code,
                    final_url: current_url,
                    redirects,
                    headers,
                    response_time: total_time,
                    raw_output: Some(stdout),
                });
            }
        }
    }

    fn parse_response_headers(
        &self,
        output: &str,
    ) -> Result<(u16, HashMap<String, String>), String> {
        let mut status_code = 0u16;
        let mut headers = HashMap::new();

        let lines: Vec<&str> = output.lines().collect();
        if lines.is_empty() {
            return Err("Empty response".to_string());
        }

        // Parse status line (e.g., "HTTP/1.1 200 OK" or "HTTP/2 301")
        let first_line = lines[0];
        let parts: Vec<&str> = first_line.split_whitespace().collect();
        for part in &parts {
            if let Ok(code) = part.parse::<u16>() {
                if code >= 100 && code < 600 {
                    status_code = code;
                    break;
                }
            }
        }

        // Parse headers
        for line in &lines[1..] {
            if line.is_empty() {
                break; // End of headers
            }
            if let Some(colon_pos) = line.find(':') {
                let key = line[..colon_pos].trim().to_lowercase();
                let value = line[colon_pos + 1..].trim().to_string();
                headers.insert(key, value);
            }
        }

        Ok((status_code, headers))
    }

    fn is_curl_available(&self) -> bool {
        Command::new("curl").arg("--version").output().is_ok()
    }
}
