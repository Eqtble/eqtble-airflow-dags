'''
## Pokemon DAG

Sample dag
'''

import json
from airflow import DAG
from airflow.configuration import conf
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.hooks.base import BaseHook
from airflow.models import Connection

from kubernetes.client import models as k8s

namespace = conf.get("kubernetes", "NAMESPACE")
# This will detect the default namespace locally and read the
# environment namespace when deployed to Astronomer.
if namespace == "default":
    config_file = "/usr/local/airflow/include/.kube/config"
    in_cluster = False
else:
    in_cluster = True
    config_file = None

snowflake_connection: Connection = BaseHook.get_connection("snowflake_sandbox")
snowflake_extra = json.loads(snowflake_connection.get_extra())

env_vars = {
    "DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE": snowflake_extra.get("database"),
    "DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD": snowflake_connection.password,
    "DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME": snowflake_connection.login,
    "DESTINATION__SNOWFLAKE__CREDENTIALS__HOST": snowflake_extra.get("host"),
    "DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE": snowflake_extra.get("warehouse"),
    "DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE": snowflake_extra.get("role"),
}

with DAG(
    dag_id="pokemon",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "UntitledDataCompany", "retries": 3},
    tags=["example"],
) as dag:
    import logging
    logging.info("Here is the update")
    KubernetesPodOperator(
        namespace=namespace,
        # image="eqtble_dlt:latest",
        image="ghcr.io/untitled-data-company/eqtable-dlt:main",
        image_pull_secrets=[k8s.V1LocalObjectReference("ghcr-login-secret")],
        # labels={"<pod-label>": "<label-name>"},
        name="airflow-pokemon",
        task_id="task-one",
        in_cluster=in_cluster,  # if set to true, will look in the cluster, if false, looks for file
        cluster_context="docker-desktop",  # is ignored when in_cluster is set to True
        config_file=config_file,
        is_delete_operator_pod=True,
        get_logs=True,
        image_pull_policy="Always",  # IfNotPresent to avoid pulling image from the non-existing local registry
        env_vars=env_vars,
        arguments=["pokemon_pipeline.py"],
    )
