use crate::adapters::dns::DnsAdapter;
use crate::models::dns::DnsResponse;
use tauri::AppHandle;

#[tauri::command]
pub async fn query_dns(
    app_handle: AppHandle,
    domain: String,
    record_type: String,
) -> Result<DnsResponse, String> {
    let adapter = DnsAdapter::with_app_handle(app_handle);
    adapter.query(&domain, &record_type).await
}

#[tauri::command]
pub async fn query_dns_multiple(
    app_handle: AppHandle,
    domain: String,
    record_types: Vec<String>,
) -> Result<Vec<DnsResponse>, String> {
    let adapter = DnsAdapter::with_app_handle(app_handle);
    let types: Vec<&str> = record_types.iter().map(|s| s.as_str()).collect();
    adapter.query_multiple(&domain, types).await
}
