use crate::adapters::certificate::CertificateAdapter;
use crate::models::certificate::TlsInfo;

#[tauri::command]
pub async fn get_certificate(host: String, port: Option<u16>) -> Result<TlsInfo, String> {
    let adapter = CertificateAdapter::new();
    let port = port.unwrap_or(443);
    adapter.get_certificate_info(&host, port).await
}
