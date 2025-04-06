
# Project BDM  
*The Data Management Stages of the BDM Project*

## Overview

This project sets up a Docker container with all the required services to run a user interface for managing data pipelines. The focus is on implementing a **Data Management** layer using a **Data Lakehouse** architecture (with **Delta Lake**).

> ⚠️ **Note:** In this first part of the project, only the **Landing Zone** (raw storage) will be used. No data analysis will be performed yet.

---

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

### 🟩 **Start Batch Ingestion (Cold Path)**  
**Status:** Enabled by default  

**Functionality:**  
Runs a batch ingestion pipeline that:
- Creates necessary folders for the Data Management process.
- Extracts data from various APIs.
- Saves data in the **Temporal Zone** (`Data Management/Landing Zone/Temporal Zone`).
- Organizes data in the **Persistent Zone** (`Data Management/Landing Zone/Persistent Zone`) using **Delta Lake**.

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
Opens a new terminal window to display results using a linter (e.g., `pylint`).

---

#### **`dags/`**

Contains Apache Airflow DAGs to schedule and automate tasks.

- **`scheduled_task.py`**:  
  - Scheduled to run daily (assuming Airflow is continuously running).
  - Extracts data from APIs and ingests into the **Landing Zone**.

---

#### **`Python/`**

This folder contains Python scripts used in the Data Management processes.

- **`Code_Quality/CheckCodeQuality.py`**  
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

- **`Monitoring/monitor_script.py`**  
  - Monitors real-time execution of both Data Management and Analysis Backbones.

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

---

## 🚀 Running the Project

### Run the User Interface:
```bash
python ./Project_1/UI.py
```

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
