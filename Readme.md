# Min light-version af Arflow

Denne komposition er mest tænkt som en udviklings version. Så den må gerne køre lidt tjept, starte hurtigt og ikke bruge for meget memory. Det er jo bare tre ting.

Opsætningen er baseret på 
* [Apache Airflows vejledning](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
  * Airflows officielle [docker-compise.yaml](https://airflow.apache.org/docs/apache-airflow/2.5.0/docker-compose.yaml), som kan hentes enten fra link på siden oven for, eller i [github projektet](https://github.com/apache/airflow) i mappen [`airflow/docs/apache-airflow/howto/docker-compose/`](https://github.com/apache/airflow/tree/main/docs/apache-airflow/howto/docker-compose)
* Desuden er jeg stærkt inspireret af Luis Guilherme Sousa de Oliveira's Capstone project [Average Temperature in Portugal in the last 20 years](https://github.com/guoliveira/data-engineer-zoomcamp-project), hvor han bl.a. laver en slanket Airflow [docker-compose.yaml](https://github.com/guoliveira/data-engineer-zoomcamp-project/blob/main/Airflow/docker-compose.yaml)

Jeg regner med at udviklings-setup'et kan køre i en enkelt tråd, dvs uden CeleryExecutor (multitråds executer), Uden celery, behøver vi ikke workers, eller redis. Jeg beholder PostgreSQL, fordi det ser ud til at køre dramatisk meget hurtigere, end med SqLite.


## Spinup


## Things done

se playbook.md