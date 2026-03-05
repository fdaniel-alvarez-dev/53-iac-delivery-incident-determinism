terraform {
  # Anti-patterns on purpose:
  # - no required_version
  # - no provider pinning
  backend "local" {}
}

