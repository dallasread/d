use crate::adapters::certificate::CertificateAdapter;
use crate::models::certificate::TlsInfo;
use tauri::AppHandle;

#[tauri::command]
pub async fn get_certificate(
    app_handle: AppHandle,
    host: String,
    port: Option<u16>,
) -> Result<TlsInfo, String> {
    let adapter = CertificateAdapter::with_app_handle(app_handle);
    let port = port.unwrap_or(443);
    adapter.get_certificate_info(&host, port).await
}
