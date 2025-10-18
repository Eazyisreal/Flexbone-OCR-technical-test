import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from pathlib import Path
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_vision_success():
    mock_response = Mock()
    mock_response.full_text_annotation = Mock(text="HELLO WORLD OCR API")
    mock_response.full_text_annotation.pages = [
        Mock(blocks=[Mock(paragraphs=[Mock(words=[Mock(symbols=[
            Mock(confidence=0.95),
            Mock(confidence=0.96)
        ])])])])
    ]
    mock_response.error.message = ""  # No error
    return mock_response

@pytest.fixture
def mock_vision_empty():
    mock_response = Mock()
    mock_response.full_text_annotation = None
    mock_response.error.message = ""  # No error
    return mock_response

@pytest.fixture
def create_test_images(tmp_path):
    """Create all test images"""
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    
    img = Image.new('RGB', (400, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 80), 'HELLO WORLD', fill='black')
    img.save(fixtures / 'test.jpg')
    
    img = Image.new('RGB', (100, 100), 'white')
    img.save(fixtures / 'blank.png')
    
    img = Image.new('RGB', (400, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 80), 'ROTATED TEXT', fill='black')
    img = img.rotate(90)
    img.save(fixtures / 'rotated.jpg')
    
    with open(fixtures / 'test.jpg', 'rb') as f:
        data = f.read()
    with open(fixtures / 'corrupt.jpg', 'wb') as f:
        f.write(data[:100])  
    
    with open(fixtures / 'large.jpg', 'wb') as f:
        f.write(b'A' * 11_000_000)
    
    with open(fixtures / 'invalid.pdf', 'w') as f:
        f.write('%PDF-1.0\ninvalid')
    
    return fixtures