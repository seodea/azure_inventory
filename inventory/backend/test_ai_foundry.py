#!/usr/bin/env python3
"""
AI Foundry 엔드포인트 테스트 스크립트
"""

import os
import requests
import json
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

tenant_id = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
subscription_id = os.getenv("SUBSCRIPTION_ID")
region = os.getenv("REGION", "koreacentral")

if not all([tenant_id, client_id, client_secret, subscription_id]):
    print("❌ 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
    exit(1)

url = "http://localhost:8000/ai-foundry/summary"

payload = {
    "tenant_id": tenant_id,
    "client_id": client_id,
    "client_secret": client_secret,
    "subscription_id": subscription_id,
    "region": region
}

print(f"🔍 AI Foundry 엔드포인트 테스트")
print(f"   URL: {url}")
print(f"   Region: {region}")
print(f"   Subscription: {subscription_id[:8]}...")
print()

try:
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"📊 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print()
        print("✅ 성공!")
        print()
        print(f"   📋 Hub 개수: {data.get('hub_count', 0)}")
        print(f"   📋 Project 개수: {data.get('project_count', 0)}")
        print(f"   📋 Deployment 개수: {data.get('deployment_count', 0)}")
        print()
        
        if data.get('hubs'):
            print("   🏢 Hub 목록:")
            for hub in data['hubs']:
                print(f"      - {hub['name']} ({hub['location']}) - {hub.get('friendly_name', '')}")
        
        if data.get('projects'):
            print()
            print("   📁 Project 목록:")
            for proj in data['projects']:
                print(f"      - {proj['name']} ({proj['location']}) - Hub: {proj.get('hub_name', 'N/A')}")
        
        if data.get('deployments'):
            print()
            print("   🚀 Deployment 목록:")
            for dep in data['deployments']:
                print(f"      - {dep['deployment_name']} @ {dep['endpoint_name']} ({dep['project_name']})")
                print(f"        Model: {dep.get('model_name', 'N/A')} v{dep.get('model_version', 'N/A')}")
        
    else:
        print()
        print("❌ 실패!")
        print()
        print(f"   에러 내용:")
        try:
            error_data = response.json()
            print(f"   {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   {response.text}")

except requests.exceptions.ConnectionError:
    print()
    print("❌ 백엔드 서버에 연결할 수 없습니다.")
    print("   백엔드가 실행 중인지 확인하세요: python main.py")

except requests.exceptions.Timeout:
    print()
    print("⏱️  요청 시간 초과")
    print("   Azure AI Foundry 리소스가 많거나 네트워크가 느릴 수 있습니다.")

except Exception as e:
    print()
    print(f"❌ 예상치 못한 오류: {e}")
