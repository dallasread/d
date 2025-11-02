// Module declarations
pub mod adapters;
pub mod commands;
pub mod models;

// Re-export commands
use commands::certificate::get_certificate;
use commands::dns::{query_dns, query_dns_multiple};
use commands::dnssec::validate_dnssec;
use commands::email::fetch_email_config;
use commands::http::fetch_http;
use commands::whois::lookup_whois;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            query_dns,
            query_dns_multiple,
            validate_dnssec,
            get_certificate,
            lookup_whois,
            fetch_http,
            fetch_email_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
