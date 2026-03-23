from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()


class PostgreSQLSummary(BaseModel):
    subscription_id: str
    region: str | None
    postgresql_count: int


@router.post("/postgresql/summary", response_model=PostgreSQLSummary)
def get_postgresql_summary(config: ServicePrincipalConfig) -> PostgreSQLSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = PostgreSQLManagementClient(credential=credential, subscription_id=config.subscription_id)
        postgresql_count = count_by_region(client.servers.list(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL 조회 실패: {e}")

    return PostgreSQLSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        postgresql_count=postgresql_count,
    )
