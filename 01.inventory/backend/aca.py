from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.appcontainers import ContainerAppsAPIClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class ACASummary(BaseModel):
    subscription_id: str
    region: str | None
    aca_count: int


@router.post("/aca/summary", response_model=ACASummary)
def get_aca_summary(config: ServicePrincipalConfig) -> ACASummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = ContainerAppsAPIClient(credential=credential, subscription_id=config.subscription_id)
        aca_count = count_by_region(client.container_apps.list_by_subscription(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ACA 조회 실패: {e}")

    return ACASummary(
        subscription_id=config.subscription_id,
        region=config.region,
        aca_count=aca_count,
    )
