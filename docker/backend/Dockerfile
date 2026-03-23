# ── Backend Dockerfile (최적화) ───────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# 시스템 패키지 및 빌드 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치 (wheel 사용)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Production Stage ───────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# wget 설치 (헬스체크용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 복사 (builder에서)
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 애플리케이션 코드만 복사 (.py 파일만)
COPY *.py ./

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8000/health || exit 1

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
