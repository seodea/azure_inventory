from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.containerregistry import ContainerRegistryManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class ACRSummary(BaseModel):
    subscription_id: str
    region: str | None
    acr_count: int


@router.post("/acr/summary", response_model=ACRSummary)
def get_acr_summary(config: ServicePrincipalConfig) -> ACRSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = ContainerRegistryManagementClient(credential=credential, subscription_id=config.subscription_id)
        acr_count = count_by_region(client.registries.list(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ACR 조회 실패: {e}")

    return ACRSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        acr_count=acr_count,
    )
