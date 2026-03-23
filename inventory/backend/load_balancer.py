from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.network import NetworkManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class LoadBalancerSummary(BaseModel):
    subscription_id: str
    region: str | None
    load_balancer_count: int


@router.post("/load-balancer/summary", response_model=LoadBalancerSummary)
def get_load_balancer_summary(config: ServicePrincipalConfig) -> LoadBalancerSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = NetworkManagementClient(credential=credential, subscription_id=config.subscription_id)
        lb_count = count_by_region(client.load_balancers.list_all(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load Balancer 조회 실패: {e}")

    return LoadBalancerSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        load_balancer_count=lb_count,
    )
