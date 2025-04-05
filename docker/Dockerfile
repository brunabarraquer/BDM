FROM apache/airflow:2.8.1-python3.10

# Switch to root user for package installation
USER root

# Clean up apt lists and create missing directories for apt-get
RUN rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/lib/apt/lists/partial \
    && apt-get clean \
    && apt-get update

# Install system dependencies including Tkinter and Java
RUN apt-get install -y \
    libtk8.6 \
    tcl8.6 \
    tk8.6 \
    python3-tk \
    openjdk-11-jdk \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Apache Spark (Version 3.1.1) and set up the environment variables
RUN wget https://archive.apache.org/dist/spark/spark-3.1.1/spark-3.1.1-bin-hadoop3.2.tgz && \
    tar xvf spark-3.1.1-bin-hadoop3.2.tgz -C /opt/ && \
    rm spark-3.1.1-bin-hadoop3.2.tgz

# Set Spark environment variables
ENV SPARK_HOME=/opt/spark-3.1.1-bin-hadoop3.2
ENV PATH=$SPARK_HOME/bin:$PATH
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PYSPARK_PYTHON=python3

# Copy the requirements.txt and install Python dependencies
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# Switch back to the airflow user
USER airflow
