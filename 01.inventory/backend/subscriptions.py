from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.subscription import SubscriptionClient

from common import get_credential

router = APIRouter()


class SubscriptionListRequest(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str


class SubscriptionInfo(BaseModel):
    subscription_id: str
    display_name: str | None = None
    state: str | None = None


class SubscriptionListResponse(BaseModel):
    subscriptions: list[SubscriptionInfo]


@router.post("/subscriptions/list", response_model=SubscriptionListResponse)
def list_subscriptions(request: SubscriptionListRequest) -> SubscriptionListResponse:
    if not all([request.tenant_id, request.client_id, request.client_secret]):
        raise HTTPException(status_code=400, detail="tenant_id, client_id, client_secret는 필수입니다.")

    try:
        credential = get_credential(request.tenant_id, request.client_id, request.client_secret)
    except Exception as exc:
        raise HTTPException(
            status_code=401, 
            detail=f"인증 실패: {type(exc).__name__} - {str(exc)}"
        ) from exc

    try:
        client = SubscriptionClient(credential)
        subscriptions: list[SubscriptionInfo] = []
        
        # 구독 목록 가져오기
        sub_list = list(client.subscriptions.list())
        
        if not sub_list:
            # 구독이 없는 경우 - 권한 문제일 수 있음
            raise HTTPException(
                status_code=403,
                detail=(
                    "구독 목록이 비어있습니다. "
                    "Service Principal에 구독 수준의 'Reader' 권한이 있는지 확인하세요. "
                    "Azure Portal → 구독 → Access control (IAM) → Role assignments"
                )
            )
        
        for sub in sub_list:
            raw_id = getattr(sub, "subscription_id", None) or getattr(sub, "id", "")
            subscription_id = str(raw_id).split("/")[-1] if raw_id else ""
            display_name = getattr(sub, "display_name", None) or subscription_id
            state = getattr(sub, "state", None)
            subscriptions.append(
                SubscriptionInfo(
                    subscription_id=str(subscription_id),
                    display_name=display_name,
                    state=str(state) if state is not None else None,
                )
            )
    except HTTPException:
        raise
    except Exception as exc:
        error_type = type(exc).__name__
        error_msg = str(exc)
        
        # 일반적인 에러 메시지 개선
        if "authorization" in error_msg.lower() or "forbidden" in error_msg.lower():
            detail = (
                f"권한 부족: {error_msg}\n\n"
                "해결 방법:\n"
                "1. Azure Portal → 구독 선택\n"
                "2. Access control (IAM) → Role assignments\n"
                "3. '+ Add' → 'Add role assignment'\n"
                "4. Role: Reader 선택\n"
                f"5. Members: Service Principal (Client ID: {request.client_id[:8]}...) 추가"
            )
        elif "authentication" in error_msg.lower() or "aadsts" in error_msg.lower():
            detail = (
                f"인증 실패: {error_msg}\n\n"
                "다음을 확인하세요:\n"
                "1. Tenant ID, Client ID, Client Secret이 정확한지\n"
                "2. Client Secret이 만료되지 않았는지\n"
                "3. Azure Portal → App registrations에서 확인"
            )
        else:
            detail = f"구독 목록 조회 실패 ({error_type}): {error_msg}"
        
        raise HTTPException(status_code=500, detail=detail) from exc

    return SubscriptionListResponse(subscriptions=subscriptions)
