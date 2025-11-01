use crate::adapters::http::HttpAdapter;
use crate::models::http::HttpResponse;
use tauri::AppHandle;

#[tauri::command]
pub async fn fetch_http(app_handle: AppHandle, url: String) -> Result<HttpResponse, String> {
    let adapter = HttpAdapter::with_app_handle(app_handle);
    adapter.fetch(&url).await
}
