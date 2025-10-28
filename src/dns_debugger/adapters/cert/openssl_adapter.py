"""Certificate adapter using OpenSSL command-line tool."""

import json
import re
import subprocess
from datetime import datetime
from typing import Optional

from dns_debugger.domain.models.certificate import (
    Certificate,
    CertificateChain,
    CertificateSubject,
    TLSInfo,
    TLSVersion,
)
from dns_debugger.domain.ports.cert_port import CertificatePort


class OpenSSLAdapter(CertificatePort):
    """Adapter for certificate operations using OpenSSL command-line tool."""

    def get_certificate_info(
        self, host: str, port: int = 443, servername: Optional[str] = None
    ) -> TLSInfo:
        """Get SSL/TLS certificate information for a host."""
        start_time = datetime.now()

        sni = servername or host

        # Get certificate chain and raw output
        cert_chain, raw_chain_output = self.get_certificate_chain(
            host, port, servername
        )

        # Get supported versions and cipher suites
        supported_versions = self._get_supported_tls_versions(host, port)
        cipher_suites = self.get_supported_cipher_suites(host, port)

        # Check OCSP stapling
        has_ocsp = self.check_ocsp_stapling(host, port)

        connection_time = (datetime.now() - start_time).total_seconds() * 1000

        return TLSInfo(
            host=host,
            port=port,
            certificate_chain=cert_chain,
            supported_versions=supported_versions,
            cipher_suites=cipher_suites,
            has_ocsp_stapling=has_ocsp,
            supports_sni=True,  # Assume SNI support for modern hosts
            connection_time_ms=connection_time,
            timestamp=datetime.now(),
            raw_data={"raw_output": raw_chain_output} if raw_chain_output else None,
        )

    def get_certificate_chain(
        self, host: str, port: int = 443, servername: Optional[str] = None
    ) -> tuple[CertificateChain, str]:
        """Get the full certificate chain for a host.

        Returns:
            Tuple of (CertificateChain, raw_output)
        """
        sni = servername or host

        try:
            # Get certificate chain using openssl s_client
            cmd = [
                "openssl",
                "s_client",
                "-connect",
                f"{host}:{port}",
                "-servername",
                sni,
                "-showcerts",
                "-verify_return_error",
            ]

            result = subprocess.run(
                cmd, input="", capture_output=True, text=True, timeout=10
            )

            # Parse certificates from output
            certificates = self._parse_certificate_chain(result.stdout)

            # Validate chain
            is_valid = result.returncode == 0
            validation_errors = []

            if not is_valid:
                # Parse error messages
                error_lines = [
                    line
                    for line in result.stderr.split("\n")
                    if "error" in line.lower()
                ]
                validation_errors.extend(error_lines)

            chain = CertificateChain(
                certificates=certificates,
                is_valid=is_valid,
                validation_errors=validation_errors,
            )

            # Return both chain and raw output
            return chain, result.stdout

        except subprocess.TimeoutExpired:
            return (
                CertificateChain(
                    certificates=[],
                    is_valid=False,
                    validation_errors=["Connection timeout"],
                ),
                "",
            )
        except Exception as e:
            return (
                CertificateChain(
                    certificates=[], is_valid=False, validation_errors=[str(e)]
                ),
                "",
            )

    def _parse_certificate_chain(self, output: str) -> list[Certificate]:
        """Parse certificate chain from openssl s_client output."""
        certificates = []

        # Split output into individual certificates
        cert_pattern = r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----"
        cert_texts = re.findall(cert_pattern, output, re.DOTALL)

        for cert_text in cert_texts:
            try:
                cert = self._parse_certificate(cert_text)
                if cert:
                    certificates.append(cert)
            except Exception:
                continue

        return certificates

    def _parse_certificate(self, cert_pem: str) -> Optional[Certificate]:
        """Parse a single PEM certificate."""
        try:
            # Use openssl x509 to parse certificate details
            cmd = ["openssl", "x509", "-text", "-noout"]

            result = subprocess.run(
                cmd, input=cert_pem, capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return None

            text = result.stdout

            # Parse subject
            subject = self._parse_subject(text, "Subject:")

            # Parse issuer
            issuer = self._parse_subject(text, "Issuer:")

            # Parse serial number
            serial_match = re.search(
                r"Serial Number:\s*\n?\s*([0-9a-f:]+)", text, re.IGNORECASE
            )
            serial_number = (
                serial_match.group(1).replace(":", "") if serial_match else ""
            )

            # Parse version
            version_match = re.search(r"Version:\s*(\d+)", text)
            version = int(version_match.group(1)) if version_match else 3

            # Parse validity dates
            not_before_match = re.search(r"Not Before\s*:\s*(.+)", text)
            not_after_match = re.search(r"Not After\s*:\s*(.+)", text)

            not_before = (
                self._parse_openssl_date(not_before_match.group(1))
                if not_before_match
                else datetime.now()
            )
            not_after = (
                self._parse_openssl_date(not_after_match.group(1))
                if not_after_match
                else datetime.now()
            )

            # Parse signature algorithm
            sig_algo_match = re.search(r"Signature Algorithm:\s*(.+)", text)
            signature_algorithm = (
                sig_algo_match.group(1).strip() if sig_algo_match else "unknown"
            )

            # Parse public key info
            pubkey_match = re.search(r"Public Key Algorithm:\s*(.+)", text)
            public_key_algorithm = (
                pubkey_match.group(1).strip() if pubkey_match else "unknown"
            )

            pubkey_size_match = re.search(r"Public-Key:\s*\((\d+)\s*bit\)", text)
            public_key_size = (
                int(pubkey_size_match.group(1)) if pubkey_size_match else 0
            )

            # Parse SANs
            san_match = re.search(r"Subject Alternative Name:\s*\n\s*(.+)", text)
            sans = []
            if san_match:
                san_text = san_match.group(1)
                sans = [
                    s.strip().replace("DNS:", "")
                    for s in san_text.split(",")
                    if "DNS:" in s
                ]

            # Get fingerprint (SHA256)
            fingerprint_cmd = ["openssl", "x509", "-fingerprint", "-sha256", "-noout"]
            fp_result = subprocess.run(
                fingerprint_cmd,
                input=cert_pem,
                capture_output=True,
                text=True,
                timeout=5,
            )

            fingerprint = ""
            if fp_result.returncode == 0:
                fp_match = re.search(r"Fingerprint=(.+)", fp_result.stdout)
                fingerprint = fp_match.group(1).strip() if fp_match else ""

            return Certificate(
                subject=subject,
                issuer=issuer,
                serial_number=serial_number,
                version=version,
                not_before=not_before,
                not_after=not_after,
                signature_algorithm=signature_algorithm,
                public_key_algorithm=public_key_algorithm,
                public_key_size=public_key_size,
                subject_alternative_names=sans,
                fingerprint_sha256=fingerprint,
            )

        except Exception:
            return None

    def _parse_subject(self, text: str, prefix: str) -> CertificateSubject:
        """Parse subject or issuer from certificate text."""
        match = re.search(f"{prefix}(.+)", text)
        if not match:
            return CertificateSubject(common_name="unknown")

        subject_text = match.group(1).strip()

        # Parse DN components
        cn = self._extract_dn_field(subject_text, "CN")
        o = self._extract_dn_field(subject_text, "O")
        ou = self._extract_dn_field(subject_text, "OU")
        l = self._extract_dn_field(subject_text, "L")
        st = self._extract_dn_field(subject_text, "ST")
        c = self._extract_dn_field(subject_text, "C")

        return CertificateSubject(
            common_name=cn or "unknown",
            organization=o,
            organizational_unit=ou,
            locality=l,
            state=st,
            country=c,
        )

    def _extract_dn_field(self, dn: str, field: str) -> Optional[str]:
        """Extract a field from a Distinguished Name."""
        pattern = f"{field}\\s*=\\s*([^,]+)"
        match = re.search(pattern, dn)
        return match.group(1).strip() if match else None

    def _parse_openssl_date(self, date_str: str) -> datetime:
        """Parse OpenSSL date format."""
        try:
            # OpenSSL format: "Jan  1 00:00:00 2024 GMT"
            return datetime.strptime(date_str.strip(), "%b %d %H:%M:%S %Y %Z")
        except ValueError:
            return datetime.now()

    def _get_supported_tls_versions(self, host: str, port: int) -> list[TLSVersion]:
        """Get supported TLS versions."""
        supported = []

        # Test each TLS version
        versions_to_test = [
            (TLSVersion.TLS_1_3, "tls1_3"),
            (TLSVersion.TLS_1_2, "tls1_2"),
            (TLSVersion.TLS_1_1, "tls1_1"),
            (TLSVersion.TLS_1_0, "tls1"),
        ]

        for version_enum, version_flag in versions_to_test:
            cmd = [
                "openssl",
                "s_client",
                f"-{version_flag}",
                "-connect",
                f"{host}:{port}",
                "-brief",
            ]

            try:
                result = subprocess.run(
                    cmd, input="", capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0 and "Verification error" not in result.stdout:
                    supported.append(version_enum)
            except:
                continue

        return supported

    def verify_certificate(
        self, host: str, port: int = 443, servername: Optional[str] = None
    ) -> tuple[bool, list[str]]:
        """Verify the certificate and chain for a host."""
        chain = self.get_certificate_chain(host, port, servername)
        return chain.is_valid, chain.validation_errors

    def check_ocsp_stapling(self, host: str, port: int = 443) -> bool:
        """Check if OCSP stapling is enabled."""
        try:
            cmd = [
                "openssl",
                "s_client",
                "-connect",
                f"{host}:{port}",
                "-status",
                "-servername",
                host,
            ]

            result = subprocess.run(
                cmd, input="", capture_output=True, text=True, timeout=5
            )

            return "OCSP Response Status: successful" in result.stdout

        except:
            return False

    def get_supported_cipher_suites(self, host: str, port: int = 443) -> list[str]:
        """Get the list of supported cipher suites."""
        try:
            cmd = [
                "openssl",
                "s_client",
                "-connect",
                f"{host}:{port}",
                "-cipher",
                "ALL",
                "-brief",
            ]

            result = subprocess.run(
                cmd, input="", capture_output=True, text=True, timeout=5
            )

            # Parse cipher from output
            cipher_match = re.search(r"Cipher:\s*(.+)", result.stdout)
            if cipher_match:
                return [cipher_match.group(1).strip()]

            return []

        except:
            return []

    def export_certificate_pem(self, certificate: Certificate) -> str:
        """Export a certificate in PEM format."""
        # This would require access to the original certificate object
        # For now, return a placeholder
        return "# Certificate export not yet implemented"

    def is_available(self) -> bool:
        """Check if OpenSSL is available."""
        try:
            subprocess.run(
                ["openssl", "version"], capture_output=True, timeout=5, check=True
            )
            return True
        except:
            return False

    def get_tool_name(self) -> str:
        """Get the name of the certificate tool."""
        return "openssl"
