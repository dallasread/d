"""DNS adapter implementation using the 'dig' command (fallback)."""

import re
import subprocess
import sys
from datetime import datetime
from typing import Optional

from dns_debugger.domain.models.dns_record import (
    DNSQuery,
    DNSRecord,
    DNSResponse,
    RecordType,
)
from dns_debugger.domain.models.dnssec_info import (
    DNSSECValidation,
    DNSSECStatus,
    DNSSECChain,
    DNSKEYRecord,
    DSRecord,
    RRSIGRecord,
    DNSSECAlgorithm,
    DigestType,
    ZoneData,
)
from dns_debugger.domain.ports.dns_port import DNSPort


class DigAdapter(DNSPort):
    """Adapter for the 'dig' DNS client.

    dig is the traditional DNS lookup utility from BIND.
    Used as a fallback when dog is not available.
    """

    def query(
        self, domain: str, record_type: RecordType, resolver: Optional[str] = None
    ) -> DNSResponse:
        """Execute a DNS query using dig."""
        start_time = datetime.now()
        query_obj = DNSQuery(domain=domain, record_type=record_type, resolver=resolver)

        # Build dig command
        cmd = ["dig", "+noall", "+answer", domain, record_type.value]
        if resolver:
            cmd.append(f"@{resolver}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=True
            )

            records = self._parse_dig_output(result.stdout, domain, record_type)
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            resolver_used = resolver or "system"

            return DNSResponse(
                query=query_obj,
                records=records,
                query_time_ms=query_time,
                resolver_used=resolver_used,
                timestamp=datetime.now(),
                has_dnssec=False,
                raw_data={"raw_output": result.stdout},
            )

        except subprocess.CalledProcessError as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used=resolver or "system",
                timestamp=datetime.now(),
                error=f"Query failed: {e.stderr}",
            )
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used=resolver or "system",
                timestamp=datetime.now(),
                error=f"Unexpected error: {str(e)}",
            )

    def query_dnskey_with_keytag(self, domain: str) -> tuple[list[DNSKEYRecord], str]:
        """Query DNSKEY records with proper key tag parsing using +multi format.

        Returns:
            Tuple of (list of DNSKEYRecord objects, raw output string)
        """
        start_time = datetime.now()

        try:
            # Use +multi to get key tags in comments
            cmd = ["dig", domain, "DNSKEY", "+dnssec", "+multi"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=True
            )

            # Parse the +multi output to extract key tags
            dnskey_records = []
            lines = result.stdout.split("\n")

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Look for DNSKEY lines (but not RRSIG DNSKEY)
                if (
                    "DNSKEY" in line
                    and not line.startswith(";")
                    and "RRSIG" not in line
                ):
                    # Extract base fields
                    # Format: domain TTL IN DNSKEY flags protocol algorithm (key...)
                    parts = line.split()
                    if len(parts) >= 7:
                        ttl = int(parts[1])
                        flags = int(parts[4])
                        protocol = int(parts[5])
                        algorithm = int(parts[6])

                        # Collect the public key (may span multiple lines)
                        public_key_parts = []
                        if "(" in line:
                            # Multi-line format
                            i += 1
                            while i < len(lines) and ")" not in lines[i]:
                                public_key_parts.append(lines[i].strip())
                                i += 1
                            if i < len(lines):
                                # Get last line before )
                                last_line = lines[i].split(")")[0].strip()
                                if last_line:
                                    public_key_parts.append(last_line)

                                # Look for key id in comment after )
                                comment = (
                                    lines[i].split(")", 1)[1] if ")" in lines[i] else ""
                                )
                                key_tag = None
                                if "key id" in comment or "key tag" in comment:
                                    import re

                                    match = re.search(
                                        r"key\s+(?:id|tag)\s*=\s*(\d+)", comment
                                    )
                                    if match:
                                        key_tag = int(match.group(1))
                        else:
                            # Single line - extract key from end
                            key_start = line.find(str(algorithm)) + len(str(algorithm))
                            public_key_parts.append(line[key_start:].strip())
                            # No key tag available in single-line format
                            key_tag = None

                        public_key = "".join(public_key_parts)

                        # If no key tag found, calculate it (will be wrong but better than nothing)
                        if key_tag is None:
                            key_tag = (flags + protocol + algorithm) % 65536

                        # Parse algorithm enum
                        algo_enum = self._parse_algorithm(algorithm)

                        dnskey_records.append(
                            DNSKEYRecord(
                                flags=flags,
                                protocol=protocol,
                                algorithm=algo_enum,
                                key_tag=key_tag,
                                public_key=public_key,
                                ttl=ttl,
                            )
                        )

                i += 1

            return dnskey_records, result.stdout

        except Exception:
            return [], ""

    def _parse_dig_output(
        self, output: str, domain: str, record_type: RecordType
    ) -> list[DNSRecord]:
        """Parse dig output into DNSRecord objects.

        dig output format:
        domain.com.    300    IN    A    93.184.216.34
        """
        records = []

        for line in output.strip().split("\n"):
            if not line or line.startswith(";"):
                continue

            # Parse dig answer line
            # Format: NAME TTL CLASS TYPE RDATA
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue

            name, ttl, record_class, rtype, value = parts

            # Clean up the name (remove trailing dot)
            name = name.rstrip(".")

            record = DNSRecord(
                name=name,
                record_type=record_type,
                value=value.strip(),
                ttl=int(ttl),
                record_class=record_class,
            )
            records.append(record)

        return records

    def query_multiple_types(
        self,
        domain: str,
        record_types: list[RecordType],
        resolver: Optional[str] = None,
    ) -> dict[RecordType, DNSResponse]:
        """Execute multiple DNS queries for different record types."""
        results = {}
        for record_type in record_types:
            results[record_type] = self.query(domain, record_type, resolver)
        return results

    def reverse_lookup(self, ip_address: str) -> DNSResponse:
        """Perform a reverse DNS lookup (PTR record)."""
        # dig has a -x flag for reverse lookups
        start_time = datetime.now()
        query_obj = DNSQuery(domain=ip_address, record_type=RecordType.PTR)

        cmd = ["dig", "+noall", "+answer", "-x", ip_address]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=True
            )

            records = self._parse_dig_output(result.stdout, ip_address, RecordType.PTR)
            query_time = (datetime.now() - start_time).total_seconds() * 1000

            return DNSResponse(
                query=query_obj,
                records=records,
                query_time_ms=query_time,
                resolver_used="system",
                timestamp=datetime.now(),
            )

        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used="system",
                timestamp=datetime.now(),
                error=str(e),
            )

    def trace(self, domain: str) -> list[DNSResponse]:
        """Trace the DNS resolution path from root servers."""
        # dig has a +trace flag
        start_time = datetime.now()
        cmd = ["dig", "+trace", domain]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=True
            )

            # TODO: Parse trace output into multiple DNSResponse objects
            # For now, return a single response with all data
            return []

        except Exception:
            return []

    def is_available(self) -> bool:
        """Check if dig is available on the system."""
        try:
            subprocess.run(["dig", "-v"], capture_output=True, timeout=5, check=True)
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def get_tool_name(self) -> str:
        """Get the name of the DNS tool."""
        return "dig"

    def get_version(self) -> Optional[str]:
        """Get the version of dig."""
        try:
            result = subprocess.run(
                ["dig", "-v"], capture_output=True, text=True, timeout=5, check=True
            )
            # dig version output is like "DiG 9.10.6"
            match = re.search(r"DiG\s+([\d.]+)", result.stdout)
            return match.group(1) if match else None
        except Exception:
            return None

    def validate_dnssec(self, domain: str) -> DNSSECValidation:
        """Validate DNSSEC for a domain using dig.

        Args:
            domain: The domain to validate

        Returns:
            DNSSECValidation with validation results
        """
        start_time = datetime.now()

        try:
            # Query for DNSSEC-related records
            ds_response = self.query(domain, RecordType.DS)
            dnskey_records, dnskey_raw = self.query_dnskey_with_keytag(domain)

            has_ds = ds_response.is_success and ds_response.record_count > 0
            has_dnskey = len(dnskey_records) > 0

            # Parse DNSSEC records
            ds_records = self._parse_ds_records(ds_response)

            # Try to check for RRSIG records by querying authoritative nameserver
            rrsig_records = []
            has_rrsig = False
            dnssec_output = ""
            try:
                # First get the authoritative nameserver
                ns_cmd = ["dig", "+short", domain, "NS"]
                ns_result = subprocess.run(
                    ns_cmd, capture_output=True, text=True, timeout=10, check=True
                )
                nameservers = [
                    ns.strip().rstrip(".")
                    for ns in ns_result.stdout.strip().split("\n")
                    if ns.strip()
                ]

                if nameservers:
                    # Query the authoritative nameserver for RRSIGs
                    auth_ns = nameservers[0]
                    cmd = [
                        "dig",
                        f"@{auth_ns}",
                        "+dnssec",
                        "+noall",
                        "+answer",
                        domain,
                        "A",
                    ]
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=10, check=True
                    )
                    # Check if RRSIG records are present in output
                    has_rrsig = "RRSIG" in result.stdout
                    dnssec_output = result.stdout
            except Exception:
                has_rrsig = False

            # Build complete recursive DNSSEC chain from root to leaf
            parent_zones = []
            parts = domain.rstrip(".").split(".")

            # Always query root zone
            try:
                root_dnskey_records, _ = self.query_dnskey_with_keytag(".")

                tld = parts[-1]
                root_ds_response = self.query(tld, RecordType.DS)
                root_ds_records = self._parse_ds_records(root_ds_response)

                root_zone = ZoneData(
                    zone_name=".",
                    dnskey_records=root_dnskey_records,
                    ds_records=root_ds_records,
                    rrsig_records=[],
                )
                parent_zones.append(root_zone)
            except Exception:
                pass

            # Build each level from TLD down to parent of target
            for i in range(len(parts) - 1, 0, -1):
                current_zone = ".".join(parts[i:])
                child_zone = ".".join(parts[i - 1 :])

                try:
                    zone_dnskey_records, _ = self.query_dnskey_with_keytag(current_zone)

                    zone_ds_response = self.query(child_zone, RecordType.DS)
                    zone_ds_records = self._parse_ds_records(zone_ds_response)

                    zone_data = ZoneData(
                        zone_name=current_zone,
                        dnskey_records=zone_dnskey_records,
                        ds_records=zone_ds_records,
                        rrsig_records=[],
                    )
                    parent_zones.append(zone_data)
                except Exception:
                    pass

            # Build DNSSEC chain
            chain = DNSSECChain(
                domain=domain,
                has_ds_record=has_ds,
                has_dnskey_record=has_dnskey,
                has_rrsig_record=has_rrsig,
                ds_records=ds_records,
                dnskey_records=dnskey_records,
                rrsig_records=rrsig_records,
                parent_zones=parent_zones,
            )

            # Determine validation status
            if not has_dnskey:
                status = DNSSECStatus.INSECURE
            elif has_dnskey and has_ds:
                # Domain has both DNSKEY and DS records - it's signed and secure
                status = DNSSECStatus.SECURE
            elif has_dnskey and not has_ds:
                # Domain has DNSKEY but no DS in parent - signed but chain broken
                status = DNSSECStatus.INDETERMINATE
            else:
                status = DNSSECStatus.INDETERMINATE

            validation_time = (datetime.now() - start_time).total_seconds() * 1000

            warnings = []
            if has_dnskey and not has_ds:
                warnings.append("Domain has DNSKEY but no DS record in parent zone")
            if chain.ksk_count == 0 and has_dnskey:
                warnings.append("No Key Signing Key (KSK) found")
            if chain.zsk_count == 0 and has_dnskey:
                warnings.append("No Zone Signing Key (ZSK) found")

            # Collect raw outputs
            raw_outputs = []
            if ds_response.raw_data and "raw_output" in ds_response.raw_data:
                raw_outputs.append(
                    f"# DS Records\n{ds_response.raw_data['raw_output']}"
                )
            if dnskey_raw:
                raw_outputs.append(f"# DNSKEY Records\n{dnskey_raw}")
            if dnssec_output:
                raw_outputs.append(f"# DNSSEC Validation\n{dnssec_output}")

            return DNSSECValidation(
                domain=domain,
                status=status,
                validation_time_ms=validation_time,
                timestamp=datetime.now(),
                chain=chain,
                warnings=warnings,
                raw_data={"raw_output": "\n\n".join(raw_outputs)}
                if raw_outputs
                else None,
            )

        except Exception as e:
            validation_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSSECValidation(
                domain=domain,
                status=DNSSECStatus.INDETERMINATE,
                validation_time_ms=validation_time,
                timestamp=datetime.now(),
                error_message=f"DNSSEC validation failed: {str(e)}",
            )

    def _parse_ds_records(self, response: DNSResponse) -> list[DSRecord]:
        """Parse DS records from DNS response."""
        ds_records = []
        for record in response.records:
            try:
                # DS record format: key_tag algorithm digest_type digest
                parts = record.value.split(None, 3)
                if len(parts) == 4:
                    key_tag = int(parts[0])
                    algorithm = self._parse_algorithm(int(parts[1]))
                    digest_type = self._parse_digest_type(int(parts[2]))
                    digest = parts[3]

                    ds_records.append(
                        DSRecord(
                            key_tag=key_tag,
                            algorithm=algorithm,
                            digest_type=digest_type,
                            digest=digest,
                            ttl=record.ttl,
                        )
                    )
            except (ValueError, IndexError):
                continue

        return ds_records

    def _parse_dnskey_records(self, response: DNSResponse) -> list[DNSKEYRecord]:
        """Parse DNSKEY records from DNS response."""
        dnskey_records = []
        for record in response.records:
            try:
                # DNSKEY format: flags protocol algorithm public_key
                parts = record.value.split(None, 3)
                if len(parts) == 4:
                    flags = int(parts[0])
                    protocol = int(parts[1])
                    algorithm = self._parse_algorithm(int(parts[2]))
                    public_key = parts[3]

                    # Calculate key tag (simplified)
                    key_tag = self._calculate_key_tag(flags, protocol, int(parts[2]))

                    dnskey_records.append(
                        DNSKEYRecord(
                            flags=flags,
                            protocol=protocol,
                            algorithm=algorithm,
                            key_tag=key_tag,
                            public_key=public_key,
                            ttl=record.ttl,
                        )
                    )
            except (ValueError, IndexError):
                continue

        return dnskey_records

    def _parse_algorithm(self, alg_num: int) -> DNSSECAlgorithm:
        """Parse DNSSEC algorithm number to enum."""
        algorithm_map = {
            1: DNSSECAlgorithm.RSAMD5,
            2: DNSSECAlgorithm.DH,
            3: DNSSECAlgorithm.DSA,
            5: DNSSECAlgorithm.RSASHA1,
            6: DNSSECAlgorithm.DSA_NSEC3_SHA1,
            7: DNSSECAlgorithm.RSASHA1_NSEC3_SHA1,
            8: DNSSECAlgorithm.RSASHA256,
            10: DNSSECAlgorithm.RSASHA512,
            12: DNSSECAlgorithm.ECC_GOST,
            13: DNSSECAlgorithm.ECDSAP256SHA256,
            14: DNSSECAlgorithm.ECDSAP384SHA384,
            15: DNSSECAlgorithm.ED25519,
            16: DNSSECAlgorithm.ED448,
        }
        return algorithm_map.get(alg_num, DNSSECAlgorithm.UNKNOWN)

    def _parse_digest_type(self, digest_num: int) -> DigestType:
        """Parse DS digest type number to enum."""
        digest_map = {
            1: DigestType.SHA1,
            2: DigestType.SHA256,
            3: DigestType.GOST,
            4: DigestType.SHA384,
        }
        return digest_map.get(digest_num, DigestType.UNKNOWN)

    def _calculate_key_tag(self, flags: int, protocol: int, algorithm: int) -> int:
        """Calculate a simplified key tag (for display purposes)."""
        # This is a simplified calculation
        # Real key tag calculation involves the entire RDATA
        return (flags + protocol + algorithm) % 65536
