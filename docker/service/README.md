# K8s 배포 가이드

## 1. Docker 이미지 빌드 및 푸시

### 환경 변수 설정
```bash
export REGISTRY="your-registry.azurecr.io"  # 또는 docker.io/username
export TAG="v1.0.0"
```

### Backend 이미지
```bash
cd /home/sdh/docker

# 빌드
docker build \
  -f backend/Dockerfile \
  -t ${REGISTRY}/inventory-backend:${TAG} \
  ../inventory/backend

# 푸시
docker push ${REGISTRY}/inventory-backend:${TAG}

# Latest 태그
docker tag ${REGISTRY}/inventory-backend:${TAG} ${REGISTRY}/inventory-backend:latest
docker push ${REGISTRY}/inventory-backend:latest
```

### Frontend 이미지
```bash
cd /home/sdh/docker

# 빌드 (도메인 무관 - 런타임 설정)
docker build \
  -f frontend/Dockerfile \
  -t ${REGISTRY}/inventory-frontend:${TAG} \
  ../inventory/frontend-vue

# 푸시
docker push ${REGISTRY}/inventory-frontend:${TAG}

# Latest 태그
docker tag ${REGISTRY}/inventory-frontend:${TAG} ${REGISTRY}/inventory-frontend:latest
docker push ${REGISTRY}/inventory-frontend:latest
```

## 2. K8s 배포

### 도메인 설정
```bash
cd /home/sdh/docker/k8s

# ConfigMap 수정 (도메인 변경)
vim configmap.yaml
```

**configmap.yaml에서 수정:**
```yaml
data:
  API_URL: "https://api.YOUR-DOMAIN.com"  # 여기 수정!
```

### 이미지 레지스트리 수정
```bash
# backend.yaml, frontend.yaml에서 수정
vim backend.yaml
vim frontend.yaml
```

**수정할 부분:**
```yaml
image: YOUR_REGISTRY/inventory-backend:latest
# →
image: your-registry.azurecr.io/inventory-backend:latest
```

### Ingress 도메인 수정
```bash
vim ingress.yaml
```

**수정할 부분:**
```yaml
spec:
  tls:
  - hosts:
    - YOUR-DOMAIN.com          # 프론트엔드 도메인
    - api.YOUR-DOMAIN.com      # 백엔드 도메인
```

### 배포 실행
```bash
cd /home/sdh/docker/k8s

# 1. ConfigMap 생성
kubectl apply -f configmap.yaml

# 2. Redis 배포
kubectl apply -f redis.yaml

# 3. Backend 배포
kubectl apply -f backend.yaml

# 4. Frontend 배포
kubectl apply -f frontend.yaml

# 5. Ingress 생성
kubectl apply -f ingress.yaml
```

## 3. 배포 확인

### Pod 상태
```bash
kubectl get pods
```

### Service 확인
```bash
kubectl get svc
```

### Ingress 확인
```bash
kubectl get ingress
```

### 로그 확인
```bash
# Backend 로그
kubectl logs -l app=inventory-backend --tail=100 -f

# Frontend 로그
kubectl logs -l app=inventory-frontend --tail=100 -f

# 특정 Pod 로그
kubectl logs <pod-name> -f
```

## 4. 도메인 변경 방법

### 방법 1: ConfigMap만 수정 (권장) ✅
```bash
# 1. ConfigMap 수정
kubectl edit configmap inventory-config

# API_URL을 새 도메인으로 변경
data:
  API_URL: "https://api.new-domain.com"

# 2. Frontend Pod 재시작 (설정 반영)
kubectl rollout restart deployment inventory-frontend

# 3. Ingress 도메인 수정
kubectl edit ingress inventory-ingress
```

### 방법 2: 이미지 재빌드 (필요 없음)
ConfigMap으로 런타임 설정이 가능하므로 재빌드 불필요!

## 5. 자동 감지 모드 (기본값)

ConfigMap에서 `API_URL`을 설정하지 않으면:
```javascript
// 자동으로 현재 도메인 사용
https://your-domain.com → https://your-domain.com:8000
```

**완전 자동 설정:**
```yaml
# configmap.yaml
data:
  API_URL: ""  # 비워두면 자동 감지
```

프론트엔드가 `inven.xyz`에서 실행되면 자동으로 `inven.xyz:8000`을 사용합니다.

## 6. 트러블슈팅

### API URL 확인
```bash
# Frontend Pod에 접속
kubectl exec -it <frontend-pod> -- sh

# config.js 확인
cat /usr/share/nginx/html/config.js
```

### 환경변수 확인
```bash
kubectl exec -it <frontend-pod> -- env | grep API_URL
kubectl exec -it <backend-pod> -- env | grep REDIS
```

### ConfigMap 확인
```bash
kubectl get configmap inventory-config -o yaml
```

## 7. Azure Container Registry 사용 시

```bash
# ACR 로그인
az acr login --name yourregistry

# 이미지 빌드 및 푸시
REGISTRY="yourregistry.azurecr.io"
TAG="v1.0.0"

docker build -f backend/Dockerfile -t ${REGISTRY}/inventory-backend:${TAG} ../inventory/backend
docker push ${REGISTRY}/inventory-backend:${TAG}

docker build -f frontend/Dockerfile -t ${REGISTRY}/inventory-frontend:${TAG} ../inventory/frontend-vue
docker push ${REGISTRY}/inventory-frontend:${TAG}

# K8s Secret 생성 (Pull용)
kubectl create secret docker-registry acr-secret \
  --docker-server=${REGISTRY} \
  --docker-username=<service-principal-id> \
  --docker-password=<service-principal-password>

# Deployment에 추가
spec:
  template:
    spec:
      imagePullSecrets:
      - name: acr-secret
```

## 📝 요약

### ✅ 도메인 변경 절차
1. **ConfigMap 수정** → `API_URL` 변경
2. **Ingress 수정** → 호스트 도메인 변경
3. **Frontend 재시작** → 설정 반영

### ✅ 이미지는 한 번만 빌드
- 도메인 무관하게 동작
- ConfigMap으로 런타임 설정
- 재빌드 불필요!

### ✅ 모든 도메인 자동 지원
- ConfigMap `API_URL: ""`로 설정
- 자동으로 현재 도메인 사용
