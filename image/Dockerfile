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


## Below is actually for another branch : integrate pip requirement in image, to load faster
#COPY requirements.txt .
#RUN python3 -m pip install --upgrade pip
#RUN python3 -m pip install --no-cache-dir -r requirements.txt

USER $AIRFLOW_UID

