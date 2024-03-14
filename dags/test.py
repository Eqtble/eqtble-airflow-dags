import json
from airflow import DAG
from airflow.configuration import conf
from airflow.hooks.base import BaseHook
from airflow.models import Connection
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime, duration
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

namespace = conf.get("kubernetes", "NAMESPACE")
# This will detect the default namespace locally and read the
# environment namespace when deployed to Astronomer.
if namespace == "default":
    config_file = "/usr/local/airflow/include/.kube/config"
    in_cluster = False
else:
    in_cluster = True
    config_file = None

    

with DAG(
    dag_id="greenhouse_eqtble_sandbox2",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    doc_md=__doc__,
    default_args={"owner": "Astro", "retries": 3},
    tags=["example"],
) as dag:
    
    def importing_connections(ti):
        workable_connection = BaseHook.get_connection("workable_eqtble_sandbox")
        greenhouse_connection = BaseHook.get_connection("greenhouse_eqtble_sandbox")
        snowflake_connection = SnowflakeHook.get_connection("snowflake_sandbox")
        snowflake_extra = json.loads(snowflake_connection.get_extra())
        ti.xcom_push(key="SOURCES__GREENHOUSE__ACCESS_TOKEN", value= greenhouse_connection.password)
        ti.xcom_push(key="SOURCES__WORKABLE__ACCESS_TOKEN", value= workable_connection.password)
        ti.xcom_push(key="SOURCES__WORKABLE__SUBDOMAIN", value= greenhouse_connection.password)
        ti.xcom_push(key="DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE", value= snowflake_extra.get("database"))
        ti.xcom_push(key="DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD", value=snowflake_connection.password)
        ti.xcom_push(key="DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME", value= snowflake_connection.login)
        ti.xcom_push(key="DESTINATION__SNOWFLAKE__CREDENTIALS__HOST", value= snowflake_extra.get("host"))
        ti.xcom_push(key="DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE", value= snowflake_extra.get("warehouse"))
        ti.xcom_push(key="DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE", value= snowflake_extra.get("role"))

        return None


    task1= PythonOperator(task_id="connection_imports", python_callable=importing_connections)

    k = kubernetesPodOperator(
        namespace=namespace,
        image="eqtble_dlt:latest",
        # labels={"<pod-label>": "<label-name>"},
        name="airflow-test-pod",
        task_id="task-one",
        in_cluster=in_cluster,  # if set to true, will look in the cluster, if false, looks for file
        cluster_context="docker-desktop",  # is ignored when in_cluster is set to True
        config_file=config_file,
        is_delete_operator_pod=True,
        get_logs=True,
        image_pull_policy="IfNotPresent",  # crucial to avoid pulling image from the non-existing local registry
        env_vars={
            "SOURCES__GREENHOUSE__ACCESS_TOKEN": "{{ti.xcom_pull(task_ids='connection_imports', key='SOURCES__GREENHOUSE__ACCESS_TOKEN')}}",
            "SOURCES__WORKABLE__ACCESS_TOKEN": "{{ti.xcom_pull(task_ids='connection_imports', key='SOURCES__WORKABLE__ACCESS_TOKEN')}}",
            "SOURCES__WORKABLE__SUBDOMAIN": "{{ti.xcom_pull(task_ids='connection_imports', key='SOURCES__WORKABLE__SUBDOMAIN')}}",
            "DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE": "{{ti.xcom_pull(task_ids='connection_imports', key='DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE')}}",
            "DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD": "{{ti.xcom_pull(task_ids='connection_imports', key='DESTINATION__SNOWFLAKE__CREDENTIALS__PASSWORD')}}",
            "DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME": "{{ti.xcom_pull(task_ids='connection_imports', key='DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME')}}",
            "DESTINATION__SNOWFLAKE__CREDENTIALS__HOST": "{{ti.xcom_pull(task_ids='connection_imports', key='DESTINATION__SNOWFLAKE__CREDENTIALS__HOST')}}",
            "DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE": "{{ti.xcom_pull(task_ids='connection_imports', key='DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE')}}",
            "DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE": "{{ti.xcom_pull(task_ids='connection_imports', key='DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE')}}"
        },
        arguments=["greenhouse_pipeline.py"],
    )
 