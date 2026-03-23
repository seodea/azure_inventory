from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, normalize_region

router = APIRouter()


class AOAISummary(BaseModel):
    subscription_id: str
    region: str | None
    aoai_count: int


@router.post("/aoai/summary", response_model=AOAISummary)
def get_aoai_summary(config: ServicePrincipalConfig) -> AOAISummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = CognitiveServicesManagementClient(credential=credential, subscription_id=config.subscription_id)
        region_norm = normalize_region(config.region)
        aoai_count = 0
        for account in client.accounts.list():
            if region_norm and normalize_region(getattr(account, "location", None)) != region_norm:
                continue
            if getattr(account, "kind", None) == "OpenAI":
                aoai_count += 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Azure OpenAI 조회 실패: {e}")

    return AOAISummary(
        subscription_id=config.subscription_id,
        region=config.region,
        aoai_count=aoai_count,
    )