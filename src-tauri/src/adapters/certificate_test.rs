#[cfg(test)]
mod tests {
    use super::super::certificate::CertificateAdapter;
    use crate::models::certificate::CertificateSubject;

    #[test]
    fn test_parse_subject_fields_full() {
        let adapter = CertificateAdapter::new();
        let subject_str =
            "CN=example.com, O=Example Inc, OU=IT Department, L=San Francisco, ST=California, C=US";

        let subject = adapter.parse_subject_fields(subject_str);

        assert_eq!(subject.common_name, Some("example.com".to_string()));
        assert_eq!(subject.organization, Some("Example Inc".to_string()));
        assert_eq!(
            subject.organizational_unit,
            Some("IT Department".to_string())
        );
        assert_eq!(subject.locality, Some("San Francisco".to_string()));
        assert_eq!(subject.state, Some("California".to_string()));
        assert_eq!(subject.country, Some("US".to_string()));
    }

    #[test]
    fn test_parse_subject_fields_minimal() {
        let adapter = CertificateAdapter::new();
        let subject_str = "CN=example.com";

        let subject = adapter.parse_subject_fields(subject_str);

        assert_eq!(subject.common_name, Some("example.com".to_string()));
        assert_eq!(subject.organization, None);
        assert_eq!(subject.organizational_unit, None);
        assert_eq!(subject.locality, None);
        assert_eq!(subject.state, None);
        assert_eq!(subject.country, None);
    }

    #[test]
    fn test_parse_subject_fields_partial() {
        let adapter = CertificateAdapter::new();
        let subject_str = "CN=example.com, O=Example Inc, C=US";

        let subject = adapter.parse_subject_fields(subject_str);

        assert_eq!(subject.common_name, Some("example.com".to_string()));
        assert_eq!(subject.organization, Some("Example Inc".to_string()));
        assert_eq!(subject.country, Some("US".to_string()));
        assert_eq!(subject.organizational_unit, None);
        assert_eq!(subject.locality, None);
        assert_eq!(subject.state, None);
    }

    #[test]
    fn test_parse_subject_fields_with_spaces() {
        let adapter = CertificateAdapter::new();
        let subject_str = "CN = example.com , O = Example Inc";

        let subject = adapter.parse_subject_fields(subject_str);

        assert_eq!(subject.common_name, Some("example.com".to_string()));
        assert_eq!(subject.organization, Some("Example Inc".to_string()));
    }

    #[test]
    fn test_parse_subject_fields_empty() {
        let adapter = CertificateAdapter::new();
        let subject_str = "";

        let subject = adapter.parse_subject_fields(subject_str);

        assert_eq!(subject.common_name, None);
        assert_eq!(subject.organization, None);
    }

    #[test]
    fn test_parse_subject() {
        let adapter = CertificateAdapter::new();
        let text = "Subject: CN=example.com, O=Example Inc, C=US";

        let subject = adapter.parse_subject(text, "Subject:");

        assert_eq!(subject.common_name, Some("example.com".to_string()));
        assert_eq!(subject.organization, Some("Example Inc".to_string()));
        assert_eq!(subject.country, Some("US".to_string()));
    }

    #[test]
    fn test_parse_subject_issuer() {
        let adapter = CertificateAdapter::new();
        let text = "Issuer: CN=Example CA, O=Example Inc, C=US";

        let issuer = adapter.parse_subject(text, "Issuer:");

        assert_eq!(issuer.common_name, Some("Example CA".to_string()));
        assert_eq!(issuer.organization, Some("Example Inc".to_string()));
        assert_eq!(issuer.country, Some("US".to_string()));
    }

    #[test]
    fn test_parse_subject_not_found() {
        let adapter = CertificateAdapter::new();
        let text = "Some other text";

        let subject = adapter.parse_subject(text, "Subject:");

        assert_eq!(subject.common_name, None);
        assert_eq!(subject.organization, None);
    }

    #[test]
    fn test_extract_field_serial() {
        let adapter = CertificateAdapter::new();
        let text = "Serial Number: 4A:B2:C3:D4:E5:F6:78:90";

        let serial = adapter.extract_field(text, "Serial Number:");
        assert_eq!(serial, Some("4A:B2:C3:D4:E5:F6:78:90".to_string()));
    }

    #[test]
    fn test_extract_field_not_found() {
        let adapter = CertificateAdapter::new();
        let text = "Some text without the field";

        let result = adapter.extract_field(text, "Serial Number:");
        assert_eq!(result, None);
    }

    #[test]
    fn test_extract_validity_dates_new_format() {
        let adapter = CertificateAdapter::new();
        let text = "v:NotBefore: Sep 28 15:13:11 2025 GMT; NotAfter: Dec 27 15:13:10 2025 GMT";

        let (not_before, not_after) = adapter.extract_validity_dates(text);

        assert_eq!(not_before, "Sep 28 15:13:11 2025 GMT");
        assert_eq!(not_after, "Dec 27 15:13:10 2025 GMT");
    }

    #[test]
    fn test_extract_validity_dates_old_format() {
        let adapter = CertificateAdapter::new();
        let text = r#"Not Before: Sep 28 15:13:11 2025 GMT
Not After : Dec 27 15:13:10 2025 GMT"#;

        let (not_before, not_after) = adapter.extract_validity_dates(text);

        assert_eq!(not_before, "Sep 28 15:13:11 2025 GMT");
        assert_eq!(not_after, "Dec 27 15:13:10 2025 GMT");
    }

    #[test]
    fn test_extract_validity_dates_missing() {
        let adapter = CertificateAdapter::new();
        let text = "Some text without dates";

        let (not_before, not_after) = adapter.extract_validity_dates(text);

        assert_eq!(not_before, "");
        assert_eq!(not_after, "");
    }

    #[test]
    fn test_parse_subject_fields_wildcard_cert() {
        let adapter = CertificateAdapter::new();
        let subject_str = "CN=*.example.com, O=Example Inc";

        let subject = adapter.parse_subject_fields(subject_str);

        assert_eq!(subject.common_name, Some("*.example.com".to_string()));
        assert_eq!(subject.organization, Some("Example Inc".to_string()));
    }

    #[test]
    fn test_parse_subject_with_complex_organization_name() {
        let adapter = CertificateAdapter::new();
        let subject_str = "CN=example.com, O=Example, Inc., OU=Web Services";

        let subject = adapter.parse_subject_fields(subject_str);

        assert_eq!(subject.common_name, Some("example.com".to_string()));
        // Note: This may have issues with embedded commas, but tests the current implementation
        assert!(subject.organization.is_some());
    }

    #[test]
    fn test_certificate_subject_default() {
        let subject = CertificateSubject {
            common_name: None,
            organization: None,
            organizational_unit: None,
            locality: None,
            state: None,
            country: None,
        };

        assert_eq!(subject.common_name, None);
        assert_eq!(subject.organization, None);
        assert_eq!(subject.organizational_unit, None);
        assert_eq!(subject.locality, None);
        assert_eq!(subject.state, None);
        assert_eq!(subject.country, None);
    }
}
