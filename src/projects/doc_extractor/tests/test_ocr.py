import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image
import pytesseract

class TestOCRExtraction(unittest.TestCase):
    def setUp(self):
        self.sample_text = "Sample document text\nwith multiple lines\nand 123 numbers"
        self.expected_text = "Sample document text with multiple lines and 123 numbers"

    def test_ocr_accuracy_clean_image(self):
        mock_image = MagicMock()
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = self.sample_text
            result = pytesseract.image_to_string(mock_image)
            self.assertEqual(result, self.sample_text)

    def test_ocr_preprocessing(self):
        mock_image = MagicMock()
        processed_image = MagicMock()
        
        with patch('PIL.Image.open') as mock_open, \
             patch('numpy.array') as mock_array, \
             patch('pytesseract.image_to_string') as mock_ocr:
            
            mock_open.return_value = mock_image
            mock_image.convert.return_value = processed_image
            mock_array.return_value = np.zeros((100, 100))
            mock_ocr.return_value = self.sample_text
            
            img = Image.open("dummy.png")
            img = img.convert('L')
            img_array = np.array(img)
            result = pytesseract.image_to_string(img)
            
            mock_image.convert.assert_called_with('L')
            self.assertEqual(result, self.sample_text)

    def test_multiline_handling(self):
        mock_image = MagicMock()
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = self.sample_text
            result = pytesseract.image_to_string(mock_image)
            cleaned = ' '.join(result.split())
            self.assertEqual(cleaned, self.expected_text)

    def test_low_quality_image(self):
        mock_image = MagicMock()
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "S@mple d0cu&ent t3xt\nw1th m|lt1ple l1n3s\n&nd 123 numb3rs"
            result = pytesseract.image_to_string(mock_image)
            self.assertNotEqual(result, self.sample_text)
            self.assertIn("123", result)

if __name__ == '__main__':
    unittest.main()