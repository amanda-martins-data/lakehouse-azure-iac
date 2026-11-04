# Camada de plataforma do ambiente dev: tudo que o Azure Resource
# Manager cria. O catalogo (Unity Catalog) fica em ../catalog porque o
# provider do Databricks so consegue planejar depois que o workspace
# existe (ADR 0016).

data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

locals {
  suffix = random_string.suffix.result
  tags = merge(var.tags, {
    projeto  = "lakehouse-azure-iac"
    ambiente = "dev"
  })
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.prefix}-dev"
  location = var.location
  tags     = local.tags
}

module "storage" {
  source = "../../../modules/storage"

  name                = "st${var.prefix}dev${local.suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tags                = local.tags

  depends_on = [azurerm_role_assignment.deployer_blob_owner]
}

module "databricks" {
  source = "../../../modules/databricks"

  workspace_name              = "dbw-${var.prefix}-dev"
  managed_resource_group_name = "rg-${var.prefix}-dev-databricks"
  access_connector_name       = "ac-${var.prefix}-dev"
  resource_group_name         = azurerm_resource_group.rg.name
  location                    = azurerm_resource_group.rg.location
  tags                        = local.tags
}

module "security" {
  source = "../../../modules/security"

  key_vault_name      = "kv-${var.prefix}-dev-${local.suffix}"
  log_analytics_name  = "log-${var.prefix}-dev"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  storage_account_id  = module.storage.storage_account_id
  tags                = local.tags
}

# Quem roda o Terraform precisa de acesso de dados para criar os
# filesystems, porque a chave compartilhada da conta esta desligada.
resource "azurerm_role_assignment" "deployer_blob_owner" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = data.azurerm_client_config.current.object_id
}

# O Unity Catalog le e grava no lake com a identidade do access
# connector. E a unica identidade com escrita nas camadas.
resource "azurerm_role_assignment" "uc_blob_contributor" {
  scope                = module.storage.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.databricks.access_connector_principal_id
}

resource "azurerm_consumption_budget_resource_group" "monthly" {
  name              = "budget-${var.prefix}-dev"
  resource_group_id = azurerm_resource_group.rg.id
  amount            = var.monthly_budget
  time_grain        = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  notification {
    enabled        = true
    threshold      = 50
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = var.alert_emails
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Forecasted"
    contact_emails = var.alert_emails
  }
}
