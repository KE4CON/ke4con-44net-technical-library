FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard ./dashboard
ENV AROC_CONFIG=/config/config.yaml AROC_HOST=0.0.0.0 AROC_PORT=8080
EXPOSE 8080
CMD ["python", "-m", "dashboard.main"]
