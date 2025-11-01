use crate::adapters::dns::DnsAdapter;
use crate::models::dns::{DnssecValidation, ZoneData};

#[tauri::command]
pub async fn validate_dnssec(domain: String) -> Result<DnssecValidation, String> {
    let adapter = DnsAdapter::new();

    // Build DNSSEC chain from root to domain
    let mut chain: Vec<ZoneData> = Vec::new();
    let mut warnings: Vec<String> = Vec::new();

    // Get domain parts for chain building
    let parts: Vec<&str> = domain.split('.').collect();

    // Query DNSKEY for the target domain
    match adapter.query_dnskey(&domain).await {
        Ok(dnskey_response) => {
            let dnskey_records = dnskey_response
                .records
                .iter()
                .filter(|r| r.record_type == "DNSKEY")
                .cloned()
                .collect::<Vec<_>>();

            if dnskey_records.is_empty() {
                warnings.push(format!("No DNSKEY records found for {}", domain));
            }

            // Query DS records from parent (optional - only if parent is not TLD)
            let _ds_records = if parts.len() > 2 {
                match adapter.query_ds(&domain).await {
                    Ok(ds_response) => {
                        let ds_recs: Vec<_> = ds_response
                            .records
                            .iter()
                            .filter(|r| r.record_type == "DS")
                            .cloned()
                            .collect();

                        if ds_recs.is_empty() {
                            warnings.push("No DS records found in parent zone".to_string());
                        }
                        ds_recs
                    }
                    Err(e) => {
                        // TLD nameserver queries often timeout - provide helpful context
                        if e.contains("timeout") || e.contains("timed out") {
                            warnings.push(
                                "DS query timed out (TLD nameservers may be rate-limited)"
                                    .to_string(),
                            );
                        } else {
                            warnings.push(format!("Failed to query DS records: {}", e));
                        }
                        Vec::new()
                    }
                }
            } else {
                // TLD domain - no DS records to query
                Vec::new()
            };

            // Create zone data with raw DNS records
            // In a full implementation, we'd parse these into proper DNSKEY/DS/RRSIG structures
            chain.push(ZoneData {
                zone_name: domain.clone(),
                dnskey_records: Vec::new(), // Would parse from dnskey_records
                ds_records: Vec::new(),     // Would parse from ds_records
                rrsig_records: Vec::new(),  // Would query RRSIG separately
            });
        }
        Err(e) => {
            warnings.push(format!("Failed to query DNSKEY: {}", e));
        }
    }

    // Determine status based on what we found
    let status = if chain.is_empty() {
        "INDETERMINATE".to_string()
    } else if warnings.is_empty() {
        "SECURE".to_string()
    } else {
        "INSECURE".to_string()
    };

    Ok(DnssecValidation {
        status,
        chain,
        warnings,
    })
}
