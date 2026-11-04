# Workspace Premium (requisito do Unity Catalog) e o access connector:
# a identidade gerenciada que o Unity Catalog usa para ler e gravar no
# ADLS. Nenhum segredo de storage circula no codigo (ADR 0015).

resource "azurerm_databricks_workspace" "ws" {
  #checkov:skip=CKV_AZURE_158:Sem Private Link nesta versao; secure cluster connectivity ligado (ADR 0017)
  #checkov:skip=CKV2_AZURE_48:CMK do DBFS fica para producao; o dado do lake mora no ADLS, nao no DBFS
  name                        = var.workspace_name
  resource_group_name         = var.resource_group_name
  location                    = var.location
  sku                         = "premium"
  managed_resource_group_name = var.managed_resource_group_name

  public_network_access_enabled = true

  custom_parameters {
    # Secure cluster connectivity: os nos do cluster nao recebem IP
    # publico, mesmo sem VNet injection (ADR 0017).
    no_public_ip = true
  }

  tags = var.tags
}

resource "azurerm_databricks_access_connector" "uc" {
  name                = var.access_connector_name
  resource_group_name = var.resource_group_name
  location            = var.location

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
