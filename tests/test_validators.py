import pytest
from io import BytesIO
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.datastructures import Headers
from app.utils.validators import validate_image, preprocess_text
from app.utils.exceptions import ValidationError

@pytest.mark.asyncio
class TestValidators:
    async def test_valid_jpg(self, create_test_images):
        with open(create_test_images / 'test.jpg', 'rb') as f:
            content = f.read()
        
        headers = Headers({"content-type": "image/jpeg"})
        file = StarletteUploadFile(
            filename="test.jpg",
            file=BytesIO(content),
            headers=headers
        )
        validated_content, metadata = await validate_image(file)
        
        assert len(validated_content) > 0
        assert metadata["format"] in ["JPEG", "JPG"]
        assert metadata["size"] == (400, 200)
    
    async def test_unsupported_format(self, create_test_images):
        with open(create_test_images / 'invalid.pdf', 'rb') as f:
            content = f.read()
        
        headers = Headers({"content-type": "application/pdf"})
        file = StarletteUploadFile(
            filename="test.pdf",
            file=BytesIO(content),
            headers=headers
        )
        with pytest.raises(ValidationError):
            await validate_image(file)
    
    async def test_too_large(self, create_test_images):
        with open(create_test_images / 'large.jpg', 'rb') as f:
            content = f.read()
        
        headers = Headers({"content-type": "image/jpeg"})
        file = StarletteUploadFile(
            filename="large.jpg",
            file=BytesIO(content),
            headers=headers
        )
        with pytest.raises(ValidationError, match="exceeds"):
            await validate_image(file)
    
    async def test_corrupt_image(self, create_test_images):
        with open(create_test_images / 'corrupt.jpg', 'rb') as f:
            content = f.read()
        
        headers = Headers({"content-type": "image/jpeg"})
        file = StarletteUploadFile(
            filename="corrupt.jpg",
            file=BytesIO(content),
            headers=headers
        )
        with pytest.raises(ValidationError, match="corrupted"):
            await validate_image(file)
    
    def test_preprocess_text(self):
        text = "  Hello\nWorld  <script>evil</script>  "
        cleaned = preprocess_text(text)
        assert "Hello" in cleaned
        assert "World" in cleaned
        assert len(cleaned) > 0