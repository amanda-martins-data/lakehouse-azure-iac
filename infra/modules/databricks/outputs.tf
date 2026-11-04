output "workspace_id" {
  description = "ID do recurso do workspace no Azure."
  value       = azurerm_databricks_workspace.ws.id
}

output "workspace_url" {
  description = "URL do workspace, sem https://."
  value       = azurerm_databricks_workspace.ws.workspace_url
}

output "access_connector_id" {
  description = "ID do access connector."
  value       = azurerm_databricks_access_connector.uc.id
}

output "access_connector_principal_id" {
  description = "Principal da identidade gerenciada do access connector."
  value       = azurerm_databricks_access_connector.uc.identity[0].principal_id
}

output "workspace_numeric_id" {
  description = "ID numerico do workspace (usado na atribuicao de metastore)."
  value       = azurerm_databricks_workspace.ws.workspace_id
}
