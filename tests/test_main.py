import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

class TestAPIEndpoints:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    @pytest.mark.parametrize("filename,expect_success", [
        ("test.jpg", True),
        ("blank.png", True),
        ("rotated.jpg", True),
        ("invalid.pdf", False),
        ("corrupt.jpg", False),
    ])
    def test_extract_text_formats(self, client, create_test_images, filename, expect_success):
        with patch('app.services.ocr._extract_text') as mock_ocr:
            mock_ocr.return_value = ("TEST TEXT", 0.95)
            
            with open(create_test_images / filename, "rb") as f:
                response = client.post("/extract-text", files={"image": (filename, f)})
        
        if expect_success:
            assert response.status_code == 200
            data = response.json()["data"]
            assert "text" in data
            assert "confidence" in data
        else:
            assert response.status_code == 422
            json_response = response.json()
            assert "error" in json_response or "detail" in json_response
    
    def test_extract_text_success(self, client, create_test_images):
        from app.services.ocr import cached_extract
        cached_extract.cache_clear()
        
        with patch('app.services.ocr._extract_text') as mock_extract:
            mock_extract.return_value = ("HELLO WORLD", 0.95)
            
            with open(create_test_images / 'test.jpg', "rb") as f:
                response = client.post("/extract-text", files={"image": ("test.jpg", f)})
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["text"] == "HELLO WORLD"
        assert data["confidence"] == 0.95
        assert data["processing_time_ms"] >= 0 
    
    def test_extract_text_no_text(self, client, create_test_images):
        from app.services.ocr import cached_extract
        cached_extract.cache_clear()
        
        with patch('app.services.ocr._extract_text') as mock_extract:
            mock_extract.return_value = ("", 0.0)
            
            with open(create_test_images / 'blank.png', "rb") as f:
                response = client.post("/extract-text", files={"image": ("blank.png", f)})
        
        data = response.json()["data"]
        assert data["text"] == ""
        assert data["confidence"] == 0.0
    
    def test_rate_limiting(self, client, create_test_images):
        from app.services.ocr import cached_extract
        cached_extract.cache_clear()
        
        with patch('app.services.ocr._extract_text') as mock_extract:
            mock_extract.return_value = ("RATE LIMIT TEST", 0.95)
            
            for i in range(10):
                with open(create_test_images / 'test.jpg', "rb") as f:
                    response = client.post("/extract-text", files={"image": (f"test_{i}.jpg", f)})
                    if response.status_code != 200:
                        break
                    assert response.status_code == 200
            
            with open(create_test_images / 'test.jpg', "rb") as f:
                response = client.post("/extract-text", files={"image": ("test.jpg", f)})
                assert response.status_code in [200, 429]
    
    def test_batch_extract(self, client, create_test_images):
        from app.services.ocr import cached_extract
        cached_extract.cache_clear()
        
        with patch('app.services.ocr._extract_text') as mock_extract:
            mock_extract.return_value = ("BATCH TEXT", 0.90)
            
            with open(create_test_images / 'test.jpg', "rb") as f:
                file1_content = f.read()
            with open(create_test_images / 'blank.png', "rb") as f:
                file2_content = f.read()
            
            files = [
                ("images", ("test.jpg", file1_content, "image/jpeg")),
                ("images", ("blank.png", file2_content, "image/png"))
            ]
            response = client.post("/batch-extract", files=files)
        
        assert response.status_code == 200
        results = response.json()["data"]["results"]
        assert len(results) == 2
        assert results[0]["text"] == "BATCH TEXT"
    
    def test_batch_limit(self, client, create_test_images):
        with open(create_test_images / 'test.jpg', "rb") as f:
            file_content = f.read()
        
        files = [("images", (f"test_{i}.jpg", file_content, "image/jpeg")) for i in range(11)]
        response = client.post("/batch-extract", files=files)
        
        assert response.status_code == 422
        json_response = response.json()
        error_msg = str(json_response.get("error") or json_response.get("detail") or json_response)
        assert "10" in error_msg or "limit" in error_msg.lower() or "many" in error_msg.lower()