# G-Fortress: NTLM Vulnerability Scanner

G-Fortress is a comprehensive security auditing platform designed to scan Windows environments for user account vulnerabilities, particularly those related to NTLM hashes and password policies. It features a web-based dashboard for managing and viewing scan reports, a secure backend API, scheduled scanning capabilities, and an agent-based approach for data collection.

## Core Features

*   **Agent-Based Scanning**: A lightweight Python agent runs on target Windows machines to securely extract SAM and SYSTEM hive data.
*   **Vulnerability Analysis**: The backend processes the collected data to identify vulnerabilities like weak passwords (placeholder logic) and passwords that haven't been changed in a long time (placeholder logic).
*   **Web Dashboard**: A modern React-based single-page application for interacting with the system. Users can view historical reports, see detailed findings per user, and schedule new scans.
*   **Secure API**: The backend is powered by a FastAPI application featuring robust security measures, including end-to-end payload encryption.
*   **End-to-End Encryption**: Implements a Diffie-Hellman key exchange (X25519) during login to establish a shared AES-256 session key. This key is used to encrypt all subsequent API communication, providing a strong layer of security against man-in-the-middle attacks. This feature can be toggled on or off from the UI.
*   **Asynchronous Scanning**: Utilizes Celery and Redis to manage and execute scans asynchronously, ensuring the UI remains responsive and scans can run in the background.
*   **Graph-Based Data Model**: Leverages a Neo4j graph database to store scan results, creating a rich, interconnected model of reports, machines, users, and their associated vulnerabilities.
*   **PDF Report Generation**: Generates detailed, professional PDF reports for each scan, summarizing findings for easy distribution and review.
*   **Dockerized Environment**: The entire application stack is containerized using Docker and Docker Compose for easy setup, deployment, and scalability.

## Architecture Overview

The project is divided into three main components that work together:

1.  **Frontend**: A React application built with Vite and styled with TailwindCSS. It uses Redux Toolkit for state management and RTK Query for data fetching. All cryptographic operations on the client-side are handled using `libsodium-wrappers`.

2.  **Backend**: A Python application built with FastAPI. It serves the REST API, handles user authentication (JWT), manages business logic, interacts with the Neo4j database via the `neontology` OGM, and dispatches tasks to the Celery workers.

3.  **NTLM Windows Agent**: A standalone Flask-based agent that must be run with Administrator privileges on target Windows machines. It exposes a single, secure endpoint for the backend to request SAM/SYSTEM hive data. Communication is secured via a shared secret.

The backend, database, and task queue system are all orchestrated by Docker Compose.

 <!-- Placeholder for a diagram -->

### Technology Stack

| Component         | Technologies                                                                                             |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| **Backend**       | Python, FastAPI, Celery, Neontology (Neo4j OGM), PyJWT, Passlib, Cryptography, ReportLab                     |
| **Frontend**      | TypeScript, React, Redux Toolkit (RTK Query), Vite, TailwindCSS                    |
| **Windows Agent** | Python, Flask, Waitress                                                                    |
| **Database**      | Neo4j                                                                                                    |
| **Task Queue**    | Redis (Broker & Result Backend)                                                                          |
| **Infrastructure**| Docker, Docker Compose, Nginx (for serving the production frontend)                                        |

## Getting Started

### Prerequisites

*   Docker
*   Docker Compose

### 1. Configuration

The entire project is configured using the `.env` file in the root directory.

1.  **Copy the Example**: If `.env` does not exist, copy the contents from the provided file listing.
2.  **Backend & Database**:
    *   `NEO4J_PASSWORD`: Set a strong password for the Neo4j database. This must match the `NEO4J_AUTH` value in `docker-compose.yml`.
    *   `DEFAULT_ADMIN_PASSWORD`: Change the default password for the initial `admin` user.
3.  **NTLM Agent Configuration**:
    *   `NTLM_AGENTS_SECRET`: This is a shared secret that the backend and all Windows agents must share. Set a long, random string.
    *   `NTLM_AGENTS_URIS`: A semicolon-separated list of URLs for the running NTLM Windows Agents. For agents running on the Docker host machine, use `http://host.docker.internal:<PORT>;`.
4.  **Frontend**:
    *   `VITE_API_BASE_URL`: The URL of the backend API that the frontend will connect to. The default `http://127.0.0.1:8000` is suitable for local development.

### 2. Running the NTLM Windows Agent

The agent must be run on each Windows machine you intend to scan.

1.  **Requirements**:
    *   Python 3.x
    *   Administrator privileges are **mandatory**.
2.  **Setup**:
    *   Copy the `ntlm_windows_agent` directory to the target machine.
    *   Create a `.env` file inside this directory with the following content:
        ```env
        SECRET="your_shared_secret_from_step_1"
        PORT=1337
        FRIENDLY_NAME="Living-Room-PC"
        ```
    *   Install dependencies: `pip install flask waitress python-dotenv`
3.  **Execution**:
    *   Open a PowerShell or Command Prompt **as Administrator**.
    *   Navigate to the `ntlm_windows_agent` directory.
    *   Run the agent: `python main.py`
4.  **Deployment (Optional)**:
    *   You can compile the agent into a single `.exe` file for easier distribution using PyInstaller:
        ```bash
        pip install pyinstaller
        pyinstaller --clean --onefile --exclude-module matplotlib main.py
        ```

### 3. Running the Main Application

From the project root directory, execute the following command:

```bash
docker compose up --build -d
```

This will build all the necessary images and start all services in the background.

### Accessing Services

*   **Frontend (Web UI)**: [http://localhost:5173](http://localhost:5173) (Dev) or [http://localhost](http://localhost) (Prod)
*   **Backend (API Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Neo4j Browser**: [http://localhost:7474](http://localhost:7474)

The default login credentials are `admin` / `admin` (or whatever you set in the `.env` file).

## Usage Workflow

1.  **Login**: Access the web UI and log in with the admin credentials.
2.  **Schedule a Scan**: Navigate to the "Scheduled Scans" page. Set a date and time for the scan to run. The Celery Beat service checks for pending scans every minute.
3.  **Execution**: The Celery Worker will pick up the scheduled task, connect to the configured NTLM agents, retrieve the data, process it for vulnerabilities, and persist the results in the Neo4j database.
4.  **View Report**: Once the scan is complete, the status will update on the "Scheduled Scans" page, and a link to the full report will appear. You can also find it on the "Reports" page.
5.  **Analyze**: Click on a report to see a detailed breakdown of findings for each user, including any detected vulnerabilities. You can also download a PDF version of the report.

## Convenience Scripts (`run.sh`)

The `run.sh` script is a wrapper around `docker compose` to simplify common development tasks.

*   **Run Backend Tests**:
    ```bash
    ./run.sh test
    ```
*   **Manage Frontend Dependencies**:
    ```bash
    # Install npm packages
    ./run.sh npm_install

    # Run an npm script
    ./run.sh npm_run build
    ```

## Testing

The backend includes a suite of tests using `pytest`. The tests cover:
*   API endpoint functionality.
*   The secure login and AES encryption/decryption flow.
*   Database interaction to ensure data is persisted and retrieved correctly.

To run the tests, use the provided script:
```bash
./run.sh test
```
