# Playbook

All the things I've done... so far

## preliminary

Set the Airflow user using the following commands:

```bash
mkdir -p ./dags ./logs ./plugins
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

Men. Mapperne er i git-repo'et. `.env` skal også bruges til at importere, uden at lave et nyt docker image pypi pakker. Så jeg putter begge i git. (men AIRFLOW_UID skal opdateres...?)


Added `docker-compose.yaml` with

  curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.5.0/docker-compose.yaml'


Redigerede `docker-compose.yaml` 

 - fjernede services:
   - redis
   - airflow-worker
 - ændrede 
   - i x-airflow-common
     - AIRFLOW__CORE__EXECUTOR: LocalExecutor
     - AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
 - tilføjede
   - i x-airflow-common/volumes
     - `- ./data_out:/opt/airflow/data_out`


kører

    docker-compose up airflow-init

Den viser nogen 'Warnings', men er nok ok

og 
    
    docker-compose up 

## Shell script `airflow.sh`

Man kan opnå en terminal på ... ved at køre:

    ./airflow.sh bash

# CPU load

Jeg synes min maskine lagger ...

Efter lidt frem og tilbage har jeg indført 

    cpu_period: 50000
    cpu_quota: 25000
    deploy:
        resources:
        limits:
            memory: 640M

i `docker-compose.yaml`, under `x-airflow-common:`

`cpu_period: 50000`
: Betyder at hver container må bruge time slot på 50000 mikrosekunder; dvs 

$$ {50.000 \over 1.000.000} = {5 \over 100} =  0,05 \ sekund $$

[50000 / 1000000 = 0.05 sekund]:#

`cpu_quota: 25000`
: Betyder at containeren må bruge 25000 mikrosekunder af hvert timeslot, defineret i `cpu_period` til 50000.   
Altså 
$${25.000 \over 50.000} = 0,5 = 50 \\% $$  
 
[25000 / 50000 = 0.5 0 50%]: #
        
        
`memory: 640M`
: under 
    ```
    deploy:
        limits:
    ```
    betyder at hver container højest må bruge 640 MB ram.
    Hvis de går over genstarter de.  
    Det er måske ikke så nyttigt...

Se også 
* <https://medium.com/codex/how-to-limit-cpu-and-memory-usage-in-docker-containers-a024b429f55e>
* <https://www.baeldung.com/ops/docker-memory-limit>

## New folder `data` for output

kilder
: * <https://github.com/apache/airflow/blob/2c6c7fdb2308de98e142618836bdf414df9768c8/Dockerfile#L37>
  * <https://github.com/guoliveira/data-engineer-zoomcamp-project> 

Jeg vil gerne have en mappe `data` hvor mine airflow tasks kan gemme data. Det skal være et volume som kan ses fra værts systemet.

Jeg opretter volumet i docker-compose.yaml, med

    volumes:
      - ./data:/opt/airflow/data


men mappen for ikke de rigtige rettigheder, så den er ikke rigtig skrivbar indefra containeren...

Jeg tester med 

    $ ./airflow.sh bash
        Creating network "airflow_docker-compose_light_default" with the default driver
        Creating volume "airflow_docker-compose_light_postgres-db-volume" with default driver
        Creating airflow_docker-compose_light_postgres_1 ... done
        Creating airflow_docker-compose_light_airflow-cli_run ... done
        default@99248299431b:/opt/airflow$ 
        
    default@99248299431b:/opt/airflow$ls -l
        total 16
        drwxrwxr-x 3 default root 4096 Dec 15 09:39 dags
        drwxr-xr-x 2 root    root 4096 Dec 15 11:33 data
        drwxrwxr-x 6 default root 4096 Dec 14 15:37 logs
        drwxrwxr-x 2 default root 4096 Dec 14 09:47 plugins

Så jeg prøver med et nyt image arvet efter det gamle

`Dockerfile`:
```Dockerfile
# First-time build can take upto 10 mins.
# also inspired form https://github.com/guoliveira/data-engineer-zoomcamp-project
FROM apache/airflow:2.5.0

ARG AIRFLOW_HOME=/opt/airflow
ARG AIRFLOW_UID="50000"
ARG AIRFLOW_GID="50000"

WORKDIR $AIRFLOW_HOME

USER root

ARG AIRFLOW_HOME
ENV AIRFLOW_HOME=${AIRFLOW_HOME}

ENV AIRFLOW_UID=${AIRFLOW_UID}
ENV AIRFLOW_GID=${AIRFLOW_GID}

RUN umask 0002; \
    mkdir -pv "${AIRFLOW_HOME}/data";  \
    chown -R "airflow:root" "${AIRFLOW_HOME}/data"; \
    find "${AIRFLOW_HOME}" -executable -print0 | xargs --null chmod g+x && \
        find "${AIRFLOW_HOME}" -print0 | xargs --null chmod g+rw
#    chown -R "airflow:root" "${AIRFLOW_HOME}/data"; \
#    chmod ug=rwx "${AIRFLOW_HOME}/data"; 

USER $AIRFLOW_UID
```

og ændrer `docker-compose.yaml` til at bruge det nye image:

```yaml
x-airflow-common:
  &airflow-common
  # image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.5.0}
  build:
    context: .
    dockerfile: ./image/Dockerfile
```

Renser, laver nyt image og up'er med det:

Rens:

    docker-compose down --volumes --rmi local

Byg alt

    docker-compose build 

Byg `airflow-cli`
    
    docker-compose build airflow-cli

Kør cli (med `airflow.sh`)

    ./airflow.sh bash

Test

    ls -l

Men det virker ikke rigtigt...

WTF!?

### Hugh?!

GIver lidt op fordi det ikke virker, og kører lokalt:

    chmod -R ug+rw data
    sudo chown -R 100999 data