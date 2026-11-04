terraform {
  required_version = ">= 1.6"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.62"
    }
  }
}

# Autentica com a mesma identidade do Azure CLI usada em ../platform.
provider "databricks" {
  host      = "https://${var.workspace_url}"
  auth_type = "azure-cli"
}
