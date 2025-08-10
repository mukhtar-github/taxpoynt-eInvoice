## Step 1.2: Implement SI-Specific Services

### SI ERP Integration Service (Full Implementation):

  # backend/app/services/firs_si/erp_integration_service.py

  from ..firs_core.base_firs_service import FIRSBaseService
  from ..firs_core.firs_api_client import FIRSAPIClient
  from typing import Dict, Any, List, Optional
  from uuid import UUID

  class FIRSSIERPIntegrationService(FIRSBaseService):
      """
      FIRS System Integrator ERP Integration Service
      
      Implements FIRS requirement: "Help businesses integrate their internal 
      ERP systems with FIRS e-invoice systems"
      """

      def __init__(self, firs_client: FIRSAPIClient):
          super().__init__()
          self.firs_client = firs_client
          self.erp_connectors = {}
          self._load_erp_connectors()

      async def create_firs_erp_integration(
          self,
          organization_id: UUID,
          erp_config: Dict[str, Any]
      ) -> Dict[str, Any]:
          """
          Create new FIRS-compliant ERP integration
          
          Steps:
          1. Validate ERP system FIRS compatibility
          2. Establish secure connection
          3. Configure FIRS data mapping
          4. Test end-to-end workflow
          5. Register with FIRS (if required)
          """

          # Step 1: FIRS Compliance Validation
          compliance_check = await self.validate_firs_compliance(
              operation='CREATE_ERP_INTEGRATION',
              data=erp_config
          )

          if compliance_check['compliance_status'] != 'COMPLIANT':
              raise FIRSComplianceError(
                  f"ERP integration failed FIRS compliance: {compliance_check.get('error')}"
              )

          # Step 2: Validate ERP FIRS Compatibility
          erp_type = erp_config.get('erp_type')
          compatibility_result = await self._validate_erp_firs_compatibility(
              erp_type=erp_type,
              erp_version=erp_config.get('version'),
              firs_requirements=True
          )

          if not compatibility_result['is_compatible']:
              raise ERPCompatibilityError(
                  f"ERP {erp_type} not compatible with FIRS requirements: "
                  f"{compatibility_result['issues']}"
              )

          # Step 3: Create Secure ERP Connection
          erp_connection = await self._establish_secure_erp_connection(
              organization_id=organization_id,
              erp_config=erp_config,
              firs_security_requirements=True
          )

          # Step 4: Configure FIRS Data Mapping
          data_mapping = await self._configure_firs_data_mapping(
              erp_type=erp_type,
              erp_connection=erp_connection,
              target_format='UBL_BIS_3.0'
          )

          # Step 5: Test FIRS Integration
          test_result = await self._test_firs_integration_workflow(
              erp_connection=erp_connection,
              data_mapping=data_mapping
          )

          if not test_result['success']:
              raise FIRSIntegrationError(
                  f"FIRS integration test failed: {test_result['errors']}"
              )

          # Step 6: Register Integration with FIRS
          firs_registration = await self._register_integration_with_firs(
              organization_id=organization_id,
              erp_connection=erp_connection,
              integration_type='SI_ERP_BRIDGE'
          )

          # Log successful integration
          integration_result = {
              'integration_id': erp_connection.id,
              'firs_registration_id': firs_registration['registration_id'],
              'erp_type': erp_type,
              'firs_compliance_verified': True,
              'data_mapping_configured': True,
              'test_results': test_result,
              'status': 'ACTIVE'
          }

          await self.log_firs_operation(
              operation='CREATE_ERP_INTEGRATION',
              organization_id=organization_id,
              data=erp_config,
              result=integration_result
          )

          return integration_result

      async def extract_and_transform_for_firs(
          self,
          integration_id: UUID,
          invoice_reference: str,
          firs_format: str = 'UBL_BIS_3.0'
      ) -> Dict[str, Any]:
          """
          Extract invoice from ERP and transform for FIRS submission
          
          FIRS Requirement: Transform ERP data to FIRS-compliant format
          """

          # Get ERP integration details
          integration = await self._get_erp_integration(integration_id)

          # Validate integration is FIRS-certified
          if not integration.firs_certified:
              raise FIRSCertificationError(
                  f"Integration {integration_id} not FIRS-certified"
              )

          # Extract raw invoice data from ERP
          raw_invoice_data = await self._extract_invoice_from_erp(
              integration=integration,
              invoice_reference=invoice_reference
          )

          # Transform to FIRS UBL format
          transformation_result = await self._transform_to_firs_ubl(
              raw_data=raw_invoice_data,
              source_format=integration.erp_format,
              target_format=firs_format,
              mapping_rules=integration.firs_mapping_rules
          )

          # Validate transformed invoice against FIRS schema
          firs_validation = await self.firs_client.validate_invoice_with_firs(
              transformation_result['firs_invoice']
          )

          if firs_validation['validation_status'] != 'VALID':
              raise FIRSValidationError(
                  f"Transformed invoice failed FIRS validation: "
                  f"{firs_validation['validation_errors']}"
              )

          # Apply FIRS compliance enhancements
          enhanced_invoice = await self._apply_firs_compliance_enhancements(
              firs_invoice=transformation_result['firs_invoice'],
              organization_id=integration.organization_id
          )

          return {
              'firs_compliant_invoice': enhanced_invoice,
              'source_data': raw_invoice_data,
              'transformation_metadata': {
                  'source_format': integration.erp_format,
                  'target_format': firs_format,
                  'mapping_rules_version': integration.mapping_rules_version,
                  'firs_validation_passed': True,
                  'compliance_enhancements_applied': True
              },
              'firs_validation_result': firs_validation
          }

      async def sync_firs_status_to_erp(
          self,
          integration_id: UUID,
          irn: str,
          firs_status_update: Dict[str, Any]
      ) -> Dict[str, Any]:
          """
          Sync FIRS status back to ERP system
          
          FIRS Requirement: Bidirectional synchronization
          """

          integration = await self._get_erp_integration(integration_id)

          # Prepare ERP-specific status update
          erp_status_update = await self._map_firs_status_to_erp(
              firs_status=firs_status_update,
              erp_type=integration.erp_type,
              mapping_rules=integration.status_mapping_rules
          )

          # Update ERP system
          erp_update_result = await self._update_erp_invoice_status(
              integration=integration,
              irn=irn,
              status_update=erp_status_update
          )

          # Log synchronization for FIRS audit
          sync_result = {
              'sync_id': f"SYNC_{irn}_{datetime.utcnow().timestamp()}",
              'irn': irn,
              'firs_status': firs_status_update.get('status'),
              'erp_update_success': erp_update_result['success'],
              'sync_timestamp': datetime.utcnow().isoformat()
          }

          await self.log_firs_operation(
              operation='SYNC_FIRS_STATUS_TO_ERP',
              organization_id=integration.organization_id,
              data={'irn': irn, 'firs_status': firs_status_update},
              result=sync_result
          )

          return sync_result

      # Private helper methods
      async def _validate_erp_firs_compatibility(
          self,
          erp_type: str,
          erp_version: str,
          firs_requirements: bool = True
      ) -> Dict[str, Any]:
          """Validate ERP system compatibility with FIRS requirements"""

          firs_compatible_erps = {
              'odoo': {
                  'min_version': '14.0',
                  'firs_certified_versions': ['16.0', '17.0'],
                  'required_modules': ['account', 'l10n_ng', 'firs_connector']
              },
              'sap': {
                  'min_version': 'S/4HANA 2020',
                  'firs_certified_versions': ['S/4HANA 2022', 'S/4HANA 2023'],
                  'required_modules': ['FI', 'SD', 'FIRS_NIGERIA']
              },
              'oracle': {
                  'min_version': '12.2',
                  'firs_certified_versions': ['19c', '21c'],
                  'required_modules': ['GL', 'AR', 'FIRS_LOCALIZATION']
              }
          }

          if erp_type not in firs_compatible_erps:
              return {
                  'is_compatible': False,
                  'issues': [f"ERP type {erp_type} not FIRS-certified"]
              }

          erp_spec = firs_compatible_erps[erp_type]

          # Check version compatibility
          if erp_version not in erp_spec['firs_certified_versions']:
              return {
                  'is_compatible': False,
                  'issues': [
                      f"ERP version {erp_version} not FIRS-certified. "
                      f"Certified versions: {erp_spec['firs_certified_versions']}"
                  ]
              }

          return {
              'is_compatible': True,
              'firs_certified': True,
              'required_modules': erp_spec['required_modules'],
              'certification_details': {
                  'erp_type': erp_type,
                  'version': erp_version,
                  'firs_certification_date': '2025-01-01',
                  'certification_authority': 'FIRS Nigeria'
              }
          }

