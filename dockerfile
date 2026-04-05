FROM python:3.12-slim
WORKDIR /app
COPY user_settings.json .
COPY Config.py .
COPY main.py .
RUN pip install --no-cache-dir telebot pytz
CMD ["python","main.py"]
