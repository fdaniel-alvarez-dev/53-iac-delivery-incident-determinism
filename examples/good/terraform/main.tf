locals {
  service_name = "onchain-gateway"
  environment  = "staging"
}

# This file is intentionally small and sanitized. The validator focuses on patterns that reduce drift:
# - version pinning
# - remote backend
# - lockfile presence

