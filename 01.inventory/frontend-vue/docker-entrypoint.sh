#!/bin/sh

# 환경변수를 config.js와 nginx.conf에 주입
echo "🔧 Injecting environment variables..."
echo "   API_URL: ${API_URL}"
echo "   BACKEND_HOST: ${BACKEND_HOST}"

# Backend 호스트 기본값 설정
BACKEND_HOST=${BACKEND_HOST:-inventory-backend:8000}

# config.js 생성 (브라우저용 - 상대 경로)
cat > /usr/share/nginx/html/config.js <<EOF
window.ENV = {
  API_URL: '${API_URL:-/api}'
};
EOF

echo "✅ Configuration injected"
cat /usr/share/nginx/html/config.js

# Nginx 설정에 Backend 호스트 주입
echo "🔧 Configuring backend proxy: ${BACKEND_HOST}"
sed -i "s|BACKEND_HOST_PLACEHOLDER|${BACKEND_HOST}|g" /etc/nginx/conf.d/default.conf

echo "✅ Nginx configuration updated"

# Nginx 시작
exec nginx -g 'daemon off;'
