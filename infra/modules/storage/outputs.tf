output "storage_account_id" {
  description = "ID da conta de storage."
  value       = azurerm_storage_account.lake.id
}

output "storage_account_name" {
  description = "Nome da conta de storage."
  value       = azurerm_storage_account.lake.name
}

output "layer_urls" {
  description = "URL abfss de cada filesystem, por nome."
  value = {
    for name, fs in azurerm_storage_data_lake_gen2_filesystem.layer :
    name => "abfss://${fs.name}@${azurerm_storage_account.lake.name}.dfs.core.windows.net/"
  }
}
