output "catalog_name" {
  description = "Catalogo criado."
  value       = databricks_catalog.lakehouse.name
}

output "schemas" {
  description = "Schemas por camada."
  value       = [for s in databricks_schema.layer : s.id]
}

output "job_id" {
  description = "ID do job bronze -> silver -> gold."
  value       = databricks_job.inmet.id
}
