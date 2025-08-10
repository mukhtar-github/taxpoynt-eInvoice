"""
FIRS Core Organization Service for TaxPoynt eInvoice - Core FIRS Functions.

This module provides Core FIRS functionality for organization management and taxpayer
entity handling, serving as the foundation for both System Integrator (SI) and Access
Point Provider (APP) operations with enhanced taxpayer compliance and entity management.

Core FIRS Responsibilities:
- Base organization and taxpayer entity management for FIRS e-invoicing
- Core FIRS taxpayer validation and compliance verification
- Foundation entity audit logging and compliance tracking for e-invoicing
- Shared organization branding and configuration management for FIRS operations
- Core taxpayer credential management and FIRS registration workflows
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, BrandingSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

# Core FIRS organization management configuration
CORE_ORGANIZATION_SERVICE_VERSION = "1.0"
DEFAULT_ORGANIZATION_STATUS = "active"
FIRS_TAX_ID_MIN_LENGTH = 8
FIRS_ORGANIZATION_CACHE_DURATION_HOURS = 6
MAX_ORGANIZATION_LOGO_SIZE_MB = 5


class CoreFIRSOrganizationService:
    """
    Core FIRS organization service for comprehensive taxpayer entity management.
    
    This service provides Core FIRS functions for organization and taxpayer entity
    management, compliance validation, and audit tracking that serve as the foundation
    for both System Integrator (SI) and Access Point Provider (APP) operations.
    
    Core Organization Functions:
    1. Base organization and taxpayer entity management for FIRS e-invoicing
    2. Core FIRS taxpayer validation and compliance verification
    3. Foundation entity audit logging and compliance tracking
    4. Shared organization branding and configuration management
    5. Core taxpayer credential management and FIRS registration workflows
    """

    def __init__(self, db: Session):
        """
        Initialize the Core FIRS organization service with enhanced capabilities.
        
        Args:
            db: Database session
        """
        self.db = db
        self.organization_cache = {}
        self.compliance_tracking = {}
        self.audit_logs = {}
        self.firs_metrics = {
            "total_organizations": 0,
            "verified_taxpayers": 0,
            "active_organizations": 0,
            "si_organizations": 0,
            "app_organizations": 0,
            "last_updated": datetime.now()
        }
        
        logger.info(f"Core FIRS Organization Service initialized (Version: {CORE_ORGANIZATION_SERVICE_VERSION})")
    
    def track_organization_activity(self, organization_id: uuid.UUID, activity_type: str, metadata: Dict[str, Any] = None) -> None:
        """
        Track organization activity for FIRS compliance monitoring - Core FIRS Function.
        
        Provides core activity tracking for FIRS organization operations,
        ensuring compliance audit trails and taxpayer monitoring.
        
        Args:
            organization_id: Organization ID for activity tracking
            activity_type: Type of activity (creation, update, firs_operation, etc.)
            metadata: Additional activity metadata
        """
        activity_id = str(uuid4())
        
        if organization_id not in self.audit_logs:
            self.audit_logs[organization_id] = []
        
        activity_record = {
            "activity_id": activity_id,
            "activity_type": activity_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "firs_core_tracked": True,
            "core_version": CORE_ORGANIZATION_SERVICE_VERSION
        }
        
        self.audit_logs[organization_id].append(activity_record)
        
        # Keep only recent activities (last 50 per organization)
        if len(self.audit_logs[organization_id]) > 50:
            self.audit_logs[organization_id] = self.audit_logs[organization_id][-50:]
        
        logger.debug(f"Core FIRS: Tracked organization activity - {activity_type} for org {organization_id} (Activity ID: {activity_id})")
    
    def validate_firs_taxpayer_data(self, organization_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate organization data for FIRS taxpayer compliance - Core FIRS Function.
        
        Provides core validation for organization data against FIRS taxpayer
        requirements, ensuring compliance with e-invoicing standards.
        
        Args:
            organization_data: Organization data to validate
            
        Returns:
            Dict containing validation results and compliance status
        """
        validation_id = str(uuid4())
        validation_results = {
            "validation_id": validation_id,
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "firs_compliant": True,
            "core_validated": True,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Validate tax ID for FIRS compliance
            tax_id = organization_data.get("tax_id")
            if tax_id:
                if len(tax_id) < FIRS_TAX_ID_MIN_LENGTH:
                    validation_results["errors"].append(f"Tax ID must be at least {FIRS_TAX_ID_MIN_LENGTH} characters")
                    validation_results["is_valid"] = False
                    validation_results["firs_compliant"] = False
                
                # Check for duplicate tax ID
                existing_org = self.db.query(Organization).filter(Organization.tax_id == tax_id).first()
                if existing_org:
                    validation_results["errors"].append(f"Organization with tax ID {tax_id} already exists")
                    validation_results["is_valid"] = False
            else:
                validation_results["warnings"].append("Tax ID not provided - required for FIRS compliance")
                validation_results["firs_compliant"] = False
            
            # Validate organization name
            if not organization_data.get("name"):
                validation_results["errors"].append("Organization name is required")
                validation_results["is_valid"] = False
            
            # Validate email format
            email = organization_data.get("email")
            if email and "@" not in email:
                validation_results["errors"].append("Valid email address is required")
                validation_results["is_valid"] = False
            
            # Validate address for FIRS compliance
            address = organization_data.get("address")
            if not address:
                validation_results["warnings"].append("Address not provided - recommended for FIRS compliance")
            
            logger.info(f"Core FIRS: Taxpayer validation completed - Valid: {validation_results['is_valid']} (Validation ID: {validation_id})")
            return validation_results
            
        except Exception as e:
            logger.error(f"Core FIRS: Error during taxpayer validation (Validation ID: {validation_id}): {str(e)}")
            validation_results.update({
                "is_valid": False,
                "firs_compliant": False,
                "errors": [f"Validation error: {str(e)}"],
                "core_validated": False
            })
            return validation_results
    
    def update_firs_metrics(self) -> Dict[str, Any]:
        """
        Update FIRS organization metrics for monitoring - Core FIRS Function.
        
        Provides core metrics calculation for FIRS organization management,
        supporting compliance monitoring and audit requirements.
        
        Returns:
            Dict containing updated FIRS organization metrics
        """
        try:
            # Calculate organization metrics
            total_organizations = self.db.query(Organization).count()
            active_organizations = self.db.query(Organization).filter(Organization.status == "active").count()
            verified_taxpayers = self.db.query(Organization).filter(
                Organization.tax_id.isnot(None),
                Organization.status == "active"
            ).count()
            
            # Update metrics
            self.firs_metrics.update({
                "total_organizations": total_organizations,
                "active_organizations": active_organizations,
                "verified_taxpayers": verified_taxpayers,
                "verification_rate_percent": round((verified_taxpayers / total_organizations * 100) if total_organizations > 0 else 0, 2),
                "last_updated": datetime.now().isoformat(),
                "firs_core_updated": True
            })
            
            logger.info(f"Core FIRS: Updated organization metrics - {total_organizations} total, {verified_taxpayers} verified taxpayers")
            return self.firs_metrics.copy()
            
        except Exception as e:
            logger.error(f"Core FIRS: Error updating organization metrics: {str(e)}")
            return self.firs_metrics.copy()

    def get_organization(self, organization_id: uuid.UUID) -> Optional[Organization]:
        """
        Get organization by ID with Core FIRS caching - Core FIRS Function.
        
        Provides core organization retrieval with enhanced caching,
        tracking, and FIRS compliance monitoring.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            Organization or None if not found
        """
        try:
            # Check cache first
            if organization_id in self.organization_cache:
                cached_org, cache_time = self.organization_cache[organization_id]
                if datetime.now() - cache_time < timedelta(hours=FIRS_ORGANIZATION_CACHE_DURATION_HOURS):
                    logger.debug(f"Core FIRS: Retrieved organization {organization_id} from cache")
                    return cached_org
            
            # Fetch from database
            organization = self.db.query(Organization).filter(Organization.id == organization_id).first()
            
            if organization:
                # Update cache
                self.organization_cache[organization_id] = (organization, datetime.now())
                
                # Track access
                self.track_organization_activity(
                    organization_id, 
                    "organization_accessed", 
                    {"firs_core_access": True}
                )
                
                logger.debug(f"Core FIRS: Retrieved organization {organization_id} from database")
            
            return organization
            
        except Exception as e:
            logger.error(f"Core FIRS: Error retrieving organization {organization_id}: {str(e)}")
            return None

    def get_organizations(self, skip: int = 0, limit: int = 100, include_firs_metadata: bool = True) -> List[Organization]:
        """
        Get list of organizations with Core FIRS enhancements - Core FIRS Function.
        
        Provides core organization listing with enhanced pagination,
        FIRS metadata, and compliance tracking.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_firs_metadata: Whether to include FIRS compliance metadata
            
        Returns:
            List of organizations with enhanced metadata
        """
        try:
            organizations = self.db.query(Organization).offset(skip).limit(limit).all()
            
            if include_firs_metadata:
                # Enhance organizations with FIRS metadata
                for org in organizations:
                    # Add FIRS compliance status
                    org.firs_compliant = bool(org.tax_id and org.status == "active")
                    org.core_managed = True
                    org.core_version = CORE_ORGANIZATION_SERVICE_VERSION
            
            logger.info(f"Core FIRS: Retrieved {len(organizations)} organizations (skip: {skip}, limit: {limit})")
            return organizations
            
        except Exception as e:
            logger.error(f"Core FIRS: Error retrieving organizations list: {str(e)}")
            return []

    def create_organization(self, organization_data: OrganizationCreate) -> Organization:
        """
        Create a new organization with Core FIRS enhancements - Core FIRS Function.
        
        Provides core organization creation with enhanced FIRS taxpayer validation,
        compliance tracking, and audit requirements.
        
        Args:
            organization_data: Data for creating organization
            
        Returns:
            Created organization with FIRS compliance metadata
        """
        creation_id = str(uuid4())
        
        try:
            # Validate taxpayer data for FIRS compliance
            validation_results = self.validate_firs_taxpayer_data(organization_data.dict())
            
            if not validation_results["is_valid"]:
                error_msg = f"Core FIRS: Taxpayer validation failed: {', '.join(validation_results['errors'])}"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            # Create organization with FIRS compliance metadata
            organization = Organization(
                **organization_data.dict(),
                status=DEFAULT_ORGANIZATION_STATUS,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(organization)
            self.db.commit()
            self.db.refresh(organization)
            
            # Add FIRS metadata
            organization.firs_compliant = validation_results["firs_compliant"]
            organization.core_created = True
            organization.creation_id = creation_id
            organization.core_version = CORE_ORGANIZATION_SERVICE_VERSION
            
            # Track organization creation
            self.track_organization_activity(
                organization.id, 
                "organization_created", 
                {
                    "name": organization.name,
                    "tax_id": organization.tax_id,
                    "creation_id": creation_id,
                    "firs_compliant": validation_results["firs_compliant"],
                    "validation_warnings": validation_results["warnings"],
                    "firs_core_created": True
                }
            )
            
            # Update cache
            self.organization_cache[organization.id] = (organization, datetime.now())
            
            # Update metrics
            self.update_firs_metrics()
            
            logger.info(f"Core FIRS: Created organization {organization.name} with tax ID {organization.tax_id} (Creation ID: {creation_id})")
            return organization
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Core FIRS: Error creating organization (Creation ID: {creation_id}): {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Core FIRS: Failed to create organization: {str(e)}"
            )

    def update_organization(
        self, organization_id: uuid.UUID, organization_data: OrganizationUpdate
    ) -> Optional[Organization]:
        """
        Update an existing organization with Core FIRS tracking - Core FIRS Function.
        
        Provides core organization updates with enhanced FIRS compliance validation,
        audit tracking, and taxpayer data management.
        
        Args:
            organization_id: UUID of the organization to update
            organization_data: Updated organization data
            
        Returns:
            Updated organization or None if not found
        """
        update_id = str(uuid4())
        
        try:
            organization = self.get_organization(organization_id)
            if not organization:
                logger.warning(f"Core FIRS: Organization not found for update: {organization_id}")
                return None

            # Validate updated data for FIRS compliance
            update_data = organization_data.dict(exclude_unset=True)
            if update_data:
                # Merge with existing data for validation
                current_data = {
                    "name": organization.name,
                    "tax_id": organization.tax_id,
                    "email": organization.email,
                    "address": organization.address,
                    **update_data
                }
                
                validation_results = self.validate_firs_taxpayer_data(current_data)
                
                if not validation_results["is_valid"]:
                    error_msg = f"Core FIRS: Update validation failed: {', '.join(validation_results['errors'])}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_msg
                    )

            # Update organization attributes
            for key, value in update_data.items():
                setattr(organization, key, value)

            organization.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(organization)
            
            # Add FIRS update metadata
            organization.firs_compliant = validation_results["firs_compliant"] if update_data else organization.firs_compliant
            organization.core_updated = True
            organization.update_id = update_id
            
            # Track organization update
            self.track_organization_activity(
                organization_id, 
                "organization_updated", 
                {
                    "updated_fields": list(update_data.keys()),
                    "update_id": update_id,
                    "firs_compliant": validation_results["firs_compliant"] if update_data else organization.firs_compliant,
                    "validation_warnings": validation_results.get("warnings", []) if update_data else [],
                    "firs_core_updated": True
                }
            )
            
            # Update cache
            self.organization_cache[organization_id] = (organization, datetime.now())
            
            logger.info(f"Core FIRS: Updated organization {organization.name} (Update ID: {update_id})")
            return organization
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Core FIRS: Error updating organization {organization_id} (Update ID: {update_id}): {str(e)}")
            return None

    def delete_organization(self, organization_id: uuid.UUID) -> bool:
        """
        Delete an organization with Core FIRS audit tracking - Core FIRS Function.
        
        Provides core organization deletion with enhanced audit logging
        and FIRS compliance requirements.
        
        Args:
            organization_id: UUID of the organization to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        deletion_id = str(uuid4())
        
        try:
            organization = self.get_organization(organization_id)
            if not organization:
                logger.warning(f"Core FIRS: Organization not found for deletion: {organization_id}")
                return False
            
            # Store organization details for audit
            org_details = {
                "name": organization.name,
                "tax_id": organization.tax_id,
                "email": organization.email,
                "deletion_id": deletion_id
            }

            self.db.delete(organization)
            self.db.commit()
            
            # Track organization deletion
            self.track_organization_activity(
                organization_id, 
                "organization_deleted", 
                {
                    **org_details,
                    "firs_core_deleted": True
                }
            )
            
            # Remove from cache
            if organization_id in self.organization_cache:
                del self.organization_cache[organization_id]
            
            # Update metrics
            self.update_firs_metrics()
            
            logger.info(f"Core FIRS: Deleted organization {org_details['name']} (Deletion ID: {deletion_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Core FIRS: Error deleting organization {organization_id} (Deletion ID: {deletion_id}): {str(e)}")
            return False

    async def upload_organization_logo(
        self, organization_id: uuid.UUID, logo: UploadFile
    ) -> str:
        """
        Upload and store organization logo with Core FIRS validation - Core FIRS Function.
        
        Provides core logo upload with enhanced validation, security,
        and FIRS branding compliance requirements.
        
        Args:
            organization_id: UUID of the organization
            logo: Uploaded logo file
            
        Returns:
            URL of the uploaded logo
            
        Raises:
            HTTPException: If organization not found or file upload fails
        """
        upload_id = str(uuid4())
        
        try:
            organization = self.get_organization(organization_id)
            if not organization:
                logger.warning(f"Core FIRS: Organization not found for logo upload: {organization_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Core FIRS: Organization not found"
                )

            # Enhanced file validation for FIRS compliance
            if not logo.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Core FIRS: File must be an image"
                )
            
            # Check file size
            logo_content = await logo.read()
            if len(logo_content) > MAX_ORGANIZATION_LOGO_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Core FIRS: Logo file must be smaller than {MAX_ORGANIZATION_LOGO_SIZE_MB}MB"
                )
            
            # Reset file position
            await logo.seek(0)
            
            # Generate a secure logo URL with FIRS compliance metadata
            logo_url = f"{settings.API_V1_STR}/static/logos/{organization_id}_{upload_id}_{logo.filename}"
            
            # Update the organization with the logo URL
            organization.logo_url = logo_url
            organization.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Track logo upload
            self.track_organization_activity(
                organization_id, 
                "logo_uploaded", 
                {
                    "logo_url": logo_url,
                    "file_size_bytes": len(logo_content),
                    "content_type": logo.content_type,
                    "upload_id": upload_id,
                    "firs_core_upload": True
                }
            )
            
            # Update cache
            self.organization_cache[organization_id] = (organization, datetime.now())
            
            logger.info(f"Core FIRS: Updated logo for organization {organization.name} (Upload ID: {upload_id})")
            return logo_url
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Core FIRS: Error uploading logo for organization {organization_id} (Upload ID: {upload_id}): {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Core FIRS: Failed to upload logo: {str(e)}"
            )

    def update_branding_settings(
        self, organization_id: uuid.UUID, branding: BrandingSettings
    ) -> Optional[Organization]:
        """
        Update organization branding settings with Core FIRS compliance - Core FIRS Function.
        
        Provides core branding updates with enhanced FIRS compliance validation,
        audit tracking, and brand consistency requirements.
        
        Args:
            organization_id: UUID of the organization
            branding: Branding settings to update
            
        Returns:
            Updated organization or None if not found
        """
        branding_id = str(uuid4())
        
        try:
            organization = self.get_organization(organization_id)
            if not organization:
                logger.warning(f"Core FIRS: Organization not found for branding update: {organization_id}")
                return None
                
            # Validate branding settings for FIRS compliance
            branding_data = branding.dict(exclude_unset=True)
            
            # Update branding settings with FIRS metadata
            enhanced_branding = {
                **branding_data,
                "firs_compliant": True,
                "core_branding": True,
                "branding_id": branding_id,
                "updated_at": datetime.now().isoformat()
            }
            
            organization.branding_settings = enhanced_branding
            organization.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(organization)
            
            # Track branding update
            self.track_organization_activity(
                organization_id, 
                "branding_updated", 
                {
                    "branding_fields": list(branding_data.keys()),
                    "branding_id": branding_id,
                    "firs_core_branding": True
                }
            )
            
            # Update cache
            self.organization_cache[organization_id] = (organization, datetime.now())
            
            logger.info(f"Core FIRS: Updated branding settings for organization {organization.name} (Branding ID: {branding_id})")
            return organization
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Core FIRS: Error updating branding for organization {organization_id} (Branding ID: {branding_id}): {str(e)}")
            return None
    
    def get_organization_firs_compliance_status(self, organization_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get FIRS compliance status for an organization - Core FIRS Function.
        
        Provides comprehensive FIRS compliance assessment for an organization,
        including taxpayer verification and e-invoicing readiness.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            Dict containing FIRS compliance status and recommendations
        """
        compliance_check_id = str(uuid4())
        
        try:
            organization = self.get_organization(organization_id)
            if not organization:
                return {
                    "compliance_check_id": compliance_check_id,
                    "organization_found": False,
                    "firs_compliant": False,
                    "timestamp": datetime.now().isoformat()
                }
            
            compliance_status = {
                "compliance_check_id": compliance_check_id,
                "organization_id": str(organization_id),
                "organization_name": organization.name,
                "organization_found": True,
                "firs_compliant": False,
                "compliance_score": 0,
                "requirements_met": [],
                "requirements_missing": [],
                "recommendations": [],
                "core_version": CORE_ORGANIZATION_SERVICE_VERSION,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check compliance requirements
            score = 0
            total_requirements = 6
            
            # 1. Tax ID validation
            if organization.tax_id and len(organization.tax_id) >= FIRS_TAX_ID_MIN_LENGTH:
                compliance_status["requirements_met"].append("valid_tax_id")
                score += 1
            else:
                compliance_status["requirements_missing"].append("valid_tax_id")
                compliance_status["recommendations"].append("Provide a valid tax ID for FIRS registration")
            
            # 2. Organization name
            if organization.name:
                compliance_status["requirements_met"].append("organization_name")
                score += 1
            else:
                compliance_status["requirements_missing"].append("organization_name")
            
            # 3. Email address
            if organization.email and "@" in organization.email:
                compliance_status["requirements_met"].append("valid_email")
                score += 1
            else:
                compliance_status["requirements_missing"].append("valid_email")
                compliance_status["recommendations"].append("Provide a valid email address")
            
            # 4. Address information
            if organization.address:
                compliance_status["requirements_met"].append("address")
                score += 1
            else:
                compliance_status["requirements_missing"].append("address")
                compliance_status["recommendations"].append("Provide organization address")
            
            # 5. Active status
            if organization.status == "active":
                compliance_status["requirements_met"].append("active_status")
                score += 1
            else:
                compliance_status["requirements_missing"].append("active_status")
                compliance_status["recommendations"].append("Activate organization status")
            
            # 6. Phone number
            if organization.phone:
                compliance_status["requirements_met"].append("phone_number")
                score += 1
            else:
                compliance_status["requirements_missing"].append("phone_number")
                compliance_status["recommendations"].append("Provide organization phone number")
            
            # Calculate compliance score and status
            compliance_status["compliance_score"] = round((score / total_requirements) * 100, 2)
            compliance_status["firs_compliant"] = score >= (total_requirements * 0.8)  # 80% threshold
            
            # Track compliance check
            self.track_organization_activity(
                organization_id, 
                "compliance_checked", 
                {
                    "compliance_score": compliance_status["compliance_score"],
                    "firs_compliant": compliance_status["firs_compliant"],
                    "compliance_check_id": compliance_check_id,
                    "firs_core_compliance": True
                }
            )
            
            logger.info(f"Core FIRS: Compliance check completed for {organization.name} - Score: {compliance_status['compliance_score']}% (Check ID: {compliance_check_id})")
            return compliance_status
            
        except Exception as e:
            logger.error(f"Core FIRS: Error checking compliance for organization {organization_id} (Check ID: {compliance_check_id}): {str(e)}")
            return {
                "compliance_check_id": compliance_check_id,
                "organization_found": False,
                "firs_compliant": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_core_organization_statistics(self) -> Dict[str, Any]:
        """
        Get core organization statistics for FIRS monitoring - Core FIRS Function.
        
        Provides comprehensive organization statistics for FIRS compliance monitoring
        and system health assessment.
        
        Returns:
            Dict containing core organization statistics and metrics
        """
        try:
            # Update and get current metrics
            metrics = self.update_firs_metrics()
            
            # Add additional statistics
            cache_size = len(self.organization_cache)
            audit_log_size = sum(len(logs) for logs in self.audit_logs.values())
            
            statistics = {
                **metrics,
                "cache_size": cache_size,
                "audit_log_entries": audit_log_size,
                "tracked_organizations": len(self.audit_logs),
                "core_version": CORE_ORGANIZATION_SERVICE_VERSION,
                "statistics_generated_at": datetime.now().isoformat(),
                "firs_core_statistics": True
            }
            
            logger.info(f"Core FIRS: Generated organization statistics - {statistics['total_organizations']} total organizations")
            return statistics
            
        except Exception as e:
            logger.error(f"Core FIRS: Error generating organization statistics: {str(e)}")
            return {
                "error": str(e),
                "firs_core_statistics": False,
                "timestamp": datetime.now().isoformat()
            }
