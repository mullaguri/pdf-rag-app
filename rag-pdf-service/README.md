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
