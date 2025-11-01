use crate::adapters::whois::WhoisAdapter;
use crate::models::whois::WhoisInfo;

#[tauri::command]
pub async fn lookup_whois(domain: String) -> Result<WhoisInfo, String> {
    let adapter = WhoisAdapter::new();
    adapter.lookup(&domain).await
}
