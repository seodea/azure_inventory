from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class VPNGatewaySummary(BaseModel):
    subscription_id: str
    region: str | None
    vpn_gateway_count: int


@router.post("/vpn-gateway/summary", response_model=VPNGatewaySummary)
def get_vpn_gateway_summary(config: ServicePrincipalConfig) -> VPNGatewaySummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        vpngw_count = count_by_region(client.vpn_gateways.list(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VPN Gateway 조회 실패: {e}")

    return VPNGatewaySummary(
        subscription_id=config.subscription_id,
        region=config.region,
        vpn_gateway_count=vpngw_count,
    )
