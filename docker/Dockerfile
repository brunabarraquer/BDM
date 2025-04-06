FROM apache/airflow:2.8.1-python3.10

# Switch to root user for package installation
USER root

# Clean up apt lists and create missing directories for apt-get
RUN rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/lib/apt/lists/partial \
    && apt-get clean \
    && apt-get update

# Install system dependencies
RUN apt-get install -y \
    libtk8.6 \
    tcl8.6 \
    tk8.6 \
    python3-tk \
    default-jdk \
    wget \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    build-essential \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Install Spark with Delta Lake
ENV SPARK_VERSION=3.4.1
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/airflow/spark
ENV PATH $PATH:${SPARK_HOME}/bin

RUN mkdir -p ${SPARK_HOME} && \
    wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    tar xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz -C /tmp && \
    cp -r /tmp/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}/* ${SPARK_HOME}/ && \
    rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    rm -rf /tmp/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}

# Download Delta Lake JAR files
RUN mkdir -p ${SPARK_HOME}/jars && \
    wget -q https://repo1.maven.org/maven2/io/delta/delta-core_2.12/2.4.0/delta-core_2.12-2.4.0.jar -P ${SPARK_HOME}/jars/ && \
    wget -q https://repo1.maven.org/maven2/io/delta/delta-storage/2.4.0/delta-storage-2.4.0.jar -P ${SPARK_HOME}/jars/

# Set Spark environment variables
ENV PYTHONPATH=${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-*.zip:${PYTHONPATH}

# Copy the requirements.txt file
COPY --chown=airflow:root requirements.txt /opt/airflow/

# Switch back to the airflow user for pip installation
USER airflow

# Install Python dependencies as the airflow user
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /opt/airflow/requirements.txt && \
    pip install --no-cache-dir delta-spark==2.4.0 pyspark==${SPARK_VERSION}

# Keep user as airflow for final image
USER airflow