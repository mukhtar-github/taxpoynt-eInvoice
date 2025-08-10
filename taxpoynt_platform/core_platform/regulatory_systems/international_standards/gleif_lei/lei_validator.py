"""
Legal Entity Identifier (LEI) Validator
======================================
Comprehensive LEI validation engine with GLEIF integration for international
entity verification and regulatory compliance requirements.
"""
import logging
import re
import hashlib
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
import asyncio
import aiohttp

from .models import (
    LEIRecord, LEIValidationResult, LEIValidationStatus, EntityStatus,
    RegistrationAuthority, NigerianEntityMapping, LEIRelationship,
    GLEIFApiResponse, LEIPerformanceMetrics
)


class LEIValidator:
    """
    Comprehensive LEI validation engine with GLEIF integration
    """
    
    def __init__(self, gleif_api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.gleif_api_key = gleif_api_key
        self.gleif_base_url = "https://api.gleif.org/api/v1"
        
        # LEI validation cache for performance
        self.validation_cache = {}
        self.cache_ttl = timedelta(hours=24)  # Cache LEI validations for 24 hours
        
        # Nigerian entity mappings cache
        self.nigerian_mappings = {}
        
        # Performance metrics
        self.performance_metrics = {
            "validations_performed": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0
        }
        
    def validate_lei(self, lei: str, include_entity_data: bool = True,
                    check_nigerian_mapping: bool = False) -> LEIValidationResult:
        """
        Validate LEI format, status, and optionally retrieve entity data
        
        Args:
            lei: LEI to validate (20-character alphanumeric)
            include_entity_data: Whether to fetch complete entity data
            check_nigerian_mapping: Whether to check Nigerian entity mappings
            
        Returns:
            Comprehensive LEI validation result
        """
        try:
            self.performance_metrics["validations_performed"] += 1
            
            # Check cache first
            cache_key = f"{lei}_{include_entity_data}_{check_nigerian_mapping}"
            if cache_key in self.validation_cache:
                cached_result = self.validation_cache[cache_key]
                if datetime.now() - cached_result["timestamp"] < self.cache_ttl:
                    self.performance_metrics["cache_hits"] += 1
                    return cached_result["result"]
            
            # Initialize validation result
            validation_result = LEIValidationResult(
                lei=lei.upper() if lei else "",
                validation_timestamp=datetime.now(),
                validation_status=LEIValidationStatus.INVALID,
                validation_score=0.0
            )
            
            # Step 1: Format validation
            format_validation = self._validate_lei_format(lei)
            validation_result.format_validation = format_validation
            
            if not format_validation.get("is_valid", False):
                validation_result.validation_errors.extend(format_validation.get("errors", []))
                validation_result.validation_status = LEIValidationStatus.INVALID
                return validation_result
            
            # Step 2: Registry lookup
            if include_entity_data:
                registry_validation = self._lookup_lei_registry(lei)
                validation_result.registry_validation = registry_validation
                
                if registry_validation.get("found", False):
                    entity_record = registry_validation.get("entity_record")
                    if entity_record:
                        validation_result.entity_record = entity_record
                        
                        # Step 3: Status validation
                        status_validation = self._validate_lei_status(entity_record)
                        validation_result.status_validation = status_validation
                        
                        # Determine overall status
                        if status_validation.get("is_active", False):
                            validation_result.validation_status = LEIValidationStatus.VALID
                        elif status_validation.get("is_expired", False):
                            validation_result.validation_status = LEIValidationStatus.EXPIRED
                            validation_result.validation_warnings.append("LEI has expired and requires renewal")
                        else:
                            validation_result.validation_status = LEIValidationStatus.INACTIVE
                            validation_result.validation_warnings.append("LEI is inactive")
                else:
                    validation_result.validation_status = LEIValidationStatus.NOT_FOUND
                    validation_result.validation_errors.append("LEI not found in GLEIF registry")
            else:
                # Format validation only
                validation_result.validation_status = LEIValidationStatus.VALID
            
            # Step 4: Nigerian entity mapping (if requested)
            if check_nigerian_mapping and validation_result.entity_record:
                nigerian_mapping = self._check_nigerian_entity_mapping(
                    lei, validation_result.entity_record
                )
                if nigerian_mapping:
                    validation_result.registry_validation["nigerian_mapping"] = nigerian_mapping
            
            # Calculate validation score
            validation_result.validation_score = self._calculate_validation_score(validation_result)
            
            # Generate recommendations
            validation_result.recommendations = self._generate_recommendations(validation_result)
            
            # Set next validation date
            validation_result.next_validation_date = self._calculate_next_validation_date(validation_result)
            
            # Cache result
            self.validation_cache[cache_key] = {
                "timestamp": datetime.now(),
                "result": validation_result
            }
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"LEI validation failed for {lei}: {str(e)}")
            self.performance_metrics["errors"] += 1
            
            # Return error result
            return LEIValidationResult(
                lei=lei.upper() if lei else "",
                validation_timestamp=datetime.now(),
                validation_status=LEIValidationStatus.ERROR,
                validation_score=0.0,
                validation_errors=[f"Validation error: {str(e)}"]
            )
    
    def _validate_lei_format(self, lei: str) -> Dict[str, Any]:
        """Validate LEI format according to ISO 17442 standard"""
        
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "format_details": {}
        }
        
        if not lei:
            validation_result["errors"].append("LEI is required")
            return validation_result
        
        # Clean and normalize
        lei = lei.strip().upper()
        validation_result["format_details"]["normalized_lei"] = lei
        
        # Check length
        if len(lei) != 20:
            validation_result["errors"].append(f"LEI must be exactly 20 characters, got {len(lei)}")
            return validation_result
        
        # Check alphanumeric
        if not lei.isalnum():
            validation_result["errors"].append("LEI must contain only alphanumeric characters")
            return validation_result
        
        # Check for forbidden characters (0, 1, O, I are not used to avoid confusion)
        forbidden_chars = set(['0', '1', 'O', 'I'])
        if any(char in forbidden_chars for char in lei):
            validation_result["warnings"].append("LEI contains characters that may cause confusion (0, 1, O, I)")
        
        # Validate check digits (positions 19-20)
        check_digit_validation = self._validate_lei_check_digits(lei)
        validation_result["format_details"]["check_digit_validation"] = check_digit_validation
        
        if not check_digit_validation.get("is_valid", False):
            validation_result["errors"].append("LEI check digit validation failed")
            return validation_result
        
        # Validate structure (positions 1-4 should be LOU identifier)
        lou_code = lei[:4]
        validation_result["format_details"]["lou_code"] = lou_code
        
        # Basic LOU code validation (should be alphanumeric)
        if not lou_code.isalnum():
            validation_result["errors"].append("Invalid LOU code in positions 1-4")
            return validation_result
        
        # Entity identifier (positions 5-18)
        entity_id = lei[4:18]
        validation_result["format_details"]["entity_identifier"] = entity_id
        
        if not entity_id.isalnum():
            validation_result["errors"].append("Invalid entity identifier in positions 5-18")
            return validation_result
        
        # If all validations pass
        validation_result["is_valid"] = True
        validation_result["format_details"]["structure"] = {
            "lou_code": lou_code,
            "entity_identifier": entity_id,
            "check_digits": lei[18:20]
        }
        
        return validation_result
    
    def _validate_lei_check_digits(self, lei: str) -> Dict[str, Any]:
        """Validate LEI check digits using mod-97 algorithm (ISO 17442)"""
        
        try:
            # Step 1: Move characters 1-4 to the end
            rearranged = lei[4:] + lei[:4]
            
            # Step 2: Replace letters with numbers (A=10, B=11, ..., Z=35)
            numeric_string = ""
            for char in rearranged:
                if char.isalpha():
                    numeric_value = ord(char) - ord('A') + 10
                    if numeric_value > 35:  # Invalid character
                        return {"is_valid": False, "error": f"Invalid character: {char}"}
                    numeric_string += str(numeric_value)
                else:
                    numeric_string += char
            
            # Step 3: Calculate mod 97
            remainder = int(numeric_string) % 97
            
            # Step 4: Check if remainder is 1
            is_valid = remainder == 1
            
            return {
                "is_valid": is_valid,
                "rearranged": rearranged,
                "numeric_string": numeric_string,
                "mod_97_result": remainder,
                "expected_remainder": 1
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Check digit calculation failed: {str(e)}"
            }
    
    def _lookup_lei_registry(self, lei: str) -> Dict[str, Any]:
        """Lookup LEI in GLEIF registry"""
        
        registry_result = {
            "found": False,
            "entity_record": None,
            "lookup_timestamp": datetime.now().isoformat(),
            "source": "GLEIF_API",
            "errors": []
        }
        
        try:
            self.performance_metrics["api_calls"] += 1
            
            # In a real implementation, this would make an actual API call
            # For this example, we'll simulate the lookup
            entity_record = self._simulate_gleif_lookup(lei)
            
            if entity_record:
                registry_result["found"] = True
                registry_result["entity_record"] = entity_record
            else:
                registry_result["errors"].append("LEI not found in GLEIF registry")
            
            return registry_result
            
        except Exception as e:
            registry_result["errors"].append(f"Registry lookup failed: {str(e)}")
            return registry_result
    
    def _simulate_gleif_lookup(self, lei: str) -> Optional[LEIRecord]:
        """Simulate GLEIF API lookup (replace with actual API call in production)"""
        
        # This is a simulation - in production, replace with actual GLEIF API call
        simulated_records = {
            "549300HRGOLQ8YH7TP18": LEIRecord(
                lei="549300HRGOLQ8YH7TP18",
                legal_name="Bloomberg Finance L.P.",
                status=EntityStatus.ACTIVE,
                initial_registration_date=date(2012, 6, 6),
                last_update_date=date(2024, 1, 15),
                renewal_date=date(2025, 6, 6),
                managing_lou="549300HRGOLQ8YH7TP18",
                legal_address={
                    "line1": "731 Lexington Avenue",
                    "city": "New York",
                    "region": "NY",
                    "country": "US",
                    "postal_code": "10022"
                },
                legal_jurisdiction="US",
                entity_category="GENERAL",
                legal_form="Limited Partnership",
                registration_authority=RegistrationAuthority.BLOOMBERG
            ),
            # Add more simulated records as needed
        }
        
        return simulated_records.get(lei)
    
    def _validate_lei_status(self, entity_record: LEIRecord) -> Dict[str, Any]:
        """Validate LEI status and renewal requirements"""
        
        current_date = date.today()
        
        status_validation = {
            "is_active": entity_record.status == EntityStatus.ACTIVE,
            "is_expired": False,
            "is_inactive": entity_record.status in [EntityStatus.INACTIVE, EntityStatus.LAPSED],
            "requires_renewal": False,
            "days_until_renewal": None,
            "status_details": {
                "current_status": entity_record.status.value,
                "last_update": entity_record.last_update_date.isoformat(),
                "renewal_date": entity_record.renewal_date.isoformat()
            }
        }
        
        # Check expiration
        if entity_record.renewal_date < current_date:
            status_validation["is_expired"] = True
            status_validation["is_active"] = False
        
        # Check renewal requirements
        days_until_renewal = (entity_record.renewal_date - current_date).days
        status_validation["days_until_renewal"] = days_until_renewal
        
        if days_until_renewal <= 90:  # Renewal required within 90 days
            status_validation["requires_renewal"] = True
        
        # Additional status checks
        if entity_record.status == EntityStatus.PENDING_TRANSFER:
            status_validation["pending_transfer"] = True
        elif entity_record.status == EntityStatus.MERGED:
            status_validation["entity_merged"] = True
        elif entity_record.status == EntityStatus.DUPLICATE:
            status_validation["duplicate_lei"] = True
        
        return status_validation
    
    def _check_nigerian_entity_mapping(self, lei: str, entity_record: LEIRecord) -> Optional[NigerianEntityMapping]:
        """Check if entity has Nigerian business identifiers"""
        
        # Check if entity is Nigerian or has Nigerian operations
        if entity_record.legal_jurisdiction == "NG":
            # Simulate Nigerian entity mapping lookup
            # In production, this would query Nigerian business registries
            
            # Extract potential Nigerian identifiers from entity record
            nigerian_mapping = NigerianEntityMapping(
                lei=lei,
                entity_name=entity_record.legal_name,
                business_classification="Private Limited Company",  # Default classification
                registered_address=entity_record.legal_address,
                mapping_date=datetime.now(),
                mapping_source="GLEIF_CAC_Integration",
                mapping_confidence=85.0  # Simulated confidence score
            )
            
            # Try to extract TIN from business registry ID
            if entity_record.business_registry_entity_id:
                registry_id = entity_record.business_registry_entity_id
                if registry_id.isdigit() and len(registry_id) in [10, 11]:
                    nigerian_mapping.tin_number = registry_id
                else:
                    nigerian_mapping.cac_registration_number = registry_id
            
            return nigerian_mapping
        
        return None
    
    def _calculate_validation_score(self, validation_result: LEIValidationResult) -> float:
        """Calculate overall validation confidence score"""
        
        score = 0.0
        
        # Format validation (30% weight)
        if validation_result.format_validation.get("is_valid", False):
            score += 30.0
        
        # Registry validation (40% weight)
        if validation_result.registry_validation.get("found", False):
            score += 40.0
        
        # Status validation (30% weight)
        if validation_result.status_validation.get("is_active", False):
            score += 30.0
        elif validation_result.status_validation.get("is_expired", False):
            score += 20.0  # Partial score for expired but valid LEI
        
        # Bonus for Nigerian mapping (5% bonus)
        if validation_result.registry_validation.get("nigerian_mapping"):
            score += 5.0
        
        # Penalty for errors
        error_penalty = len(validation_result.validation_errors) * 5.0
        score = max(0.0, score - error_penalty)
        
        return min(100.0, score)
    
    def _generate_recommendations(self, validation_result: LEIValidationResult) -> List[str]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Format issues
        if not validation_result.format_validation.get("is_valid", False):
            recommendations.append("Correct LEI format issues before using for regulatory reporting")
        
        # Registry issues
        if not validation_result.registry_validation.get("found", False):
            recommendations.append("Verify LEI exists in GLEIF registry or register new LEI")
        
        # Status issues
        if validation_result.status_validation.get("is_expired", False):
            recommendations.append("Renew expired LEI immediately to maintain compliance")
        elif validation_result.status_validation.get("requires_renewal", False):
            days_until_renewal = validation_result.status_validation.get("days_until_renewal", 0)
            recommendations.append(f"Schedule LEI renewal - due in {days_until_renewal} days")
        
        # Nigerian specific
        if (validation_result.entity_record and 
            validation_result.entity_record.legal_jurisdiction == "NG" and
            not validation_result.registry_validation.get("nigerian_mapping")):
            recommendations.append("Link LEI to Nigerian business identifiers (TIN, CAC registration)")
        
        # Performance recommendations
        if validation_result.validation_score < 90:
            recommendations.append("Address validation issues to improve compliance confidence")
        
        return recommendations
    
    def _calculate_next_validation_date(self, validation_result: LEIValidationResult) -> datetime:
        """Calculate recommended next validation date"""
        
        base_interval = timedelta(days=90)  # Default 90-day validation cycle
        
        # Adjust based on status
        if validation_result.validation_status == LEIValidationStatus.EXPIRED:
            base_interval = timedelta(days=7)  # Weekly checks for expired LEIs
        elif validation_result.validation_status == LEIValidationStatus.INVALID:
            base_interval = timedelta(days=30)  # Monthly checks for invalid LEIs
        elif validation_result.status_validation.get("requires_renewal", False):
            days_until_renewal = validation_result.status_validation.get("days_until_renewal", 90)
            base_interval = timedelta(days=min(30, days_until_renewal // 2))  # More frequent checks before renewal
        
        return datetime.now() + base_interval
    
    def batch_validate_leis(self, leis: List[str], 
                           include_entity_data: bool = True) -> Dict[str, LEIValidationResult]:
        """
        Validate multiple LEIs in batch for improved performance
        
        Args:
            leis: List of LEIs to validate
            include_entity_data: Whether to include entity data for each LEI
            
        Returns:
            Dictionary mapping LEI to validation result
        """
        try:
            results = {}
            
            for lei in leis:
                try:
                    validation_result = self.validate_lei(
                        lei=lei,
                        include_entity_data=include_entity_data,
                        check_nigerian_mapping=True
                    )
                    results[lei] = validation_result
                    
                except Exception as e:
                    self.logger.error(f"Batch validation failed for LEI {lei}: {str(e)}")
                    results[lei] = LEIValidationResult(
                        lei=lei,
                        validation_timestamp=datetime.now(),
                        validation_status=LEIValidationStatus.ERROR,
                        validation_score=0.0,
                        validation_errors=[f"Batch validation error: {str(e)}"]
                    )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch LEI validation failed: {str(e)}")
            raise
    
    def search_entities_by_name(self, entity_name: str, 
                              country_filter: Optional[str] = None) -> List[LEIRecord]:
        """
        Search for entities by legal name
        
        Args:
            entity_name: Entity name to search for
            country_filter: Optional country code filter
            
        Returns:
            List of matching LEI records
        """
        try:
            # In production, this would call GLEIF API search endpoint
            # For now, return empty list as this is a simulation
            self.logger.info(f"Searching for entities with name: {entity_name}")
            
            # Simulate API call delay
            import time
            time.sleep(0.1)
            
            return []  # Return empty list in simulation
            
        except Exception as e:
            self.logger.error(f"Entity search failed: {str(e)}")
            raise
    
    def get_entity_relationships(self, lei: str) -> List[LEIRelationship]:
        """
        Get entity relationships for given LEI
        
        Args:
            lei: LEI to get relationships for
            
        Returns:
            List of entity relationships
        """
        try:
            # In production, this would call GLEIF relationship API
            self.logger.info(f"Getting relationships for LEI: {lei}")
            
            # Return empty list in simulation
            return []
            
        except Exception as e:
            self.logger.error(f"Relationship lookup failed: {str(e)}")
            raise
    
    def generate_validation_report(self, validation_results: Dict[str, LEIValidationResult]) -> Dict[str, Any]:
        """
        Generate comprehensive validation report
        
        Args:
            validation_results: Dictionary of LEI validation results
            
        Returns:
            Comprehensive validation report
        """
        try:
            total_leis = len(validation_results)
            
            # Status breakdown
            status_counts = {}
            for result in validation_results.values():
                status = result.validation_status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Score statistics
            scores = [result.validation_score for result in validation_results.values()]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Common issues
            all_errors = []
            all_warnings = []
            for result in validation_results.values():
                all_errors.extend(result.validation_errors)
                all_warnings.extend(result.validation_warnings)
            
            # Error frequency analysis
            error_frequency = {}
            for error in all_errors:
                error_frequency[error] = error_frequency.get(error, 0) + 1
            
            common_errors = sorted(error_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
            
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_leis_validated": total_leis,
                    "average_validation_score": round(avg_score, 2),
                    "validation_status_breakdown": status_counts
                },
                "quality_metrics": {
                    "valid_leis": status_counts.get("valid", 0),
                    "invalid_leis": status_counts.get("invalid", 0),
                    "expired_leis": status_counts.get("expired", 0),
                    "not_found_leis": status_counts.get("not_found", 0),
                    "validation_success_rate": round((status_counts.get("valid", 0) / total_leis) * 100, 2) if total_leis > 0 else 0
                },
                "issues_analysis": {
                    "total_errors": len(all_errors),
                    "total_warnings": len(all_warnings),
                    "most_common_errors": [{"error": error, "count": count} for error, count in common_errors]
                },
                "recommendations": self._generate_report_recommendations(validation_results),
                "performance_metrics": self.performance_metrics.copy()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Validation report generation failed: {str(e)}")
            raise
    
    def _generate_report_recommendations(self, validation_results: Dict[str, LEIValidationResult]) -> List[str]:
        """Generate recommendations based on validation report analysis"""
        
        recommendations = []
        
        total_leis = len(validation_results)
        valid_leis = sum(1 for result in validation_results.values() 
                        if result.validation_status == LEIValidationStatus.VALID)
        
        # Overall quality recommendations
        success_rate = (valid_leis / total_leis) * 100 if total_leis > 0 else 0
        
        if success_rate < 80:
            recommendations.append("LEI validation success rate is below 80% - review entity data quality")
        
        # Expired LEI recommendations
        expired_count = sum(1 for result in validation_results.values()
                          if result.validation_status == LEIValidationStatus.EXPIRED)
        
        if expired_count > 0:
            recommendations.append(f"Renew {expired_count} expired LEIs to maintain regulatory compliance")
        
        # Not found recommendations
        not_found_count = sum(1 for result in validation_results.values()
                            if result.validation_status == LEIValidationStatus.NOT_FOUND)
        
        if not_found_count > 0:
            recommendations.append(f"Investigate {not_found_count} LEIs not found in registry - may require re-registration")
        
        # Performance recommendations
        cache_hit_rate = (self.performance_metrics["cache_hits"] / 
                         self.performance_metrics["validations_performed"]) * 100 if self.performance_metrics["validations_performed"] > 0 else 0
        
        if cache_hit_rate < 50:
            recommendations.append("Consider implementing longer cache TTL for better performance")
        
        return recommendations
    
    def clear_cache(self):
        """Clear validation cache"""
        self.validation_cache.clear()
        self.logger.info("LEI validation cache cleared")
    
    def get_performance_metrics(self) -> LEIPerformanceMetrics:
        """Get current performance metrics"""
        
        cache_hit_rate = 0.0
        if self.performance_metrics["validations_performed"] > 0:
            cache_hit_rate = (self.performance_metrics["cache_hits"] / 
                            self.performance_metrics["validations_performed"]) * 100
        
        return LEIPerformanceMetrics(
            metrics_date=date.today(),
            reporting_period="current_session",
            total_validations=self.performance_metrics["validations_performed"],
            successful_validations=self.performance_metrics["validations_performed"] - self.performance_metrics["errors"],
            failed_validations=self.performance_metrics["errors"],
            validation_success_rate=round(
                ((self.performance_metrics["validations_performed"] - self.performance_metrics["errors"]) /
                 self.performance_metrics["validations_performed"]) * 100, 2
            ) if self.performance_metrics["validations_performed"] > 0 else 0,
            api_calls=self.performance_metrics["api_calls"],
            cache_hit_rate=round(cache_hit_rate, 2)
        )