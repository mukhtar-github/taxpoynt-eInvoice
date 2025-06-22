"""
WebSocket Service for Real-Time Dashboard Updates

This service provides WebSocket infrastructure for:
- Real-time metric updates
- Live activity feed streaming
- Integration status notifications
- Critical event alerts
- Dashboard state synchronization
"""
import json
import asyncio
import logging
from typing import Dict, Set, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.services.activity_service import ActivityService
from app.services.metrics_service import MetricsService
from app.models.user import User

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # Store active connections by organization_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store user info for each connection
        self.connection_users: Dict[WebSocket, Dict[str, Any]] = {}
        # Store subscription preferences
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user: User, organization_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Add to organization group
        if organization_id not in self.active_connections:
            self.active_connections[organization_id] = set()
        self.active_connections[organization_id].add(websocket)
        
        # Store user info
        self.connection_users[websocket] = {
            "user_id": user.id,
            "user_email": user.email,
            "organization_id": organization_id,
            "connected_at": datetime.utcnow()
        }
        
        # Default subscriptions
        self.subscriptions[websocket] = {
            "activities", "metrics", "integrations", "alerts"
        }
        
        logger.info(f"WebSocket connected: {user.email} (org: {organization_id})")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        user_info = self.connection_users.get(websocket)
        if user_info:
            organization_id = user_info["organization_id"]
            
            # Remove from organization group
            if organization_id in self.active_connections:
                self.active_connections[organization_id].discard(websocket)
                if not self.active_connections[organization_id]:
                    del self.active_connections[organization_id]
            
            # Clean up user info and subscriptions
            del self.connection_users[websocket]
            self.subscriptions.pop(websocket, None)
            
            logger.info(f"WebSocket disconnected: {user_info['user_email']}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_organization(
        self, 
        message: Dict[str, Any], 
        organization_id: str,
        event_type: str = None
    ):
        """Broadcast a message to all connections in an organization."""
        if organization_id not in self.active_connections:
            return

        # Filter connections by subscription
        connections = self.active_connections[organization_id].copy()
        
        for websocket in connections:
            # Check if user is subscribed to this event type
            if event_type and event_type not in self.subscriptions.get(websocket, set()):
                continue
                
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                self.disconnect(websocket)

    async def broadcast_to_all(self, message: Dict[str, Any], event_type: str = None):
        """Broadcast a message to all active connections."""
        for organization_id in list(self.active_connections.keys()):
            await self.broadcast_to_organization(message, organization_id, event_type)

    def get_connection_count(self, organization_id: str = None) -> int:
        """Get the number of active connections."""
        if organization_id:
            return len(self.active_connections.get(organization_id, set()))
        return sum(len(connections) for connections in self.active_connections.values())

    async def update_subscription(self, websocket: WebSocket, subscriptions: Set[str]):
        """Update subscription preferences for a connection."""
        if websocket in self.subscriptions:
            self.subscriptions[websocket] = subscriptions
            logger.info(f"Updated subscriptions for {self.connection_users[websocket]['user_email']}: {subscriptions}")


# Global connection manager instance
manager = ConnectionManager()


