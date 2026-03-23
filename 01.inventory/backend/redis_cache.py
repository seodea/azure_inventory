from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from azure.mgmt.redis import RedisManagementClient
from common import ServicePrincipalConfig, get_credential, validate_config, count_by_region

router = APIRouter()

class RedisSummary(BaseModel):
    subscription_id: str
    region: str | None
    redis_count: int

@router.post("/redis/summary", response_model=RedisSummary)
def get_redis_summary(config: ServicePrincipalConfig) -> RedisSummary:
    validate_config(config)
    credential = get_credential(config.tenant_id, config.client_id, config.client_secret)
    try:
        client = RedisManagementClient(credential=credential, subscription_id=config.subscription_id)
        count = count_by_region(client.redis.list_by_subscription(), config.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis 조회 실패: {e}")
    return RedisSummary(subscription_id=config.subscription_id, region=config.region, redis_count=count)
