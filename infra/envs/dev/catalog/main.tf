# Camada de catalogo do ambiente dev: Unity Catalog sobre o lake
# criado em ../platform. Roda depois da plataforma, com a URL do
# workspace e o access connector como entrada (ADR 0014 e 0016).

locals {
  account    = var.storage_account_name
  layers     = ["bronze", "silver", "gold"]
  layer_url  = { for l in concat(local.layers, ["managed"]) : l => "abfss://${l}@${local.account}.dfs.core.windows.net/" }
  principals = toset([var.data_engineers_group, var.data_analysts_group])
}

resource "databricks_metastore_assignment" "this" {
  count        = var.metastore_id == null ? 0 : 1
  metastore_id = var.metastore_id
  workspace_id = var.workspace_numeric_id
}

# Credencial de storage baseada na identidade gerenciada do access
# connector: o Unity Catalog nunca ve uma chave de conta.
resource "databricks_storage_credential" "lake" {
  name    = "cred-lakehouse-dev"
  comment = "Identidade gerenciada do access connector do ambiente dev."

  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }

  depends_on = [databricks_metastore_assignment.this]
}

resource "databricks_external_location" "layer" {
  for_each        = local.layer_url
  name            = "loc-${each.key}-dev"
  url             = each.value
  credential_name = databricks_storage_credential.lake.name
  comment         = "Camada ${each.key} do lakehouse dev."
}

resource "databricks_catalog" "lakehouse" {
  name         = var.catalog_name
  storage_root = databricks_external_location.layer["managed"].url
  comment      = "Lakehouse dev: dados publicos do INMET e do IBGE."

  properties = {
    ambiente = "dev"
    origem   = "lakehouse-azure-iac"
  }
}

resource "databricks_schema" "layer" {
  for_each     = toset(local.layers)
  catalog_name = databricks_catalog.lakehouse.name
  name         = each.value
  storage_root = databricks_external_location.layer[each.value].url
  comment      = "Camada ${each.value}."
}

# Quem pode usar o catalogo: os dois grupos.
resource "databricks_grants" "catalog" {
  catalog = databricks_catalog.lakehouse.name

  dynamic "grant" {
    for_each = local.principals
    content {
      principal  = grant.value
      privileges = ["USE_CATALOG"]
    }
  }
}

# Engenharia escreve em bronze e silver.
resource "databricks_grants" "engineering_layers" {
  for_each = toset(["bronze", "silver"])
  schema   = databricks_schema.layer[each.value].id

  grant {
    principal  = var.data_engineers_group
    privileges = ["USE_SCHEMA", "CREATE_TABLE", "MODIFY", "SELECT"]
  }
}

# Gold: engenharia publica, analistas so leem.
resource "databricks_grants" "gold" {
  schema = databricks_schema.layer["gold"].id

  dynamic "grant" {
    for_each = local.principals
    content {
      principal  = grant.value
      privileges = grant.value == var.data_engineers_group ? ["USE_SCHEMA", "CREATE_TABLE", "MODIFY", "SELECT"] : ["USE_SCHEMA", "SELECT"]
    }
  }
}

resource "databricks_grants" "external_locations" {
  for_each          = databricks_external_location.layer
  external_location = each.value.id

  grant {
    principal  = var.data_engineers_group
    privileges = ["READ_FILES", "WRITE_FILES", "CREATE_EXTERNAL_TABLE"]
  }
}
