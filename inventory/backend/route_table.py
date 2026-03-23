from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class RouteTableSummary(BaseModel):
    subscription_id: str
    region: str | None
    route_table_count: int


@router.post("/route-table/summary", response_model=RouteTableSummary)
def get_route_table_summary(config: ServicePrincipalConfig) -> RouteTableSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        route_table_count = count_by_region(client.route_tables.list_all(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route Table 조회 실패: {e}")

    return RouteTableSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        route_table_count=route_table_count,
    )
