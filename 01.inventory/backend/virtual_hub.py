from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class VirtualHubSummary(BaseModel):
    subscription_id: str
    region: str | None
    virtual_hub_count: int


@router.post("/virtual-hub/summary", response_model=VirtualHubSummary)
def get_virtual_hub_summary(config: ServicePrincipalConfig) -> VirtualHubSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        vhub_count = count_by_region(client.virtual_hubs.list(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Virtual Hub 조회 실패: {e}")

    return VirtualHubSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        virtual_hub_count=vhub_count,
    )
