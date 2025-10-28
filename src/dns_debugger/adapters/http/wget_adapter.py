"""HTTP adapter implementation using wget command (fallback)."""

import re
import subprocess
from datetime import datetime
from typing import Optional

from dns_debugger.domain.models.http_info import HTTPResponse, HTTPRedirect, HTTPMethod
from dns_debugger.domain.ports.http_port import HTTPPort


class WgetAdapter(HTTPPort):
    """Adapter for HTTP requests using wget command-line tool (fallback)."""

    def request(
        self,
        url: str,
        method: HTTPMethod = HTTPMethod.HEAD,
        follow_redirects: bool = True,
        timeout: int = 10,
    ) -> HTTPResponse:
        """Execute an HTTP request using wget."""
        start_time = datetime.now()

        # Build wget command
        cmd = [
            "wget",
            "--spider",  # Don't download, just check
            "--server-response",  # Show server response
            "-O",
            "/dev/null",  # Discard output
            "--timeout",
            str(timeout),
            url,
        ]

        if method == HTTPMethod.HEAD:
            cmd.insert(1, "--method=HEAD")

        if not follow_redirects:
            cmd.insert(1, "--max-redirect=0")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout + 5, check=False
            )

            # Parse wget output (goes to stderr)
            response = self._parse_wget_output(url, result.stderr, start_time)
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

    def _parse_wget_output(
        self, url: str, stderr: str, start_time: datetime
    ) -> HTTPResponse:
        """Parse wget stderr output into HTTPResponse."""
        query_time = (datetime.now() - start_time).total_seconds() * 1000

        lines = stderr.split("\n")

        # Parse HTTP responses
        headers = {}
        status_code = 0
        status_text = ""
        redirect_chain = []
        final_url = url

        for line in lines:
            # HTTP status line: "  HTTP/1.1 200 OK"
            if "HTTP/" in line and re.search(r"HTTP/[\d.]+ \d+", line):
                match = re.search(r"HTTP/[\d.]+ (\d+) (.+)", line)
                if match:
                    sc = int(match.group(1))
                    st = match.group(2).strip()

                    # If this is a redirect, save it
                    if 300 <= sc < 400 and status_code != 0:
                        redirect_chain.append(
                            HTTPRedirect(
                                from_url=url,
                                to_url=final_url,
                                status_code=status_code,
                                location_header="",
                            )
                        )

                    status_code = sc
                    status_text = st

            # Location header
            elif "Location:" in line:
                location = line.split("Location:", 1)[1].strip()
                final_url = location
                if redirect_chain and redirect_chain[-1]:
                    redirect_chain[-1].to_url = location
                    redirect_chain[-1].location_header = location

            # Parse headers (lines with colons)
            elif ":" in line and not line.strip().startswith("--"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    if key and not key.startswith("http"):
                        headers[key] = value

        # Extract specific headers
        content_length = None
        if "content-length" in headers:
            try:
                content_length = int(headers["content-length"])
            except ValueError:
                pass

        content_type = headers.get("content-type")
        server = headers.get("server")

        # Check for errors
        error = None
        if status_code == 0:
            # Look for wget error messages
            for line in lines:
                if "failed:" in line.lower() or "error" in line.lower():
                    error = line.strip()
                    break

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

    def check_url(self, url: str) -> HTTPResponse:
        """Quick check if a URL is accessible using HEAD request."""
        return self.request(url, method=HTTPMethod.HEAD)

    def is_available(self) -> bool:
        """Check if wget is available."""
        try:
            result = subprocess.run(
                ["which", "wget"], capture_output=True, timeout=5, check=False
            )
            return result.returncode == 0
        except:
            return False

    def get_tool_name(self) -> str:
        """Get the name of the HTTP tool."""
        return "wget"

    def get_version(self) -> Optional[str]:
        """Get the version of wget."""
        try:
            result = subprocess.run(
                ["wget", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            # wget version output: "GNU Wget 1.21.3 ..."
            match = re.search(r"Wget ([\d.]+)", result.stdout)
            return match.group(1) if match else None
        except:
            return None
