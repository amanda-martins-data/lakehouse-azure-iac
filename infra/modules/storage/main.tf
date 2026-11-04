# ADLS Gen2 do lakehouse: uma conta com namespace hierarquico e um
# filesystem por camada. O acesso e sempre por identidade (Entra ID):
# chave compartilhada desligada, nenhum container publico.

resource "azurerm_storage_account" "lake" {
  # Excecoes conscientes, cada uma com a decisao que a justifica:
  #checkov:skip=CKV_AZURE_59:Acesso publico de rede mantido; o controle e por identidade (ADR 0017)
  #checkov:skip=CKV2_AZURE_33:Sem private endpoint nesta versao (ADR 0017)
  #checkov:skip=CKV_AZURE_206:LRS em dev por custo; replication_type e variavel para outros ambientes
  #checkov:skip=CKV2_AZURE_1:Chave gerenciada pela Microsoft + criptografia de infraestrutura; CMK fica para producao
  #checkov:skip=CKV_AZURE_33:A conta nao usa Queue service; auditoria do blob vai para o Log Analytics
  name                     = var.name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = var.replication_type
  is_hns_enabled           = true

  min_tls_version                   = "TLS1_2"
  https_traffic_only_enabled        = true
  allow_nested_items_to_be_public   = false
  shared_access_key_enabled         = false
  infrastructure_encryption_enabled = true
  default_to_oauth_authentication   = true
  local_user_enabled                = false

  # ADR 0017: sem VNet injection nesta versao. O acesso publico fica
  # restrito por identidade (RBAC + Unity Catalog), nao por rede.
  public_network_access_enabled = true

  blob_properties {
    delete_retention_policy {
      days = var.soft_delete_days
    }
    container_delete_retention_policy {
      days = var.soft_delete_days
    }
  }

  tags = var.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "layer" {
  for_each           = toset(var.layers)
  name               = each.value
  storage_account_id = azurerm_storage_account.lake.id
}

# Dado bruto raramente e relido depois de virar silver: vai para a
# camada fria apos N dias sem modificacao.
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.lake.id

  rule {
    name    = "bronze-para-cool"
    enabled = true

    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["bronze/"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than = var.bronze_cool_after_days
      }
    }
  }
}
