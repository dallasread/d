#[cfg(test)]
mod tests {
    use super::super::dns::DnsAdapter;
    use crate::models::dns::{DnsRecord, DnsResponse};

    #[test]
    fn test_parse_dig_output_single_a_record() {
        let adapter = DnsAdapter::new();
        let output = "example.com.		3600	IN	A	93.184.216.34";

        let result = adapter.parse_dig_output(output, "A");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].name, "example.com.");
        assert_eq!(records[0].record_type, "A");
        assert_eq!(records[0].value, "93.184.216.34");
        assert_eq!(records[0].ttl, 3600);
    }

    #[test]
    fn test_parse_dig_output_multiple_a_records() {
        let adapter = DnsAdapter::new();
        let output = r#"example.com.		300	IN	A	93.184.216.34
example.com.		300	IN	A	93.184.216.35"#;

        let result = adapter.parse_dig_output(output, "A");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 2);
        assert_eq!(records[0].value, "93.184.216.34");
        assert_eq!(records[1].value, "93.184.216.35");
    }

    #[test]
    fn test_parse_dig_output_mx_records() {
        let adapter = DnsAdapter::new();
        let output = r#"example.com.		3600	IN	MX	10 mail.example.com.
example.com.		3600	IN	MX	20 mail2.example.com."#;

        let result = adapter.parse_dig_output(output, "MX");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 2);
        assert_eq!(records[0].value, "10 mail.example.com.");
        assert_eq!(records[1].value, "20 mail2.example.com.");
    }

    #[test]
    fn test_parse_dig_output_txt_records() {
        let adapter = DnsAdapter::new();
        let output = r#"example.com.		3600	IN	TXT	"v=spf1 include:_spf.example.com ~all""#;

        let result = adapter.parse_dig_output(output, "TXT");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 1);
        assert!(records[0].value.contains("v=spf1"));
    }

    #[test]
    fn test_parse_dig_output_ns_records() {
        let adapter = DnsAdapter::new();
        let output = r#"example.com.		86400	IN	NS	ns1.example.com.
example.com.		86400	IN	NS	ns2.example.com."#;

        let result = adapter.parse_dig_output(output, "NS");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 2);
        assert_eq!(records[0].value, "ns1.example.com.");
        assert_eq!(records[1].value, "ns2.example.com.");
    }

    #[test]
    fn test_parse_dig_output_aaaa_records() {
        let adapter = DnsAdapter::new();
        let output = "example.com.		3600	IN	AAAA	2606:2800:220:1:248:1893:25c8:1946";

        let result = adapter.parse_dig_output(output, "AAAA");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].record_type, "AAAA");
        assert_eq!(records[0].value, "2606:2800:220:1:248:1893:25c8:1946");
    }

    #[test]
    fn test_parse_dig_output_empty() {
        let adapter = DnsAdapter::new();
        let output = "";

        let result = adapter.parse_dig_output(output, "A");
        assert!(result.is_err());
    }

    #[test]
    fn test_parse_dig_output_with_comments() {
        let adapter = DnsAdapter::new();
        let output = r#"; <<>> DiG 9.10.6 <<>>
;; ANSWER SECTION:
example.com.		3600	IN	A	93.184.216.34"#;

        let result = adapter.parse_dig_output(output, "A");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].value, "93.184.216.34");
    }

    #[test]
    fn test_parse_dnskey_records() {
        let adapter = DnsAdapter::new();
        let records = vec![
            DnsRecord {
                name: "example.com.".to_string(),
                record_type: "DNSKEY".to_string(),
                value: "257 3 8 AwEAAa...base64key... ; key id = 5116".to_string(),
                ttl: 3600,
            },
            DnsRecord {
                name: "example.com.".to_string(),
                record_type: "DNSKEY".to_string(),
                value: "256 3 8 AwEAAb...base64key... ; key id = 12345".to_string(),
                ttl: 3600,
            },
        ];

        let dnskey_records = adapter.parse_dnskey_records(&records);
        assert_eq!(dnskey_records.len(), 2);

        // KSK (Key Signing Key) - flags 257
        assert_eq!(dnskey_records[0].flags, 257);
        assert_eq!(dnskey_records[0].protocol, 3);
        assert_eq!(dnskey_records[0].algorithm, 8);
        assert_eq!(dnskey_records[0].key_tag, 5116);
        assert!(dnskey_records[0]
            .public_key
            .contains("AwEAAa...base64key..."));

        // ZSK (Zone Signing Key) - flags 256
        assert_eq!(dnskey_records[1].flags, 256);
        assert_eq!(dnskey_records[1].key_tag, 12345);
    }

    #[test]
    fn test_parse_dnskey_records_without_key_tag() {
        let adapter = DnsAdapter::new();
        let records = vec![DnsRecord {
            name: "example.com.".to_string(),
            record_type: "DNSKEY".to_string(),
            value: "257 3 8 AwEAAa...base64key...".to_string(),
            ttl: 3600,
        }];

        let dnskey_records = adapter.parse_dnskey_records(&records);
        assert_eq!(dnskey_records.len(), 1);
        // Should fall back to flags as key tag
        assert_eq!(dnskey_records[0].key_tag, 257);
    }

    #[test]
    fn test_parse_ds_records() {
        let adapter = DnsAdapter::new();
        let records = vec![
            DnsRecord {
                name: "example.com.".to_string(),
                record_type: "DS".to_string(),
                value: "5116 8 2 ABC123DEF456...".to_string(),
                ttl: 86400,
            },
            DnsRecord {
                name: "example.com.".to_string(),
                record_type: "DS".to_string(),
                value: "12345 8 1 789ABC...".to_string(),
                ttl: 86400,
            },
        ];

        let ds_records = adapter.parse_ds_records(&records);
        assert_eq!(ds_records.len(), 2);

        assert_eq!(ds_records[0].key_tag, 5116);
        assert_eq!(ds_records[0].algorithm, 8);
        assert_eq!(ds_records[0].digest_type, 2);
        assert_eq!(ds_records[0].digest, "ABC123DEF456...");

        assert_eq!(ds_records[1].key_tag, 12345);
        assert_eq!(ds_records[1].algorithm, 8);
        assert_eq!(ds_records[1].digest_type, 1);
    }

    #[test]
    fn test_parse_rrsig_records() {
        let adapter = DnsAdapter::new();
        let records = vec![DnsRecord {
            name: "example.com.".to_string(),
            record_type: "RRSIG".to_string(),
            value: "A 8 2 300 20250115000000 20250101000000 12345 example.com. ABC123=="
                .to_string(),
            ttl: 300,
        }];

        let rrsig_records = adapter.parse_rrsig_records(&records);
        assert_eq!(rrsig_records.len(), 1);

        assert_eq!(rrsig_records[0].type_covered, "A");
        assert_eq!(rrsig_records[0].algorithm, 8);
        assert_eq!(rrsig_records[0].labels, 2);
        assert_eq!(rrsig_records[0].original_ttl, 300);
        assert_eq!(rrsig_records[0].signature_expiration, "20250115000000");
        assert_eq!(rrsig_records[0].signature_inception, "20250101000000");
        assert_eq!(rrsig_records[0].key_tag, 12345);
        assert_eq!(rrsig_records[0].signer_name, "example.com.");
        assert_eq!(rrsig_records[0].signature, "ABC123==");
    }

    #[test]
    fn test_parse_rrsig_records_multiline() {
        let adapter = DnsAdapter::new();
        let records = vec![DnsRecord {
            name: "example.com.".to_string(),
            record_type: "RRSIG".to_string(),
            value: "A 8 2 300 ( 20250115000000 20250101000000 12345 example.com. ABC123== )"
                .to_string(),
            ttl: 300,
        }];

        let rrsig_records = adapter.parse_rrsig_records(&records);
        assert_eq!(rrsig_records.len(), 1);
        assert_eq!(rrsig_records[0].type_covered, "A");
    }

    #[test]
    fn test_parse_dig_output_multiline_dnskey() {
        let adapter = DnsAdapter::new();
        let output = r#"example.com.		3600	IN	DNSKEY	257 3 8 ( AwEAAa8GMxKnN0wpBW5qfH6W ; KSK; alg = RSASHA256 ; key id = 5116
                                  Vh+D8gMZCEANdBlQ2jYw ) ; {key id = 5116}"#;

        let result = adapter.parse_dig_output(output, "DNSKEY");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].record_type, "DNSKEY");
        // Should capture the entire value including continuation lines
        assert!(records[0].value.contains("257 3 8"));
    }

    #[test]
    fn test_parse_dig_output_cname() {
        let adapter = DnsAdapter::new();
        let output = "www.example.com.		3600	IN	CNAME	example.com.";

        let result = adapter.parse_dig_output(output, "CNAME");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].record_type, "CNAME");
        assert_eq!(records[0].value, "example.com.");
    }

    #[test]
    fn test_parse_dig_output_soa() {
        let adapter = DnsAdapter::new();
        let output = "example.com.		3600	IN	SOA	ns1.example.com. admin.example.com. 2025010101 3600 900 604800 86400";

        let result = adapter.parse_dig_output(output, "SOA");
        assert!(result.is_ok());

        let records = result.unwrap();
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].record_type, "SOA");
        assert!(records[0].value.contains("ns1.example.com."));
    }

    #[tokio::test]
    async fn test_dns_response_structure() {
        // Test that DnsResponse can be properly constructed
        let response = DnsResponse {
            records: vec![DnsRecord {
                name: "example.com.".to_string(),
                record_type: "A".to_string(),
                value: "93.184.216.34".to_string(),
                ttl: 3600,
            }],
            query_time: 0.123,
            resolver: "system".to_string(),
            raw_output: Some("example.com. 3600 IN A 93.184.216.34".to_string()),
        };

        assert_eq!(response.records.len(), 1);
        assert_eq!(response.query_time, 0.123);
        assert_eq!(response.resolver, "system");
        assert!(response.raw_output.is_some());
    }
}
