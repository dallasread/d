# Application Panels Guide

This document describes each panel in the DNS debugger application. Always read/write code comments for implementation details.

## General Principles

**Fast:** All backend commands are executed with cache-busting flags to ensure fresh, authoritative results:
- DNS queries use `+nocache` or equivalent flags
- HTTP requests use cache control headers
- Results reflect current real-world state, not cached values
- All queries have a max runtime of 5 seconds

**Result Sharing:** Command results are shared between tools and panels to improve performance:
- Cache results by domain
- Cache is busted upon refresh
- Multiple panels (e.g., Dashboard, DNS) read from shared stores
- This prevents redundant backend queries while maintaining data freshness

**Separate data from interface:** Let's keep data separate from how it is displayed because this application will have several mediums to display the data.

---

## Dashboard

### Purpose

The purpose of this panel is to provide a quick overview of the domain's health across all diagnostic categories. It aggregates data from other panels to show summary metrics and status indicators.

### Tools

- None (aggregates data from other panels)

---

## Registration

### Purpose

The purpose of this panel is to diagnose domain registration details including registrar information, current status, current delegation, current expiration status at the registrar level.

### Tools

- `whois`

---

## DNS

### Purpose

The purpose of this panel is to show the current DNS records for common domain setups (email, blog, www, apex), displaying values, TTLs, and query performance metrics.

### Tools

- `dig`

---

## DNSSEC

### Purpose

The purpose of this panel is to show the state of DNSSEC for the domain. This is done by validating the DNSSEC chain of trust from the root zone down to the target domain, showing the complete cryptographic chain and identifying any breaks or misconfigurations. We query authoritative name servers each step of the way, generally with +short for performance reasons.

The cryptographic chain is established by the keytags on the DS records of the parent zone and the DNSKEY records of the child zone. This calculation is made recursively from the root zone to the target zone.

### Tools

- `dig`

---

## Certificate

### Purpose

The purpose of this panel is show the status of the SSL reported for the domain. If available, we show validity dates, subject alternative names (SANs), chain validation status, and certificate chain.

### Tools

- `openssl s_client`

---

## HTTP

### Purpose

The purpose of this panel is to diagnose HTTP and HTTPS connectivity for both the apex domain and www subdomain. We want to see the status codes, response times, redirect chains (status + location), and important headers like Server, Content-Type, and Content-Length.

This allows us to identify:
- If the domain redirects HTTP to HTTPS
- If the apex domain redirects to www or vice versa
- Response times for each protocol and subdomain
- Complete redirect chains showing all intermediate hops

### Tools

- `curl`

---

## Email

### Purpose

The purpose of this panel is to diagnose email authentication via SPF record validation, DMARC policy check, DKIM public key lookup, and MX record validation.

### Tools

- `dig`

---

## Logs

### Purpose

The purpose of this panel is to provide complete transparency into all backend commands executed during diagnostics, enabling users to learn the underlying tools and debug issues independently.

### Tools

- None (displays logs of other tools)

---

## Architecture Notes

### Why External Tools?

All panels use external command-line tools rather than DNS libraries because:
1. **Transparency** - Users can see and replicate exact commands
2. **Flexibility** - Tools like `dig` have years of edge-case handling
3. **Education** - Logs teach users how to debug DNS themselves
4. **Portability** - No need to bundle complex libraries
5. **Raw Access** - Get exact output format needed (e.g., `dig +multi` for DNSSEC key tags)

### Caching Strategy

- **DNS records** - Cached by domain (fast queries, but cache prevents redundant requests)
- **WHOIS** - Heavy cache (data changes infrequently)
- **DNSSEC** - Cache validation results (slow to compute, 5-10s)
- **Certificates** - Cache (changes infrequently)
- **HTTP** - Light cache (status codes can change)
- **Logs** - Never cleared (persist for session)

### Loading States

All queries run in parallel (except DNSSEC internal queries which must be sequential). The `LoadingProgress` component shows real-time status of each query type with sub-query details.

**Critical Path:** DNSSEC is always slowest (5-10s) due to sequential root → TLD → domain queries required by DNSSEC chain validation.
