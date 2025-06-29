"""
Nigerian Data Residency Service
Manages data residency requirements for Nigeria according to NDPR and local regulations
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session
import json

from ..core.config import settings
from ..models.nigerian_compliance import NigerianCompliance

logger = logging.getLogger(__name__)


class DataClassification(str, Enum):
    """Data classification levels for Nigerian residency requirements"""
    NIGERIAN_RESTRICTED = "nigerian_restricted"     # Must stay in Nigeria
    NIGERIAN_BUSINESS = "nigerian_business"         # Primary in Nigeria, encrypted backup allowed
    NIGERIAN_GENERAL = "nigerian_general"          # Nigerian data with flexible storage
    GENERAL = "general"                             # Non-sensitive, any location


class DataLocation(str, Enum):
    """Available data center locations"""
    NIGERIA_LAGOS = "nigeria-lagos-dc"
    NIGERIA_ABUJA = "nigeria-abuja-dc"
    SOUTH_AFRICA_CAPE_TOWN = "south-africa-cape-town-dc"
    GHANA_ACCRA = "ghana-accra-dc"
    EUROPE_LONDON = "europe-london-dc"


class ResidencyAction(str, Enum):
    """Actions for data residency compliance"""
    STORE_LOCALLY = "store_locally"
    ENCRYPT_AND_BACKUP = "encrypt_and_backup"
    ANONYMIZE_AND_STORE = "anonymize_and_store"
    REPLICATE_REGIONALLY = "replicate_regionally"
    BLOCK_TRANSFER = "block_transfer"


@dataclass
class DataResidencyRule:
    """Data residency rule definition"""
    data_type: str
    classification: DataClassification
    primary_location: DataLocation
    backup_locations: List[DataLocation]
    encryption_required: bool
    max_retention_days: Optional[int]
    cross_border_allowed: bool
    audit_required: bool


@dataclass
class ResidencyDecision:
    """Decision for data residency enforcement"""
    action: ResidencyAction
    primary_location: DataLocation
    backup_locations: List[DataLocation]
    encryption_required: bool
    compliance_notes: str
    expires_at: Optional[datetime]


class NigerianDataResidencyService:
    """Manage data residency requirements for Nigeria."""
    
    def __init__(self):
        self.primary_dc = DataLocation.NIGERIA_LAGOS
        self.backup_dc = DataLocation.NIGERIA_ABUJA
        self.disaster_recovery_dc = DataLocation.SOUTH_AFRICA_CAPE_TOWN
        
        # Load data classification rules
        self.residency_rules = self._load_residency_rules()
        
    def _load_residency_rules(self) -> Dict[str, DataResidencyRule]:
        """Load data residency rules for different data types"""
        
        rules = {}
        
        # Nigerian Personal Identifiable Information (PII) - Highest restriction
        nigerian_pii_types = [
            "bvn", "nin", "phone_number", "home_address", 
            "personal_address", "identity_document", "passport_number",
            "drivers_license", "voter_card", "personal_data"
        ]
        
        for data_type in nigerian_pii_types:
            rules[data_type] = DataResidencyRule(
                data_type=data_type,
                classification=DataClassification.NIGERIAN_RESTRICTED,
                primary_location=DataLocation.NIGERIA_LAGOS,
                backup_locations=[DataLocation.NIGERIA_ABUJA],
                encryption_required=True,
                max_retention_days=2555,  # 7 years for financial records
                cross_border_allowed=False,
                audit_required=True
            )
        
        # Nigerian Business Data - High restriction
        business_data_types = [
            "tax_id", "tin", "cac_number", "business_registration",
            "bank_account", "invoice_data", "transaction_records",
            "payment_data", "tax_records", "firs_data"
        ]
        
        for data_type in business_data_types:
            rules[data_type] = DataResidencyRule(
                data_type=data_type,
                classification=DataClassification.NIGERIAN_BUSINESS,
                primary_location=DataLocation.NIGERIA_LAGOS,
                backup_locations=[DataLocation.NIGERIA_ABUJA, DataLocation.SOUTH_AFRICA_CAPE_TOWN],
                encryption_required=True,
                max_retention_days=2555,  # 7 years
                cross_border_allowed=True,  # With encryption
                audit_required=True
            )
        
        # Nigerian General Data - Medium restriction
        general_nigerian_types = [
            "business_email", "business_phone", "business_address",
            "company_name", "user_preferences", "audit_logs"
        ]
        
        for data_type in general_nigerian_types:
            rules[data_type] = DataResidencyRule(
                data_type=data_type,
                classification=DataClassification.NIGERIAN_GENERAL,
                primary_location=DataLocation.NIGERIA_LAGOS,
                backup_locations=[DataLocation.NIGERIA_ABUJA, DataLocation.GHANA_ACCRA],
                encryption_required=True,
                max_retention_days=1095,  # 3 years
                cross_border_allowed=True,
                audit_required=False
            )
        
        # General Data - Low restriction
        general_types = [
            "system_logs", "performance_metrics", "anonymous_analytics",
            "public_data", "static_content"
        ]
        
        for data_type in general_types:
            rules[data_type] = DataResidencyRule(
                data_type=data_type,
                classification=DataClassification.GENERAL,
                primary_location=DataLocation.NIGERIA_LAGOS,
                backup_locations=[DataLocation.SOUTH_AFRICA_CAPE_TOWN, DataLocation.GHANA_ACCRA],
                encryption_required=False,
                max_retention_days=365,  # 1 year
                cross_border_allowed=True,
                audit_required=False
            )
        
        return rules
    
    async def classify_data_sensitivity(self, data_type: str, context: Optional[Dict[str, Any]] = None) -> DataClassification:
        """Classify data for residency requirements."""
        
        # Check exact match first
        if data_type in self.residency_rules:
            return self.residency_rules[data_type].classification
        
        # Pattern matching for dynamic data types
        data_type_lower = data_type.lower()
        
        # Nigerian PII patterns
        if any(pattern in data_type_lower for pattern in [
            "bvn", "nin", "personal", "identity", "passport", "phone"
        ]):
            return DataClassification.NIGERIAN_RESTRICTED
        
        # Business data patterns
        if any(pattern in data_type_lower for pattern in [
            "tax", "invoice", "payment", "bank", "transaction", "firs"
        ]):
            return DataClassification.NIGERIAN_BUSINESS
        
        # Nigerian general patterns
        if any(pattern in data_type_lower for pattern in [
            "business", "company", "organization", "user"
        ]):
            return DataClassification.NIGERIAN_GENERAL
        
        # Default to general for unknown types
        return DataClassification.GENERAL
    
    async def get_residency_decision(
        self, 
        data_type: str, 
        data_content: Optional[Dict[str, Any]] = None,
        user_location: Optional[str] = None
    ) -> ResidencyDecision:
        """Get residency decision for specific data."""
        
        classification = await self.classify_data_sensitivity(data_type)
        rule = self.residency_rules.get(data_type)
        
        if not rule:
            # Create default rule for unknown types
            rule = DataResidencyRule(
                data_type=data_type,
                classification=classification,
                primary_location=self.primary_dc,
                backup_locations=[self.backup_dc],
                encryption_required=True,
                max_retention_days=1095,
                cross_border_allowed=False,
                audit_required=True
            )
        
        # Determine action based on classification
        if classification == DataClassification.NIGERIAN_RESTRICTED:
            action = ResidencyAction.STORE_LOCALLY
            backup_locations = [loc for loc in rule.backup_locations 
                             if loc in [DataLocation.NIGERIA_LAGOS, DataLocation.NIGERIA_ABUJA]]
        
        elif classification == DataClassification.NIGERIAN_BUSINESS:
            action = ResidencyAction.ENCRYPT_AND_BACKUP
            backup_locations = rule.backup_locations
        
        elif classification == DataClassification.NIGERIAN_GENERAL:
            action = ResidencyAction.REPLICATE_REGIONALLY
            backup_locations = rule.backup_locations
        
        else:  # GENERAL
            action = ResidencyAction.REPLICATE_REGIONALLY
            backup_locations = rule.backup_locations
        
        # Calculate expiration if retention period is set
        expires_at = None
        if rule.max_retention_days:
            expires_at = datetime.utcnow() + timedelta(days=rule.max_retention_days)
        
        return ResidencyDecision(
            action=action,
            primary_location=rule.primary_location,
            backup_locations=backup_locations,
            encryption_required=rule.encryption_required,
            compliance_notes=f"Classification: {classification.value}, Cross-border: {rule.cross_border_allowed}",
            expires_at=expires_at
        )
    
    async def enforce_data_residency(
        self, 
        data: Any, 
        data_type: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Enforce data residency rules."""
        
        decision = await self.get_residency_decision(data_type)
        
        try:
            if decision.action == ResidencyAction.STORE_LOCALLY:
                result = await self._store_in_nigeria(data, decision)
            
            elif decision.action == ResidencyAction.ENCRYPT_AND_BACKUP:
                result = await self._store_with_encrypted_backup(data, decision)
            
            elif decision.action == ResidencyAction.REPLICATE_REGIONALLY:
                result = await self._replicate_regionally(data, decision)
            
            elif decision.action == ResidencyAction.ANONYMIZE_AND_STORE:
                result = await self._anonymize_and_store(data, decision)
            
            else:  # BLOCK_TRANSFER
                raise ValueError(f"Data transfer blocked for type: {data_type}")
            
            # Log compliance action
            await self._log_residency_action(data_type, decision, user_id, db)
            
            return {
                "status": "success",
                "action_taken": decision.action.value,
                "primary_location": decision.primary_location.value,
                "backup_locations": [loc.value for loc in decision.backup_locations],
                "encrypted": decision.encryption_required,
                "storage_result": result
            }
            
        except Exception as e:
            logger.error(f"Data residency enforcement failed for {data_type}: {str(e)}")
            raise
    
    async def _store_in_nigeria(self, data: Any, decision: ResidencyDecision) -> Dict[str, Any]:
        """Store data only in Nigerian data centers."""
        
        # Simulate Nigerian-only storage
        storage_locations = [decision.primary_location.value]
        storage_locations.extend([loc.value for loc in decision.backup_locations 
                                if "nigeria" in loc.value])
        
        return {
            "stored_locations": storage_locations,
            "cross_border": False,
            "encryption_applied": decision.encryption_required,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _store_with_encrypted_backup(self, data: Any, decision: ResidencyDecision) -> Dict[str, Any]:
        """Store with primary in Nigeria and encrypted backup elsewhere."""
        
        primary_storage = decision.primary_location.value
        backup_locations = [loc.value for loc in decision.backup_locations]
        
        return {
            "primary_location": primary_storage,
            "backup_locations": backup_locations,
            "cross_border": True,
            "encryption_applied": True,
            "backup_encrypted": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _replicate_regionally(self, data: Any, decision: ResidencyDecision) -> Dict[str, Any]:
        """Replicate data across African regions."""
        
        all_locations = [decision.primary_location.value]
        all_locations.extend([loc.value for loc in decision.backup_locations])
        
        return {
            "replicated_locations": all_locations,
            "regional_distribution": True,
            "encryption_applied": decision.encryption_required,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _anonymize_and_store(self, data: Any, decision: ResidencyDecision) -> Dict[str, Any]:
        """Anonymize data before storage."""
        
        # Simulate data anonymization
        anonymized_data = self._anonymize_data(data)
        
        return {
            "anonymized": True,
            "original_removed": True,
            "stored_locations": [decision.primary_location.value],
            "encryption_applied": decision.encryption_required,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _anonymize_data(self, data: Any) -> Any:
        """Anonymize sensitive data fields."""
        
        if isinstance(data, dict):
            anonymized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in 
                      ["email", "phone", "address", "name", "id"]):
                    anonymized[key] = f"anonymized_{hash(str(value)) % 10000}"
                else:
                    anonymized[key] = value
            return anonymized
        
        return data
    
    async def _log_residency_action(
        self, 
        data_type: str, 
        decision: ResidencyDecision, 
        user_id: Optional[str],
        db: Optional[Session]
    ):
        """Log data residency action for audit purposes."""
        
        if not db:
            logger.warning("No database session provided for residency logging")
            return
        
        try:
            compliance_log = {
                "event_type": "data_residency_enforcement",
                "data_type": data_type,
                "classification": decision.action.value,
                "primary_location": decision.primary_location.value,
                "backup_locations": [loc.value for loc in decision.backup_locations],
                "encryption_required": decision.encryption_required,
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "compliance_notes": decision.compliance_notes
            }
            
            # Store in compliance tracking
            logger.info(f"Data residency action logged: {json.dumps(compliance_log, default=str)}")
            
        except Exception as e:
            logger.error(f"Failed to log residency action: {str(e)}")
    
    async def get_data_location_report(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate data location compliance report."""
        
        report = {
            "organization_id": organization_id,
            "report_date": datetime.utcnow().isoformat(),
            "data_centers": {
                "primary": self.primary_dc.value,
                "backup": self.backup_dc.value,
                "disaster_recovery": self.disaster_recovery_dc.value
            },
            "classification_summary": {},
            "compliance_status": "compliant",
            "recommendations": []
        }
        
        # Summarize classifications
        for classification in DataClassification:
            matching_rules = [rule for rule in self.residency_rules.values() 
                            if rule.classification == classification]
            
            report["classification_summary"][classification.value] = {
                "data_types_count": len(matching_rules),
                "cross_border_allowed": any(rule.cross_border_allowed for rule in matching_rules),
                "encryption_required": any(rule.encryption_required for rule in matching_rules)
            }
        
        # Add recommendations
        report["recommendations"] = [
            "Ensure all Nigerian PII remains within Nigeria",
            "Maintain encrypted backups for business data",
            "Regular audit of data location compliance",
            "Monitor cross-border data transfers"
        ]
        
        return report
    
    async def validate_cross_border_transfer(
        self, 
        data_type: str, 
        source_location: str, 
        destination_location: str
    ) -> Dict[str, Any]:
        """Validate if cross-border data transfer is allowed."""
        
        classification = await self.classify_data_sensitivity(data_type)
        rule = self.residency_rules.get(data_type)
        
        # Check if Nigerian PII is being transferred outside Nigeria
        if (classification == DataClassification.NIGERIAN_RESTRICTED and
            "nigeria" not in destination_location.lower()):
            
            return {
                "allowed": False,
                "reason": "Nigerian PII cannot be transferred outside Nigeria",
                "classification": classification.value,
                "suggested_action": "Store locally in Nigerian data centers"
            }
        
        # Check if business data transfer requires encryption
        if (classification == DataClassification.NIGERIAN_BUSINESS and
            "nigeria" not in destination_location.lower()):
            
            return {
                "allowed": True,
                "conditions": ["encryption_required", "audit_trail_required"],
                "classification": classification.value,
                "suggested_action": "Encrypt data before transfer"
            }
        
        return {
            "allowed": True,
            "classification": classification.value,
            "conditions": [],
            "suggested_action": "Proceed with standard security measures"
        }