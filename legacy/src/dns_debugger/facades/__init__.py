"""Facades for separating data fetching from display logic."""

from dns_debugger.facades.dashboard_facade import (
    DashboardFacade,
    HTTPHealthData,
    CertHealthData,
    DNSHealthData,
    RegistryHealthData,
    DNSSECHealthData,
    EmailHealthData,
)

__all__ = [
    "DashboardFacade",
    "HTTPHealthData",
    "CertHealthData",
    "DNSHealthData",
    "RegistryHealthData",
    "DNSSECHealthData",
    "EmailHealthData",
]
