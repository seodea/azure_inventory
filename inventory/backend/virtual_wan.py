from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class VirtualWANSummary(BaseModel):
    subscription_id: str
    region: str | None
    virtual_wan_count: int


@router.post("/virtual-wan/summary", response_model=VirtualWANSummary)
def get_virtual_wan_summary(config: ServicePrincipalConfig) -> VirtualWANSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        vwan_count = count_by_region(client.virtual_wans.list(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Virtual WAN 조회 실패: {e}")

    return VirtualWANSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        virtual_wan_count=vwan_count,
    )
