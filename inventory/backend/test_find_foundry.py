#!/usr/bin/env python3
"""
AI Foundry 리소스 타입 찾기 스크립트
"""

import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient

load_dotenv()

tenant_id = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
subscription_id = os.getenv("SUBSCRIPTION_ID")

credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

resource_client = ResourceManagementClient(credential, subscription_id)

print("🔍 모든 리소스 타입 검색 중...")
print()

# 모든 리소스 조회
all_resources = {}
foundry_resources = []

for resource in resource_client.resources.list():
    resource_type = resource.type
    
    # 리소스 타입별 카운트
    if resource_type not in all_resources:
        all_resources[resource_type] = []
    all_resources[resource_type].append(resource.name)
    
    # "foundry" 또는 "ai" 관련 리소스 필터링
    if any(keyword in resource_type.lower() for keyword in ['foundry', 'aiservices', 'cognitiveservices', 'machinelearning']):
        foundry_resources.append({
            'name': resource.name,
            'type': resource.type,
            'location': resource.location,
            'id': resource.id
        })

print(f"📊 전체 리소스 타입: {len(all_resources)}개")
print()

print("🎯 AI/Foundry 관련 리소스:")
print()

if foundry_resources:
    for res in foundry_resources:
        print(f"  📦 {res['name']}")
        print(f"     타입: {res['type']}")
        print(f"     위치: {res['location']}")
        print(f"     ID: {res['id']}")
        print()
else:
    print("  ❌ AI/Foundry 관련 리소스를 찾을 수 없습니다.")
    print()

print("=" * 80)
print()
print("📋 모든 리소스 타입 목록:")
print()

for resource_type, names in sorted(all_resources.items()):
    print(f"  {resource_type}: {len(names)}개")
    if len(names) <= 3:
        for name in names:
            print(f"    - {name}")