class WebSocketService:
    """Service for handling WebSocket events and broadcasts."""
    
    @staticmethod
    async def broadcast_activity_update(
        db: Session,
        organization_id: str,
        activity_data: Dict[str, Any] = None
    ):
        """Broadcast new activity to all organization connections."""
        try:
            # Get latest activities if no specific data provided
            if not activity_data:
                activities = ActivityService.get_activities(
                    db=db,
                    organization_id=organization_id,
                    limit=5
                )
                activity_data = {
                    "activities": activities,
                    "timestamp": datetime.utcnow().isoformat()
                }

            message = {
                "type": "activity_update",
                "data": activity_data,
                "timestamp": datetime.utcnow().isoformat()
            }

            await manager.broadcast_to_organization(
                message, 
                organization_id, 
                event_type="activities"
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast activity update: {e}")

    @staticmethod
    async def broadcast_metrics_update(
        db: Session,
        organization_id: str,
        metric_type: str = "summary"
    ):
        """Broadcast updated metrics to organization connections."""
        try:
            # Get latest metrics based on type
            if metric_type == "summary":
                metrics_data = MetricsService.get_dashboard_summary(db, organization_id)
            else:
                # Could add other metric types here
                metrics_data = {"type": metric_type, "updated": True}

            message = {
                "type": "metrics_update",
                "metric_type": metric_type,
                "data": metrics_data,
                "timestamp": datetime.utcnow().isoformat()
            }

            await manager.broadcast_to_organization(
                message, 
                organization_id, 
                event_type="metrics"
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast metrics update: {e}")

    @staticmethod
    async def broadcast_integration_status(
        organization_id: str,
        integration_id: str,
        status: str,
        details: Dict[str, Any] = None
    ):
        """Broadcast integration status change."""
        try:
            message = {
                "type": "integration_status",
                "data": {
                    "integration_id": integration_id,
                    "status": status,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            await manager.broadcast_to_organization(
                message, 
                organization_id, 
                event_type="integrations"
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast integration status: {e}")

    @staticmethod
    async def broadcast_critical_alert(
        organization_id: str,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "high",
        details: Dict[str, Any] = None
    ):
        """Broadcast critical alert notification."""
        try:
            alert_message = {
                "type": "critical_alert",
                "data": {
                    "alert_type": alert_type,
                    "title": title,
                    "message": message,
                    "severity": severity,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            await manager.broadcast_to_organization(
                alert_message, 
                organization_id, 
                event_type="alerts"
            )
            
        except Exception as e:
            logger.error(f"Failed to broadcast critical alert: {e}")

    @staticmethod
    async def send_connection_info(websocket: WebSocket):
        """Send connection information to a newly connected client."""
        try:
            user_info = manager.connection_users.get(websocket)
            if user_info:
                message = {
                    "type": "connection_info",
                    "data": {
                        "status": "connected",
                        "organization_id": user_info["organization_id"],
                        "connected_at": user_info["connected_at"].isoformat(),
                        "subscriptions": list(manager.subscriptions.get(websocket, set())),
                        "total_connections": manager.get_connection_count(
                            user_info["organization_id"]
                        )
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.send_personal_message(message, websocket)
                
        except Exception as e:
            logger.error(f"Failed to send connection info: {e}")

    @staticmethod
    async def handle_client_message(
        websocket: WebSocket,
        message: Dict[str, Any],
        db: Session
    ):
        """Handle incoming messages from clients."""
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe":
                # Update subscription preferences
                subscriptions = set(message.get("subscriptions", []))
                await manager.update_subscription(websocket, subscriptions)
                
            elif message_type == "ping":
                # Respond to ping with pong
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )
                
            elif message_type == "request_update":
                # Client requesting specific data update
                user_info = manager.connection_users.get(websocket)
                if user_info:
                    data_type = message.get("data_type")
                    organization_id = user_info["organization_id"]
                    
                    if data_type == "activities":
                        await WebSocketService.broadcast_activity_update(
                            db, organization_id
                        )
                    elif data_type == "metrics":
                        await WebSocketService.broadcast_metrics_update(
                            db, organization_id
                        )
                        
        except Exception as e:
            logger.error(f"Failed to handle client message: {e}")


# Background task for periodic updates
class BackgroundUpdater:
    """Background service for periodic WebSocket updates."""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.is_running = False
        
    async def start_periodic_updates(self, interval: int = 30):
        """Start periodic updates for all active connections."""
        self.is_running = True
        
        while self.is_running:
            try:
                # Only update if there are active connections
                if manager.get_connection_count() > 0:
                    db = self.db_session_factory()
                    try:
                        # Update metrics for all organizations with active connections
                        for organization_id in manager.active_connections.keys():
                            await WebSocketService.broadcast_metrics_update(
                                db, organization_id
                            )
                            await WebSocketService.broadcast_activity_update(
                                db, organization_id
                            )
                    finally:
                        db.close()
                        
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in periodic updates: {e}")
                await asyncio.sleep(interval)
    
    def stop_periodic_updates(self):
        """Stop periodic updates."""
        self.is_running = False