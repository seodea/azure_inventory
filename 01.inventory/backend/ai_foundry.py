from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from common import ServicePrincipalConfig, get_credential, validate_config, normalize_region

router = APIRouter()


# ── 응답 모델 ─────────────────────────────────────────────────────────────────

class FoundryHubInfo(BaseModel):
    name: str
    resource_group: str
    location: str
    sku: str
    friendly_name: str
    public_network_access: str
    provisioning_state: str


class FoundryProjectInfo(BaseModel):
    name: str
    resource_group: str
    location: str
    hub_name: str
    friendly_name: str
    public_network_access: str
    provisioning_state: str


class FoundryDeploymentInfo(BaseModel):
    project_name: str
    resource_group: str
    endpoint_name: str
    deployment_name: str
    model_name: str
    model_version: str
    model_format: str
    instance_type: str
    provisioning_state: str


class FoundrySummary(BaseModel):
    subscription_id: str
    region: Optional[str]
    # kind별로 분류
    foundry_count: int           # AIServices만
    speech_count: int            # SpeechServices
    form_recognizer_count: int   # FormRecognizer
    # 기존 유지
    hub_count: int
    project_count: int
    deployment_count: int
    # 상세 리스트
    foundry_list: list[FoundryHubInfo]
    speech_list: list[FoundryHubInfo]
    form_recognizer_list: list[FoundryHubInfo]
    hubs: list[FoundryHubInfo]
    projects: list[FoundryProjectInfo]
    deployments: list[FoundryDeploymentInfo]


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _rg(resource_id: str) -> str:
    parts = (resource_id or "").split("/")
    return parts[4] if len(parts) > 4 else ""


def _get_ml_client(credential, sub_id: str):
    try:
        from azure.mgmt.machinelearningservices import AzureMachineLearningWorkspaces
        return AzureMachineLearningWorkspaces(
            credential=credential,
            subscription_id=sub_id,
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail=(
                "azure-mgmt-machinelearningservices 패키지가 필요합니다. "
                "pip install azure-mgmt-machinelearningservices"
            ),
        )


def _get_resource_client(credential, sub_id: str):
    """Azure Resource Management 클라이언트 생성 (모든 리소스 조회용)"""
    try:
        from azure.mgmt.resource import ResourceManagementClient
        return ResourceManagementClient(
            credential=credential,
            subscription_id=sub_id,
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="azure-mgmt-resource 패키지가 필요합니다."
        )


def _get_cognitive_client(credential, sub_id: str):
    """Azure Cognitive Services 클라이언트 생성"""
    try:
        from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
        return CognitiveServicesManagementClient(
            credential=credential,
            subscription_id=sub_id,
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="azure-mgmt-cognitiveservices 패키지가 필요합니다."
        )


