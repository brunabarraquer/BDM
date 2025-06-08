
# Project BDM  
*The Data Management Stages of the BDM Project*

## Overview

This project sets up a Dockerized environment to run a user interface for managing end-to-end data pipelines, from data ingestion and preparation to the consumption layer for product visualization.

The focus is on implementing a robust **Data Management** layer using a **Data Lakehouse** architecture (with **Delta Lake**), and building a frotend with **Streamlit**.


## 📁 Project Structure

### 1. `docker/`

This folder contains the necessary configuration files to build and run Docker services:

- **`docker-compose.yml`**: Defines the services and how they interact.
- **`Dockerfile`**: Builds the Apache Airflow service and installs necessary dependencies.
- **`requirements.txt`**: Lists all Python packages required to run the project.

---

### 2. `Project_1/`

This folder contains the core functionality for Part 1 of the project.

#### **`UI.py`**

A graphical interface (script-based) with four main functions accessible via buttons:

---

### 🟩 **Start Batch Ingestion, Data Enrichment & Data Preparation**  
**Status:** Enabled by default  

**Functionality:**  
Runs a end-to-end pipeline that:
- Creates necessary folders for the Data Management process.
- Extracts data from various APIs.
- Saves data in the **Temporal Zone** (`Data Management/Landing Zone/Temporal Zone`).
- Organizes data in the **Persistent Zone** (`Data Management/Landing Zone/Persistent Zone`) using **Delta Lake**.
- Cleans data and stored in the **Trusted Zone**.
- Generates KPIs and distributes data into the **Exploitation Zone**.

**Display:**
- **Left terminal:** Shows the progress of the data pipeline.
- **Right terminal:** Displays real-time monitoring logs.

**Notes:**
- The Temporal Zone ingestion works regardless of environment settings.
- Storing data in Delta Lake requires local configuration (e.g., `JAVA_HOME`, `HADOOP_HOME`, `SPARK_HOME`).
- Alternatively, using Apache Airflow inside Docker handles Delta storage correctly (see docs for usage).

---

### 🔴 **Start Streaming Ingestion (Hot Path)**  
**Status:** Enabled by default  

**Functionality:**  
Simulates real-time data ingestion by fetching and printing data immediately.

**Notes:**
- Output is displayed in the system terminal, not in the interface terminal (due to threading limitations).

---

### 🟠 **Start Streaming Ingestion (Warm Path)**  
**Status:** Enabled by default  

**Functionality:**  
Simulates near real-time ingestion, fetching and printing data every minute (interval is configurable).

**Notes:**
- Like the Hot Path, output is printed to the system terminal.

---

### 🔎 **Check Code Quality**  
**Status:** Enabled by default  

**Functionality:**  
Checks the quality of all Python code, including `UI.py` and other scripts.

**Display:**  
Opens a new terminal window to display results.

---

#### **`dags/`**

Contains Apache Airflow DAGs to schedule and automate tasks.

- **`scheduled_task.py`**:  
  - Scheduled to run daily (assuming Airflow is continuously running).
  - Cleans and moves data through all zones.

---

#### **`Python/`**

This folder contains Python scripts used in the Data Management processes.

- **`Code_Quality/check_code_quality.py`**  
  - Script to check and report code quality of the Python files.

- **`Data_Management/`**
  - Core logic for data ingestion and folder management.
  - Structure:
    - **`Data_Ingestion/`**
      - `Batch_Ingestion/`: Batch (cold path) scripts.
      - `Streaming_Ingestion/`: Hot and warm path ingestion scripts.
    - **`Landing_Zone/`**
      - Scripts to:
        - Create folder structure.
        - Move data from Temporal Zone to Persistent Zone using Delta Lake.
    - **`Trusted_Zone/`**
      - Script to:
        - Cleans adn validates data (e.g., ranges, null checks).
        - Integrates **Great Expectations** for data quality enforcement.
        - Move data from Persistent Zone to Trusted Zone.
    - **`Exploitation_Zone/`**
      - Scripts to:
        - Computes KPIs and aggregates.
        - Distributes final datasets and consumption.
        - Move data from Trusted Zone to Exploitation Zone.
    - **`utils.py`**
      - Contains helper functions used across the pipeline.

- **`Monitoring/monitor.py`**  
  - Monitors real-time execution of Data Management process.

---

#### **`Streamlit/`**
This folder contains scripts used for the **Consumption Layer** to visualize the proposed products.

- **`products/`**:
  - Core of the Consumption Layer, where contains all the business domains to perform the tasks.
    - **`utility_code/`**
      - scripts to compute user-based and item-based recommeder systems.
    - Contains business domain visualizations as separate Streamlit products.
  - **`app.py`**:
    - Main Streamlit entry point that allows users to select and launch specific product visualizations.

---

#### **`Test/`**

Contains unit tests to verify the functionality of project components.

- **`Data Ingestion Test/`**: Tests for ingestion-related scripts.
- **`Landing Zone Test/`**: Tests for Landing Zone management logic.

---

## 💻 Installation Instructions

> ⚠️ **Python version required:** ≥ 3.10.0  
Install it from: https://www.python.org/downloads/

### 1. Create a Virtual Environment
```bash
python -m venv myenv
myenv\Scripts\activate  # On Windows
# or
source myenv/bin/activate  # On Unix/macOS
```

### 2. Install Project Dependencies
```bash
pip install -r ./docker/requirements.txt
```

### 3. Build and Start Docker Containers
Navigate to the docker/ directory and run the following command to build the Docker image and start all services defined in the docker-compose.yml file:

```bash
docker-compose up --build
```

Once the containers are up, you can run the project scripts. To stop the Docker containers, use the following command:

```bash
docker-compose down
```
### 4. Deactivating the Virtual Environment
After you're done working in the virtual environment, deactivate it by running the following command:

```bash
deactivate
```

---

## 🚀 Running the Project

### Run the User Interface:
```bash
python ./Project_1/UI.py
```

### Run the Streamlit App (Consumption Layer)
```bash
cd ./Project_1/Streamlit
streamlit run app.py
```
>Note: Make sure the Data Management process has been executed first.

### Run Unit Tests:
Navigate to the appropriate test folder and run:

```bash
python -m unittest test_file_name.py
```

---

## 🔧 Notes on Delta Lake

Delta Lake requires specific environment variables to be properly configured when running locally:

- `JAVA_HOME`
- `HADOOP_HOME`
- `SPARK_HOME`

These are already handled within the Docker container when using **Apache Airflow**, which is recommended for persistent storage tasks.
