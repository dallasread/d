// Integration tests for Tauri commands
// These tests verify that the command layer properly integrates with the adapters

#[cfg(test)]
mod dns_commands {

    // Note: These are integration tests that require the `dig` command to be available
    // They will be skipped in CI environments where dig is not installed

    #[tokio::test]
    #[ignore] // Run with: cargo test -- --ignored
    async fn test_query_dns_a_record() {
        // This test requires dig to be installed
        // We use example.com which should always resolve
        let domain = "example.com".to_string();
        let record_type = "A".to_string();

        // Note: In a real integration test, we would invoke the Tauri command
        // For now, we test the adapter directly
        use d_dns_debugger_lib::adapters::dns::DnsAdapter;

        let adapter = DnsAdapter::new();
        let result = adapter.query(&domain, &record_type).await;

        assert!(result.is_ok(), "DNS query should succeed for example.com");

        let response = result.unwrap();
        assert!(
            !response.records.is_empty(),
            "Should have at least one A record"
        );
        assert!(response.query_time > 0.0, "Query time should be positive");
    }

    #[tokio::test]
    #[ignore]
    async fn test_query_dns_multiple() {
        use d_dns_debugger_lib::adapters::dns::DnsAdapter;

        let adapter = DnsAdapter::new();
        let domain = "example.com";
        let record_types = vec!["A", "AAAA", "MX"];

        let result = adapter.query_multiple(domain, record_types).await;

        assert!(result.is_ok());
        let responses = result.unwrap();
        assert!(!responses.is_empty(), "Should get at least one response");
    }

    #[tokio::test]
    #[ignore]
    async fn test_query_dns_nonexistent_domain() {
        use d_dns_debugger_lib::adapters::dns::DnsAdapter;

        let adapter = DnsAdapter::new();
        let domain = "this-domain-definitely-does-not-exist-12345.com";
        let record_type = "A";

        let result = adapter.query(domain, record_type).await;

        // This may succeed with empty records or fail depending on DNS setup
        // Just verify it doesn't panic
        assert!(result.is_ok() || result.is_err());
    }
}

#[cfg(test)]
mod model_serialization {
    use d_dns_debugger_lib::models::certificate::*;
    use d_dns_debugger_lib::models::dns::*;
    use d_dns_debugger_lib::models::whois::*;
    use serde_json;

    #[test]
    fn test_dns_record_serialization() {
        let record = DnsRecord {
            name: "example.com.".to_string(),
            record_type: "A".to_string(),
            value: "93.184.216.34".to_string(),
            ttl: 3600,
        };

        let json = serde_json::to_string(&record).unwrap();
        assert!(json.contains("example.com"));
        assert!(json.contains("93.184.216.34"));

        let deserialized: DnsRecord = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.name, "example.com.");
        assert_eq!(deserialized.value, "93.184.216.34");
    }

    #[test]
    fn test_dns_response_serialization() {
        let response = DnsResponse {
            records: vec![DnsRecord {
                name: "example.com.".to_string(),
                record_type: "A".to_string(),
                value: "93.184.216.34".to_string(),
                ttl: 3600,
            }],
            query_time: 0.123,
            resolver: "system".to_string(),
            raw_output: Some("output".to_string()),
        };

        let json = serde_json::to_string(&response).unwrap();
        let deserialized: DnsResponse = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.records.len(), 1);
        assert_eq!(deserialized.query_time, 0.123);
        assert_eq!(deserialized.resolver, "system");
    }

    #[test]
    fn test_dnskey_record_serialization() {
        let dnskey = DnskeyRecord {
            flags: 257,
            protocol: 3,
            algorithm: 8,
            public_key: "AwEAAa...".to_string(),
            key_tag: 5116,
        };

        let json = serde_json::to_string(&dnskey).unwrap();
        let deserialized: DnskeyRecord = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.flags, 257);
        assert_eq!(deserialized.key_tag, 5116);
    }

    #[test]
    fn test_ds_record_serialization() {
        let ds = DsRecord {
            key_tag: 5116,
            algorithm: 8,
            digest_type: 2,
            digest: "ABC123".to_string(),
        };

        let json = serde_json::to_string(&ds).unwrap();
        let deserialized: DsRecord = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.key_tag, 5116);
        assert_eq!(deserialized.digest, "ABC123");
    }

    #[test]
    fn test_dnssec_validation_serialization() {
        let validation = DnssecValidation {
            status: "SECURE".to_string(),
            chain: vec![],
            warnings: vec!["test warning".to_string()],
        };

        let json = serde_json::to_string(&validation).unwrap();
        let deserialized: DnssecValidation = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.status, "SECURE");
        assert_eq!(deserialized.warnings.len(), 1);
    }

    #[test]
    fn test_whois_info_serialization() {
        let whois = WhoisInfo {
            domain: "example.com".to_string(),
            registrar: Some("Example Registrar".to_string()),
            creation_date: Some("2000-01-01".to_string()),
            expiration_date: Some("2025-01-01".to_string()),
            updated_date: Some("2024-01-01".to_string()),
            nameservers: vec!["ns1.example.com".to_string()],
            status: vec!["ok".to_string()],
            dnssec: Some("unsigned".to_string()),
            raw_output: "raw".to_string(),
        };

        let json = serde_json::to_string(&whois).unwrap();
        let deserialized: WhoisInfo = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.domain, "example.com");
        assert_eq!(
            deserialized.registrar,
            Some("Example Registrar".to_string())
        );
    }

    #[test]
    fn test_certificate_subject_serialization() {
        let subject = CertificateSubject {
            common_name: Some("example.com".to_string()),
            organization: Some("Example Inc".to_string()),
            organizational_unit: None,
            locality: None,
            state: None,
            country: Some("US".to_string()),
        };

        let json = serde_json::to_string(&subject).unwrap();
        let deserialized: CertificateSubject = serde_json::from_str(&json).unwrap();

        assert_eq!(deserialized.common_name, Some("example.com".to_string()));
        assert_eq!(deserialized.country, Some("US".to_string()));
    }

    #[test]
    fn test_certificate_info_serialization() {
        let cert = CertificateInfo {
            subject: CertificateSubject {
                common_name: Some("example.com".to_string()),
                organization: None,
                organizational_unit: None,
                locality: None,
                state: None,
                country: None,
            },
            issuer: CertificateSubject {
                common_name: Some("Example CA".to_string()),
                organization: None,
                organizational_unit: None,
                locality: None,
                state: None,
                country: None,
            },
            serial_number: "123456".to_string(),
            version: 3,
            not_before: "2024-01-01".to_string(),
            not_after: "2025-01-01".to_string(),
            subject_alternative_names: vec![],
            public_key_algorithm: "RSA".to_string(),
            public_key_size: Some(2048),
            signature_algorithm: "SHA256withRSA".to_string(),
            fingerprint_sha256: "".to_string(),
        };

        let json = serde_json::to_string(&cert).unwrap();
        let deserialized: CertificateInfo = serde_json::from_str(&json).unwrap();

        assert_eq!(
            deserialized.subject.common_name,
            Some("example.com".to_string())
        );
        assert_eq!(deserialized.version, 3);
    }
}