# Update Your ERP Connector Configuration:

# Update your _validate_erp_firs_compatibility method
'sap': {
    'min_version': 'S/4HANA 2020',
    'firs_certified_versions': ['S/4HANA 2022', 'S/4HANA 2023', 'S/4HANA Cloud'],
    'required_modules': ['FI', 'SD'],  # Remove FIRS_NIGERIA as it doesn't exist
    'api_endpoints': {
        'billing_document': '/sap/opu/odata/sap/API_BILLING_DOCUMENT_SRV',
        'journal_entry': '/sap/opu/odata/sap/API_OPLACCTGDOCITEMCUBE_SRV',
        'business_partner': '/sap/opu/odata/sap/API_BUSINESS_PARTNER',
        'edocument': '/sap/opu/odata/sap/EDOCUMENT_SRV'  # If available
    }
}

## SAP-Specific Extraction Method:

async def _extract_invoice_from_sap(
    self,
    integration: Any,
    invoice_reference: str
) -> Dict[str, Any]:
    """Extract invoice from SAP S/4HANA using OData APIs"""
    
    sap_client = self.erp_connectors.get('sap')
    
    # Step 1: Try Billing Document API first (for SD invoices)
    try:
        billing_doc = await sap_client.get(
            f"/API_BILLING_DOCUMENT_SRV/A_BillingDocument('{invoice_reference}')",
            params={
                "$expand": "to_Item,to_Partner,to_PricingElement"
            }
        )
        
        if billing_doc:
            return await self._transform_sap_billing_to_standard(billing_doc)
    
    except NotFoundError:
        # Step 2: Try Journal Entry API (for FI invoices)
        journal_entries = await sap_client.get(
            "/API_OPLACCTGDOCITEMCUBE_SRV/A_JournalEntryItem",
            params={
                "$filter": f"OriginalReferenceDocument eq '{invoice_reference}'",
                "$expand": "to_BusinessPartner"
            }
        )
        
        if journal_entries:
            return await self._transform_sap_journal_to_standard(journal_entries)
    
    raise InvoiceNotFoundError(f"Invoice {invoice_reference} not found in SAP")

