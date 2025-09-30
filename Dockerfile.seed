FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY seed_neo4j.py ./
COPY neo4j_utils.py ./
COPY data/data_subset ./data/data_subset
# If you want to use the full dataset, uncomment the line below and set the DATA_FOLDER env variable accordingly
#COPY data/mooc ./data/mooc
CMD ["python", "seed_neo4j.py"]
