use crate::adapters::email::{EmailAdapter, EmailConfig};
use tauri::AppHandle;

#[tauri::command]
pub async fn fetch_email_config(
    app_handle: AppHandle,
    domain: String,
    existing_mx_records: Option<Vec<String>>,
    existing_txt_records: Option<Vec<String>>,
) -> Result<EmailConfig, String> {
    let adapter = EmailAdapter::with_app_handle(app_handle);

    // Use existing MX records if provided, otherwise query
    let mx_future = async {
        if let Some(existing) = existing_mx_records {
            adapter.parse_mx_records(&domain, &existing)
        } else {
            adapter.query_mx(&domain).await
        }
    };

    // For SPF, DKIM, and DMARC, use existing TXT records if provided
    let spf_future = async {
        if let Some(ref txt_records) = existing_txt_records {
            adapter.parse_spf_from_txt(&domain, txt_records)
        } else {
            adapter.query_spf(&domain).await
        }
    };

    // DKIM and DMARC need to be queried (DKIM uses selectors, DMARC uses _dmarc subdomain)
    let dkim_future = adapter.query_dkim(&domain);
    let dmarc_future = adapter.query_dmarc(&domain);

    let (mx_result, spf_result, dkim_result, dmarc_result) =
        tokio::join!(mx_future, spf_future, dkim_future, dmarc_future);

    let mx_records = mx_result.unwrap_or_else(|_| Vec::new());
    let spf_record = spf_result.ok().flatten();
    let dkim_records = dkim_result.unwrap_or_else(|_| Vec::new());
    let dmarc_record = dmarc_result.ok().flatten();

    // Calculate security score based on what's configured
    let security_score =
        calculate_security_score(&mx_records, &spf_record, &dkim_records, &dmarc_record);

    Ok(EmailConfig {
        mx_records,
        spf_record,
        dkim_records,
        dmarc_record,
        security_score,
    })
}

fn calculate_security_score(
    mx_records: &[crate::adapters::email::MxRecord],
    spf_record: &Option<crate::adapters::email::SpfRecord>,
    dkim_records: &[crate::adapters::email::DkimRecord],
    dmarc_record: &Option<crate::adapters::email::DmarcRecord>,
) -> u8 {
    let mut score = 0u8;

    // MX records configured (20 points)
    if !mx_records.is_empty() {
        score += 20;
    }

    // SPF configured (30 points)
    if let Some(spf) = spf_record {
        if spf.is_valid {
            score += 30;
            // Bonus for strict policy
            if spf.policy == "fail" {
                score += 5;
            }
        }
    }

    // DKIM configured (25 points)
    if !dkim_records.is_empty() {
        score += 25;
    }

    // DMARC configured (25 points)
    if let Some(dmarc) = dmarc_record {
        if dmarc.is_valid {
            score += 20;
            // Bonus for enforcement policy
            match dmarc.policy.as_str() {
                "reject" => score += 10,
                "quarantine" => score += 5,
                _ => {}
            }
        }
    }

    score.min(100)
}
