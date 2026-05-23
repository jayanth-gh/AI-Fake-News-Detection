import pandas as pd
import numpy as np
import re
import string
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os

def wordopt(text):
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r"\\W"," ",text) 
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>+', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\n', '', text)
    text = re.sub(r'\w*\d\w*', '', text)    
    return text

def main():
    print("Loading datasets...")
    try:
        df_fake = pd.read_csv('data/News _dataset/Fake.csv')
        df_true = pd.read_csv('data/News _dataset/True.csv')
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return

    # Add labels: 0 for FAKE, 1 for REAL
    df_fake['class'] = 0 
    df_true['class'] = 1 

    print(f"Loaded {len(df_fake)} FAKE news and {len(df_true)} REAL news.")

    # Combine datasets
    df_marge = pd.concat([df_fake, df_true], axis=0)

    # Let's combine title and text for better context
    df_marge['content'] = df_marge['title'] + " " + df_marge['text']

    df = df_marge.drop(['title', 'subject', 'date', 'text'], axis=1)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    print("Preprocessing text data (this may take a minute)...")
    df['content'] = df['content'].apply(wordopt)

    x = df['content']
    y = df['class']

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)

    print("Vectorizing Text Data using TF-IDF...")
    vectorization = TfidfVectorizer(stop_words='english', max_df=0.7)
    xv_train = vectorization.fit_transform(x_train)
    xv_test = vectorization.transform(x_test)

    print("\nTraining Logistic Regression Model...")
    LR = LogisticRegression()
    LR.fit(xv_train, y_train)
    pred_lr = LR.predict(xv_test)
    acc_lr = accuracy_score(y_test, pred_lr)
    print(f"Logistic Regression Accuracy: {acc_lr*100:.2f}%")
    print(classification_report(y_test, pred_lr))
    
    print("\nTraining Naive Bayes Model...")
    NB = MultinomialNB()
    NB.fit(xv_train, y_train)
    pred_nb = NB.predict(xv_test)
    acc_nb = accuracy_score(y_test, pred_nb)
    print(f"Naive Bayes Accuracy: {acc_nb*100:.2f}%")

    model_dir = 'app/ml/models'
    os.makedirs(model_dir, exist_ok=True)
    
    print("\nSaving Best Models (Vectorizers and LR Classifiers)...")
    # Saving both models for the backend API to use
    joblib.dump(LR, os.path.join(model_dir, 'logistic_regression_model.pkl'))
    joblib.dump(vectorization, os.path.join(model_dir, 'tfidf_vectorizer.pkl'))
    print(f"Models saved successfully correctly to {model_dir}!")

if __name__ == "__main__":
    main()
