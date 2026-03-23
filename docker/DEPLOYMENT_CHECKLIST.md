# 배포 체크리스트

## ✅ 로컬에서 받아갈 파일 목록

```
/home/sdh/docker/
├── backend/
│   └── Dockerfile                    # Backend 이미지 빌드용
├── frontend/
│   ├── Dockerfile                    # Frontend 이미지 빌드용
│   ├── nginx.conf                    # Frontend Nginx 설정
│   └── docker-entrypoint.sh          # 런타임 환경변수 주입
├── k8s/
│   ├── configmap.yaml                ✅ 업데이트됨 (API_URL: "/api")
│   ├── redis.yaml                    ✅ Redis StatefulSet
│   ├── backend.yaml                  ✅ Backend Deployment
│   ├── frontend.yaml                 ✅ Frontend Deployment
│   ├── ingress.yaml                  ✅ 업데이트됨 (/api 프록시)
│   ├── README.md                     ✅ 배포 가이드
│   ├── install-ingress-controller.sh ✅ Ingress Controller 설치
│   ├── test-service-principal.py     ✅ SP 테스트 스크립트
│   └── debug-backend.sh              ✅ Backend 디버깅
├── docker-compose.yml                # Docker Compose 배포용
└── docker-compose.dev.yml            # 개발 환경용
```

## 📝 배포 전 수정 필요 사항

### 1. **이미지 레지스트리 변경**
- `k8s/backend.yaml` → `image: wotnek90/inventory:backend-v1`
- `k8s/frontend.yaml` → `image: wotnek90/inventory:frontend-v1`

### 2. **도메인 변경**
- `k8s/ingress.yaml` → `host: inven.xyz` (실제 도메인으로 변경)

### 3. **이메일 변경** (cert-manager ClusterIssuer)
- README의 ClusterIssuer 예시에서 이메일 변경

## 🚀 AKS 배포 순서

```bash
# 1. Ingress Controller 설치
./k8s/install-ingress-controller.sh

# 2. ConfigMap 적용
kubectl apply -f k8s/configmap.yaml

# 3. Redis 배포
kubectl apply -f k8s/redis.yaml

# 4. Backend 배포
kubectl apply -f k8s/backend.yaml

# 5. Frontend 배포
kubectl apply -f k8s/frontend.yaml

# 6. Ingress 배포
kubectl apply -f k8s/ingress.yaml

# 7. External IP 확인
kubectl get ingress -n default inventory-ingress
```

## 🔑 핵심 설정

### ConfigMap (`configmap.yaml`)
```yaml
API_URL: "/api"  # ✅ 상대 경로 사용
```

### Ingress (`ingress.yaml`)
```yaml
paths:
  - path: /api(/|$)(.*)      # ✅ /api/* → Backend
  - path: /                   # ✅ 나머지 → Frontend
```

## 🌐 통신 구조

```
브라우저 → https://inven.xyz
          ↓
      Ingress Controller
          ↓
    ┌─────┴──────┐
    ↓            ↓
  Frontend    /api → Backend → Redis
 (ClusterIP)     (ClusterIP)  (ClusterIP)
```

## ✨ 변경 사항 요약

1. ✅ Ingress에 `/api` 프록시 경로 추가
2. ✅ ConfigMap API_URL을 `/api`로 변경
3. ✅ Frontend Nginx는 정적 파일 서빙만
4. ✅ Backend, Redis는 ClusterIP (내부만)
5. ✅ 외부 접근은 Ingress만

## 🎯 테스트 방법

```bash
# 1. Health Check
curl https://inven.xyz/api/health

# 2. API Docs
curl https://inven.xyz/api/docs

# 3. Frontend
curl https://inven.xyz/
```
