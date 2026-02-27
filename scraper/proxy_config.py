"""
Proxy pool configuration for scraping.

To add proxies:
1. Free rotating proxies: https://free-proxy-list.net/
2. Paid services: Oxylabs, Brightdata, Smartproxy
3. Format: "http://username:password@host:port" or "http://host:port"

Example:
PROXY_POOL = [
    "http://proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:3128",
    "socks5://proxy3.example.com:1080",
]
"""

# Add your proxy URLs here
PROXY_POOL: list[str] = [
    # Example (uncomment and replace with real proxies):
    # "http://proxy1.example.com:8080",
    # "http://proxy2.example.com:8080",
]

# Proxy rotation strategy
PROXY_ROTATION_STRATEGY = "round_robin"  # Options: round_robin, random, sticky_domain

# Health check settings
PROXY_HEALTH_CHECK_ENABLED = True
PROXY_HEALTH_CHECK_URL = "https://httpbin.org/ip"
PROXY_HEALTH_CHECK_INTERVAL_MINUTES = 30
