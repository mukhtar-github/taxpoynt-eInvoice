"""
Salesforce CRM Integration Models.

This module contains data models, transformers, and utilities for Salesforce CRM integration.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class SalesforceOpportunity(BaseModel):
    """Model for Salesforce Opportunity data."""
    
    id: str = Field(..., alias="Id")
    name: str = Field(..., alias="Name")
    amount: Optional[float] = Field(None, alias="Amount")
    close_date: Optional[str] = Field(None, alias="CloseDate")
    stage_name: str = Field(..., alias="StageName")
    probability: Optional[float] = Field(None, alias="Probability")
    type: Optional[str] = Field(None, alias="Type")
    lead_source: Optional[str] = Field(None, alias="LeadSource")
    description: Optional[str] = Field(None, alias="Description")
    created_date: Optional[str] = Field(None, alias="CreatedDate")
    last_modified_date: Optional[str] = Field(None, alias="LastModifiedDate")
    
    # Account information
    account_id: Optional[str] = Field(None, alias="AccountId")
    account_name: Optional[str] = None
    account_billing_street: Optional[str] = None
    account_billing_city: Optional[str] = None
    account_billing_state: Optional[str] = None
    account_billing_country: Optional[str] = None
    account_billing_postal_code: Optional[str] = None
    account_phone: Optional[str] = None
    account_website: Optional[str] = None
    
    # Owner information
    owner_id: Optional[str] = Field(None, alias="OwnerId")
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        
    @validator('amount', pre=True)
    def validate_amount(cls, v):
        """Validate and convert amount to float."""
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0
    
    @validator('probability', pre=True)
    def validate_probability(cls, v):
        """Validate probability value."""
        if v is None:
            return None
        try:
            prob = float(v)
            return max(0.0, min(100.0, prob))  # Clamp between 0 and 100
        except (ValueError, TypeError):
            return 0.0


class SalesforceAccount(BaseModel):
    """Model for Salesforce Account data."""
    
    id: str = Field(..., alias="Id")
    name: str = Field(..., alias="Name")
    billing_street: Optional[str] = Field(None, alias="BillingStreet")
    billing_city: Optional[str] = Field(None, alias="BillingCity")
    billing_state: Optional[str] = Field(None, alias="BillingState")
    billing_country: Optional[str] = Field(None, alias="BillingCountry")
    billing_postal_code: Optional[str] = Field(None, alias="BillingPostalCode")
    phone: Optional[str] = Field(None, alias="Phone")
    website: Optional[str] = Field(None, alias="Website")
    industry: Optional[str] = Field(None, alias="Industry")
    
    class Config:
        allow_population_by_field_name = True


class SalesforceContact(BaseModel):
    """Model for Salesforce Contact data."""
    
    id: str = Field(..., alias="Id")
    first_name: Optional[str] = Field(None, alias="FirstName")
    last_name: str = Field(..., alias="LastName")
    email: Optional[str] = Field(None, alias="Email")
    phone: Optional[str] = Field(None, alias="Phone")
    title: Optional[str] = Field(None, alias="Title")
    account_id: Optional[str] = Field(None, alias="AccountId")
    
    class Config:
        allow_population_by_field_name = True


class SalesforceUser(BaseModel):
    """Model for Salesforce User (Owner) data."""
    
    id: str = Field(..., alias="Id")
    name: str = Field(..., alias="Name")
    email: str = Field(..., alias="Email")
    username: Optional[str] = Field(None, alias="Username")
    
    class Config:
        allow_population_by_field_name = True


class OpportunityToInvoiceTransformer:
    """Transforms Salesforce opportunity data to TaxPoynt invoice format."""
    
    @staticmethod
    def transform_opportunity_to_invoice(
        opportunity: Dict[str, Any],
        connection_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Salesforce opportunity to invoice format.
        
        Args:
            opportunity: Salesforce opportunity data
            connection_settings: Optional connection settings for customization
            
        Returns:
            Dict in TaxPoynt invoice format
        """
        try:
            settings = connection_settings or {}
            
            # Extract basic opportunity data
            opportunity_id = opportunity.get("Id", "")
            opportunity_name = opportunity.get("Name", "")
            amount = opportunity.get("Amount", 0)
            close_date = opportunity.get("CloseDate")
            stage_name = opportunity.get("StageName", "")
            
            # Parse amount
            try:
                amount = float(amount) if amount else 0.0
            except (ValueError, TypeError):
                amount = 0.0
            
            # Get currency from settings or default to USD
            currency = settings.get("default_currency", "USD")
            
            # Convert currency if needed (for Nigerian companies)
            if currency == "NGN" and amount > 0:
                # If amount is in USD, convert to NGN (simplified - should use real exchange rates)
                usd_to_ngn_rate = settings.get("usd_to_ngn_rate", 800)  # Default rate
                if opportunity.get("CurrencyIsoCode") == "USD":
                    amount = amount * usd_to_ngn_rate
            
            # Generate invoice number
            invoice_number = f"SF-{opportunity_id[-6:]}"  # Use last 6 chars of SF ID
            
            # Extract account information
            account = opportunity.get("Account", {}) or {}
            account_name = account.get("Name", "")
            
            # Create customer data
            customer_data = {
                "name": account_name,
                "email": "",  # Will be populated from contacts if available
                "phone": account.get("Phone", ""),
                "company": account_name,
                "address": {
                    "street": account.get("BillingStreet", ""),
                    "city": account.get("BillingCity", ""),
                    "state": account.get("BillingState", ""),
                    "country": account.get("BillingCountry", ""),
                    "postal_code": account.get("BillingPostalCode", "")
                },
                "tax_id": "",  # Can be added if available in Salesforce
                "industry": account.get("Industry", "")
            }
            
            # Create line items
            line_items = []
            
            # Check if opportunity has products/line items
            if "OpportunityLineItems" in opportunity and opportunity["OpportunityLineItems"]:
                # Use actual line items from opportunity
                for line_item in opportunity["OpportunityLineItems"]:
                    item = {
                        "description": line_item.get("Name", line_item.get("PricebookEntry", {}).get("Name", "Service")),
                        "quantity": line_item.get("Quantity", 1),
                        "unit_price": line_item.get("UnitPrice", 0),
                        "total": line_item.get("TotalPrice", 0),
                        "product_code": line_item.get("ProductCode", ""),
                        "service_date": line_item.get("ServiceDate", close_date)
                    }
                    line_items.append(item)
            else:
                # Create single line item for the opportunity
                line_items.append({
                    "description": opportunity_name or f"Service for Opportunity {opportunity_id}",
                    "quantity": 1,
                    "unit_price": amount,
                    "total": amount,
                    "product_code": "SERVICE",
                    "service_date": close_date
                })
            
            # Calculate tax
            tax_rate = settings.get("default_tax_rate", 7.5)  # Default VAT rate for Nigeria
            subtotal = sum(item["total"] for item in line_items)
            tax_amount = subtotal * (tax_rate / 100)
            total_amount = subtotal + tax_amount
            
            # Add tax information to line items
            for item in line_items:
                item["tax_rate"] = tax_rate
                item["tax_amount"] = item["total"] * (tax_rate / 100)
            
            # Create invoice data
            invoice_data = {
                "invoice_number": invoice_number,
                "description": f"Invoice for {opportunity_name}",
                "currency": currency,
                "subtotal": subtotal,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total": total_amount,
                "due_date": close_date,
                "issue_date": datetime.now().strftime("%Y-%m-%d"),
                "customer": customer_data,
                "line_items": line_items,
                "notes": opportunity.get("Description", ""),
                "metadata": {
                    "source": "salesforce",
                    "opportunity_id": opportunity_id,
                    "opportunity_stage": stage_name,
                    "owner_id": opportunity.get("OwnerId", ""),
                    "account_id": opportunity.get("AccountId", ""),
                    "transformed_at": datetime.now().isoformat(),
                    "probability": opportunity.get("Probability", 0)
                }
            }
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Failed to transform opportunity to invoice: {str(e)}")
            raise ValueError(f"Invoice transformation failed: {str(e)}")
    
    @staticmethod
    def transform_opportunity_to_deal(
        opportunity: Dict[str, Any],
        connection_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Salesforce opportunity to TaxPoynt deal format.
        
        Args:
            opportunity: Salesforce opportunity data
            connection_settings: Optional connection settings
            
        Returns:
            Dict in TaxPoynt deal format
        """
        try:
            settings = connection_settings or {}
            
            # Extract account information
            account = opportunity.get("Account", {}) or {}
            owner = opportunity.get("Owner", {}) or {}
            
            # Extract customer data
            customer_data = {
                "name": account.get("Name", ""),
                "email": "",  # Will be populated from contacts
                "phone": account.get("Phone", ""),
                "company": account.get("Name", ""),
                "title": "",
                "address": {
                    "street": account.get("BillingStreet", ""),
                    "city": account.get("BillingCity", ""),
                    "state": account.get("BillingState", ""),
                    "country": account.get("BillingCountry", ""),
                    "postal_code": account.get("BillingPostalCode", "")
                },
                "custom_fields": {
                    "industry": account.get("Industry", ""),
                    "website": account.get("Website", ""),
                    "account_id": account.get("Id", "")
                }
            }
            
            # Extract deal data
            deal_data = {
                "source": opportunity.get("LeadSource", "salesforce"),
                "owner": {
                    "id": owner.get("Id", ""),
                    "name": owner.get("Name", ""),
                    "email": owner.get("Email", "")
                },
                "type": opportunity.get("Type", ""),
                "probability": opportunity.get("Probability", 0),
                "expected_close_date": opportunity.get("CloseDate"),
                "description": opportunity.get("Description", ""),
                "lead_source": opportunity.get("LeadSource", ""),
                "campaign_id": opportunity.get("CampaignId", ""),
                "forecast_category": opportunity.get("ForecastCategory", ""),
                "next_step": opportunity.get("NextStep", ""),
                "custom_properties": {
                    "has_opportunity_line_items": opportunity.get("HasOpportunityLineItem", False),
                    "is_closed": opportunity.get("IsClosed", False),
                    "is_won": opportunity.get("IsWon", False),
                    "fiscal_quarter": opportunity.get("FiscalQuarter", ""),
                    "fiscal_year": opportunity.get("FiscalYear", "")
                }
            }
            
            # Format amount
            amount = opportunity.get("Amount", 0)
            if amount is None:
                amount = 0
            
            # Get currency from opportunity or default
            currency = opportunity.get("CurrencyIsoCode", settings.get("default_currency", "USD"))
            
            # Create deal object
            deal = {
                "external_deal_id": opportunity.get("Id", ""),
                "deal_title": opportunity.get("Name", ""),
                "deal_amount": str(amount),
                "deal_currency": currency,
                "deal_stage": opportunity.get("StageName", ""),
                "deal_probability": opportunity.get("Probability", 0),
                "customer_data": customer_data,
                "deal_data": deal_data,
                "created_at_source": opportunity.get("CreatedDate"),
                "updated_at_source": opportunity.get("LastModifiedDate"),
                "closed_at_source": opportunity.get("CloseDate") if opportunity.get("IsClosed") else None,
                "invoice_generated": False,
                "sync_status": "success"
            }
            
            return deal
            
        except Exception as e:
            logger.error(f"Failed to transform opportunity to deal: {str(e)}")
            raise ValueError(f"Deal transformation failed: {str(e)}")


class SalesforceDataValidator:
    """Validates Salesforce data for integrity and completeness."""
    
    @staticmethod
    def validate_opportunity(opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Salesforce opportunity data.
        
        Args:
            opportunity: Opportunity data to validate
            
        Returns:
            Dict with validation results
        """
        issues = []
        warnings = []
        
        # Required fields
        if not opportunity.get("Id"):
            issues.append("Missing required field: Id")
        
        if not opportunity.get("Name"):
            issues.append("Missing required field: Name")
        
        if not opportunity.get("StageName"):
            issues.append("Missing required field: StageName")
        
        # Amount validation
        amount = opportunity.get("Amount")
        if amount is not None:
            try:
                amount_float = float(amount)
                if amount_float < 0:
                    warnings.append("Negative amount detected")
            except (ValueError, TypeError):
                issues.append("Invalid amount format")
        else:
            warnings.append("No amount specified")
        
        # Date validation
        close_date = opportunity.get("CloseDate")
        if close_date:
            try:
                # Try to parse the date
                datetime.fromisoformat(close_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                warnings.append("Invalid close date format")
        else:
            warnings.append("No close date specified")
        
        # Probability validation
        probability = opportunity.get("Probability")
        if probability is not None:
            try:
                prob_float = float(probability)
                if not 0 <= prob_float <= 100:
                    warnings.append("Probability should be between 0 and 100")
            except (ValueError, TypeError):
                warnings.append("Invalid probability format")
        
        # Account validation
        account = opportunity.get("Account")
        if not account or not account.get("Name"):
            warnings.append("Missing account information")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "opportunity_id": opportunity.get("Id", "unknown")
        }
    
    @staticmethod
    def validate_customer_data(customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate customer data extracted from Salesforce.
        
        Args:
            customer_data: Customer data to validate
            
        Returns:
            Dict with validation results
        """
        issues = []
        warnings = []
        
        # Name validation
        if not customer_data.get("name") and not customer_data.get("company"):
            issues.append("Either customer name or company name is required")
        
        # Email validation
        email = customer_data.get("email")
        if email and "@" not in email:
            warnings.append("Invalid email format")
        
        # Phone validation
        phone = customer_data.get("phone")
        if phone:
            # Basic phone validation
            cleaned_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if len(cleaned_phone) < 10:
                warnings.append("Phone number appears to be too short")
        
        # Address validation
        address = customer_data.get("address", {})
        if not any([address.get("street"), address.get("city"), address.get("country")]):
            warnings.append("Incomplete address information")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


class SalesforceAPIResponse(BaseModel):
    """Model for Salesforce API responses."""
    
    total_size: int = Field(..., alias="totalSize")
    done: bool = Field(..., alias="done")
    records: List[Dict[str, Any]] = Field(..., alias="records")
    next_records_url: Optional[str] = Field(None, alias="nextRecordsUrl")
    
    class Config:
        allow_population_by_field_name = True


class SalesforceError(BaseModel):
    """Model for Salesforce API error responses."""
    
    message: str
    error_code: str = Field(..., alias="errorCode")
    fields: Optional[List[str]] = None
    
    class Config:
        allow_population_by_field_name = True


class SalesforceWebhookEvent(BaseModel):
    """Model for Salesforce webhook/platform events."""
    
    event_type: str
    object_id: str
    object_type: str
    created_date: datetime
    changed_fields: Optional[List[str]] = None
    event_data: Dict[str, Any] = {}
    
    @validator('created_date', pre=True)
    def parse_created_date(cls, v):
        """Parse Salesforce datetime format."""
        if isinstance(v, str):
            try:
                # Handle Salesforce datetime format
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now()
        return v