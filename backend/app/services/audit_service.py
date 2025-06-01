"""
Audit logging service for TaxPoynt eInvoice Platform functionality.

This service provides a centralized way to record audit logs for transmission operations
to support compliance requirements, security analysis, and troubleshooting.
"""

import logging
from typing import Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime
from fastapi import Request

from sqlalchemy.orm import Session
from app.models.transmission_audit_log import TransmissionAuditLog, AuditActionType
from app.db.session import get_db

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs for platform operations."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def log_transmission_action(
        self,
        action_type: Union[AuditActionType, str],
        transmission_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        action_status: str = "success",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_path: Optional[str] = None,
        request_method: Optional[str] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_code: Optional[int] = None,
        error_message: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> TransmissionAuditLog:
        """
        Log an action related to transmission operations.
        
        Args:
            action_type: Type of action being performed
            transmission_id: UUID of the transmission if applicable
            organization_id: UUID of the organization
            user_id: UUID of the user performing the action
            action_status: Status of the action (success, failure)
            ip_address: IP address of the client
            user_agent: User agent string of the client
            resource_path: API endpoint or resource identifier
            request_method: HTTP method
            request_body: Sanitized request body
            response_code: HTTP response code
            error_message: Error details if applicable
            context_data: Additional contextual information
            
        Returns:
            The created audit log entry
        """
        try:
            # Create audit log entry
            audit_log = TransmissionAuditLog(
                transmission_id=transmission_id,
                action_type=action_type,
                action_timestamp=datetime.now(),
                action_status=action_status,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                organization_id=organization_id,
                resource_path=resource_path,
                request_method=request_method,
                request_body=request_body,
                response_code=response_code,
                error_message=error_message,
                context_data=context_data
            )
            
            # Add and commit
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            return audit_log
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create audit log: {str(e)}")
            # Still log to application logs even if DB insert failed
            logger.info(
                f"AUDIT: {action_type} | transmission={transmission_id} | "
                f"user={user_id} | status={action_status} | error={error_message}"
            )
            raise
    
    @staticmethod
    def from_request(request: Request, db: Optional[Session] = None) -> 'AuditService':
        """
        Create an AuditService instance from a FastAPI request.
        
        Args:
            request: The FastAPI request object
            db: Optional database session
            
        Returns:
            AuditService instance
        """
        if db is None:
            # Get DB session from request state if available
            db = request.state.db if hasattr(request.state, 'db') else next(get_db())
            
        return AuditService(db)
    
    def log_request(
        self,
        request: Request,
        action_type: Union[AuditActionType, str],
        transmission_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        action_status: str = "success",
        response_code: Optional[int] = None,
        error_message: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> TransmissionAuditLog:
        """
        Log an API request with details extracted from the request object.
        
        Args:
            request: The FastAPI request object
            action_type: Type of action being performed
            transmission_id: UUID of the transmission if applicable
            organization_id: UUID of the organization
            user_id: UUID of the user performing the action
            action_status: Status of the action (success, failure)
            response_code: HTTP response code
            error_message: Error details if applicable
            context_data: Additional contextual information
            
        Returns:
            The created audit log entry
        """
        # Extract request details
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        request_method = request.method
        resource_path = request.url.path
        
        # Extract request body if available (with sanitization for sensitive data)
        request_body = None
        if hasattr(request, "body"):
            try:
                # Only attempt to get JSON body for POST/PUT/PATCH requests
                if request_method in ["POST", "PUT", "PATCH"] and hasattr(request, "_json"):
                    body_json = request._json
                    # Sanitize sensitive fields
                    if isinstance(body_json, dict):
                        sanitized_body = body_json.copy()
                        for sensitive_field in ["password", "token", "secret", "key"]:
                            if sensitive_field in sanitized_body:
                                sanitized_body[sensitive_field] = "***REDACTED***"
                        request_body = sanitized_body
            except:
                # If we can't access the body, don't include it
                pass
        
        return self.log_transmission_action(
            action_type=action_type,
            transmission_id=transmission_id,
            organization_id=organization_id,
            user_id=user_id,
            action_status=action_status,
            ip_address=client_host,
            user_agent=user_agent,
            resource_path=resource_path,
            request_method=request_method,
            request_body=request_body,
            response_code=response_code,
            error_message=error_message,
            context_data=context_data
        )
