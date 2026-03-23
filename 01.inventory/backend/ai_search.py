from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.search import SearchManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class AISearchSummary(BaseModel):
    subscription_id: str
    region: str | None
    ai_search_count: int


@router.post("/ai-search/summary", response_model=AISearchSummary)
def get_ai_search_summary(config: ServicePrincipalConfig) -> AISearchSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = SearchManagementClient(credential=credential, subscription_id=config.subscription_id)
        ai_search_count = count_by_region(client.services.list_by_subscription(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Search 조회 실패: {e}")

    return AISearchSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        ai_search_count=ai_search_count,
    )
