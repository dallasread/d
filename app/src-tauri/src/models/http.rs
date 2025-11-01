use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpResponse {
    pub url: String,
    pub status_code: u16,
    pub final_url: String,
    pub redirects: Vec<HttpRedirect>,
    pub headers: HashMap<String, String>,
    pub response_time: f64,
    pub raw_output: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpRedirect {
    pub from_url: String,
    pub to_url: String,
    pub status_code: u16,
}
