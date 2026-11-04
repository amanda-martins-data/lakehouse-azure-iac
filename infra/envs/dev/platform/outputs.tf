output "resource_group_name" {
  description = "Resource group do ambiente."
  value       = azurerm_resource_group.rg.name
}

output "storage_account_name" {
  description = "Conta de storage do lake."
  value       = module.storage.storage_account_name
}

output "layer_urls" {
  description = "URLs abfss das camadas."
  value       = module.storage.layer_urls
}

output "workspace_url" {
  description = "URL do workspace do Databricks. Entrada do ambiente ../catalog."
  value       = module.databricks.workspace_url
}

output "workspace_numeric_id" {
  description = "ID numerico do workspace. Entrada opcional do ambiente ../catalog."
  value       = module.databricks.workspace_numeric_id
}

output "access_connector_id" {
  description = "Access connector do Unity Catalog. Entrada do ambiente ../catalog."
  value       = module.databricks.access_connector_id
}

output "key_vault_uri" {
  description = "URI do Key Vault."
  value       = module.security.key_vault_uri
}