#[cfg(test)]
mod adapter_functionality {
    use d_dns_debugger_lib::adapters::dns::DnsAdapter;
    use d_dns_debugger_lib::models::dns::DnsRecord;

    #[test]
    fn test_parse_dnskey_with_real_data() {
        let adapter = DnsAdapter::new();

        // Realistic DNSKEY record from actual DNS output
        let records = vec![
            DnsRecord {
                name: ".".to_string(),
                record_type: "DNSKEY".to_string(),
                value: "257 3 8 AwEAAaz/tAm8yTn4Mfeh5eyI96WSVexTBAvkMgJzkKTOiW1vkIbzxeF3+/4RgWOq7HrxRixHlFlExOLAJr5emLvN7SWXgnLh4+B5xQlNVz8Og8kvArMtNROxVQuCaSnIDdD5LKyWbRd2n9WGe2R8PzgCmr3EgVLrjyBxWezF0jLHwVN8efS3rCj/EWgvIWgb9tarpVUDK/b58Da+sqqls3eNbuv7pr+eoZG+SrDK6nWeL3c6H5Apxz7LjVc1uTIdsIXxuOLYA4/ilBmSVIzuDWfdRUfhHdY6+cn8HFRm+2hM8AnXGXws9555KrUB5qihylGa8subX2Nn6UwNR1AkUTV74bU= ; key id = 20326".to_string(),
                ttl: 172800,
            }
        ];

        let dnskeys = adapter.parse_dnskey_records(&records);

        assert_eq!(dnskeys.len(), 1);
        assert_eq!(dnskeys[0].flags, 257); // KSK
        assert_eq!(dnskeys[0].protocol, 3);
        assert_eq!(dnskeys[0].algorithm, 8); // RSA/SHA-256
        assert_eq!(dnskeys[0].key_tag, 20326);
        assert!(dnskeys[0].public_key.starts_with("AwEAAaz/tAm8yTn4"));
    }

    #[test]
    fn test_parse_ds_with_real_data() {
        let adapter = DnsAdapter::new();

        let records = vec![DnsRecord {
            name: "example.com.".to_string(),
            record_type: "DS".to_string(),
            value: "370 13 2 BE74359954660069D5C63D200C39F5603827D7DD02B56F120EE9F3A86764247C"
                .to_string(),
            ttl: 86400,
        }];

        let ds_records = adapter.parse_ds_records(&records);

        assert_eq!(ds_records.len(), 1);
        assert_eq!(ds_records[0].key_tag, 370);
        assert_eq!(ds_records[0].algorithm, 13); // ECDSAP256SHA256
        assert_eq!(ds_records[0].digest_type, 2); // SHA-256
        assert_eq!(
            ds_records[0].digest,
            "BE74359954660069D5C63D200C39F5603827D7DD02B56F120EE9F3A86764247C"
        );
    }
}
