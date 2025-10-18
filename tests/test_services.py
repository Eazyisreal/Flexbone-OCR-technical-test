
import pytest
from unittest.mock import patch, Mock, MagicMock
from app.services.ocr import cached_extract, _extract_text

class TestOCRService:
    def test_cached_extract(self):
        with patch('app.services.ocr._extract_text') as mock_extract:
            mock_extract.return_value = ("cached text", 0.95)
            
            result1 = cached_extract("hash123", b"image")
            result2 = cached_extract("hash123", b"image")
            assert result1 == result2
            mock_extract.assert_called_once()
    
    @patch('app.services.ocr.vision.ImageAnnotatorClient')
    def test_ocr_success(self, mock_client):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        mock_response = Mock()
        mock_response.error.message = "" 
        mock_response.full_text_annotation = Mock(text="SUCCESS")
        mock_response.full_text_annotation.pages = [
            Mock(blocks=[Mock(paragraphs=[Mock(words=[Mock(symbols=[
                Mock(confidence=0.95)
            ])])])])
        ]
        mock_instance.document_text_detection.return_value = mock_response
        
        text, confidence = _extract_text(b"image")
        assert text == "SUCCESS"
        assert confidence > 0
    
    @patch('app.services.ocr.vision.ImageAnnotatorClient')
    def test_ocr_no_text(self, mock_client):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        mock_response = Mock()
        mock_response.error.message = ""  
        mock_response.full_text_annotation = None
        mock_instance.document_text_detection.return_value = mock_response
        
        text, confidence = _extract_text(b"image")
        assert text == ""
        assert confidence == 0.0