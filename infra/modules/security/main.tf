# Key Vault para segredos que nao puderem ser substituidos por
# identidade gerenciada, e Log Analytics para auditar acesso ao
# Key Vault e ao storage.

resource "azurerm_key_vault" "kv" {
  #checkov:skip=CKV_AZURE_109:Sem firewall de rede nesta versao; acesso por RBAC (ADR 0017)
  #checkov:skip=CKV_AZURE_189:Acesso publico de rede mantido; controle por identidade (ADR 0017)
  #checkov:skip=CKV2_AZURE_32:Sem private endpoint nesta versao (ADR 0017)
  name                = var.key_vault_name
  resource_group_name = var.resource_group_name
  location            = var.location
  tenant_id           = var.tenant_id
  sku_name            = "standard"

  enable_rbac_authorization  = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 90

  # ADR 0017: acesso por identidade, sem rede privada nesta versao.
  public_network_access_enabled = true

  tags = var.tags
}

resource "azurerm_log_analytics_workspace" "logs" {
  name                = var.log_analytics_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  daily_quota_gb      = var.log_daily_quota_gb

  tags = var.tags
}

resource "azurerm_monitor_diagnostic_setting" "key_vault" {
  name                       = "kv-to-log-analytics"
  target_resource_id         = azurerm_key_vault.kv.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  enabled_log {
    category = "AuditEvent"
  }

  metric {
    category = "AllMetrics"
  }
}

# Leitura, escrita e exclusao de blobs no lake ficam registradas.
resource "azurerm_monitor_diagnostic_setting" "lake_blobs" {
  name                       = "lake-blobs-to-log-analytics"
  target_resource_id         = "${var.storage_account_id}/blobServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  enabled_log {
    category = "StorageRead"
  }

  enabled_log {
    category = "StorageWrite"
  }

  enabled_log {
    category = "StorageDelete"
  }

  metric {
    category = "Transaction"
  }
}
