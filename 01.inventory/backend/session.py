"""
세션 관리 API
Redis를 사용하여 사용자 인증 정보를 서버 측에 저장
Redis가 없을 경우 메모리(딕셔너리) fallback 사용
"""

import secrets
import json
import time
from datetime import timedelta
from typing import Optional, Dict

from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
import redis

router = APIRouter()

# Redis 클라이언트 (환경변수로 설정 가능)
import os
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"

# 메모리 기반 세션 저장소 (Redis fallback)
memory_sessions: Dict[str, tuple[str, float]] = {}  # {token: (data_json, expire_time)}

redis_client = None

if USE_REDIS:
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5
        )
        # 연결 테스트
        redis_client.ping()
        print(f"✅ Redis 연결 성공: {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"⚠️  Redis 연결 실패: {e}")
        print("   메모리 기반 세션으로 동작합니다.")
        redis_client = None
else:
    print("ℹ️  Redis 사용 안 함 (USE_REDIS=false)")
    print("   메모리 기반 세션으로 동작합니다.")

# 세션 만료 시간 (10분)
SESSION_EXPIRE = 600  # seconds


# ── 요청/응답 모델 ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str
    region: Optional[str] = None


class SessionResponse(BaseModel):
    session_token: str
    expires_in: int


class SessionData(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str
    region: Optional[str] = None


# ── 세션 관리 함수 ──────────────────────────────────────────────────────────

def generate_session_token() -> str:
    """안전한 세션 토큰 생성"""
    return secrets.token_urlsafe(32)


def save_session(token: str, data: SessionData) -> bool:
    """세션 데이터를 Redis 또는 메모리에 저장"""
    if redis_client:
        try:
            session_data = data.model_dump_json()
            redis_client.setex(
                f"session:{token}",
                SESSION_EXPIRE,
                session_data
            )
            return True
        except Exception as e:
            print(f"Redis 세션 저장 실패, 메모리로 fallback: {e}")
    
    # 메모리 저장 (fallback)
    try:
        session_data = data.model_dump_json()
        expire_time = time.time() + SESSION_EXPIRE
        memory_sessions[token] = (session_data, expire_time)
        # 만료된 세션 정리
        _cleanup_expired_sessions()
        return True
    except Exception as e:
        print(f"메모리 세션 저장 실패: {e}")
        return False


def get_session(token: str) -> Optional[SessionData]:
    """Redis 또는 메모리에서 세션 데이터 조회"""
    if redis_client:
        try:
            data = redis_client.get(f"session:{token}")
            if data:
                return SessionData.model_validate_json(data)
        except Exception as e:
            print(f"Redis 세션 조회 실패, 메모리에서 조회: {e}")
    
    # 메모리에서 조회 (fallback)
    try:
        if token in memory_sessions:
            session_data, expire_time = memory_sessions[token]
            # 만료 확인
            if time.time() < expire_time:
                return SessionData.model_validate_json(session_data)
            else:
                # 만료된 세션 삭제
                del memory_sessions[token]
        return None
    except Exception as e:
        print(f"메모리 세션 조회 실패: {e}")
        return None


def delete_session(token: str) -> bool:
    """세션 삭제"""
    success = False
    
    if redis_client:
        try:
            redis_client.delete(f"session:{token}")
            success = True
        except Exception as e:
            print(f"Redis 세션 삭제 실패: {e}")
    
    # 메모리에서도 삭제
    if token in memory_sessions:
        del memory_sessions[token]
        success = True
    
    return success


def refresh_session(token: str) -> bool:
    """세션 만료 시간 갱신"""
    if redis_client:
        try:
            if redis_client.expire(f"session:{token}", SESSION_EXPIRE):
                return True
        except Exception as e:
            print(f"Redis 세션 갱신 실패: {e}")
    
    # 메모리에서 갱신 (fallback)
    if token in memory_sessions:
        session_data, _ = memory_sessions[token]
        expire_time = time.time() + SESSION_EXPIRE
        memory_sessions[token] = (session_data, expire_time)
        return True
    
    return False


def _cleanup_expired_sessions():
    """만료된 메모리 세션 정리"""
    now = time.time()
    expired_tokens = [
        token for token, (_, expire_time) in memory_sessions.items()
        if now >= expire_time
    ]
    for token in expired_tokens:
        del memory_sessions[token]
    
    if expired_tokens:
        print(f"만료된 세션 {len(expired_tokens)}개 정리됨")


# ── API 엔드포인트 ──────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=SessionResponse)
def login(request: LoginRequest):
    """
    로그인 - 인증 정보를 받아 세션 생성
    Redis가 없으면 메모리 세션 사용
    """
    # 세션 토큰 생성
    token = generate_session_token()
    
    # 세션 데이터 저장
    session_data = SessionData(
        tenant_id=request.tenant_id,
        client_id=request.client_id,
        client_secret=request.client_secret,
        subscription_id=request.subscription_id,
        region=request.region
    )
    
    if not save_session(token, session_data):
        raise HTTPException(status_code=500, detail="세션 저장 실패")
    
    return SessionResponse(
        session_token=token,
        expires_in=SESSION_EXPIRE
    )


@router.get("/auth/session", response_model=SessionData)
def get_session_data(session_token: Optional[str] = Cookie(default=None)):
    """
    세션 조회 - 세션 토큰으로 인증 정보 조회
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="세션 토큰이 없습니다.")
    
    session_data = get_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")
    
    # 세션 만료 시간 갱신
    refresh_session(session_token)
    
    return session_data


@router.post("/auth/logout")
def logout(session_token: Optional[str] = Cookie(default=None)):
    """
    로그아웃 - 세션 삭제
    """
    if session_token:
        delete_session(session_token)
    
    return {"message": "로그아웃 되었습니다."}


@router.post("/auth/refresh")
def refresh(session_token: Optional[str] = Cookie(default=None)):
    """
    세션 갱신 - 만료 시간 연장
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="세션 토큰이 없습니다.")
    
    if not refresh_session(session_token):
        raise HTTPException(status_code=401, detail="세션 갱신 실패")
    
    return {"message": "세션이 갱신되었습니다.", "expires_in": SESSION_EXPIRE}


@router.get("/auth/health")
def health_check():
    """
    세션 서비스 상태 확인
    """
    if redis_client:
        try:
            redis_client.ping()
            return {
                "status": "healthy",
                "storage": "redis",
                "message": "Redis 연결 정상",
                "sessions": redis_client.dbsize() if redis_client else 0
            }
        except Exception as e:
            return {
                "status": "degraded",
                "storage": "memory",
                "message": f"Redis 오류, 메모리 사용 중: {e}",
                "sessions": len(memory_sessions)
            }
    else:
        return {
            "status": "healthy",
            "storage": "memory",
            "message": "메모리 기반 세션 사용",
            "sessions": len(memory_sessions)
        }
