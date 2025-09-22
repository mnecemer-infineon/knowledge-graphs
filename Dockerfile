FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY seed_neo4j.py ./
COPY neo4j_utils.py ./
COPY data/*.json ./data/
CMD ["python", "seed_neo4j.py"]
