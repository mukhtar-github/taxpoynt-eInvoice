from fastapi import APIRouter

from app.api.endpoints import auth, client, integration
 
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(client.router, prefix="/clients", tags=["clients"])
api_router.include_router(integration.router, prefix="/integrations", tags=["integrations"]) 