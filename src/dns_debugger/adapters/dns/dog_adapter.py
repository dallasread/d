"""DNS adapter implementation using the 'dog' command."""

import json
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


class DogAdapter(DNSPort):
    """Adapter for the 'dog' DNS client.

    dog is a modern DNS client with colorful output and JSON support.
    https://dns.lookup.dog/
    """

    def query(
        self, domain: str, record_type: RecordType, resolver: Optional[str] = None
    ) -> DNSResponse:
        """Execute a DNS query using dog."""
        start_time = datetime.now()
        query_obj = DNSQuery(domain=domain, record_type=record_type, resolver=resolver)

        # Build dog command
        cmd = ["dog", domain, record_type.value, "--json"]
        if resolver:
            cmd.extend(["@", resolver])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=True
            )

            # Parse JSON output from dog
            data = json.loads(result.stdout)
            records = self._parse_dog_output(data, domain, record_type)

            query_time = (datetime.now() - start_time).total_seconds() * 1000
            resolver_used = resolver or "system"

            return DNSResponse(
                query=query_obj,
                records=records,
                query_time_ms=query_time,
                resolver_used=resolver_used,
                timestamp=datetime.now(),
                has_dnssec=False,  # TODO: Parse DNSSEC info from dog output
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
        except json.JSONDecodeError as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used=resolver or "system",
                timestamp=datetime.now(),
                error=f"Failed to parse dog output: {str(e)}",
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

    def _parse_dog_output(
        self, data: dict, domain: str, record_type: RecordType
    ) -> list[DNSRecord]:
        """Parse dog JSON output into DNSRecord objects."""
        records = []

        # dog JSON format has an "answers" section
        answers = data.get("answers", [])

        for answer in answers:
            record = DNSRecord(
                name=answer.get("name", domain),
                record_type=record_type,
                value=answer.get("data", ""),
                ttl=answer.get("ttl", 0),
                record_class=answer.get("class", "IN"),
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
        return self.query(ip_address, RecordType.PTR)

    def trace(self, domain: str) -> list[DNSResponse]:
        """Trace the DNS resolution path from root servers."""
        # TODO: Implement DNS tracing
        # This requires iterative queries starting from root servers
        raise NotImplementedError("DNS tracing not yet implemented")

    def is_available(self) -> bool:
        """Check if dog is available on the system."""
        try:
            subprocess.run(
                ["dog", "--version"], capture_output=True, timeout=5, check=True
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def get_tool_name(self) -> str:
        """Get the name of the DNS tool."""
        return "dog"

    def get_version(self) -> Optional[str]:
        """Get the version of dog."""
        try:
            result = subprocess.run(
                ["dog", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            # dog version output is like "dog 0.1.0"
            return result.stdout.strip().split()[-1]
        except Exception:
            return None

    def query_dnskey_with_keytag(self, domain: str) -> tuple[list[DNSKEYRecord], str]:
        """Query DNSKEY records with proper key tag parsing.

        Note: Dog's JSON output doesn't include key tags, so we fall back to dig +multi
        for accurate key tag parsing.

        Returns:
            Tuple of (list of DNSKEYRecord objects, raw output string)
        """
        start_time = datetime.now()

        try:
            # Use dig +multi to get key tags in comments
            # This is a fallback since dog doesn't expose key tags
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

    def _get_parent_zones(self, domain: str) -> list[str]:
        """Get list of parent zones from domain up to root.

        Args:
            domain: The domain to analyze (e.g., "www.example.com")

        Returns:
            List of parent zones (e.g., ["com", "."] for "example.com")
        """
        parts = domain.rstrip(".").split(".")
        zones = []

        # Build parent zones from TLD up to root
        if len(parts) >= 2:
            # TLD (e.g., "com")
            zones.append(parts[-1])

        # Always add root
        zones.append(".")

        return zones

    def _query_zone_data(self, zone_name: str, child_domain: str) -> ZoneData:
        """Query DNSSEC data for a specific zone.

        Args:
            zone_name: The zone to query (e.g., "com", ".")
            child_domain: The child domain to get DS records for

        Returns:
            ZoneData with DNSKEY and DS records for this zone
        """
        # Query DNSKEY records for this zone
        dnskey_response = self.query(zone_name, RecordType.DNSKEY)
        dnskey_records = self._parse_dnskey_records(dnskey_response)

        # Query DS records for the child domain from this zone's perspective
        # DS records for child are published in parent zone
        ds_response = self.query(child_domain, RecordType.DS)
        ds_records = self._parse_ds_records(ds_response)

        return ZoneData(
            zone_name=zone_name,
            dnskey_records=dnskey_records,
            ds_records=ds_records,
            rrsig_records=[],  # TODO: Parse RRSIG if needed
        )

    def validate_dnssec(self, domain: str) -> DNSSECValidation:
        """Validate DNSSEC for a domain.

        Args:
            domain: The domain to validate

        Returns:
            DNSSECValidation with validation results
        """
        start_time = datetime.now()

        try:
            # Query for DNSSEC-related records for target domain
            ds_response = self.query(domain, RecordType.DS)
            dnskey_records, dnskey_raw = self.query_dnskey_with_keytag(domain)

            # Query A record with DNSSEC validation
            # Note: dog doesn't have built-in DNSSEC validation like delv
            # We check for presence of DNSSEC records

            has_ds = ds_response.is_success and ds_response.record_count > 0
            has_dnskey = len(dnskey_records) > 0

            # Parse DNSSEC records
            ds_records = self._parse_ds_records(ds_response)

            # Try to get RRSIG records for SOA (always exists)
            rrsig_records = []
            try:
                # Query for SOA record and look for RRSIG in additional section
                cmd = ["dog", domain, "SOA", "--json"]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10, check=True
                )
                data = json.loads(result.stdout)
                # Check if there are RRSIG records in the response
                # This is tool-dependent and may need adjustment
                has_rrsig = "additional" in data and any(
                    r.get("type") == "RRSIG" for r in data.get("additional", [])
                )
            except Exception:
                has_rrsig = False

            # Build complete recursive DNSSEC chain from root to leaf
            # For a.b.c.d.com, we need: . -> com -> d.com -> c.d.com -> b.c.d.com -> a.b.c.d.com
            parent_zones = []
            parts = domain.rstrip(".").split(".")

            # Build the full chain recursively
            # Start with root, then build each level down to the target

            # Always query root zone
            try:
                # Root zone DNSKEY
                root_dnskey_records, _ = self.query_dnskey_with_keytag(".")

                # DS records for TLD in root zone
                tld = parts[-1]
                root_ds_response = self.query(tld, RecordType.DS)
                root_ds_records = self._parse_ds_records(root_ds_response)

                root_zone = ZoneData(
                    zone_name=".",
                    dnskey_records=root_dnskey_records,
                    ds_records=root_ds_records,  # DS for TLD
                    rrsig_records=[],
                )
                parent_zones.append(root_zone)
            except Exception:
                pass

            # Now build each level from TLD down to parent of target
            # For example.com: query com zone
            # For a.b.example.com: query com, then example.com, then b.example.com
            for i in range(len(parts) - 1, 0, -1):
                # Build the current zone name
                current_zone = ".".join(parts[i:])
                # Build the child zone name (what this zone delegates to)
                child_zone = ".".join(parts[i - 1 :])

                try:
                    # DNSKEY for current zone
                    zone_dnskey_records, _ = self.query_dnskey_with_keytag(current_zone)

                    # DS records for child zone (published in current zone)
                    zone_ds_response = self.query(child_zone, RecordType.DS)
                    zone_ds_records = self._parse_ds_records(zone_ds_response)

                    zone_data = ZoneData(
                        zone_name=current_zone,
                        dnskey_records=zone_dnskey_records,
                        ds_records=zone_ds_records,  # DS for child
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

            return DNSSECValidation(
                domain=domain,
                status=status,
                validation_time_ms=validation_time,
                timestamp=datetime.now(),
                chain=chain,
                warnings=warnings,
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
