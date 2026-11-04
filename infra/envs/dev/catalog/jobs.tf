# Job bronze -> silver -> gold. O codigo vem direto do repositorio
# (git_source), entao o que roda no Databricks e exatamente o que o
# CI testou. O agendamento nasce pausado: nada roda sem decisao.

data "databricks_spark_version" "lts" {
  long_term_support = true
}

data "databricks_node_type" "smallest" {
  local_disk = true
}

locals {
  job_args = [
    "--input", "${local.layer_url["bronze"]}landing/inmet",
    "--reference", "${local.layer_url["bronze"]}landing/ibge/municipios.csv",
    "--bronze-root", local.layer_url["bronze"],
    "--silver-root", local.layer_url["silver"],
    "--gold-root", local.layer_url["gold"],
    "--catalog", databricks_catalog.lakehouse.name,
  ]
}

resource "databricks_job" "inmet" {
  name = "lakehouse-dev-inmet"

  git_source {
    url      = var.repo_url
    provider = "gitHub"
    branch   = var.repo_branch
  }

  job_cluster {
    job_cluster_key = "single_node"

    new_cluster {
      spark_version      = data.databricks_spark_version.lts.id
      node_type_id       = data.databricks_node_type.smallest.id
      num_workers        = 0
      data_security_mode = "SINGLE_USER"

      spark_conf = {
        "spark.databricks.cluster.profile" = "singleNode"
        "spark.master"                     = "local[*]"
      }

      custom_tags = {
        "ResourceClass" = "SingleNode"
      }
    }
  }

  task {
    task_key        = "bronze"
    job_cluster_key = "single_node"

    spark_python_task {
      python_file = "jobs/bronze_ingest.py"
      source      = "GIT"
      parameters  = local.job_args
    }
  }

  task {
    task_key        = "silver"
    job_cluster_key = "single_node"

    depends_on {
      task_key = "bronze"
    }

    spark_python_task {
      python_file = "jobs/silver_conform.py"
      source      = "GIT"
      parameters  = local.job_args
    }
  }

  task {
    task_key        = "gold"
    job_cluster_key = "single_node"

    depends_on {
      task_key = "silver"
    }

    spark_python_task {
      python_file = "jobs/gold_metrics.py"
      source      = "GIT"
      parameters  = local.job_args
    }
  }

  schedule {
    quartz_cron_expression = "0 0 6 * * ?"
    timezone_id            = "America/Sao_Paulo"
    pause_status           = "PAUSED"
  }
}
