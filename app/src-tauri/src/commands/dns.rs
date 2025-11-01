use crate::adapters::dns::DnsAdapter;
use crate::models::dns::DnsResponse;

#[tauri::command]
pub async fn query_dns(domain: String, record_type: String) -> Result<DnsResponse, String> {
    let adapter = DnsAdapter::new();
    adapter.query(&domain, &record_type).await
}

#[tauri::command]
pub async fn query_dns_multiple(domain: String, record_types: Vec<String>) -> Result<Vec<DnsResponse>, String> {
    let adapter = DnsAdapter::new();
    let types: Vec<&str> = record_types.iter().map(|s| s.as_str()).collect();
    adapter.query_multiple(&domain, types).await
}
