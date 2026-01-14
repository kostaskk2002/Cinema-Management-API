# Cinema Management System

Backend RESTful API για σύστημα διαχείρισης κινηματογράφου.

## Προαπαιτούμενα

- Python 3.9+
- MySQL 8.0+
- pip

## Εγκατάσταση

1. Clone το repository
2. Δημιούργησε virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ή
   venv\Scripts\activate  # Windows
```

3. Εγκατάστησε τα dependencies:
```bash
   pip install -r requirements.txt
```


## Εκτέλεση
```bash
uvicorn app.main:app --reload
```

API Documentation: http://localhost:8000/docs

## Testing
```bash
pytest
```