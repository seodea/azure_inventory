import io
from typing import Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from azure.identity import ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from openpyxl import Workbook


router = APIRouter()


class ServicePrincipalConfig(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str
    region: Optional[str] = None


class SubnetInfo(BaseModel):
    subscription_id: str
    resource_group: str
    vnet_name: str
    vnet_location: str
    vnet_address_space: str
    subnet_name: str
    subnet_address_prefix: str
    subnet_nsg: str
    subnet_route_table: str
    private_endpoint_policies: str
    private_link_service_policies: str


class NetworkSummary(BaseModel):
    subscription_id: str
    region: Optional[str]
    vnet_count: int
    subnet_count: int
    items: list[SubnetInfo]


def _get_resource_group_from_id(resource_id: str) -> str:
    parts = resource_id.split("/")
    try:
        idx = parts.index("resourceGroups") + 1
        return parts[idx]
    except ValueError:
        return ""
    except IndexError:
        return ""


def _create_network_client(
    subscription_id: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> NetworkManagementClient:
    try:
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
    except Exception as exc:  # pragma: no cover - 방어적 코드
        raise HTTPException(status_code=400, detail=f"자격 증명 생성 실패: {exc}") from exc

    return NetworkManagementClient(credential=credential, subscription_id=subscription_id)


def _iter_vnet_subnets(client: NetworkManagementClient, config: ServicePrincipalConfig):
    """vNet / Subnet 정보를 순회하면서 공통 포맷으로 반환."""
    sub_id = config.subscription_id

    for vnet in client.virtual_networks.list_all():
        if config.region and getattr(vnet, "location", None) and vnet.location != config.region:
            continue

        vnet_name = vnet.name
        vnet_rg = _get_resource_group_from_id(vnet.id)
        vnet_location = vnet.location
        vnet_address_space = ""
        if getattr(vnet, "address_space", None) and getattr(vnet.address_space, "address_prefixes", None):
            vnet_address_space = ",".join(vnet.address_space.address_prefixes)

        subnets = client.subnets.list(vnet_rg, vnet_name)

        for subnet in subnets:
            subnet_name = subnet.name
            subnet_prefix = ""
            if hasattr(subnet, "address_prefixes") and subnet.address_prefixes:
                subnet_prefix = ",".join(subnet.address_prefixes)
            elif getattr(subnet, "address_prefix", None):
                subnet_prefix = subnet.address_prefix

            subnet_nsg = subnet.network_security_group.id if getattr(subnet, "network_security_group", None) else ""
            subnet_route_table = subnet.route_table.id if getattr(subnet, "route_table", None) else ""
            pe_policies = getattr(subnet, "private_endpoint_network_policies", "") or ""
            pls_policies = getattr(subnet, "private_link_service_network_policies", "") or ""

            yield {
                "subscription_id": sub_id,
                "resource_group": vnet_rg,
                "vnet_name": vnet_name,
                "vnet_location": vnet_location,
                "vnet_address_space": vnet_address_space,
                "subnet_name": subnet_name,
                "subnet_address_prefix": subnet_prefix,
                "subnet_nsg": subnet_nsg,
                "subnet_route_table": subnet_route_table,
                "private_endpoint_policies": pe_policies,
                "private_link_service_policies": pls_policies,
            }


@router.post("/network/summary", response_model=NetworkSummary)
def get_network_summary(config: ServicePrincipalConfig) -> NetworkSummary:
    """선택한 구독/리전에 대한 vNet/Subnet 요약 정보를 반환."""
    if not all([config.subscription_id, config.tenant_id, config.client_id, config.client_secret]):
        raise HTTPException(status_code=400, detail="tenant_id, client_id, client_secret, subscription_id는 필수입니다.")

    client = _create_network_client(
        subscription_id=config.subscription_id,
        tenant_id=config.tenant_id,
        client_id=config.client_id,
        client_secret=config.client_secret,
    )

    items_raw = list(_iter_vnet_subnets(client, config))
    items = [SubnetInfo(**item) for item in items_raw]

    vnet_names = {item.vnet_name for item in items}

    return NetworkSummary(
        subscription_id=config.subscription_id,
        region=config.region,
        vnet_count=len(vnet_names),
        subnet_count=len(items),
        items=items,
    )


@router.post("/export/vnet-subnet")
def export_vnet_subnet(config: ServicePrincipalConfig) -> Response:
    if not all([config.subscription_id, config.tenant_id, config.client_id, config.client_secret]):
        raise HTTPException(status_code=400, detail="tenant_id, client_id, client_secret, subscription_id는 필수입니다.")

    client = _create_network_client(
        subscription_id=config.subscription_id,
        tenant_id=config.tenant_id,
        client_id=config.client_id,
        client_secret=config.client_secret,
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "vnet_subnets"

    ws.append(
        [
            "SubscriptionId",
            "ResourceGroup",
            "VNetName",
            "VNetLocation",
            "VNetAddressSpace",
            "SubnetName",
            "SubnetAddressPrefix",
            "SubnetNSG",
            "SubnetRouteTable",
            "PrivateEndpointPolicies",
            "PrivateLinkServicePolicies",
        ]
    )

    for item in _iter_vnet_subnets(client, config):
        ws.append(
            [
                item["subscription_id"],
                item["resource_group"],
                item["vnet_name"],
                item["vnet_location"],
                item["vnet_address_space"],
                item["subnet_name"],
                item["subnet_address_prefix"],
                item["subnet_nsg"],
                item["subnet_route_table"],
                item["private_endpoint_policies"],
                item["private_link_service_policies"],
            ]
        )

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    headers = {
        "Content-Disposition": 'attachment; filename="azure_vnet_subnets.xlsx"',
    }

    return Response(
        content=stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

