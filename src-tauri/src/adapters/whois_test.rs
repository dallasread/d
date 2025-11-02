#[cfg(test)]
mod tests {
    use super::super::whois::WhoisAdapter;

    #[test]
    fn test_get_whois_server_com() {
        let adapter = WhoisAdapter::new();
        let server = adapter.get_whois_server("example.com");
        assert_eq!(server, Some("whois.verisign-grs.com".to_string()));
    }

    #[test]
    fn test_get_whois_server_io() {
        let adapter = WhoisAdapter::new();
        let server = adapter.get_whois_server("example.io");
        assert_eq!(server, Some("whois.nic.io".to_string()));
    }

    #[test]
    fn test_get_whois_server_org() {
        let adapter = WhoisAdapter::new();
        let server = adapter.get_whois_server("example.org");
        assert_eq!(server, Some("whois.pir.org".to_string()));
    }

    #[test]
    fn test_get_whois_server_uk() {
        let adapter = WhoisAdapter::new();
        let server = adapter.get_whois_server("example.uk");
        assert_eq!(server, Some("whois.nic.uk".to_string()));
    }

    #[test]
    fn test_get_whois_server_unknown_tld() {
        let adapter = WhoisAdapter::new();
        let server = adapter.get_whois_server("example.unknowntld");
        assert_eq!(server, None);
    }

    #[test]
    fn test_get_whois_server_net() {
        let adapter = WhoisAdapter::new();
        let server = adapter.get_whois_server("example.net");
        assert_eq!(server, Some("whois.verisign-grs.com".to_string()));
    }

    #[test]
    fn test_extract_field_simple() {
        let adapter = WhoisAdapter::new();
        let text = r#"Domain Name: EXAMPLE.COM
Registrar: Example Registrar Inc.
Creation Date: 1995-08-14T04:00:00Z"#;

        let registrar = adapter.extract_field(text, &["Registrar:"]);
        assert_eq!(registrar, Some("Example Registrar Inc.".to_string()));

        let creation_date = adapter.extract_field(text, &["Creation Date:"]);
        assert_eq!(creation_date, Some("1995-08-14T04:00:00Z".to_string()));
    }

    #[test]
    fn test_extract_field_multiple_patterns() {
        let adapter = WhoisAdapter::new();
        let text = "created: 1995-08-14T04:00:00Z";

        let creation_date = adapter.extract_field(text, &["Creation Date:", "created:"]);
        assert_eq!(creation_date, Some("1995-08-14T04:00:00Z".to_string()));
    }

    #[test]
    fn test_extract_field_not_found() {
        let adapter = WhoisAdapter::new();
        let text = "Domain Name: EXAMPLE.COM";

        let result = adapter.extract_field(text, &["Registrar:"]);
        assert_eq!(result, None);
    }

    #[test]
    fn test_extract_nameservers() {
        let adapter = WhoisAdapter::new();
        let text = r#"Domain Name: EXAMPLE.COM
Name Server: NS1.EXAMPLE.COM
Name Server: NS2.EXAMPLE.COM
Name Server: NS3.EXAMPLE.COM"#;

        let nameservers = adapter.extract_nameservers(text);
        assert_eq!(nameservers.len(), 3);
        assert_eq!(nameservers[0], "ns1.example.com");
        assert_eq!(nameservers[1], "ns2.example.com");
        assert_eq!(nameservers[2], "ns3.example.com");
    }

    #[test]
    fn test_extract_nameservers_case_insensitive() {
        let adapter = WhoisAdapter::new();
        let text = r#"name server: ns1.EXAMPLE.COM
NAME SERVER: ns2.example.com"#;

        let nameservers = adapter.extract_nameservers(text);
        assert_eq!(nameservers.len(), 2);
        assert_eq!(nameservers[0], "ns1.example.com");
        assert_eq!(nameservers[1], "ns2.example.com");
    }

