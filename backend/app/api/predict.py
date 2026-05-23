import os
import re
import json
import urllib.parse
from typing import List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
import pytesseract
from PIL import Image
import io
import requests
from bs4 import BeautifulSoup
import joblib
import string

# Setup Windows Tesseract Path explicitly to bypass PATH issues
tesseract_windows_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.name == 'nt' and os.path.exists(tesseract_windows_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_windows_path

from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db import models
from app.schemas import schemas
from app.api.auth import get_current_user

from duckduckgo_search import DDGS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


TRUSTED_SOURCES = {
    "thehindu.com": 0.95,
    "indianexpress.com": 0.93,
    "ndtv.com": 0.90,
    "indiatoday.com": 0.87,
    "timesofindia.com": 0.85,
    "news18.com": 0.82,
    "bbc.com": 0.90,
    "reuters.com": 0.90,
}

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml', 'models'))
MODEL_PATH = os.path.join(MODEL_DIR, 'logistic_regression_model.pkl')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')

ML_MODEL = None
VECTORIZER = None


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r"\\W", ' ', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>+', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text.strip()


def get_source_weight(domain: str) -> float:
    """
    Get weight for a source domain with intelligent matching.
    
    Features:
    - Case-insensitive matching
    - Partial domain matching (e.g., "ndtv-india.com" matches "ndtv.com")
    - Falls back to range 0.30-0.70 for unknown sources
    
    Args:
        domain: Source domain name (e.g., "thehindu.com", "www.ndtv.com")
    
    Returns:
        float: Weight between 0.0 and 1.0
    """
    domain_lower = domain.lower()
    
    # Remove common prefixes for matching
    domain_clean = domain_lower.replace("www.", "").replace("m.", "")
    
    # 1. Exact match
    if domain_clean in TRUSTED_SOURCES:
        return TRUSTED_SOURCES[domain_clean]
    
    # 2. Partial match - check if any trusted source is contained in domain
    for trusted_domain, weight in TRUSTED_SOURCES.items():
        if trusted_domain in domain_clean or domain_clean in trusted_domain:
            return weight
    
    # 3. Unknown source - return weight between 0.30 and 0.70
    # Use a simple hash-based distribution to be pseudo-deterministic
    hash_val = hash(domain_clean) % 100
    unknown_weight = 0.30 + (hash_val / 100.0) * 0.40  # Range: 0.30 - 0.70
    return round(unknown_weight, 2)


def load_ml_components() -> None:
    global ML_MODEL, VECTORIZER
    if ML_MODEL is not None and VECTORIZER is not None:
        return
    try:
        ML_MODEL = joblib.load(MODEL_PATH)
        VECTORIZER = joblib.load(VECTORIZER_PATH)
    except Exception as e:
        print(f"Failed to load local ML model or vectorizer: {e}")
        ML_MODEL = None
        VECTORIZER = None


def predict_with_local_model(text: str) -> tuple[str, float]:
    load_ml_components()
    if ML_MODEL is None or VECTORIZER is None:
        return "UNCERTAIN", 0.0

    try:
        cleaned = clean_text(text)
        features = VECTORIZER.transform([cleaned])
        prediction = ML_MODEL.predict(features)[0]
        confidence = 0.0
        if hasattr(ML_MODEL, 'predict_proba'):
            probs = ML_MODEL.predict_proba(features)[0]
            confidence = float(max(probs) * 100.0)
        verdict = "REAL" if int(prediction) == 1 else "FAKE"
        return verdict, confidence
    except Exception as e:
        print(f"Local ML prediction failed: {e}")
        return "UNCERTAIN", 0.0

# Configure Gemini API
# Provide a fallback just in case the key isn't set
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
# We will use 'gemini-1.5-flash' or 'gemini-1.5-pro' for robust reasoning.

class LLMResponse(BaseModel):
    verdict: str
    confidence: float
    reasoning: str
    sources: List[dict]

def fetch_live_news(query: str, fallback_text: str | None = None) -> list:
    """Uses DuckDuckGo to search for recent articles related to the text."""
    try:
        ddgs = DDGS()
        # 1. Try news-specific search using the optimized query
        results = ddgs.news(query, max_results=5)

        # 2. If no articles are found, retry with the raw claim/headline text
        if not results and fallback_text:
            results = ddgs.news(fallback_text, max_results=5)

        # 3. If still empty, fall back to the more general text search
        if not results:
            results = ddgs.text(query, max_results=5)

        # 4. Final fallback: search the raw claim text using text search
        if not results and fallback_text:
            results = ddgs.text(fallback_text, max_results=5)

        return results if results else []
    except Exception as e:
        print(f"Error fetching live news: {e}")
        return []

def analyze_with_llm(claim: str, news_context: list):
    """Uses Gemini API to extract claims, verify against news, and output a strict JSON."""
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        # Mock Response if no API key is set for development
        return {
            "verdict": "UNCERTAIN",
            "confidence": 0.5,
            "reasoning": "Gemini API key is not configured. Real-time fact-checking requires an active LLM key.",
            "sources": [{"title": "API Key Missing", "url": "http://localhost", "stance": "neutral"}]
        }
        
    try:
        genai.configure(api_key=api_key)
        # Prepare context string
        context_str = "Recent News Context:\n"
        for i, article in enumerate(news_context):
            title = article.get('title', 'Unknown Title')
            body = article.get('body', '')
            url = article.get('url', article.get('href', ''))
            context_str += f"[{i+1}] Title: {title}\nSummary: {body}\nLink: {url}\n\n"

        import datetime
        current_date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""
You are an elite, highly accurate investigative journalist AI. 
Analyze the following claim against the provided live news context.
Today's Date and Time: {current_date_str}

Determine if the claim is REAL, FAKE, or UNCERTAIN.
Important Guidelines:
1. You may receive conflicting search results. Always prioritize the consensus of the most relevant news.
2. If one source mentions a future release date but other sources talk about active box-office collections, assume the movie IS currently released and the first source is an old or inaccurate scrape. Do not hastily mark true news as 'FAKE' because of a single outdated source. 
3. Distinguish between minor stat discrepancies (e.g., small differences in box office numbers) and outright fabrications. If the core event is heavily supported but minor numbers differ, the claim is still largely 'REAL'.
4. Determine your stance (support/contradict/neutral) for each referenced source independently.

You must return your response EXCLUSIVELY as a raw JSON object with the exact keys.

Output schema:
{{
  "verdict": "REAL" | "FAKE" | "UNCERTAIN",
  "confidence": <float between 0 and 1>,
  "reasoning": "<A paragraph explaining the rationale based on the consensus of the sources>",
  "sources": [
    {{"title": "<article title>", "url": "<article url>", "stance": "support" | "contradict" | "neutral"}}
  ]
}}

Claim to verify: "{claim}"

{context_str}
"""
        # 1. Attempt using the 2.5 Flash model explicitly
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            raw_text = response.text
        except Exception as fallback_e:
            # 2. Fallback to Gemini Flash Latest
            print(f"Fallback to gemini-flash-latest due to: {fallback_e}")
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Legacy JSON extraction
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        
        try:
            return json.loads(raw_text.strip())
        except Exception as json_err:
            return {
                "verdict": "UNCERTAIN",
                "confidence": 0.0,
                "reasoning": f"LLM generated invalid JSON: {raw_text}",
                "sources": []
            }
            
    except Exception as e:
        print(f"Exception during LLM reasoning: {e}")
        return {
            "verdict": "UNCERTAIN",
            "confidence": 0.0,
            "reasoning": f"Error occurred during LLM verification: {str(e)}",
            "sources": []
        }

def extract_search_query(claim: str, api_key: str) -> str:
    """Uses LLM to summarize a long text claim into a 3-5 word concise search string for DuckDuckGo."""
    try:
        genai.configure(api_key=api_key)
        prompt = f"Convert this text into a concise 4-word search engine query targeting the core factual claim/entities. Return strictly only the search keywords without quotes.\n\nText: {claim[:500]}"
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip().replace('"', '')
    except:
        return claim[:60] # Fallback to strict trim if it fails

@router.post("/predict", response_model=schemas.PredictionResponse)
def predict_news(request: schemas.PredictionRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    # Reload API Key securely per request
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")

    local_verdict, local_confidence = predict_with_local_model(request.text)

    if not api_key:
        verdict = local_verdict if local_verdict != "UNCERTAIN" else "UNCERTAIN"
        confidence = local_confidence if local_confidence > 0 else 50.0
        reasoning = "Gemini API key is not configured. Using the local dataset-trained classifier for prediction."
        mapped_sources = []
    else:    
        # 1. Advanced Search Query Extraction (Fixing the naive slicing)
        optimized_query = extract_search_query(request.text, api_key)
        
        # 2. Fetch Real-time News Context using DuckDuckGo with optimized query
        # If the optimized query fails, retry using the raw headline/text.
        live_news = fetch_live_news(optimized_query, fallback_text=request.text)
        
        # 3. Extract keywords, cross-compare, and reason via LLM
        analysis = analyze_with_llm(request.text, live_news)
        
        reasoning = analysis.get("reasoning", "No comprehensive reasoning provided.")
        raw_sources = analysis.get("sources", [])
        llm_verdict = analysis.get("verdict", "UNCERTAIN")
        llm_confidence = analysis.get("confidence", 0.0)

        if isinstance(llm_confidence, float) and llm_confidence <= 1.0:
            llm_confidence *= 100.0
        llm_confidence = max(0.0, min(llm_confidence, 100.0))
        

        # Initialize source scoring variables
        score = 0.0
        total_weight = 0.0
        mapped_sources = []
        clickbait_keywords = ["shocking", "unbelievable", "you won't believe", "mind-blowing", "secret"]
        
        for s in raw_sources:
            url = s.get("url", "")
            title = s.get("title", "Unknown")
            stance = s.get("stance", "neutral")
            
            domain = "unknown"
            if url:
                try:
                    parsed_url = urllib.parse.urlparse(url)
                    domain = parsed_url.netloc
                    if domain.startswith("www."):
                        domain = domain[4:]
                except Exception:
                    pass
            
            # Get source weight using intelligent matching (case-insensitive, partial match)
            weight = get_source_weight(domain)
            
            # Clickbait penalty
            title_lower = title.lower()
            if any(kw in title_lower for kw in clickbait_keywords):
                weight = max(0.1, weight - 0.1) # Floor weight at 0.1
                
            pred_val = 0
            prediction_str = "UNCERTAIN"
            if stance == "support":
                pred_val = 1
                prediction_str = "REAL"
            elif stance == "contradict":
                pred_val = -1
                prediction_str = "FAKE"
            
            score += pred_val * weight
            total_weight += weight
            
            mapped_sources.append(schemas.SourceItem(
                title=title,
                url=url,
                stance=stance,
                domain=domain,
                weight=round(weight, 2),
                prediction=prediction_str
            ))
            
        if not raw_sources:
            verdict = local_verdict if local_verdict != "UNCERTAIN" else llm_verdict
            confidence = local_confidence if local_confidence > 0 else llm_confidence
        else:
            if total_weight > 0:
                confidence = (abs(score) / total_weight) * 100.0
            else:
                confidence = llm_confidence if llm_confidence > 0 else local_confidence

            if score > 0:
                verdict = "REAL"
            elif score < 0:
                verdict = "FAKE"
            else:
                verdict = llm_verdict if llm_verdict in ["REAL", "FAKE", "UNCERTAIN"] else local_verdict
                if confidence == 0.0:
                    confidence = max(local_confidence, llm_confidence)

    # Save to History
    history_record = models.PredictionHistory(
        text=request.text,
        prediction=verdict,
        confidence=confidence,
        user_id=current_user.id
    )
    db.add(history_record)
    db.commit()

    return schemas.PredictionResponse(
        prediction=verdict,
        confidence=confidence,
        reasoning=reasoning,
        sources=mapped_sources,
        result=verdict
    )

@router.post("/predict/image", response_model=schemas.PredictionResponse)
async def predict_news_image(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        extracted_text = pytesseract.image_to_string(image).strip()
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=500, 
            detail="Tesseract OCR is not installed or not in PATH. Please install Tesseract-OCR for Windows."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")

    if not extracted_text or len(extracted_text) < 5:
        raise HTTPException(status_code=400, detail="No readable text found in the uploaded image. Try a clearer image.")

    # Pass the extracted text through the standard pipeline
    request = schemas.PredictionRequest(text=extracted_text)
    return predict_news(request, db, current_user)

@router.post("/predict/link", response_model=schemas.LinkPredictionResponse)
def predict_news_link(
    request: schemas.LinkPredictionRequest, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    url = request.url
    flags = []
    
    clickbait_keywords = ["shocking", "unbelievable", "you won't believe", "mind-blowing", "secret", "miracle", "100% cure"]

    # 1. Expand URL & extract domain
    expanded_url = url
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        expanded_url = response.url
        if len(response.history) > 0:
            flags.append("Shortened URL")
    except Exception:
        # Fallback if HEAD fails
        pass

    if not expanded_url.startswith("https"):
        flags.append("Non-HTTPS")

    # Extract Domain
    domain = "unknown"
    try:
        parsed_url = urllib.parse.urlparse(expanded_url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        pass
    
    # Check if domain is in trusted sources using intelligent matching
    domain_weight = get_source_weight(domain)
    if domain_weight <= 0.70:  # Unknown or lower-trust source
        flags.append("Unknown Source")

    # 2. Extract Article Content
    title = ""
    full_text = ""
    try:
        # User-Agent to avoid simple bot blockers
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        page = requests.get(expanded_url, headers=headers, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            
        paragraphs = soup.find_all('p')
        full_text = " ".join([p.get_text() for p in paragraphs])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape URL: {str(e)}")
        
    if not full_text or len(full_text) < 10:
        raise HTTPException(status_code=400, detail="Insufficient textual content found on the provided link.")

    title_lower = title.lower()
    if any(kw in title_lower for kw in clickbait_keywords):
        flags.append("Clickbait")

    # 3. Formulate standard prediction
    text_to_eval = f"Title: {title}\nContent: {full_text[:4000]}"
    standard_request = schemas.PredictionRequest(text=text_to_eval)
    
    # We call predict_news to do internal weighting & fact checking
    prediction_response = predict_news(standard_request, db, current_user)
    
    return schemas.LinkPredictionResponse(
        result=prediction_response.result,
        confidence=prediction_response.confidence,
        original_url=url,
        expanded_url=expanded_url,
        domain=domain,
        flags=flags,
        sources_used=prediction_response.sources
    )

@router.get("/history", response_model=list[schemas.HistoryItem])
def get_user_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    history = db.query(models.PredictionHistory).filter(models.PredictionHistory.user_id == current_user.id).order_by(models.PredictionHistory.timestamp.desc()).limit(20).all()
    return history

@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total = db.query(models.PredictionHistory).filter(models.PredictionHistory.user_id == current_user.id).count()
    fake_count = db.query(models.PredictionHistory).filter(
        models.PredictionHistory.user_id == current_user.id,
        models.PredictionHistory.prediction.in_(["FAKE"]) # Count all versions of FAKE
    ).count()
    real_count = db.query(models.PredictionHistory).filter(
        models.PredictionHistory.user_id == current_user.id,
        models.PredictionHistory.prediction.in_(["REAL"])
    ).count()

    return schemas.DashboardStats(
        total_predictions=total,
        fake_count=fake_count,
        real_count=real_count
    )
