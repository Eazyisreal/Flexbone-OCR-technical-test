from fastapi import FastAPI, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time
import asyncio
import hashlib
import structlog
from typing import List
from app.services.ocr import cached_extract
from app.utils.validators import validate_image, preprocess_text
from app.utils.exceptions import ValidationError
from app.middleware.rate_limiter import limiter, SlowAPIMiddleware
from app.config import settings

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="OCR API", 
    version="1.0",
    docs_url="/", 
    redoc_url=None  
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

class APIResponse(BaseModel):
    success: bool
    status_code: int
    data: dict | None = None
    error: str = ""

class OCRData(BaseModel):
    text: str = ""
    confidence: float = 0.0
    processing_time_ms: int = 0
    metadata: dict = {}

class BatchResult(BaseModel):
    results: List[dict]

@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    response_data = APIResponse(
        success=False, 
        status_code=exc.status_code, 
        error=exc.detail["error"]
    )
    return JSONResponse(content=response_data.dict(), status_code=exc.status_code)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", exc=str(exc))
    response_data = APIResponse(
        success=False, 
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="Internal server error"
    )
    return JSONResponse(content=response_data.dict(), status_code=500)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info("request_processed", method=request.method, url=str(request.url), duration=duration)
    return response

@app.get("/health")
async def health():
    return {"status": "healthy"}

async def process_single_image(image: UploadFile):
    from app.utils.exceptions import ValidationError

    try:
        content, metadata = await validate_image(image)
        image_hash = hashlib.sha256(content).hexdigest()
        text, confidence = cached_extract(image_hash, content)  
        text = preprocess_text(text)  
        data = {
            "text": text,
            "confidence": confidence,
            "processing_time_ms": 0,
            "metadata": metadata 
        }
        return data
    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error("ocr_processing_error", error=str(e))
        raise ValidationError(f"OCR processing failed: {str(e)}")

@app.post(
    "/extract-text",
    response_model=APIResponse,
    responses={
        200: {
            "description": "Successful OCR extraction",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "status_code": 200,
                        "data": {
                            "text": "HELLO WORLD OCR API",
                            "confidence": 0.95,
                            "processing_time_ms": 2878,
                            "metadata": {
                                "format": "JPEG",
                                "size": [400, 200],
                                "mode": "RGB",
                                "exif": {}
                            }
                        },
                        "error": ""
                    }
                }
            }
        }
    }
)
@limiter.limit(settings.rate_limit)
async def extract_text(request:Request, image: UploadFile = File(...)):  
    start_time = time.time()
    data = await process_single_image(image)
    data["processing_time_ms"] = int((time.time() - start_time) * 1000)
    response_data = APIResponse(success=True, status_code=status.HTTP_200_OK, data=data)
    return response_data

@app.post(
    "/batch-extract",
    response_model=APIResponse,
    responses={
        200: {
            "description": "Successful batch OCR extraction",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "status_code": 200,
                        "data": {
                            "results": [
                                {
                                    "text": "FIRST IMAGE TEXT",
                                    "confidence": 0.92,
                                    "processing_time_ms": 1500,
                                    "metadata": {"format": "PNG", "size": [300, 400]}
                                },
                                {
                                    "text": "SECOND IMAGE TEXT", 
                                    "confidence": 0.88,
                                    "processing_time_ms": 1200,
                                    "metadata": {"format": "JPEG", "size": [500, 300]}
                                }
                            ]
                        },
                        "error": ""
                    }
                }
            }
        }
    }
)
@limiter.limit("5/minute")  
async def batch_extract(request:Request, images: List[UploadFile] = File(...)): 
    from app.utils.exceptions import ValidationError  

    if len(images) > 10:  
        raise ValidationError("Max 10 images per batch.")
    tasks = [process_single_image(img) for img in images]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    processed = []
    for result in results:
        if isinstance(result, Exception):
            processed.append({"error": str(result)})
        else:
            result["processing_time_ms"] = 100
            processed.append(result)
    response_data = APIResponse(success=True, status_code=status.HTTP_200_OK, data={"results": processed})
    return response_data