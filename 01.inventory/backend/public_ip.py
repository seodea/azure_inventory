from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class PublicIPSummary(BaseModel):
    subscription_id: str
    region: str | None
    public_ip_count: int


@router.post("/public-ip/summary", response_model=PublicIPSummary)
def get_public_ip_summary(config: ServicePrincipalConfig) -> PublicIPSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        public_ip_count = count_by_region(client.public_ip_addresses.list_all(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Public IP 조회 실패: {e}")

    return PublicIPSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        public_ip_count=public_ip_count,
    )