## Key SAP Integration Considerations
### 1. Authentication Setup
 # SAP uses OAuth2 or Basic Auth for APIs
sap_auth_config = {
    'auth_type': 'oauth2',  # or 'basic'
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'token_url': 'https://{host}/oauth/token',
    'scope': ['API_BILLING_DOCUMENT_SRV_0001']
}

### 2. Data Mapping for FIRS
SAP uses value mappings to map internal values to external formats like PEPPOL, which is similar to what you need for FIRS:
SAP_TO_FIRS_MAPPING = {
    'document_types': {
        'F2': 'INVOICE',  # SAP Invoice to FIRS Invoice
        'G2': 'CREDIT_NOTE',  # SAP Credit Memo
        'L2': 'DEBIT_NOTE'   # SAP Debit Memo
    },
    'tax_codes': {
        'O1': 'VAT_STANDARD',  # Nigerian VAT
        'O0': 'VAT_EXEMPT'
    }
}

### 3. Electronic Document Integration
SAP S/4HANA Cloud has built-in electronic document functionality through the eDocument Cockpit.
You can leverage this:
 # Check if SAP has eDocument framework configured
edoc_config = {
    'use_edocument': True,  # If customer uses SAP eDocument
    'edoc_api': '/sap/opu/odata/sap/EDOCUMENT_SRV',
    'auto_submit': False  # Let TaxPoynt handle FIRS submission
}

