FROM python:3.12-slim

WORKDIR /srv

COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api api
COPY ml/models ml/models

ENV PYTHONPATH=/srv

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
