import os
from typing import Optional, Tuple, Union
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

def preprocess_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    _, thresholded = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresholded

def load_image(file_path: str) -> Optional[np.ndarray]:
    try:
        image = cv2.imread(file_path)
        if image is None:
            return None
        return image
    except Exception:
        return None

def load_pdf(file_path: str, dpi: int = 300) -> Optional[list[np.ndarray]]:
    try:
        images = convert_from_path(file_path, dpi=dpi)
        return [np.array(img) for img in images]
    except Exception:
        return None

def perform_ocr(image: np.ndarray, lang: str = 'eng') -> str:
    preprocessed = preprocess_image(image)
    pil_image = Image.fromarray(preprocessed)
    text = pytesseract.image_to_string(pil_image, lang=lang)
    return text.strip()

def process_file(file_path: str, lang: str = 'eng') -> Optional[Union[str, list[str]]]:
    if not os.path.exists(file_path):
        return None
    
    if file_path.lower().endswith('.pdf'):
        pdf_images = load_pdf(file_path)
        if pdf_images is None:
            return None
        return [perform_ocr(img, lang) for img in pdf_images]
    else:
        image = load_image(file_path)
        if image is None:
            return None
        return perform_ocr(image, lang)

def get_text_snippet(text: Union[str, list[str]], max_length: int = 200) -> str:
    if isinstance(text, list):
        text = ' '.join(text)
    return text[:max_length] + '...' if len(text) > max_length else text