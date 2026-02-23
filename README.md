# SpendingTracker

SpendingTracker is a FastAPI-based web service that provides functional REST APIs to manage personal spending, categories, reports, and transactions. 

## Features
- **Auth**: User signup, signin (JWT), and profile updates.
- **Categories**: Create, read, update, delete expense categories.
- **Transactions**: Record and track transactions.
- **Reports**: Request spending reports efficiently managed through Apache Kafka and processed using background tasks.

## Setup and Installation

The project uses `make` commands to simplify setting up the environment.

### 1. Requirements
Ensure you have Python 3 and `make` installed.

### 2. Generate RSA Keys (for JWT)
```bash
make generate_RSA_keys
```

### 3. Build Environment
Create a virtual environment (`venv`) and install dependencies:
```bash
make build
```

### 4. Database Migrations
To generate new Alembic migrations:
```bash
make new_migration
```

To apply migrations to the database:
```bash
make migrate
```

## Running the Application

To start the FastAPI web server using `uvicorn`:
```bash
make run
```
The server will be available at `http://localhost:8000`.

## Testing and Linting

**Run Linter (ruff):**
```bash
make lint
```

**Run Tests (pytest):**
```bash
make test
```

## API Endpoints

### Auth
- `POST /signup`: Register a new user and receive a JWT.
- `POST /signin`: Sign in.
- `GET /verify`: Get current user info.
- `PATCH /users/{user_id}`: Update user data.

### Categories
- `GET /`: Get all categories for the authenticated user.
- `POST /`: Create a new category.
- `GET /{category_id}`: Get category details.
- `PUT /{category_id}`: Update a category.
- `DELETE /{category_id}`: Delete a category.

### Transactions
- `GET /`: List all user transactions.
- `POST /`: Create a new transaction.
- `GET /{transaction_id}`: Show transaction details.
- `PUT /{transaction_id}`: Edit a transaction.
- `DELETE /{transaction_id}`: Remove a transaction.

### Reports
- `POST /create_report`: Create a new report (processes asynchronously via Kafka).
- `GET /get_report`: Get report by ID.
- `DELETE /delete_report`: Delete a report.
