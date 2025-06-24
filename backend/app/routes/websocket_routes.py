"""
WebSocket Routes for Real-Time Dashboard Updates

Provides WebSocket endpoints for:
- Real-time dashboard metrics
- Live activity feed updates
- Integration status notifications
- Critical event alerts
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user_websocket
from app.services.websocket_service import manager, WebSocketService
from app.models.user import User
from app.schemas.user import User as UserSchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/dashboard/{organization_id}")
async def websocket_dashboard_endpoint(
    websocket: WebSocket,
    organization_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> None:
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Provides:
    - Real-time activity feed updates
    - Live metrics streaming
    - Integration status notifications
    - Critical event alerts
    
    Authentication via token query parameter or header.
    """
    # Authenticate user
    try:
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication required")
            return
            
        # Verify user has access to organization
        if hasattr(user, 'organization_id') and user.organization_id != organization_id:
            await websocket.close(code=4003, reason="Access denied to organization")
            return
            
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Connect to WebSocket manager
    await manager.connect(websocket, user, organization_id)
    
    try:
        # Send initial connection info
        await WebSocketService.send_connection_info(websocket)
        
        # Send initial data
        await WebSocketService.broadcast_activity_update(db, organization_id)
        await WebSocketService.broadcast_metrics_update(db, organization_id)
        
        # Listen for client messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client message
                await WebSocketService.handle_client_message(websocket, message, db)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": "2025-06-22T12:00:00Z"
                    },
                    websocket
                )
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message(
                    {
                        "type": "error", 
                        "message": "Internal server error",
                        "timestamp": "2025-06-22T12:00:00Z"
                    },
                    websocket
                )
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/activities/{organization_id}")
async def websocket_activities_endpoint(
    websocket: WebSocket,
    organization_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> None:
    """
    WebSocket endpoint specifically for activity feed updates.
    Lightweight endpoint for clients that only need activity updates.
    """
    # Authenticate user
    try:
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication required")
            return
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect(websocket, user, organization_id)
    
    # Subscribe only to activities
    await manager.update_subscription(websocket, {"activities"})
    
    try:
        # Send initial activity data
        await WebSocketService.broadcast_activity_update(db, organization_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle activity-specific messages
                if message.get("type") == "request_activities":
                    await WebSocketService.broadcast_activity_update(db, organization_id)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in activities WebSocket: {e}")
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/integrations/{organization_id}")
async def websocket_integrations_endpoint(
    websocket: WebSocket,
    organization_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> None:
    """
    WebSocket endpoint for integration status updates.
    Provides real-time integration health and sync status.
    """
    # Authenticate user
    try:
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication required")
            return
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect(websocket, user, organization_id)
    
    # Subscribe only to integrations
    await manager.update_subscription(websocket, {"integrations"})
    
    try:
        # Send initial integration status (could be implemented)
        initial_message = {
            "type": "integration_status",
            "data": {
                "message": "Integration monitoring started",
                "timestamp": "2025-06-22T12:00:00Z"
            }
        }
        await manager.send_personal_message(initial_message, websocket)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle integration-specific messages
                if message.get("type") == "request_integration_status":
                    # Could trigger integration status check
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in integrations WebSocket: {e}")
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


# Helper endpoint to get WebSocket connection info
@router.get("/ws/status")
async def get_websocket_status(
    organization_id: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user_websocket)
):
    """Get WebSocket connection statistics."""
    return {
        "total_connections": manager.get_connection_count(),
        "organization_connections": manager.get_connection_count(organization_id) if organization_id else None,
        "active_organizations": list(manager.active_connections.keys()),
        "status": "active"
    }