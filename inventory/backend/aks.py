from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.containerservice import ContainerServiceClient
from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()

class AKSSummary(BaseModel):
    subscription_id: str
    region: str | None
    aks_count: int

@router.post("/aks/summary", response_model=AKSSummary)
def get_aks_summary(config: ServicePrincipalConfig) -> AKSSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = ContainerServiceClient(credential=credential, subscription_id=config.subscription_id)
        count = count_by_region(client.managed_clusters.list(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AKS 조회 실패: {e}")
    return AKSSummary(subscription_id=config.subscription_id, region=config.region, aks_count=count)
