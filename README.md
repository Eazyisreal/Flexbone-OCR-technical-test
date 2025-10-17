#  OCR Image Text Extraction API


> A fully containerized OCR API that extracts text from uploaded images using Google Cloud Vision, deployed on Cloud Run.
> Built for scalability, reliability, and production-readiness.

---

##  Live Demo

🔗 **Public URL:** [https://flexbone-ocr-technical-test-732014265147.europe-west1.run.app](https://flexbone-ocr-technical-test-732014265147.europe-west1.run.app)

---

##  Overview

This project implements an **OCR (Optical Character Recognition) API** designed to process uploaded images and extract text with confidence scoring.

It was built for the **Google Cloud Run Technical Challenge** — demonstrating skills in:

* API design (FastAPI)
* Cloud deployment (GCP Cloud Run)
* Vision-based ML integration (Google Cloud Vision API)
* Containerization and best DevOps practices

---

## ⚙️ Features

| Feature            | Description                                                           |
| ------------------ | --------------------------------------------------------------------- |
|  OCR Extraction  | Uses Google Cloud Vision for high-accuracy text detection             |
|  File Upload     | Accepts `.jpg`, `.jpeg`, `.png`, `.gif`, `.tiff`, `.webp`             |
|  Async Processing | FastAPI async I/O for efficient handling                              |
|  Metadata        | Extracts format, size, mode, and EXIF info                            |
|  Retry + Caching | Tenacity-based retry & LRU caching for repeated images                |
|  Validation      | File type & size validation (10MB limit)                              |
|  Security       | Sanitized output, size control, IAM-based auth (no keys in container) |
|  Rate Limiting   | Prevents abuse (SlowAPI)                                              |
|  Logging         | Structured JSON logs for observability                                |

---

##  API Documentation

### **Base URL:**

```
https://flexbone-ocr-technical-test-732014265147.europe-west1.run.app
```

### **Endpoints**

| Endpoint         | Method | Description                       | Rate Limit |
| ---------------- | ------ | --------------------------------- | ---------- |
| `/health`        | GET    | Health check                      | None       |
| `/extract-text`  | POST   | Extract text from a single image  | 10/min     |
| `/batch-extract` | POST   | Extract text from multiple images | 5/min      |

---

###  1. Extract Text (Single Image)

**POST** `/extract-text`

```bash
curl -X POST -F "image=@test_image.jpg" \
  https://flexbone-ocr-technical-test-732014265147.europe-west1.run.app/extract-text
```

####  Response (Success)

```json
{
  "success": true,
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
```

####  Response (Error)

```json
{
  "success": false,
  "status_code": 422,
  "data": null,
  "error": "File exceeds 10MB limit."
}
```

---

###  2. Batch Extraction (BONUS)

**POST** `/batch-extract`

```bash
curl -X POST \
  -F "image=@image1.jpg" \
  -F "image=@image2.png" \
  https://flexbone-ocr-technical-test-732014265147.europe-west1.run.app/batch-extract
```

####  Response

```json
{
  "success": true,
  "data": {
    "results": [
      { "text": "FIRST IMAGE", "confidence": 0.92 },
      { "text": "SECOND IMAGE", "confidence": 0.88 }
    ]
  }
}
```

---

##  Technical Implementation

| Component      | Details                                            |
| -------------- | -------------------------------------------------- |
| **Framework**  | FastAPI (async, type-safe, OpenAPI auto-docs)      |
| **OCR Engine** | Google Cloud Vision API                            |
| **Validation** | Pillow (image verification, metadata extraction)   |
| **Caching**    | LRU (via `functools.lru_cache`)                    |
| **Retries**    | Tenacity (exponential backoff for Vision API)      |
| **Security**   | No secrets in image, IAM-based credentials         |
| **Deployment** | Dockerized, built & deployed to GCP Cloud Run      |
| **Monitoring** | Structured logging (`structlog`) + `/health` route |

---

##  Architecture Diagram

```plaintext
+------------+       +------------------+       +---------------------+
|   Client   | --->  |   Cloud Run API  | --->  | Google Vision API   |
| (curl/UI)  |       |  (FastAPI + LRU) |       |  (OCR + Metadata)   |
+------------+       +------------------+       +---------------------+
```

---

##  Deployment Strategy

| Step                    | Description                                                            |
| ----------------------- | ---------------------------------------------------------------------- |
| **1. Containerization** | Multi-stage Docker build (non-root user)                               |
| **2. Auth**             | Mounted credentials via volume (`/app/credentials`)                    |
| **3. Deployment**       | `gcloud run deploy ocr-api --image gcr.io/... --allow-unauthenticated` |
| **4. Scaling**          | Auto-scales (min instances = 0, max = 80 concurrency)                  |
| **5. Monitoring**       | Cloud Logging + Healthcheck                                            |

---

##  Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/ocr-api.git
cd ocr-api

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set Google credentials (path to your JSON key)
export GOOGLE_APPLICATION_CREDENTIALS=./credentials/vision_key.json

# 4. Run locally
uvicorn app.main:app --host 0.0.0.0 --port 8080

# 5. Test
curl -X POST -F "image=@test_image.jpg" http://localhost:8080/extract-text
```

---

## Sample Test Images

| File          | Purpose       | Expected Result      |
| ------------- | ------------- | -------------------- |
| `test.jpg`    | Clear text    | `"HELLO WORLD"`      |
| `rotated.jpg` | Rotated image | `"ROTATED TEXT"`     |
| `blank.png`   | Empty         | `""` (confidence: 0) |



##  Author

**Isreal Aluko**
 [LinkedIn](https://linkedin.com/in/eazyisreal) | [GitHub](https://github.com/eazyisreal)

