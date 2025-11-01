use crate::adapters::dns::DnsAdapter;
use crate::models::dns::{DnssecValidation, ZoneData};
use std::collections::HashSet;

#[tauri::command]
pub async fn validate_dnssec(domain: String) -> Result<DnssecValidation, String> {
    let adapter = DnsAdapter::new();
    let mut chain: Vec<ZoneData> = Vec::new();
    let mut warnings: Vec<String> = Vec::new();

    // Parse domain parts (e.g., "www.example.com" -> ["www", "example", "com"])
    let parts: Vec<&str> = domain.trim_end_matches('.').split('.').collect();

    // Build full chain: root → TLD → domain → subdomain(s)
    // For meat.io: root → io → meat.io
    // For www.example.com: root → com → example.com → www.example.com

    // Step 1: Query root zone (.)
    match adapter.query_dnskey(".").await {
        Ok(root_response) => {
            let root_dnskeys = adapter.parse_dnskey_records(&root_response.records);
            let root_rrsigs = adapter.parse_rrsig_records(&root_response.records);

            // Query DS records for TLD from root
            let tld = parts.last().unwrap_or(&"");
            let root_ds = match adapter.query_ds(tld).await {
                Ok(ds_response) => adapter.parse_ds_records(&ds_response.records),
                Err(_) => Vec::new(),
            };

            chain.push(ZoneData {
                zone_name: ".".to_string(),
                dnskey_records: root_dnskeys,
                ds_records: root_ds,
                rrsig_records: root_rrsigs,
            });
        }
        Err(e) => {
            warnings.push(format!("Failed to query root zone: {}", e));
        }
    }

    // Step 2: Build chain from TLD down to target domain recursively
    // For "meat.io": query ["io", "meat.io"]
    // For "www.example.com": query ["com", "example.com", "www.example.com"]
    for i in (0..parts.len()).rev() {
        let current_zone = parts[i..].join(".");
        let child_zone = if i > 0 {
            Some(parts[i - 1..].join("."))
        } else {
            None
        };

        match adapter.query_dnskey(&current_zone).await {
            Ok(zone_response) => {
                let zone_dnskeys = adapter.parse_dnskey_records(&zone_response.records);
                let zone_rrsigs = adapter.parse_rrsig_records(&zone_response.records);

                // Query DS records for child zone (if exists)
                let zone_ds = if let Some(ref child) = child_zone {
                    match adapter.query_ds(child).await {
                        Ok(ds_response) => adapter.parse_ds_records(&ds_response.records),
                        Err(e) => {
                            if e.contains("timeout") || e.contains("timed out") {
                                warnings.push(format!(
                                    "DS query timed out for {} (TLD nameservers may be rate-limited)",
                                    child
                                ));
                            }
                            Vec::new()
                        }
                    }
                } else {
                    Vec::new()
                };

                if zone_dnskeys.is_empty() && current_zone == domain {
                    warnings.push(format!("No DNSKEY records found for {}", domain));
                }

                if !zone_ds.is_empty() || !zone_dnskeys.is_empty() || !zone_rrsigs.is_empty() {
                    chain.push(ZoneData {
                        zone_name: current_zone.clone(),
                        dnskey_records: zone_dnskeys,
                        ds_records: zone_ds,
                        rrsig_records: zone_rrsigs,
                    });
                }
            }
            Err(e) => {
                if current_zone == domain {
                    warnings.push(format!("Failed to query DNSKEY for {}: {}", domain, e));
                }
            }
        }
    }

    // Determine validation status
    let target_zone = chain.iter().find(|z| z.zone_name == domain);
    let has_dnskey = target_zone
        .map(|z| !z.dnskey_records.is_empty())
        .unwrap_or(false);

    // Check if target domain has DS record in parent zone
    let parent_zone = if parts.len() > 1 {
        let parent_name = parts[1..].join(".");
        chain.iter().find(|z| z.zone_name == parent_name)
    } else {
        None
    };
    let has_ds = parent_zone
        .map(|z| !z.ds_records.is_empty())
        .unwrap_or(false);

    let status = if !has_dnskey {
        "INSECURE".to_string()
    } else if has_dnskey && has_ds {
        // Check if DS records match DNSKEY key tags
        if let (Some(target), Some(parent)) = (target_zone, parent_zone) {
            let ds_keytags: HashSet<u16> = parent.ds_records.iter().map(|ds| ds.key_tag).collect();
            let dnskey_keytags: HashSet<u16> = target
                .dnskey_records
                .iter()
                .map(|key| key.key_tag)
                .collect();

            if ds_keytags.iter().any(|tag| dnskey_keytags.contains(tag)) {
                "SECURE".to_string()
            } else {
                warnings.push(format!(
                    "DS key tags {:?} don't match DNSKEY tags {:?}",
                    ds_keytags, dnskey_keytags
                ));
                "BOGUS".to_string()
            }
        } else {
            "SECURE".to_string()
        }
    } else if has_dnskey && !has_ds {
        warnings.push("Domain has DNSKEY but no DS record in parent zone".to_string());
        "INSECURE".to_string()
    } else {
        "INDETERMINATE".to_string()
    };

    Ok(DnssecValidation {
        status,
        chain,
        warnings,
    })
}
