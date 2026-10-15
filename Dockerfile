FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY run_analysis.py ./
COPY data/sample ./data/sample

# root olmayan kullanıcı; çıktılar /app/outputs altına yazılır (volume ile dışarı alınır)
RUN useradd --create-home appuser && mkdir -p /app/outputs && chown -R appuser /app
USER appuser

# Varsayılan: sentetik demo verisiyle uçtan uca analiz. Argümanlar ezilebilir, örn:
#   docker run --rm -v "$PWD/data:/app/data" -v "$PWD/outputs:/app/outputs" <imaj> --input data/raw/etut.xlsx
ENTRYPOINT ["python", "run_analysis.py"]
CMD ["--demo"]
