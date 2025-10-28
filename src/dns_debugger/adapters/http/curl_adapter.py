"""HTTP adapter implementation using curl command."""

import json
import re
import subprocess
from datetime import datetime
from typing import Optional

from dns_debugger.domain.models.http_info import HTTPResponse, HTTPRedirect, HTTPMethod
from dns_debugger.domain.ports.http_port import HTTPPort


class CurlAdapter(HTTPPort):
    """Adapter for HTTP requests using curl command-line tool."""

    def request(
        self,
        url: str,
        method: HTTPMethod = HTTPMethod.HEAD,
        follow_redirects: bool = True,
        timeout: int = 10,
    ) -> HTTPResponse:
        """Execute an HTTP request using curl."""
        start_time = datetime.now()

        # Build curl command
        cmd = [
            "curl",
            "-s",  # Silent
            "-S",  # Show errors
            "-L" if follow_redirects else "",  # Follow redirects
            "-I" if method == HTTPMethod.HEAD else "",  # HEAD request
            "-X",
            method.value,  # HTTP method
            "-w",
            json.dumps(
                {  # Write out format (JSON)
                    "status_code": "%{http_code}",
                    "final_url": "%{url_effective}",
                    "redirect_count": "%{num_redirects}",
                    "total_time": "%{time_total}",
                    "content_type": "%{content_type}",
                }
            ),
            "--max-time",
            str(timeout),
            "--connect-timeout",
            str(timeout),
            url,
        ]

        # Remove empty strings
        cmd = [c for c in cmd if c]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout + 5, check=False
            )

            # Parse curl output
            response = self._parse_curl_output(
                url, result.stdout, result.stderr, start_time
            )
            return response

        except subprocess.TimeoutExpired:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return HTTPResponse(
                url=url,
                final_url=url,
                status_code=0,
                status_text="Timeout",
                response_time_ms=query_time,
                redirect_chain=[],
                headers={},
                content_length=None,
                content_type=None,
                server=None,
                timestamp=datetime.now(),
                error=f"Request timed out after {timeout}s",
            )
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return HTTPResponse(
                url=url,
                final_url=url,
                status_code=0,
                status_text="Error",
                response_time_ms=query_time,
                redirect_chain=[],
                headers={},
                content_length=None,
                content_type=None,
                server=None,
                timestamp=datetime.now(),
                error=str(e),
            )

    def _parse_curl_output(
        self, url: str, stdout: str, stderr: str, start_time: datetime
    ) -> HTTPResponse:
        """Parse curl output into HTTPResponse."""
        query_time = (datetime.now() - start_time).total_seconds() * 1000

        # Split headers from the JSON stats at the end
        lines = stdout.strip().split("\n")

        # Last line should be our JSON stats
        stats = {}
        try:
            if lines and lines[-1].startswith("{"):
                stats = json.loads(lines[-1])
                lines = lines[:-1]  # Remove stats from headers
        except json.JSONDecodeError:
            pass

        # Parse headers
        headers = {}
        status_code = 0
        status_text = ""
        redirect_chain = []

        # Parse HTTP response sections (can be multiple due to redirects)
        current_section = []
        for line in lines:
            if line.startswith("HTTP/"):
                if current_section:
                    # Process previous section as a redirect
                    sc, st = self._parse_status_line(current_section[0])
                    if 300 <= sc < 400:
                        location = self._extract_header(current_section, "Location")
                        if location:
                            redirect_chain.append(
                                HTTPRedirect(
                                    from_url=url
                                    if not redirect_chain
                                    else redirect_chain[-1].to_url,
                                    to_url=location,
                                    status_code=sc,
                                    location_header=location,
                                )
                            )
                current_section = [line]
            elif line.strip():
                current_section.append(line)

        # Parse final section (actual response)
        if current_section:
            status_code, status_text = self._parse_status_line(current_section[0])
            headers = self._parse_headers(current_section[1:])

        # Extract specific headers
        content_length = None
        if "content-length" in headers:
            try:
                content_length = int(headers["content-length"])
            except ValueError:
                pass

        content_type = stats.get("content_type") or headers.get("content-type")
        server = headers.get("server")

        final_url = stats.get("final_url", url)

        # Check for errors in stderr
        error = None
        if stderr and "curl:" in stderr:
            error = stderr.strip()

        return HTTPResponse(
            url=url,
            final_url=final_url,
            status_code=status_code,
            status_text=status_text,
            response_time_ms=query_time,
            redirect_chain=redirect_chain,
            headers=headers,
            content_length=content_length,
            content_type=content_type,
            server=server,
            timestamp=datetime.now(),
            error=error,
        )

    def _parse_status_line(self, line: str) -> tuple[int, str]:
        """Parse HTTP status line."""
        # Format: HTTP/1.1 200 OK
        match = re.match(r"HTTP/[\d.]+ (\d+) (.+)", line)
        if match:
            return int(match.group(1)), match.group(2).strip()
        return 0, "Unknown"

    def _parse_headers(self, lines: list[str]) -> dict[str, str]:
        """Parse HTTP headers."""
        headers = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        return headers

    def _extract_header(self, lines: list[str], header_name: str) -> Optional[str]:
        """Extract a specific header value."""
        for line in lines[1:]:  # Skip status line
            if ":" in line:
                key, value = line.split(":", 1)
                if key.strip().lower() == header_name.lower():
                    return value.strip()
        return None

    def check_url(self, url: str) -> HTTPResponse:
        """Quick check if a URL is accessible using HEAD request."""
        return self.request(url, method=HTTPMethod.HEAD)

    def is_available(self) -> bool:
        """Check if curl is available."""
        try:
            result = subprocess.run(
                ["which", "curl"], capture_output=True, timeout=5, check=False
            )
            return result.returncode == 0
        except:
            return False

    def get_tool_name(self) -> str:
        """Get the name of the HTTP tool."""
        return "curl"

    def get_version(self) -> Optional[str]:
        """Get the version of curl."""
        try:
            result = subprocess.run(
                ["curl", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            # curl version output: "curl 7.64.1 ..."
            match = re.search(r"curl ([\d.]+)", result.stdout)
            return match.group(1) if match else None
        except:
            return None
