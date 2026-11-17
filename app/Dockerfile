FROM public.ecr.aws/docker/library/python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir boto3
COPY app.py .
USER nobody
EXPOSE 8080
CMD ["python", "app.py"]
