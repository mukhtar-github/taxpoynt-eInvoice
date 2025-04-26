from fastapi import APIRouter

from app.api.endpoints import auth, client, integration, irn
 
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(client.router, prefix="/clients", tags=["clients"])
api_router.include_router(integration.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(irn.router, prefix="/irn", tags=["irn"]) 