    #[test]
    fn test_extract_nameservers_empty() {
        let adapter = WhoisAdapter::new();
        let text = "Domain Name: EXAMPLE.COM";

        let nameservers = adapter.extract_nameservers(text);
        assert_eq!(nameservers.len(), 0);
    }

    #[test]
    fn test_extract_status() {
        let adapter = WhoisAdapter::new();
        let text = r#"Domain Name: EXAMPLE.COM
Domain Status: clientTransferProhibited
Domain Status: clientUpdateProhibited
Status: ok"#;

        let status = adapter.extract_status(text);
        assert_eq!(status.len(), 3);
        assert!(status.contains(&"clientTransferProhibited".to_string()));
        assert!(status.contains(&"clientUpdateProhibited".to_string()));
        assert!(status.contains(&"ok".to_string()));
    }

    #[test]
    fn test_extract_status_case_insensitive() {
        let adapter = WhoisAdapter::new();
        let text = r#"STATUS: clientTransferProhibited
status: ok"#;

        let status = adapter.extract_status(text);
        assert_eq!(status.len(), 2);
    }

    #[test]
    fn test_parse_whois_output_full() {
        let adapter = WhoisAdapter::new();
        let output = r#"Domain Name: EXAMPLE.COM
Registrar: Example Registrar Inc.
Creation Date: 1995-08-14T04:00:00Z
Expiration Date: 2025-08-13T04:00:00Z
Updated Date: 2024-08-13T09:11:03Z
Name Server: NS1.EXAMPLE.COM
Name Server: NS2.EXAMPLE.COM
Domain Status: clientTransferProhibited
DNSSEC: unsigned"#;

        let result = adapter.parse_whois_output(output, "example.com");
        assert!(result.is_ok());

        let info = result.unwrap();
        assert_eq!(info.domain, "example.com");
        assert_eq!(info.registrar, Some("Example Registrar Inc.".to_string()));
        assert_eq!(info.creation_date, Some("1995-08-14T04:00:00Z".to_string()));
        assert_eq!(
            info.expiration_date,
            Some("2025-08-13T04:00:00Z".to_string())
        );
        assert_eq!(info.updated_date, Some("2024-08-13T09:11:03Z".to_string()));
        assert_eq!(info.nameservers.len(), 2);
        assert_eq!(info.status.len(), 1);
        assert_eq!(info.dnssec, Some("unsigned".to_string()));
        assert_eq!(info.raw_output, output);
    }

    #[test]
    fn test_parse_whois_output_minimal() {
        let adapter = WhoisAdapter::new();
        let output = "Domain Name: EXAMPLE.COM";

        let result = adapter.parse_whois_output(output, "example.com");
        assert!(result.is_ok());

        let info = result.unwrap();
        assert_eq!(info.domain, "example.com");
        assert_eq!(info.registrar, None);
        assert_eq!(info.creation_date, None);
        assert_eq!(info.nameservers.len(), 0);
    }

    #[test]
    fn test_get_whois_server_app_dev() {
        let adapter = WhoisAdapter::new();

        let app_server = adapter.get_whois_server("example.app");
        assert_eq!(app_server, Some("whois.nic.google".to_string()));

        let dev_server = adapter.get_whois_server("example.dev");
        assert_eq!(dev_server, Some("whois.nic.google".to_string()));
    }

    #[test]
    fn test_get_whois_server_international_tlds() {
        let adapter = WhoisAdapter::new();

        assert_eq!(
            adapter.get_whois_server("example.jp"),
            Some("whois.jprs.jp".to_string())
        );
        assert_eq!(
            adapter.get_whois_server("example.de"),
            Some("whois.denic.de".to_string())
        );
        assert_eq!(
            adapter.get_whois_server("example.fr"),
            Some("whois.nic.fr".to_string())
        );
        assert_eq!(
            adapter.get_whois_server("example.au"),
            Some("whois.auda.org.au".to_string())
        );
    }
}
