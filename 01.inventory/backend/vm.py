from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.compute import ComputeManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class VMSummary(BaseModel):
    subscription_id: str
    region: str | None
    vm_count: int


@router.post("/vm/summary", response_model=VMSummary)
def get_vm_summary(config: ServicePrincipalConfig) -> VMSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = ComputeManagementClient(credential=credential, subscription_id=config.subscription_id)
        vm_count = count_by_region(client.virtual_machines.list_all(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VM 조회 실패: {e}")

    return VMSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        vm_count=vm_count,
    )
