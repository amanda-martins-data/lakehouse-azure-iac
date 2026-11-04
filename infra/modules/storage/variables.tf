variable "name" {
  description = "Nome da conta de storage (3 a 24 caracteres, minusculas e numeros, unico no Azure)."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.name))
    error_message = "O nome deve ter de 3 a 24 caracteres, apenas letras minusculas e numeros."
  }
}

variable "resource_group_name" {
  description = "Resource group onde a conta sera criada."
  type        = string
}

variable "location" {
  description = "Regiao do Azure."
  type        = string
}

variable "replication_type" {
  description = "Replicacao da conta. LRS e suficiente para dev; ver ADR 0016 para producao."
  type        = string
  default     = "LRS"

  validation {
    condition     = contains(["LRS", "ZRS", "GRS", "GZRS"], var.replication_type)
    error_message = "Use LRS, ZRS, GRS ou GZRS."
  }
}

variable "layers" {
  description = "Filesystems criados na conta: as tres camadas e o espaco de tabelas gerenciadas do catalogo."
  type        = list(string)
  default     = ["bronze", "silver", "gold", "managed"]
}

variable "soft_delete_days" {
  description = "Dias de retencao para blobs e containers apagados."
  type        = number
  default     = 7
}

variable "bronze_cool_after_days" {
  description = "Dias sem modificacao ate o dado bronze ir para a camada cool."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags aplicadas a todos os recursos."
  type        = map(string)
  default     = {}
}
