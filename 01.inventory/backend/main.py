from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from network       import router as network_router
from nsg           import router as nsg_router
from route_table   import router as route_table_router
from public_ip     import router as public_ip_router
from load_balancer import router as load_balancer_router
from app_gateway   import router as app_gateway_router
from virtual_wan   import router as virtual_wan_router
from virtual_hub   import router as virtual_hub_router
from vpn_gateway   import router as vpn_gateway_router
from express_route import router as express_route_router
from vm            import router as vm_router
from cae           import router as cae_router
from aca           import router as aca_router
from acr           import router as acr_router
from mongodb       import router as mongodb_router
from postgresql    import router as postgresql_router
from redis_cache   import router as redis_router
from aks           import router as aks_router
from ai_foundry    import router as ai_foundry_router
from ai_search     import router as ai_search_router
from aoai          import router as aoai_router
from subscriptions import router as subscriptions_router
from export        import router as export_router
from session       import router as session_router

app = FastAPI(title="Azure Inventory API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

# 세션 관리
app.include_router(session_router)

# 네트워킹
app.include_router(network_router)
app.include_router(nsg_router)
app.include_router(route_table_router)
app.include_router(public_ip_router)
app.include_router(load_balancer_router)
app.include_router(app_gateway_router)
app.include_router(virtual_wan_router)
app.include_router(virtual_hub_router)
app.include_router(vpn_gateway_router)
app.include_router(express_route_router)

# 컴퓨트
app.include_router(vm_router)

# 컨테이너
app.include_router(cae_router)
app.include_router(aca_router)
app.include_router(acr_router)
app.include_router(aks_router)

# 데이터베이스
app.include_router(mongodb_router)
app.include_router(postgresql_router)
app.include_router(redis_router)

# AI / 분석
app.include_router(ai_foundry_router)
app.include_router(ai_search_router)
app.include_router(aoai_router)

# 구독 목록
app.include_router(subscriptions_router)

# 엑셀 내보내기
app.include_router(export_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)