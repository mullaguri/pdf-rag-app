Full Workflow (Build + Tag + Push)
powershell# 
docker build -t mullaguris/rag-pdf-service:latest -t mullaguris/rag-pdf-service:v1.0.0 .
docker push mullaguris/rag-pdf-service:latest
docker push mullaguris/rag-pdf-service:v1.0.0


docker pull mullaguris/rag-pdf-service:latest

docker run -p 8000:8000 --env-file .env suresh/rag-pdf-service:latest


## RUN LOCALLY:

.venv\Scripts\activate

uv pip install  -r requirements.txt

mkdir vectorstore\faiss_index

uv run uvicorn main:app --reload

Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force; 
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Prompt to verify:
=================
purchase terms and contains terms and conditions agreed and invoice contains invoiced amount based on agreement. compare the invoice and agreement list the discrepancies.


dimensions = {
        # HuggingFace models
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "sentence-transformers/all-mpnet-base-v2": 768,
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 768,
 
        # OpenAI models
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
 
        # Cohere models
        "embed-multilingual-v3.0": 1024,
        "embed-english-v3.0": 1024,
 
        # Ollama models (typically same as base model)
            "llama2": 4096,
            "llama3": 4096,
            "mistral": 4096,
        }


OLLAMA Local Configuration
==========================
ollama pull llama3
ollama list

curl http://localhost:11434/api/tags

Test Embedding:
curl -Uri "http://localhost:11434/api/embeddings" -Method POST -ContentType "application/json" -Body '{"model": "llama3", "prompt": "Hello world"}'

# On macOS
brew install tesseract
brew install poppler

# On Debian/Ubuntu
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils

Windows:
choco install tesseract
choco install poppler

Go to: https://github.com/UB-Mannheim/tesseract/wiki
Download the latest Windows installer
Run the installer (note the installation path)


If `pytesseract` still can't find your Tesseract installation, you can specify the path in your `.env` file:

```
TESSERACT_PATH=/path/to/your/tesseract
```

For example, on macOS with Homebrew on Apple Silicon, this would be:
`TESSERACT_PATH=/opt/homebrew/bin/tesseract`

On an Intel Mac with Homebrew, it would be:
`TESSERACT_PATH=/usr/local/bin/tesseract`
