from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class ExpressRouteSummary(BaseModel):
    subscription_id: str
    region: str | None
    express_route_count: int


@router.post("/express-route/summary", response_model=ExpressRouteSummary)
def get_express_route_summary(config: ServicePrincipalConfig) -> ExpressRouteSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        er_count = count_by_region(client.express_route_circuits.list_all(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Express Route 조회 실패: {e}")

    return ExpressRouteSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        express_route_count=er_count,
    )
