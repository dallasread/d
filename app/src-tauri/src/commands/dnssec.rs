use crate::adapters::dns::DnsAdapter;
use crate::models::dns::{DnssecValidation, ZoneData};
use std::collections::HashSet;

#[tauri::command]
pub async fn validate_dnssec(domain: String) -> Result<DnssecValidation, String> {
    let adapter = DnsAdapter::new();
    let mut chain: Vec<ZoneData> = Vec::new();
    let mut warnings: Vec<String> = Vec::new();

    // Parse domain parts
    let parts: Vec<&str> = domain.trim_end_matches('.').split('.').collect();

    // Only query TLD and target domain (skip root - too slow)
    // Start from TLD (e.g., "io" for "meat.io")
    let zones_to_query: Vec<String> = if parts.len() >= 2 {
        vec![
            parts[parts.len() - 1..].join("."), // TLD (e.g., "io")
            domain.clone(),                     // Target domain (e.g., "meat.io")
        ]
    } else {
        vec![domain.clone()]
    };

    for current_zone in zones_to_query {
        // Query DNSKEY for this zone
        match adapter.query_dnskey(&current_zone).await {
            Ok(zone_response) => {
                let zone_dnskeys = adapter.parse_dnskey_records(&zone_response.records);
                let zone_rrsigs = adapter.parse_rrsig_records(&zone_response.records);

                // For TLD: query DS records for the target domain
                // For target: we already have its DNSKEY
                let zone_ds = if current_zone != domain && parts.len() >= 2 {
                    // This is the TLD, query DS for target domain
                    match adapter.query_ds(&domain).await {
                        Ok(ds_response) => adapter.parse_ds_records(&ds_response.records),
                        Err(e) => {
                            if e.contains("timeout") || e.contains("timed out") {
                                warnings.push(format!(
                                    "DS query timed out (TLD nameservers may be rate-limited)"
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

    // Check if target domain has DS record in parent (TLD)
    let tld_zone = if parts.len() >= 2 {
        chain.iter().find(|z| z.zone_name == parts[parts.len() - 1])
    } else {
        None
    };
    let has_ds = tld_zone.map(|z| !z.ds_records.is_empty()).unwrap_or(false);

    let status = if !has_dnskey {
        "INSECURE".to_string()
    } else if has_dnskey && has_ds {
        // Check if DS records match DNSKEY key tags
        if let (Some(target), Some(tld)) = (target_zone, tld_zone) {
            let ds_keytags: HashSet<u16> = tld.ds_records.iter().map(|ds| ds.key_tag).collect();
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
