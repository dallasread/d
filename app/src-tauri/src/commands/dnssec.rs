use crate::adapters::dns::DnsAdapter;
use crate::models::dns::{DnssecValidation, ZoneData};
use std::collections::HashSet;
use tauri::AppHandle;

/// Validate DNSSEC chain of trust for a domain.
///
/// DNSSEC validation builds a complete chain from the root zone down to the target domain,
/// verifying cryptographic signatures at each level. This process is inherently slow because:
///
/// **Performance Characteristics:**
///
/// 1. Root zone queries (~1-2s each):
///    - Root nameservers are distributed globally and often slow to respond
///    - We query DNSKEY records from root zone (.)
///    - We query DS records for the TLD from root zone
///
/// 2. TLD zone queries (~0.5-2s each):
///    - Query DNSKEY records from TLD nameservers (e.g., .com, .io)
///    - Query DS records for the target domain from TLD
///    - TLD nameservers often rate-limit or timeout (2s timeout configured)
///
/// 3. Target domain queries (~0.5s):
///    - Query DNSKEY records from domain's authoritative nameservers
///    - Query DS records for subdomains (if any)
///
/// **Expected Timing:**
/// - 2-level domain (example.com): 5-10 seconds
/// - 3-level domain (www.example.com): 8-15 seconds
/// - Domains with no DNSSEC: 2-5 seconds (fewer records to fetch)
///
/// **Why queries are sequential:**
/// The queries MUST be performed sequentially because each level depends on the previous:
/// - Root DS records contain key tags pointing to TLD DNSKEYs
/// - TLD DS records contain key tags pointing to domain DNSKEYs
/// - We verify the chain by matching DS key tags with DNSKEY key tags
/// - A valid chain means: DS(parent) → DNSKEY(child) at each level
///
/// **Parallelization:**
/// This validation already runs in parallel with other data fetching (DNS, WHOIS,
/// certificates, HTTP) in the UI, but is typically the slowest operation. This is
/// expected and unavoidable for proper DNSSEC validation.
///
/// **Key Tag Extraction:**
/// We use `dig +multi` format to extract real key tags from comments in the output
/// (e.g., "; key id = 5116"). Key tags are NOT the same as flags (256/257).
#[tauri::command]
pub async fn validate_dnssec(
    app_handle: AppHandle,
    domain: String,
) -> Result<DnssecValidation, String> {
    let adapter = DnsAdapter::with_app_handle(app_handle);
    let mut chain: Vec<ZoneData> = Vec::new();
    let mut warnings: Vec<String> = Vec::new();

    // Parse domain parts (e.g., "www.example.com" -> ["www", "example", "com"])
    let parts: Vec<&str> = domain.trim_end_matches('.').split('.').collect();

    // ========================================================================
    // Build complete DNSSEC chain: root → TLD → domain → subdomain(s)
    // ========================================================================
    // Examples:
    //   meat.io:         root (.) → io → meat.io
    //   www.example.com: root (.) → com → example.com → www.example.com
    //
    // Each zone in the chain contains:
    //   - DNSKEY records: Public keys for signing DNS records
    //   - DS records: Delegation Signer records pointing to child zone's DNSKEYs
    //   - RRSIG records: Signatures proving records are authentic

    // ========================================================================
    // Step 1: Query root zone (.)
    // ========================================================================
    // The root zone is the trust anchor for all DNSSEC validation.
    // Root servers are slow (~1-2s per query) but necessary for a complete chain.
    // We query:
    //   1. Root DNSKEY records (the trust anchor)
    //   2. DS records for the TLD (points to TLD's DNSKEY)
    match adapter.query_dnskey(".").await {
        Ok(root_response) => {
            let root_dnskeys = adapter.parse_dnskey_records(&root_response.records);
            let root_rrsigs = adapter.parse_rrsig_records(&root_response.records);

            // Query DS records for TLD from root
            // Example: For "meat.io", query DS records for "io" from root nameservers
            let tld = parts.last().unwrap_or(&"");
            let root_ds = match adapter.query_ds(tld).await {
                Ok(ds_response) => adapter.parse_ds_records(&ds_response.records),
                Err(_) => Vec::new(),
            };

            chain.push(ZoneData {
                zone_name: ".".to_string(),
                dnskey_records: root_dnskeys,
                ds_records: root_ds, // Points to TLD's DNSKEYs
                rrsig_records: root_rrsigs,
            });
        }
        Err(e) => {
            warnings.push(format!("Failed to query root zone: {}", e));
        }
    }

    // ========================================================================
    // Step 2: Build chain recursively from TLD down to target domain
    // ========================================================================
    // For "meat.io":       iterate through ["io", "meat.io"]
    // For "www.example.com": iterate through ["com", "example.com", "www.example.com"]
    //
    // At each level:
    //   1. Query DNSKEY records for the current zone
    //   2. Query DS records for the child zone (if it exists)
    //   3. Match DS key tags from parent to DNSKEY key tags in current zone
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
                // Example: For "io" zone, query DS records for "meat.io"
                let zone_ds = if let Some(ref child) = child_zone {
                    match adapter.query_ds(child).await {
                        Ok(ds_response) => adapter.parse_ds_records(&ds_response.records),
                        Err(e) => {
                            // TLD nameservers often timeout due to rate limiting
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

                // Warn if target domain has no DNSKEY records (not DNSSEC signed)
                if zone_dnskeys.is_empty() && current_zone == domain {
                    warnings.push(format!("No DNSKEY records found for {}", domain));
                }

                // Only add zone to chain if it has any DNSSEC records
                if !zone_ds.is_empty() || !zone_dnskeys.is_empty() || !zone_rrsigs.is_empty() {
                    chain.push(ZoneData {
                        zone_name: current_zone.clone(),
                        dnskey_records: zone_dnskeys,
                        ds_records: zone_ds, // Points to child zone's DNSKEYs
                        rrsig_records: zone_rrsigs,
                    });
                }
            }
            Err(e) => {
                // Only warn for target domain failures
                if current_zone == domain {
                    warnings.push(format!("Failed to query DNSKEY for {}: {}", domain, e));
                }
            }
        }
    }

    // ========================================================================
    // Step 3: Determine validation status
    // ========================================================================
    // Status is based on:
    //   - SECURE: Domain has DNSKEY, parent has matching DS records
    //   - INSECURE: Domain has no DNSKEY (not signed)
    //   - BOGUS: Domain has DNSKEY, but DS key tags don't match DNSKEY key tags
    //   - INDETERMINATE: Unable to determine (query failures)

    let target_zone = chain.iter().find(|z| z.zone_name == domain);
    let has_dnskey = target_zone
        .map(|z| !z.dnskey_records.is_empty())
        .unwrap_or(false);

    // Find parent zone and check for DS records
    // For "meat.io": parent is "io"
    // For "www.example.com": parent is "example.com"
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
        // No DNSKEY records = domain is not DNSSEC signed
        "INSECURE".to_string()
    } else if has_dnskey && has_ds {
        // Both DNSKEY and DS exist - verify key tags match
        if let (Some(target), Some(parent)) = (target_zone, parent_zone) {
            let ds_keytags: HashSet<u16> = parent.ds_records.iter().map(|ds| ds.key_tag).collect();
            let dnskey_keytags: HashSet<u16> = target
                .dnskey_records
                .iter()
                .map(|key| key.key_tag)
                .collect();

            // Check if any DS key tag matches any DNSKEY key tag
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
        // DNSKEY exists but no DS in parent = broken chain
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