### 4. Alternative Development Approach
While waiting for full access, you can:
 # 1. Build with Mock SAP Responses
class MockSAPConnector:
    """Simulates SAP API responses for development"""
    
    async def get_billing_document(self, doc_id):
        return {
            "BillingDocument": doc_id,
            "BillingDocumentDate": "2025-01-15",
            "CustomerID": "0000010000",
            "NetAmount": 10000.00,
            "TaxAmount": 750.00,
            "DocumentCurrency": "NGN",
            "Items": [{
                "ItemNumber": "10",
                "Material": "MAT001",
                "Quantity": 10,
                "NetAmount": 10000.00
            }]
        }

 # 2. Use Public OData Services for Testing
 # SAP provides public demo services at:
 # https://services.odata.org/V4/Northwind/Northwind.svc/

## Recommended Immediate Action Plan
### Week 1: API Development with Mocks
 #1. Complete Odoo Integration - It's accessible now
 #2. Build FIRS Integration Layer - SAP-agnostic components
 #3. Create Integration Abstraction:
    class ERPConnectorFactory:
    @staticmethod
    def create_connector(erp_type: str, config: dict):
        if erp_type == 'sap':
            return SAPConnector(config) if not config.get('use_mock') \
                   else MockSAPConnector(config)
        elif erp_type == 'odoo':
            return OdooConnector(config)
    This way, you can switch between mock and real SAP APIs seamlessly when access is granted.

# Oracle
## Technical Advantages
### 1. Superior API Architecture
Oracle offers more modern, comprehensive APIs:
 # Oracle's REST APIs are more developer-friendly
'oracle': {
    'min_version': '12.2',
    'firs_certified_versions': ['19c', '21c', 'Cloud ERP'],
    'required_modules': ['GL', 'AR', 'AP'],
    'api_endpoints': {
        'invoices': '/fscmRestApi/resources/11.13.18.05/invoices',
        'customers': '/crmRestApi/resources/11.13.18.05/accounts', 
        'receivables': '/fscmRestApi/resources/11.13.18.05/receivables',
        'erpIntegrations': '/fscmRestApi/resources/11.13.18.05/erpintegrations'
    }
 }

### 2. Technical Quick Start
 # Oracle REST API Example
 curl -X GET \
  https://your-instance.oraclecloud.com/fscmRestApi/resources/11.13.18.05/invoices \
  -H 'Authorization: Bearer [token]' \
  -H 'Content-Type: application/json'

## Development Strategy with Oracle
 # Start building Oracle connector immediately
class OracleERPConnector:
    def __init__(self, config):
        self.base_url = config['instance_url']
        self.auth = self._setup_oauth(config)
    
    async def extract_invoice(self, invoice_id):
        endpoint = f"/fscmRestApi/resources/11.13.18.05/invoices/{invoice_id}"
        response = await self.get(endpoint)
        return self._transform_to_firs_format(response)

# My Recommendation
Pursue all three integration simultaneously, but prioritize based on speed to market:
1. Odoo - Build and deploy first (immediate access)
2. Oracle - Start integration now (free tier available)
3. SAP - Continue pursuing (largest market, but blocked)






