# Email LLM Search

A Python package for searching emails using LLM and vector embeddings.

## Installation

```bash
pip install -e .
```
If torch cpu version not found, try:
```bash
pip install -e . --extra-index-url https://download.pytorch.org/whl/cpu
```

## Usage

There are several ways to run the application:

### 1. Using the console script (after installation)

```bash
email-llm-search
```

### 2. Using the Python module

```bash
python -m email_llm_search
```

### 3. Using the run_app.py script

```bash
python run_app.py
```

### 4. From Python code

```python
from email_llm_search import main

# Run the main application
main.run()
```

## Development

### Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install development dependencies: `pip install -e ".[dev]"`

### Testing

Run tests with pytest:

```bash
pytest
```

## License

MIT 