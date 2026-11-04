output "key_vault_id" {
  description = "ID do Key Vault."
  value       = azurerm_key_vault.kv.id
}

output "key_vault_uri" {
  description = "URI do Key Vault."
  value       = azurerm_key_vault.kv.vault_uri
}

output "log_analytics_workspace_id" {
  description = "ID do workspace do Log Analytics."
  value       = azurerm_log_analytics_workspace.logs.id
}
