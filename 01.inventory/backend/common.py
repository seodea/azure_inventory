from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel
from azure.identity import ClientSecretCredential


class ServicePrincipalConfig(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str
    region: Optional[str] = None


def get_credential(tenant_id: str, client_id: str, client_secret: str) -> ClientSecretCredential:
    try:
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"자격 증명 생성 실패: {exc}") from exc


def validate_config(config: ServicePrincipalConfig) -> None:
    if not all([config.subscription_id, config.tenant_id, config.client_id, config.client_secret]):
        raise HTTPException(
            status_code=400,
            detail="tenant_id, client_id, client_secret, subscription_id는 필수입니다.",
        )


def count_by_region(iterator, region: Optional[str]) -> int:
    region_norm = normalize_region(region)
    count = 0
    for item in iterator:
        if region_norm and normalize_region(getattr(item, "location", None)) != region_norm:
            continue
        count += 1
    return count


def normalize_region(region: Optional[str]) -> Optional[str]:
    if region is None:
        return None
    value = str(region).strip().lower()
    if not value:
        return None
    if value in {"all", "전체", "*"}:
        return None
    for ch in (" ", "-", "_"):
        value = value.replace(ch, "")
    return value or None