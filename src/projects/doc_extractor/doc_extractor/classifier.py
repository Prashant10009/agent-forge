import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

class DocumentType(Enum):
    INSURANCE_POLICY = "insurance_policy"
    INSURANCE_CLAIM = "insurance_claim"
    BANK_STATEMENT = "bank_statement"
    POLICE_REPORT = "police_report"
    CONTRACT = "contract"
    UNKNOWN = "unknown"

@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float
    text_snippet: str

class DocumentClassifier:
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.vectorizer = None
        self.classes_ = None
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self):
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('clf', LogisticRegression(multi_class='multinomial'))
        ])

    def train(self, texts: List[str], labels: List[DocumentType], test_size: float = 0.2):
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        train_preds = self.model.predict(X_train)
        test_preds = self.model.predict(X_test)
        
        train_acc = accuracy_score(y_train, train_preds)
        test_acc = accuracy_score(y_test, test_preds)
        
        return train_acc, test_acc

    def predict(self, text: str) -> ClassificationResult:
        if not self.model:
            raise ValueError("Model not trained or loaded")
            
        snippet = text[:200] + "..." if len(text) > 200 else text
        probs = self.model.predict_proba([text])[0]
        pred_idx = np.argmax(probs)
        confidence = float(probs[pred_idx])
        doc_type = self.model.classes_[pred_idx]
        
        return ClassificationResult(
            document_type=doc_type,
            confidence=confidence,
            text_snippet=snippet
        )

    def save_model(self, path: str):
        if not self.model:
            raise ValueError("No model to save")
        joblib.dump(self.model, path)

    def load_model(self, path: str):
        self.model = joblib.load(path)

def main():
    classifier = DocumentClassifier()
    
    # Example training data - in practice this would come from a dataset
    texts = [
        "This is an insurance policy document...",
        "Claim form for accident...",
        "Bank statement for account...",
        "Police report about incident...",
        "Contract agreement between parties..."
    ]
    labels = [
        DocumentType.INSURANCE_POLICY,
        DocumentType.INSURANCE_CLAIM,
        DocumentType.BANK_STATEMENT,
        DocumentType.POLICE_REPORT,
        DocumentType.CONTRACT
    ]
    
    train_acc, test_acc = classifier.train(texts, labels)
    print(f"Training accuracy: {train_acc:.2f}, Test accuracy: {test_acc:.2f}")
    
    test_text = "This bank statement shows transactions..."
    result = classifier.predict(test_text)
    print(f"Predicted: {result.document_type.value}, Confidence: {result.confidence:.2f}")

if __name__ == "__main__":
    main()