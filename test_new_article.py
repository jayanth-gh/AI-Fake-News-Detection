import os
import re
import string
import joblib
import sys

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\\W", " ", text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>+', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text.strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_new_article.py \"Your news article text here\"")
        return

    article_text = sys.argv[1]

    model_dir = os.path.join('backend', 'app', 'ml', 'models')
    model_path = os.path.join(model_dir, 'logistic_regression_model.pkl')
    vectorizer_path = os.path.join(model_dir, 'tfidf_vectorizer.pkl')

    print('Loading saved model and vectorizer...')
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    print('Preprocessing input text...')
    cleaned_text = clean_text(article_text)

    print('Vectorizing text...')
    vectorized_text = vectorizer.transform([cleaned_text])

    print('Predicting...')
    prediction = model.predict(vectorized_text)[0]
    probability = model.predict_proba(vectorized_text)[0]

    result = "REAL" if prediction == 1 else "FAKE"
    confidence = probability[prediction] * 100

    print(f'\nPrediction: {result}')
    print(f'Confidence: {confidence:.2f}%')
    print(f'Probability of Fake: {probability[0]*100:.2f}%')
    print(f'Probability of Real: {probability[1]*100:.2f}%')

if __name__ == '__main__':
    main()