from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.cosmosdb import CosmosDBManagementClient

from common import ServicePrincipalConfig, get_credential, validate_config

router = APIRouter()


class MongoDBSummary(BaseModel):
    subscription_id: str
    region: str | None
    mongodb_count: int


@router.post("/mongodb/summary", response_model=MongoDBSummary)
def get_mongodb_summary(config: ServicePrincipalConfig) -> MongoDBSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = CosmosDBManagementClient(credential=credential, subscription_id=config.subscription_id)
        region = config.region
        mongodb_count = 0
        for account in client.database_accounts.list():
            if region and getattr(account, "location", None) and account.location != region:
                continue
            capabilities = [c.name for c in (account.capabilities or [])]
            if getattr(account, "kind", None) == "MongoDB" or "EnableMongo" in capabilities:
                mongodb_count += 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cosmos DB(MongoDB) 조회 실패: {e}")

    return MongoDBSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        mongodb_count=mongodb_count,
    )
