from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.appcontainers import ContainerAppsAPIClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class CAESummary(BaseModel):
    subscription_id: str
    region: str | None
    cae_count: int


@router.post("/cae/summary", response_model=CAESummary)
def get_cae_summary(config: ServicePrincipalConfig) -> CAESummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = ContainerAppsAPIClient(credential=credential, subscription_id=config.subscription_id)
        cae_count = count_by_region(client.managed_environments.list_by_subscription(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CAE 조회 실패: {e}")

    return CAESummary(
        subscription_id=config.subscription_id,
        region=config.region,
        cae_count=cae_count,
    )
