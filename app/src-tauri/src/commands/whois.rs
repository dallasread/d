use crate::adapters::whois::WhoisAdapter;
use crate::models::whois::WhoisInfo;
use tauri::AppHandle;

#[tauri::command]
pub async fn lookup_whois(app_handle: AppHandle, domain: String) -> Result<WhoisInfo, String> {
    let adapter = WhoisAdapter::with_app_handle(app_handle);
    adapter.lookup(&domain).await
}
