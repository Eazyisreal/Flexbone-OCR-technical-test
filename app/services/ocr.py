
from google.cloud import vision
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from functools import lru_cache
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)

@lru_cache(maxsize=settings.cache_size)
def cached_extract(image_hash: str, content: bytes) -> tuple[str, float]:
    return _extract_text(content)

@retry(
    stop=stop_after_attempt(settings.vision_retry_attempts),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception)
)
def _extract_text(content: bytes) -> tuple[str, float]:
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=content)
    
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise ValueError(response.error.message)
    
    if response.full_text_annotation:
        full_text = response.full_text_annotation.text.strip()
        confidences = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        for symbol in word.symbols:
                            if symbol.confidence:
                                confidences.append(symbol.confidence)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    else:
        full_text, avg_conf = "", 0.0
    
    logger.info("ocr_success", text_len=len(full_text), confidence=round(avg_conf, 2))
    return full_text, round(avg_conf, 2)