def _parse_model_info(model) -> tuple[str, str, str]:
    """model 필드에서 (name, version, format) 추출. arm id 문자열도 처리."""
    if not model:
        return "", "", ""
    # ARM ID 문자열인 경우: .../models/{name}/versions/{version}
    if isinstance(model, str):
        parts = model.split("/")
        try:
            name    = parts[parts.index("models") + 1]
            version = parts[parts.index("versions") + 1]
        except (ValueError, IndexError):
            name    = parts[-1]
            version = ""
        return name, version, ""
    # 객체인 경우
    name    = getattr(model, "name", "")    or getattr(model, "model_name", "")    or ""
    version = getattr(model, "version", "") or getattr(model, "model_version", "") or ""
    fmt     = getattr(model, "format", "")  or getattr(model, "model_format", "")  or ""
    return str(name), str(version), str(fmt)


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post("/ai-foundry/summary", response_model=FoundrySummary)
def get_ai_foundry_summary(config: ServicePrincipalConfig) -> FoundrySummary:
    validate_config(config)

    credential        = get_credential(config.tenant_id, config.client_id, config.client_secret)
    ml_client         = _get_ml_client(credential, config.subscription_id)
    resource_client   = _get_resource_client(credential, config.subscription_id)
    cognitive_client  = _get_cognitive_client(credential, config.subscription_id)
    region_norm       = normalize_region(config.region)

    # kind별로 분류
    foundry_list:          list[FoundryHubInfo] = []  # AIServices
    speech_list:           list[FoundryHubInfo] = []  # SpeechServices
    form_recognizer_list:  list[FoundryHubInfo] = []  # FormRecognizer
    
    hubs:        list[FoundryHubInfo]        = []
    projects:    list[FoundryProjectInfo]    = []
    deployments: list[FoundryDeploymentInfo] = []

    # ── CognitiveServices 리소스 조회 ──────────────────────────────────────
    try:
        # AI Foundry = Microsoft.CognitiveServices/accounts만 조회
        foundry_filters = [
            "resourceType eq 'Microsoft.CognitiveServices/accounts'",
        ]
        
        for filter_str in foundry_filters:
            try:
                resources = resource_client.resources.list(filter=filter_str)
                
                for resource in resources:
                    # Region 필터링
                    if region_norm and normalize_region(resource.location) != region_norm:
                        continue
                    
                    rg = resource.id.split('/')[4]  # resource group 추출
                    
                    # Microsoft.CognitiveServices/accounts 상세 정보 조회
                    try:
                        account = cognitive_client.accounts.get(rg, resource.name)
                        
                        loc  = getattr(account, "location", "") or ""
                        sku  = str(account.sku.name) if getattr(account, "sku", None) else ""
                        kind = str(getattr(account, "kind", "") or "")
                        
                        # properties 접근
                        props = getattr(account, "properties", None)
                        if props:
                            pna = str(getattr(props, "public_network_access", "") or "")
                            ps  = str(getattr(props, "provisioning_state", "") or "")
                        else:
                            pna = ""
                            ps  = ""
                        
                        # kind에 따라 분류
                        info = FoundryHubInfo(
                            name=account.name or "",
                            resource_group=rg,
                            location=loc,
                            sku=sku,
                            friendly_name=f"{kind}",
                            public_network_access=pna,
                            provisioning_state=ps,
                        )
                        
                        if kind == "AIServices":
                            foundry_list.append(info)
                        elif kind == "SpeechServices":
                            speech_list.append(info)
                        elif kind == "FormRecognizer":
                            form_recognizer_list.append(info)
                        else:
                            # 기타는 hubs에 포함
                            hubs.append(info)
                            
                    except Exception:
                        # 개별 리소스 조회 실패는 무시
                        continue
            except Exception:
                # 필터 조회 실패는 무시
                continue
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Foundry 리소스 조회 실패: {e}")

    # ── 배포 모델 수집 (Project별 online endpoint → deployment) ──────────────
    for proj in projects:
        try:
            for ep in ml_client.online_endpoints.list(proj.resource_group, proj.name):
                ep_name = ep.name or ""
                try:
                    for dep in ml_client.online_deployments.list(
                        proj.resource_group, proj.name, ep_name
                    ):
                        m_name, m_version, m_fmt = _parse_model_info(
                            getattr(dep, "model", None)
                        )
                        deployments.append(FoundryDeploymentInfo(
                            project_name=proj.name,
                            resource_group=proj.resource_group,
                            endpoint_name=ep_name,
                            deployment_name=dep.name or "",
                            model_name=m_name,
                            model_version=m_version,
                            model_format=m_fmt,
                            instance_type=str(getattr(dep, "instance_type", "") or ""),
                            provisioning_state=str(getattr(dep, "provisioning_state", "") or ""),
                        ))
                except Exception:
                    continue
        except Exception:
            continue

    return FoundrySummary(
        subscription_id=config.subscription_id,
        region=config.region,
        # kind별 카운트
        foundry_count=len(foundry_list),
        speech_count=len(speech_list),
        form_recognizer_count=len(form_recognizer_list),
        # 기존 필드 (하위 호환성)
        hub_count=len(hubs),
        project_count=len(projects),
        deployment_count=len(deployments),
        # 상세 리스트
        foundry_list=foundry_list,
        speech_list=speech_list,
        form_recognizer_list=form_recognizer_list,
        hubs=hubs,
        projects=projects,
        deployments=deployments,
    )