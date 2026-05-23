# Fake News Detection System

A complete full-stack AI-powered web application for detecting fake news. Built with React (Vite, TailwindCSS) on the frontend and FastAPI, SQLite, and Scikit-Learn on the backend. This system classifies news text as REAL or FAKE, provides explainable AI insights, and tracks user history with interactive analytics dashboards.

## Features

- **Machine Learning Analysis:** Uses Logistic Regression powered by TF-IDF (Term Frequency-Inverse Document Frequency) text vectorization.
- **Explainable AI (ExAI):** Highlights the specific words and their weights that swayed the model towards the decision.
- **User Authentication:** Secure JWT-based login and registration system.
- **Interactive Dashboards:** Visualizations of your previously analyzed items using Chart.js.
- **Clean Modern Architecture:** Decoupled frontend components and secure backend endpoints.

## Tech Stack

- **Frontend:** React, Vite, Tailwind CSS, Lucide Icons, Chart.js
- **Backend:** Python, FastAPI, SQLAlchemy (SQLite)
- **Machine Learning Tools:** Pandas, Scikit-learn, Numpy, Joblib

## Folder Structure

```
fake_news_detector/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI Routes (predict, auth)
│   │   ├── core/         # Core application config
│   │   ├── db/           # SQLite database models and setup
│   │   ├── ml/           # Stored trained models (PKL files)
│   │   └── schemas/      # Pydantic typing schemas
│   ├── data/             # Training datasets (True.csv, Fake.csv)
│   ├── requirements.txt
│   ├── train.py          # Script to pretrain the models
│   └── main.py           # Application entrypoint
└── frontend/
    ├── src/
    │   ├── components/   # Reusable UI (Navbar, ExplainableWords)
    │   ├── context/      # React contexts (Auth)
    │   ├── pages/        # Views (Home, Login, Dashboard)
    │   └── services/     # Axios API instances
    ├── tailwind.config.js
    └── vite.config.js
```

## Setup & Run Instructions

### 1. Model Training & Backend Setup

First, ensure you have Python 3.9+ installed.

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run the training script (needs to be run ONCE to build the models)
python train.py

# Start the FastAPI server
uvicorn app.main:app --reload
```

The server will run on `http://localhost:8000`. You can test APIs at `http://localhost:8000/docs`.

### 2. Frontend Setup

In a new terminal:

```bash
cd frontend
npm install

# Start the Vite development server
npm run dev
```

The application will run on `http://localhost:5173`. Open it in your browser, register an account, and try it out!
