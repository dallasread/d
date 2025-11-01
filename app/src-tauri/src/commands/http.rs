use crate::adapters::http::HttpAdapter;
use crate::models::http::HttpResponse;

#[tauri::command]
pub async fn fetch_http(url: String) -> Result<HttpResponse, String> {
    let adapter = HttpAdapter::new();
    adapter.fetch(&url).await
}
