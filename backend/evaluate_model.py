import os
import re
import string
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


def wordopt(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\\W", " ", text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>+', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text.strip()


def load_dataset():
    fake_path = os.path.join('backend', 'data', 'News _dataset', 'Fake.csv')
    true_path = os.path.join('backend', 'data', 'News _dataset', 'True.csv')

    df_fake = pd.read_csv(fake_path)
    df_true = pd.read_csv(true_path)

    df_fake['class'] = 0
    df_true['class'] = 1

    df = pd.concat([df_fake, df_true], ignore_index=True)
    df['content'] = (df['title'] + ' ' + df['text']).apply(wordopt)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    return df


def main():
    model_dir = os.path.join('backend', 'app', 'ml', 'models')
    model_path = os.path.join(model_dir, 'logistic_regression_model.pkl')
    vectorizer_path = os.path.join(model_dir, 'tfidf_vectorizer.pkl')

    print('Loading saved model and vectorizer...')
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    print('Loading dataset and preparing test split...')
    df = load_dataset()

    from sklearn.model_selection import train_test_split
    x = df['content']
    y = df['class']

    _, x_test, _, y_test = train_test_split(x, y, test_size=0.25, random_state=42)

    print('Transforming test data with the saved TF-IDF vectorizer...')
    xv_test = vectorizer.transform(x_test)

    print('Predicting with saved Logistic Regression model...')
    y_pred = model.predict(xv_test)

    print('\n=== Saved Model Performance ===')
    print('Test samples:', len(y_test))
    print('Accuracy:', accuracy_score(y_test, y_pred))
    print('\nClassification Report:\n')
    print(classification_report(y_test, y_pred, digits=4))
    print('Confusion Matrix:')
    print(confusion_matrix(y_test, y_pred))


if __name__ == '__main__':
    main()
