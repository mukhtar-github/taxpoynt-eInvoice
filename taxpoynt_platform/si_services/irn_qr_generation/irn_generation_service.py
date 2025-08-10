"""
FIRS SI IRN Generation Service (Refactored)

Refactored service that uses granular components to eliminate duplication.
Maintains backward compatibility while leveraging the new architecture.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List, Union, Set
from sqlalchemy.orm import Session

# Import granular components
from .irn_generator import IRNGenerator
from .qr_code_generator import QRCodeGenerator
from .sequence_manager import SequenceManager
from .duplicate_detector import DuplicateDetector
from .irn_validator import IRNValidator, ValidationLevel

# Import authentication services for FIRS integration
from taxpoynt_platform.si_services.authentication import (
    FIRSAuthService,
    AuthenticationManager,
    AuthenticationError
)

# Legacy imports for backward compatibility
from app.core.config import settings
from app.models.irn import IRNRecord, InvoiceData, IRNValidationRecord, IRNStatus
from app.models.user import User
from app.models.organization import Organization
from app.schemas.irn import IRNCreate, IRNBatchGenerateRequest
from app.cache.irn_cache import IRNCache

logger = logging.getLogger(__name__)


class IRNGenerationService:
    """
    Refactored IRN Generation Service using granular components.
    
    This service maintains the same interface as the original monolithic service
    but delegates all functionality to the appropriate granular components.
    """
    
    def __init__(self, auth_manager: Optional[AuthenticationManager] = None):
        # Initialize granular components
        self.irn_generator = IRNGenerator()
        self.qr_generator = QRCodeGenerator()
        self.sequence_manager = SequenceManager()
        self.duplicate_detector = DuplicateDetector()
        self.irn_validator = IRNValidator()
        
        # Initialize authentication services for FIRS integration
        self.auth_manager = auth_manager or AuthenticationManager()
        self.firs_auth_service = FIRSAuthService()
        
        # Cache for performance
        self.irn_cache = IRNCache()
    
    def generate_irn(self, invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Generate IRN using granular components (eliminates duplication)
        
        Args:
            invoice_data: Dictionary containing invoice details
            
        Returns:
            Tuple containing (irn_value, verification_code, hash_value)
        """
        try:
            # Check for duplicates first
            existing_irn = self.duplicate_detector.check_duplicate_invoice(invoice_data)
            if existing_irn:
                logger.warning(f"Duplicate invoice detected. Existing IRN: {existing_irn}")
                raise ValueError(f"Invoice already has IRN: {existing_irn}")
            
            # Generate IRN using granular component
            irn_value, verification_code, hash_value = self.irn_generator.generate_irn(invoice_data)
            
            # Validate generated IRN
            validation_result = self.irn_validator.validate_irn(
                irn_value=irn_value,
                verification_code=verification_code,
                validation_level=ValidationLevel.STANDARD
            )
            
            if not validation_result.is_valid:
                error_msg = f"Generated IRN failed validation: {', '.join(validation_result.errors)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Log warnings if any
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"IRN validation warning: {warning}")
            
            # Register IRN to prevent future duplicates
            organization_id = invoice_data.get('organization_id', 'unknown')
            registration_success = self.duplicate_detector.register_irn(
                irn_value=irn_value,
                invoice_data=invoice_data,
                organization_id=organization_id
            )
            
            if not registration_success:
                logger.error("Failed to register IRN for duplicate detection")
                raise ValueError("IRN registration failed")
            
            # Cache the result
            if hasattr(self.irn_cache, 'set'):
                cache_key = f"irn_{irn_value}"
                cache_data = {
                    'irn_value': irn_value,
                    'verification_code': verification_code,
                    'hash_value': hash_value,
                    'generated_at': datetime.now().isoformat()
                }
                self.irn_cache.set(cache_key, cache_data, ttl=3600)  # 1 hour TTL
            
            logger.info(f"Successfully generated IRN: {irn_value} for invoice: {invoice_data.get('invoice_number', '')}")
            
            return irn_value, verification_code, hash_value
            
        except Exception as e:
            logger.error(f"Error generating IRN: {str(e)}")
            raise
    
    async def generate_irn_async(self, invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Async version of IRN generation"""
        return self.generate_irn(invoice_data)
    
    def generate_qr_code(
        self,
        irn_value: str,
        verification_code: str,
        invoice_data: Dict[str, Any],
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate QR code using granular component
        
        Args:
            irn_value: Generated IRN
            verification_code: IRN verification code
            invoice_data: Invoice data
            format_type: QR code format (json, compact, url)
            
        Returns:
            QR code data and image information
        """
        try:
            # Generate QR data
            qr_data = self.qr_generator.generate_qr_data(
                irn_value=irn_value,
                verification_code=verification_code,
                invoice_data=invoice_data
            )
            
            # Generate QR string
            qr_string = self.qr_generator.generate_qr_string(
                irn_value=irn_value,
                verification_code=verification_code,
                invoice_data=invoice_data,
                format_type=format_type
            )
            
            # Generate QR code image
            qr_image_info = self.qr_generator.generate_qr_code_image(qr_string)
            
            result = {
                'qr_data': qr_data,
                'qr_string': qr_string,
                'qr_image': qr_image_info,
                'format_type': format_type,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Generated QR code for IRN: {irn_value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating QR code for IRN {irn_value}: {str(e)}")
            raise
    
    def validate_irn(
        self,
        irn_value: str,
        verification_code: Optional[str] = None,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Dict[str, Any]:
        """
        Validate IRN using granular component
        
        Args:
            irn_value: IRN to validate
            verification_code: Optional verification code
            validation_level: Level of validation
            
        Returns:
            Validation result dictionary
        """
        try:
            validation_result = self.irn_validator.validate_irn(
                irn_value=irn_value,
                verification_code=verification_code,
                validation_level=validation_level
            )
            
            result = {
                'is_valid': validation_result.is_valid,
                'validation_level': validation_result.validation_level.value,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'irn_info': validation_result.irn_info,
                'validated_at': datetime.now().isoformat()
            }
            
            if validation_result.errors:
                logger.warning(f"IRN validation failed for {irn_value}: {validation_result.errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating IRN {irn_value}: {str(e)}")
            raise
    
    async def get_next_sequence(self, organization_id: str) -> int:
        """Get next sequence number for organization"""
        return await self.sequence_manager.get_next_sequence(organization_id)
    
    def get_irn_info(self, irn_value: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an IRN
        
        Args:
            irn_value: IRN to analyze
            
        Returns:
            IRN information dictionary or None if invalid
        """
        try:
            # Check cache first
            if hasattr(self.irn_cache, 'get'):
                cache_key = f"irn_{irn_value}"
                cached_data = self.irn_cache.get(cache_key)
                if cached_data:
                    return cached_data
            
            # Check in duplicate detector registry
            irn_record = self.duplicate_detector.check_duplicate_irn(irn_value)
            if irn_record:
                return {
                    'irn_value': irn_record.irn_value,
                    'organization_id': irn_record.organization_id,
                    'created_at': irn_record.created_at.isoformat(),
                    'invoice_hash': irn_record.invoice_hash,
                    'invoice_summary': irn_record.invoice_data_summary
                }
            
            # Extract basic info from IRN structure
            validation_result = self.irn_validator.validate_irn(irn_value, validation_level=ValidationLevel.BASIC)
            return validation_result.irn_info
            
        except Exception as e:
            logger.error(f"Error getting IRN info for {irn_value}: {str(e)}")
            return None
    
    async def authenticate_with_firs(
        self,
        environment: str = "sandbox",
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Authenticate with FIRS for IRN submission
        
        Args:
            environment: FIRS environment (sandbox/production)
            credentials: FIRS credentials (optional, can use stored)
            
        Returns:
            Authentication result with session details
        """
        try:
            # Use FIRS authentication service
            auth_result = await self.firs_auth_service.authenticate(
                environment=environment,
                credentials=credentials,
                context={"service": "irn_generation", "purpose": "irn_submission"}
            )
            
            if auth_result.success:
                logger.info(f"Successfully authenticated with FIRS {environment}")
                return {
                    'success': True,
                    'environment': environment,
                    'auth_data': auth_result.auth_data,
                    'session_id': auth_result.session_id,
                    'expires_at': auth_result.expires_at,
                    'authenticated_at': datetime.now().isoformat()
                }
            else:
                logger.error(f"FIRS authentication failed: {auth_result.error_message}")
                return {
                    'success': False,
                    'environment': environment,
                    'error': auth_result.error_message,
                    'attempted_at': datetime.now().isoformat()
                }
                
        except AuthenticationError as e:
            logger.error(f"FIRS authentication error: {e}")
            return {
                'success': False,
                'environment': environment,
                'error': str(e),
                'attempted_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error during FIRS authentication: {e}")
            return {
                'success': False,
                'environment': environment,
                'error': f"Authentication failed: {str(e)}",
                'attempted_at': datetime.now().isoformat()
            }
    
    async def submit_irn_to_firs(
        self,
        irn_value: str,
        invoice_data: Dict[str, Any],
        environment: str = "sandbox"
    ) -> Dict[str, Any]:
        """
        Submit IRN to FIRS for validation and registration
        
        Args:
            irn_value: Generated IRN
            invoice_data: Original invoice data
            environment: FIRS environment
            
        Returns:
            Submission result from FIRS
        """
        try:
            # First authenticate if not already authenticated
            auth_result = await self.authenticate_with_firs(environment)
            if not auth_result['success']:
                return {
                    'success': False,
                    'error': f"Authentication failed: {auth_result.get('error')}",
                    'irn': irn_value
                }
            
            # Submit IRN using authenticated session
            submission_result = await self.firs_auth_service.submit_irn(
                irn_value=irn_value,
                invoice_data=invoice_data,
                auth_data=auth_result['auth_data'],
                environment=environment
            )
            
            if submission_result.success:
                logger.info(f"Successfully submitted IRN {irn_value} to FIRS {environment}")
                return {
                    'success': True,
                    'irn': irn_value,
                    'firs_response': submission_result.response_data,
                    'submitted_at': datetime.now().isoformat(),
                    'environment': environment
                }
            else:
                logger.error(f"FIRS IRN submission failed: {submission_result.error_message}")
                return {
                    'success': False,
                    'irn': irn_value,
                    'error': submission_result.error_message,
                    'firs_error_code': submission_result.error_code,
                    'submitted_at': datetime.now().isoformat(),
                    'environment': environment
                }
                
        except Exception as e:
            logger.error(f"Error submitting IRN {irn_value} to FIRS: {e}")
            return {
                'success': False,
                'irn': irn_value,
                'error': str(e),
                'submitted_at': datetime.now().isoformat(),
                'environment': environment
            }
    
    async def validate_irn_with_firs(
        self,
        irn_value: str,
        environment: str = "sandbox"
    ) -> Dict[str, Any]:
        """
        Validate IRN with FIRS directly
        
        Args:
            irn_value: IRN to validate
            environment: FIRS environment
            
        Returns:
            FIRS validation result
        """
        try:
            # Authenticate with FIRS
            auth_result = await self.authenticate_with_firs(environment)
            if not auth_result['success']:
                return {
                    'success': False,
                    'error': f"Authentication failed: {auth_result.get('error')}",
                    'irn': irn_value
                }
            
            # Validate with FIRS
            validation_result = await self.firs_auth_service.validate_irn(
                irn_value=irn_value,
                auth_data=auth_result['auth_data'],
                environment=environment
            )
            
            if validation_result.success:
                logger.info(f"IRN {irn_value} validated successfully with FIRS {environment}")
                return {
                    'success': True,
                    'irn': irn_value,
                    'is_valid': validation_result.is_valid,
                    'firs_data': validation_result.response_data,
                    'validated_at': datetime.now().isoformat(),
                    'environment': environment
                }
            else:
                logger.warning(f"FIRS IRN validation failed: {validation_result.error_message}")
                return {
                    'success': False,
                    'irn': irn_value,
                    'error': validation_result.error_message,
                    'validated_at': datetime.now().isoformat(),
                    'environment': environment
                }
                
        except Exception as e:
            logger.error(f"Error validating IRN {irn_value} with FIRS: {e}")
            return {
                'success': False,
                'irn': irn_value,
                'error': str(e),
                'validated_at': datetime.now().isoformat(),
                'environment': environment
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'duplicate_detection': self.duplicate_detector.get_statistics(),
            'sequence_manager': self.sequence_manager.export_sequence_state(),
            'service_info': {
                'components_loaded': True,
                'cache_enabled': hasattr(self.irn_cache, 'get'),
                'timestamp': datetime.now().isoformat()
            }
        }


# Backward compatibility functions (delegate to service instance)
_service_instance = None

def get_service_instance() -> IRNGenerationService:
    """Get singleton service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = IRNGenerationService()
    return _service_instance

def generate_irn(invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Backward compatibility function for generate_irn
    
    This maintains the original function signature while using the new architecture.
    """
    service = get_service_instance()
    return service.generate_irn(invoice_data)

def validate_irn_format(irn_value: str) -> bool:
    """Backward compatibility function for IRN format validation"""
    service = get_service_instance()
    validation_result = service.validate_irn(irn_value, validation_level=ValidationLevel.BASIC)
    return validation_result['is_valid']

def get_irn_expiration_date(irn_value: str) -> Optional[datetime]:
    """Backward compatibility function for IRN expiration"""
    service = get_service_instance()
    irn_info = service.get_irn_info(irn_value)
    
    if irn_info and 'timestamp' in irn_info:
        # Assume 1 year expiration from generation
        try:
            generation_time = datetime.fromisoformat(irn_info['timestamp'])
            return generation_time + timedelta(days=365)
        except (ValueError, TypeError):
            pass
    
    return None

def create_validation_record(irn_value: str, validation_result: Dict[str, Any]) -> IRNValidationRecord:
    """Backward compatibility function for creating validation records"""
    # This would need to be adapted based on your actual model structure
    return IRNValidationRecord(
        irn_value=irn_value,
        is_valid=validation_result.get('is_valid', False),
        validation_errors=validation_result.get('errors', []),
        validated_at=datetime.now()
    )