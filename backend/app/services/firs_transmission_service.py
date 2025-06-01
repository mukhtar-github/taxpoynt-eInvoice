"""
FIRS Transmission Service

This module provides specialized functionality for secure transmissions to FIRS API.
It handles encryption, digital signatures, retry logic, and receipt storage.
"""

import base64
import json
import logging
import uuid
import httpx
import backoff
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.models.certificate import Certificate
from app.models.receipt import TransmissionReceipt
from app.schemas.transmission import TransmissionCreate, TransmissionUpdate
from app.services.transmission_service import TransmissionService
from app.utils.firs_encryption import FIRSEncryptionUtility
from app.core.config import settings

logger = logging.getLogger(__name__)

class FIRSTransmissionService:
    """Service for secure FIRS API transmissions with enhanced security."""
    
    def __init__(self, db: Session):
        self.db = db
        self.transmission_service = TransmissionService(db)
        
        # Initialize FIRS encryption utility with the public key path from settings
        self.encryption_utility = FIRSEncryptionUtility(
            public_key_path=settings.FIRS_PUBLIC_KEY_PATH
        )
        
        # FIRS API endpoints
        self.api_endpoints = {
            "auth": f"{settings.FIRS_API_BASE_URL}/auth/token",
            "invoice_submission": f"{settings.FIRS_API_BASE_URL}/einvoice/submit",
            "batch_submission": f"{settings.FIRS_API_BASE_URL}/einvoice/batch-submit",
            "status": f"{settings.FIRS_API_BASE_URL}/einvoice/status"
        }
        
    async def _get_auth_token(self) -> str:
        """
        Get authentication token from FIRS API.
        
        Returns:
            Authentication token string
        
        Raises:
            ValueError: If authentication fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_endpoints["auth"],
                    json={
                        "client_id": settings.FIRS_CLIENT_ID,
                        "client_secret": settings.FIRS_CLIENT_SECRET,
                        "grant_type": "client_credentials"
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"FIRS authentication failed: {response.status_code} - {response.text}")
                    raise ValueError(f"FIRS authentication failed: {response.status_code}")
                    
                auth_data = response.json()
                return auth_data.get("access_token")
        except Exception as e:
            logger.error(f"Error getting FIRS auth token: {str(e)}")
            raise ValueError(f"Failed to authenticate with FIRS API: {str(e)}")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, httpx.HTTPStatusError, ValueError),
        max_tries=3,
        giveup=lambda e: isinstance(e, ValueError) and "authentication failed" in str(e).lower()
    )
    async def transmit_to_firs(
        self, 
        transmission_id: UUID,
        retrying: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Transmit a payload to FIRS API with secure encryption and retry capabilities.
        
        Args:
            transmission_id: ID of the transmission record
            retrying: Whether this is a retry attempt
            
        Returns:
            Tuple of (success: bool, response_data: Dict)
        """
        # Get the transmission record
        transmission = self.db.query(TransmissionRecord).filter(
            TransmissionRecord.id == transmission_id
        ).first()
        
        if not transmission:
            raise ValueError(f"Transmission record {transmission_id} not found")
            
        # Update status to in progress
        if not retrying:
            transmission.status = TransmissionStatus.IN_PROGRESS
            self.db.commit()
            
        try:
            # Get auth token
            auth_token = await self._get_auth_token()
            
            # Determine endpoint based on metadata
            is_batch = transmission.transmission_metadata.get("is_batch", False)
            endpoint_key = "batch_submission" if is_batch else "invoice_submission"
            
            # Add security headers
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Transmission-ID": str(transmission.id),
                "X-Client-Certificate-ID": str(transmission.certificate_id) if transmission.certificate_id else ""
            }
            
            # Send the request with exponential backoff for retries
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_endpoints[endpoint_key],
                    content=transmission.encrypted_payload,
                    headers=headers
                )
                
                # Process response
                response_data = response.json() if response.status_code in (200, 201, 202) else {}
                success = response.status_code in (200, 201, 202)
                
                # Update transmission record
                if success:
                    transmission.status = TransmissionStatus.COMPLETED
                    transmission.response_data = response_data
                    
                    # Create receipt record
                    receipt = self._create_receipt(transmission, response_data)
                else:
                    transmission.status = TransmissionStatus.FAILED
                    transmission.response_data = {
                        "error": {
                            "status_code": response.status_code,
                            "message": response.text
                        }
                    }
                
                # Update metadata with transmission result
                metadata = transmission.transmission_metadata or {}
                metadata["last_transmission"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": success,
                    "status_code": response.status_code
                }
                
                if retrying:
                    retry_history = metadata.get("retry_history", [])
                    if retry_history:
                        retry_history[-1]["status"] = "completed" if success else "failed"
                        retry_history[-1]["response_code"] = response.status_code
                        metadata["retry_history"] = retry_history
                
                transmission.transmission_metadata = metadata
                self.db.commit()
                
                return success, response_data
                
        except Exception as e:
            logger.error(f"Error transmitting to FIRS: {str(e)}")
            
            # Update transmission record with error
            transmission.status = TransmissionStatus.FAILED
            
            # Update metadata with error
            metadata = transmission.transmission_metadata or {}
            metadata["last_transmission"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
            
            if retrying:
                retry_history = metadata.get("retry_history", [])
                if retry_history:
                    retry_history[-1]["status"] = "failed"
                    retry_history[-1]["error"] = str(e)
                    metadata["retry_history"] = retry_history
                    
            transmission.transmission_metadata = metadata
            self.db.commit()
            
            return False, {"error": str(e)}
    
    async def create_firs_transmission(
        self,
        payload: Dict[str, Any],
        organization_id: UUID,
        certificate_id: Optional[UUID] = None,
        submission_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None,
        max_retries: int = 3
    ) -> TransmissionRecord:
        """
        Create and prepare a secure transmission to FIRS.
        
        Args:
            payload: The data to transmit
            organization_id: Organization ID
            certificate_id: Optional certificate ID for signing
            submission_id: Optional submission ID
            metadata: Additional metadata
            user_id: User ID creating the transmission
            max_retries: Maximum retry attempts
            
        Returns:
            The created transmission record
        """
        if not payload:
            raise ValueError("No payload provided for FIRS transmission")
            
        # Prepare metadata
        transmission_metadata = metadata or {}
        transmission_metadata.update({
            "destination": "FIRS",
            "is_batch": isinstance(payload, list),
            "created_at": datetime.utcnow().isoformat(),
            "encryption_standard": "FIRS-RSA-OAEP-AES-256-GCM"
        })
        
        # Encrypt the payload with FIRS encryption utility
        encrypted_payload, encryption_metadata = self.encryption_utility.encrypt_firs_payload(payload)
        
        # Create transmission create schema
        transmission_in = TransmissionCreate(
            organization_id=organization_id,
            certificate_id=certificate_id,
            submission_id=submission_id,
            payload=payload,  # Original payload
            encrypt_payload=True,  # Encryption already handled
            destination="FIRS",
            destination_endpoint=self.api_endpoints["invoice_submission"],
            max_retries=max_retries,
            retry_delay_seconds=300,  # 5 minutes
            metadata=transmission_metadata
        )
        
        # Create the transmission record
        transmission_record = self.transmission_service.create_transmission(
            transmission_in=transmission_in,
            user_id=user_id
        )
        
        # Override with our pre-encrypted payload
        transmission_record.encrypted_payload = encrypted_payload
        transmission_record.encryption_metadata = encryption_metadata
        self.db.commit()
        
        return transmission_record
    
    def _create_receipt(self, transmission: TransmissionRecord, response_data: Dict[str, Any]) -> TransmissionReceipt:
        """
        Create a transmission receipt from successful response.
        
        Args:
            transmission: The transmission record
            response_data: Response data from FIRS
            
        Returns:
            The created receipt record
        """
        # Extract receipt data from FIRS response
        receipt_data = {
            "receipt_id": response_data.get("receipt_id", str(uuid.uuid4())),
            "transmission_id": str(transmission.id),
            "submission_id": str(transmission.submission_id) if transmission.submission_id else None,
            "timestamp": response_data.get("timestamp", datetime.utcnow().isoformat()),
            "status": response_data.get("status", "COMPLETED"),
            "receipt_data": response_data
        }
        
        # Create receipt record
        receipt = TransmissionReceipt(
            id=uuid.uuid4(),
            transmission_id=transmission.id,
            organization_id=transmission.organization_id,
            receipt_id=receipt_data["receipt_id"],
            receipt_timestamp=datetime.fromisoformat(receipt_data["timestamp"]) if isinstance(receipt_data["timestamp"], str) else datetime.utcnow(),
            receipt_data=receipt_data,
            verification_status="PENDING",
            created_at=datetime.utcnow()
        )
        
        self.db.add(receipt)
        self.db.commit()
        
        return receipt
    
    async def check_transmission_status(self, transmission_id: UUID) -> Dict[str, Any]:
        """
        Check the status of a transmission with FIRS.
        
        Args:
            transmission_id: ID of the transmission record
            
        Returns:
            Status information dict
        """
        # Get the transmission record
        transmission = self.db.query(TransmissionRecord).filter(
            TransmissionRecord.id == transmission_id
        ).first()
        
        if not transmission:
            raise ValueError(f"Transmission record {transmission_id} not found")
            
        # If the transmission is not completed, return current status
        if transmission.status != TransmissionStatus.COMPLETED:
            return {
                "transmission_id": str(transmission.id),
                "status": transmission.status,
                "last_updated": transmission.transmission_metadata.get("last_transmission", {}).get(
                    "timestamp", datetime.utcnow().isoformat()
                )
            }
            
        try:
            # Get auth token
            auth_token = await self._get_auth_token()
            
            # Extract FIRS reference from response data
            firs_reference = None
            if transmission.response_data:
                firs_reference = transmission.response_data.get("submission_id") or \
                                transmission.response_data.get("reference_id") or \
                                transmission.response_data.get("receipt_id")
            
            if not firs_reference:
                return {
                    "transmission_id": str(transmission.id),
                    "status": "UNKNOWN",
                    "error": "No FIRS reference found in response data"
                }
                
            # Query FIRS status endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_endpoints['status']}/{firs_reference}",
                    headers={
                        "Authorization": f"Bearer {auth_token}",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    
                    # Update metadata with latest status
                    metadata = transmission.transmission_metadata or {}
                    metadata["status_history"] = metadata.get("status_history", [])
                    metadata["status_history"].append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": status_data.get("status"),
                        "details": status_data
                    })
                    
                    transmission.transmission_metadata = metadata
                    self.db.commit()
                    
                    return status_data
                else:
                    return {
                        "transmission_id": str(transmission.id),
                        "status": "ERROR",
                        "error": f"Status check failed: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error checking transmission status: {str(e)}")
            return {
                "transmission_id": str(transmission.id),
                "status": "ERROR",
                "error": f"Status check failed: {str(e)}"
            }
