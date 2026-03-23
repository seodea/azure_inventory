from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class NSGSummary(BaseModel):
    subscription_id: str
    region: str | None
    nsg_count: int


@router.post("/nsg/summary", response_model=NSGSummary)
def get_nsg_summary(config: ServicePrincipalConfig) -> NSGSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        nsg_count = count_by_region(client.network_security_groups.list_all(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NSG 조회 실패: {e}")

    return NSGSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        nsg_count=nsg_count,
    )
