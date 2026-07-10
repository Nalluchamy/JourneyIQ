# JourneyIQ ML Service Skeleton

This service serves as the core template for the Machine Learning and Recommendation Engine features of the JourneyIQ platform.

## Objective

In future phases, this service will be responsible for:
- Building user and product embedding spaces.
- Performing real-time recommendation updates using collaborative filtering / deep learning.
- Serving personalization APIs for the main FastAPI backend.
- Running inference for Customer Lifetime Value (CLV) and churn models.

## Structure

```text
ml-service/
├── app/
│   └── main.py       # FastAPI application entrypoint
├── Dockerfile        # Environment packaging configuration
├── requirements.txt  # Python requirements (FastAPI, uvicorn, pydantic-settings)
└── README.md         # Service documentation
```

## Running Locally

1. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --port 8001 --reload
   ```
   The service will be active at `http://localhost:8001`.
