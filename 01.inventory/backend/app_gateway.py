from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class AppGatewaySummary(BaseModel):
    subscription_id: str
    region: str | None
    app_gateway_count: int


@router.post("/app-gateway/summary", response_model=AppGatewaySummary)
def get_app_gateway_summary(config: ServicePrincipalConfig) -> AppGatewaySummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        agw_count = count_by_region(client.application_gateways.list_all(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"App Gateway 조회 실패: {e}")

    return AppGatewaySummary(
        subscription_id=config.subscription_id,
        region=config.region,
        app_gateway_count=agw_count,
    )
