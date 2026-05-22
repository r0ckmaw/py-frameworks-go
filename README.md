# Household Manager API

A modern FastAPI-based webserver for managing household inventory and recipes. Built with Python 3.14, `uv`, and `SQLAlchemy`.

## Features

- **Inventory Management**: CRUD operations for household items with categories and expiration dates.
- **Smart Alerts**: Endpoints for expiring items and low-stock tracking.
- **Recipe Management**: Create recipes and cross-reference with inventory.
- **Intelligent Cooking**: "Cook Recipe" feature that automatically deducts ingredients using FEFO (First Expiring, First Out) logic.
- **Shopping List Generator**: Consolidate missing ingredients from multiple recipes into a single shopping list.
- **Search**: Case-insensitive search for both items and recipes.
- **Modern Tooling**: Linting with `ruff` and type checking with `ty`.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed on your system.
- Python 3.14 (managed automatically by `uv` via `.python-version`).

## Setup

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Database**:
   By default, the project uses a local SQLite database (`household.db`). 
   
   To use **PostgreSQL** (via Docker):
   1. Start the container: `docker compose up -d`
   2. Run the server with the database URL:
      ```bash
      DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/household_db PYTHONPATH=src uv run uvicorn household_manager.main:app --reload
      ```

## Running the Server

Start the development server with:

```bash
PYTHONPATH=src uv run uvicorn household_manager.main:app --reload
```

The API will be available at `http://localhost:8000`.
You can access the interactive Swagger documentation at `http://localhost:8000/docs`.

## Running Tests

The project includes two main test scripts:

1. **Inventory Tests**:
   ```bash
   PYTHONPATH=src uv run tests/test_api.py
   ```

2. **Recipe & Intelligence Tests**:
   ```bash
   PYTHONPATH=src uv run tests/test_recipe.py
   ```

## Code Quality

To maintain modern coding standards, we use:

- **Linting & Formatting**: `uv run ruff check . --fix` and `uv run ruff format .`
- **Type Checking**: `uv run ty check`
