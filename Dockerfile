FROM python:3.12-slim
WORKDIR /app
COPY bot.py content.json ./
RUN useradd --create-home botuser
USER botuser
ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]
