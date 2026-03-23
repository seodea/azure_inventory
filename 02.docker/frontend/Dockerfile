# ── Frontend Dockerfile (Multi-stage build) ────────────────────────────────

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Build argument (빌드 시 주입)
ARG VITE_API_URL=https://api.inven.xyz
ENV VITE_API_URL=$VITE_API_URL

# package.json 복사 및 의존성 설치
COPY package*.json ./
RUN npm ci

# 소스 코드 복사 및 빌드
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Entrypoint 스크립트 복사
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 빌드된 정적 파일 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 환경변수 (런타임에 설정 가능)
ENV API_URL=""

# 포트 노출
EXPOSE 80

# 헬스체크 (Docker Compose용)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Entrypoint 스크립트 실행
ENTRYPOINT ["/docker-entrypoint.sh"]
