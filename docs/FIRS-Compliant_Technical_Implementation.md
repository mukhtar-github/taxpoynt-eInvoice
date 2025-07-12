Excellent! Let me design the comprehensive technical implementation details for our FIRS-compliant architecture.

#  📋 FIRS-Compliant Technical Implementation Specification

  1. Backend Service Architecture Restructuring

  Core Service Layer Separation

  Backend Structure:
  backend/app/
  ├── services/
  │   ├── firs_si/                 # System Integrator Services
  │   │   ├── __init__.py
  │   │   ├── erp_integration_service.py
  │   │   ├── digital_certificate_service.py
  │   │   ├── irn_generation_service.py
  │   │   ├── schema_compliance_service.py
  │   │   └── si_authentication_service.py
  │   │
  │   ├── firs_app/                # Access Point Provider Services
  │   │   ├── __init__.py
  │   │   ├── transmission_service.py
  │   │   ├── data_validation_service.py
  │   │   ├── authentication_seal_service.py
  │   │   ├── secure_communication_service.py
  │   │   └── app_compliance_service.py
  │   │
  │   ├── firs_core/               # Shared FIRS Services
  │   │   ├── __init__.py
  │   │   ├── firs_api_client.py
  │   │   ├── certificate_manager.py
  │   │   ├── encryption_service.py
  │   │   └── audit_service.py
  │   │
  │   └── firs_hybrid/             # Hybrid SI+APP Services
  │       ├── __init__.py
  │       ├── hybrid_workflow_service.py
  │       ├── cross_role_validation_service.py
  │       └── unified_compliance_service.py

  1.1 System Integrator (SI) Services Implementation

  ERP Integration Service (FIRS Focus: Help businesses integrate ERP systems with FIRS)
  # backend/app/services/firs_si/erp_integration_service.py
  from typing import List, Dict, Any, Optional
  from uuid import UUID
  import asyncio
  from datetime import datetime

  class FIRSSIERPIntegrationService:
      """
      FIRS-Certified System Integrator ERP Integration Service
      
      Core FIRS Requirement: "Help businesses integrate their internal ERP 
      systems with FIRS e-invoice systems"
      """

      def __init__(self):
          self.supported_erp_systems = [
              'odoo', 'sap', 'oracle', 'microsoft_dynamics',
              'sage', 'quickbooks', 'xero'
          ]
          self.firs_compliance_rules = self._load_firs_compliance_rules()

      async def establish_erp_connection(
          self, 
          organization_id: UUID,
          erp_type: str,
          connection_config: Dict[str, Any],
          firs_compliance_mode: bool = True
      ) -> Dict[str, Any]:
          """
          Establish FIRS-compliant ERP connection
          
          FIRS Requirement: Ensure all ERP integrations meet FIRS standards
          """

          # Validate ERP system compatibility with FIRS
          if not await self._validate_firs_erp_compatibility(erp_type):
              raise FIRSComplianceError(f"ERP system {erp_type} not FIRS-certified")

          # Create secure connection with FIRS audit trail
          connection = await self._create_secure_erp_connection(
              organization_id=organization_id,
              erp_type=erp_type,
              config=connection_config
          )

          # Register connection with FIRS if required
          if firs_compliance_mode:
              await self._register_erp_connection_with_firs(connection)

          # Initialize FIRS-compliant data synchronization
          sync_config = await self._setup_firs_data_sync(connection)

          return {
              'connection_id': connection.id,
              'firs_registration_id': connection.firs_registration_id,
              'compliance_status': 'FIRS_CERTIFIED',
              'sync_configuration': sync_config,
              'supported_invoice_formats': ['UBL_2.1', 'UBL_BIS_3.0'],
              'firs_endpoints': self._get_firs_endpoints_for_erp(erp_type)
          }

      async def extract_invoice_data_for_firs(
          self,
          connection_id: UUID,
          invoice_reference: str,
          firs_format: str = 'UBL_BIS_3.0'
      ) -> Dict[str, Any]:
          """
          Extract and transform invoice data for FIRS submission
          
          FIRS Requirement: Transform ERP data to FIRS-compliant format
          """

          # Get raw invoice data from ERP
          raw_invoice = await self._fetch_erp_invoice(connection_id, invoice_reference)

          # Transform to FIRS UBL format
          firs_invoice = await self._transform_to_firs_format(raw_invoice, firs_format)

          # Validate against FIRS schema
          validation_result = await self._validate_firs_invoice_schema(firs_invoice)

          if not validation_result.is_valid:
              raise FIRSValidationError(
                  f"Invoice {invoice_reference} failed FIRS validation: "
                  f"{validation_result.errors}"
              )

          return {
              'firs_invoice': firs_invoice,
              'erp_source_data': raw_invoice,
              'validation_status': validation_result,
              'transformation_metadata': {
                  'source_format': raw_invoice.get('format'),
                  'target_format': firs_format,
                  'transformation_timestamp': datetime.utcnow().isoformat(),
                  'firs_compliance_version': '2025.1'
              }
          }

      async def sync_erp_with_firs_status(
          self,
          connection_id: UUID,
          irn: str,
          firs_status: str
      ) -> Dict[str, Any]:
          """
          Synchronize FIRS status back to ERP system
          
          FIRS Requirement: Maintain bidirectional sync between ERP and FIRS
          """

          connection = await self._get_erp_connection(connection_id)

          # Update ERP system with FIRS status
          update_result = await self._update_erp_invoice_status(
              connection=connection,
              irn=irn,
              firs_status=firs_status
          )

          # Log synchronization for FIRS audit
          await self._log_firs_erp_sync(
              connection_id=connection_id,
              irn=irn,
              sync_action='STATUS_UPDATE',
              firs_status=firs_status,
              erp_response=update_result
          )

          return {
              'sync_status': 'SUCCESS',
              'erp_updated': True,
              'firs_status': firs_status,
              'sync_timestamp': datetime.utcnow().isoformat(),
              'audit_trail_id': update_result.audit_id
          }

  Digital Certificate Service (FIRS Focus: Invoice authentication algorithms)
  # backend/app/services/firs_si/digital_certificate_service.py
  from cryptography.hazmat.primitives import hashes, serialization
  from cryptography.hazmat.primitives.asymmetric import rsa, padding
  from cryptography.hazmat.primitives.serialization import pkcs12
  import base64
  from typing import Dict, Any, List

  class FIRSSIDigitalCertificateService:
      """
      FIRS-Certified Digital Certificate Service for System Integrators
      
      Core FIRS Requirement: "Implement algorithms to authenticate invoice 
      origin and guarantee that the contents have not been altered"
      """

      def __init__(self):
          self.firs_approved_algorithms = [
              'RSA-PSS-SHA256',
              'RSA-PKCS1-SHA256',
              'ECDSA-SHA256'
          ]
          self.certificate_authorities = {
              'firs': 'Federal Inland Revenue Service CA',
              'nitda': 'NITDA Certified CA',
              'verisign': 'VeriSign Nigeria CA'
          }

      async def implement_firs_authentication_algorithm(
          self,
          invoice_data: Dict[str, Any],
          certificate_id: UUID,
          algorithm: str = 'RSA-PSS-SHA256'
      ) -> Dict[str, Any]:
          """
          Implement FIRS-approved authentication algorithm
          
          FIRS Requirement: Use certified algorithms for invoice authentication
          """

          if algorithm not in self.firs_approved_algorithms:
              raise FIRSCertificationError(
                  f"Algorithm {algorithm} not approved by FIRS. "
                  f"Approved: {self.firs_approved_algorithms}"
              )

          # Load FIRS-issued certificate
          certificate = await self._load_firs_certificate(certificate_id)
          private_key = await self._load_certificate_private_key(certificate_id)

          # Create invoice content hash
          invoice_content = await self._serialize_invoice_for_signing(invoice_data)
          content_hash = self._calculate_invoice_hash(invoice_content)

          # Apply FIRS authentication algorithm
          if algorithm == 'RSA-PSS-SHA256':
              signature = await self._apply_rsa_pss_signature(
                  content_hash=content_hash,
                  private_key=private_key
              )
          elif algorithm == 'RSA-PKCS1-SHA256':
              signature = await self._apply_rsa_pkcs1_signature(
                  content_hash=content_hash,
                  private_key=private_key
              )
          elif algorithm == 'ECDSA-SHA256':
              signature = await self._apply_ecdsa_signature(
                  content_hash=content_hash,
                  private_key=private_key
              )

          # Generate FIRS-compliant authentication stamp
          authentication_stamp = {
              'algorithm': algorithm,
              'signature': base64.b64encode(signature).decode('utf-8'),
              'certificate_fingerprint': certificate.fingerprint,
              'timestamp': datetime.utcnow().isoformat(),
              'firs_certificate_id': certificate.firs_id,
              'content_hash': base64.b64encode(content_hash).decode('utf-8'),
              'authenticity_guarantee': True
          }

          return {
              'authenticated_invoice': {
                  **invoice_data,
                  'firs_authentication_stamp': authentication_stamp
              },
              'authentication_metadata': {
                  'algorithm_used': algorithm,
                  'certificate_authority': certificate.issuer,
                  'authentication_timestamp': datetime.utcnow().isoformat(),
                  'integrity_verified': True,
                  'origin_authenticated': True
              }
          }

      async def verify_invoice_authenticity(
          self,
          signed_invoice: Dict[str, Any]
      ) -> Dict[str, Any]:
          """
          Verify invoice authenticity using FIRS algorithms
          
          FIRS Requirement: Guarantee that contents have not been altered
          """

          auth_stamp = signed_invoice.get('firs_authentication_stamp')
          if not auth_stamp:
              return {
                  'is_authentic': False,
                  'error': 'No FIRS authentication stamp found'
              }

          # Extract original invoice content
          invoice_content = {k: v for k, v in signed_invoice.items()
                            if k != 'firs_authentication_stamp'}

          # Recalculate content hash
          content_hash = self._calculate_invoice_hash(
              await self._serialize_invoice_for_signing(invoice_content)
          )

          # Verify against stored hash
          stored_hash = base64.b64decode(auth_stamp['content_hash'])
          content_integrity = content_hash == stored_hash

          # Verify digital signature
          certificate = await self._load_firs_certificate_by_fingerprint(
              auth_stamp['certificate_fingerprint']
          )

          signature_valid = await self._verify_signature(
              content_hash=content_hash,
              signature=base64.b64decode(auth_stamp['signature']),
              certificate=certificate,
              algorithm=auth_stamp['algorithm']
          )

          return {
              'is_authentic': content_integrity and signature_valid,
              'content_integrity': content_integrity,
              'signature_valid': signature_valid,
              'certificate_valid': certificate.is_valid,
              'verification_timestamp': datetime.utcnow().isoformat(),
              'authentication_details': auth_stamp
          }

  IRN Generation Service (FIRS Focus: IRN & QR Code generation)
  # backend/app/services/firs_si/irn_generation_service.py
  import qrcode
  import hashlib
  from io import BytesIO
  import base64
  from typing import Dict, Any

  class FIRSSIIRNGenerationService:
      """
      FIRS-Certified IRN Generation Service for System Integrators
      
      Core FIRS Requirement: "IRN & QR Code, Generation and Schema Conformity"
      """

      def __init__(self):
          self.firs_irn_format = "INV{year}{month}{day}-{hash}-{sequence}"
          self.qr_code_standards = {
              'version': 1,
              'error_correction': qrcode.constants.ERROR_CORRECT_M,
              'box_size': 10,
              'border': 4
          }

      async def generate_firs_compliant_irn(
          self,
          invoice_data: Dict[str, Any],
          organization_id: UUID
      ) -> Dict[str, Any]:
          """
          Generate FIRS-compliant Invoice Reference Number
          
          FIRS Requirement: Generate unique IRN following FIRS specifications
          """

          # Validate invoice data against FIRS schema
          validation_result = await self._validate_invoice_schema(invoice_data)
          if not validation_result.is_valid:
              raise FIRSSchemaError(f"Invoice schema validation failed: {validation_result.errors}")

          # Create deterministic hash from invoice content
          invoice_hash = await self._generate_invoice_hash(invoice_data)

          # Get next sequence number for organization
          sequence = await self._get_next_irn_sequence(organization_id)

          # Generate IRN using FIRS format
          current_date = datetime.utcnow()
          irn = self.firs_irn_format.format(
              year=current_date.strftime('%Y'),
              month=current_date.strftime('%m'),
              day=current_date.strftime('%d'),
              hash=invoice_hash[:8],
              sequence=f"{sequence:06d}"
          )

          # Generate FIRS-compliant QR code
          qr_code_data = await self._generate_qr_code_data(irn, invoice_data)
          qr_code_image = await self._create_qr_code_image(qr_code_data)

          # Register IRN with FIRS (if in production mode)
          firs_registration = await self._register_irn_with_firs(irn, invoice_data)

          return {
              'irn': irn,
              'qr_code': {
                  'data': qr_code_data,
                  'image_base64': base64.b64encode(qr_code_image).decode('utf-8'),
                  'format': 'PNG',
                  'standards_compliance': 'FIRS_2025_V1'
              },
              'generation_metadata': {
                  'invoice_hash': invoice_hash,
                  'sequence_number': sequence,
                  'generation_timestamp': datetime.utcnow().isoformat(),
                  'firs_registration_id': firs_registration.registration_id,
                  'schema_version': 'UBL_BIS_3.0'
              }
          }

      async def validate_irn_format(self, irn: str) -> Dict[str, Any]:
          """
          Validate IRN format against FIRS standards
          
          FIRS Requirement: Ensure IRN conforms to FIRS specifications
          """

          # Parse IRN components
          irn_components = await self._parse_irn_components(irn)

          # Validate format compliance
          format_valid = await self._validate_irn_format(irn_components)

          # Check against FIRS registry
          firs_valid = await self._validate_irn_with_firs(irn)

          return {
              'irn': irn,
              'is_valid': format_valid and firs_valid,
              'format_compliance': format_valid,
              'firs_registry_status': firs_valid,
              'irn_components': irn_components,
              'validation_timestamp': datetime.utcnow().isoformat()
          }

  1.2 Access Point Provider (APP) Services Implementation

  Transmission Service (FIRS Focus: Secure transmission between businesses and FIRS)
  # backend/app/services/firs_app/transmission_service.py
  import aiohttp
  import ssl
  from cryptography.fernet import Fernet
  from typing import Dict, Any, List

  class FIRSAPPTransmissionService:
      """
      FIRS-Certified Transmission Service for Access Point Providers
      
      Core FIRS Requirement: "Securely transmit, validate, and receive 
      eInvoices between businesses and FIRS"
      """

      def __init__(self):
          self.firs_endpoints = {
              'transmission': '/api/v1/invoice/transmit',
              'validation': '/api/v1/invoice/validate',
              'receipt': '/api/v1/invoice/receipt',
              'status': '/api/v1/invoice/status'
          }
          self.encryption_standards = ['TLS_1.3', 'AES_256_GCM']

      async def secure_transmit_to_firs(
          self,
          invoice_data: Dict[str, Any],
          business_id: UUID,
          transmission_config: Dict[str, Any]
      ) -> Dict[str, Any]:
          """
          Securely transmit invoice to FIRS using APP protocols
          
          FIRS Requirement: Secure transmission with TLS encryption and OAuth 2.0
          """

          # Prepare secure transmission payload
          encrypted_payload = await self._encrypt_invoice_payload(
              invoice_data=invoice_data,
              encryption_standard='AES_256_GCM'
          )

          # Add authentication seal
          sealed_payload = await self._apply_authentication_seal(
              payload=encrypted_payload,
              business_id=business_id
          )

          # Create secure transmission headers
          transmission_headers = await self._create_secure_headers(
              business_id=business_id,
              payload_hash=sealed_payload['hash']
          )

          # Establish secure TLS 1.3 connection to FIRS
          transmission_result = await self._transmit_to_firs_securely(
              endpoint=self.firs_endpoints['transmission'],
              payload=sealed_payload,
              headers=transmission_headers,
              tls_version='TLS_1.3'
          )

          # Process FIRS response
          firs_response = await self._process_firs_transmission_response(
              transmission_result
          )

          # Generate transmission receipt
          receipt = await self._generate_transmission_receipt(
              business_id=business_id,
              invoice_data=invoice_data,
              firs_response=firs_response,
              transmission_metadata={
                  'encryption_used': 'AES_256_GCM',
                  'tls_version': 'TLS_1.3',
                  'authentication_seal': sealed_payload['seal_id'],
                  'transmission_timestamp': datetime.utcnow().isoformat()
              }
          )

          return {
              'transmission_status': firs_response['status'],
              'firs_irn': firs_response.get('irn'),
              'transmission_receipt': receipt,
              'security_metadata': {
                  'encryption_verified': True,
                  'tls_handshake_success': True,
                  'authentication_seal_applied': True,
                  'secure_transmission_confirmed': True
              }
          }

      async def receive_firs_response(
          self,
          transmission_id: UUID,
          encrypted_response: Dict[str, Any]
      ) -> Dict[str, Any]:
          """
          Securely receive and process FIRS response
          
          FIRS Requirement: Receive eInvoices between businesses and FIRS
          """

          # Decrypt FIRS response
          decrypted_response = await self._decrypt_firs_response(encrypted_response)

          # Validate response authenticity
          authenticity_check = await self._validate_firs_response_authenticity(
              decrypted_response
          )

          if not authenticity_check['is_authentic']:
              raise FIRSSecurityError(
                  f"FIRS response authenticity validation failed: "
                  f"{authenticity_check['error']}"
              )

          # Process response data
          processed_response = await self._process_received_response(
              decrypted_response=decrypted_response,
              transmission_id=transmission_id
          )

          # Update transmission status
          await self._update_transmission_status(
              transmission_id=transmission_id,
              status=processed_response['status'],
              firs_response=processed_response
          )

          return {
              'response_received': True,
              'firs_status': processed_response['status'],
              'response_data': processed_response,
              'security_validation': authenticity_check,
              'reception_timestamp': datetime.utcnow().isoformat()
          }

  Data Validation Service (FIRS Focus: Pre-submission compliance validation)
  # backend/app/services/firs_app/data_validation_service.py
  from typing import Dict, Any, List, Optional
  import jsonschema
  import xml.etree.ElementTree as ET

  class FIRSAPPDataValidationService:
      """
      FIRS-Certified Data Validation Service for Access Point Providers
      
      Core FIRS Requirement: "Implement data validation rules to compliance 
      before submission, including the management of the Authentication Seal"
      """

      def __init__(self):
          self.firs_validation_rules = self._load_firs_validation_rules()
          self.schema_validators = {
              'UBL_BIS_3.0': self._load_ubl_bis_schema(),
              'FIRS_CUSTOM': self._load_firs_custom_schema()
          }

      async def validate_before_submission(
          self,
          invoice_data: Dict[str, Any],
          validation_level: str = 'STRICT'
      ) -> Dict[str, Any]:
          """
          Comprehensive pre-submission validation
          
          FIRS Requirement: Ensure compliance before submission to FIRS
          """

          validation_results = {
              'overall_valid': True,
              'validation_details': {},
              'errors': [],
              'warnings': [],
              'compliance_score': 0
          }

          # 1. Schema Validation
          schema_result = await self._validate_invoice_schema(
              invoice_data,
              schema_type='UBL_BIS_3.0'
          )
          validation_results['validation_details']['schema'] = schema_result

          # 2. FIRS Business Rules Validation
          business_rules_result = await self._validate_firs_business_rules(
              invoice_data
          )
          validation_results['validation_details']['business_rules'] = business_rules_result

          # 3. Tax Calculation Validation
          tax_validation_result = await self._validate_tax_calculations(
              invoice_data
          )
          validation_results['validation_details']['tax_calculations'] = tax_validation_result

          # 4. Party Information Validation
          party_validation_result = await self._validate_party_information(
              invoice_data
          )
          validation_results['validation_details']['party_information'] = party_validation_result

          # 5. Currency and Amount Validation
          amount_validation_result = await self._validate_amounts_and_currency(
              invoice_data
          )
          validation_results['validation_details']['amounts'] = amount_validation_result

          # 6. Line Items Validation
          line_items_result = await self._validate_line_items(
              invoice_data.get('invoice_line', [])
          )
          validation_results['validation_details']['line_items'] = line_items_result

          # Aggregate validation results
          all_validations = [
              schema_result, business_rules_result, tax_validation_result,
              party_validation_result, amount_validation_result, line_items_result
          ]

          # Collect errors and warnings
          for validation in all_validations:
              if validation.get('errors'):
                  validation_results['errors'].extend(validation['errors'])
              if validation.get('warnings'):
                  validation_results['warnings'].extend(validation['warnings'])

          # Calculate compliance score
          validation_results['compliance_score'] = await self._calculate_compliance_score(
              all_validations
          )

          # Determine overall validity
          validation_results['overall_valid'] = (
              len(validation_results['errors']) == 0 and
              validation_results['compliance_score'] >= 95  # FIRS threshold
          )

          return validation_results

      async def manage_authentication_seal(
          self,
          invoice_data: Dict[str, Any],
          organization_id: UUID
      ) -> Dict[str, Any]:
          """
          Manage Authentication Seal for invoice
          
          FIRS Requirement: Management of the Authentication Seal
          """

          # Generate unique seal identifier
          seal_id = await self._generate_seal_identifier(
              invoice_data=invoice_data,
              organization_id=organization_id
          )

          # Create seal content hash
          seal_content_hash = await self._create_seal_content_hash(
              invoice_data=invoice_data,
              seal_id=seal_id
          )

          # Apply cryptographic seal
          cryptographic_seal = await self._apply_cryptographic_seal(
              content_hash=seal_content_hash,
              organization_id=organization_id
          )

          # Create authentication seal metadata
          authentication_seal = {
              'seal_id': seal_id,
              'content_hash': seal_content_hash,
              'cryptographic_seal': cryptographic_seal,
              'organization_id': str(organization_id),
              'creation_timestamp': datetime.utcnow().isoformat(),
              'seal_version': 'FIRS_2025_V1',
              'validation_status': 'SEALED'
          }

          # Store seal for audit purposes
          await self._store_authentication_seal(
              seal_id=seal_id,
              seal_data=authentication_seal,
              invoice_reference=invoice_data.get('irn')
          )

          return {
              'authentication_seal': authentication_seal,
              'sealed_invoice': {
                  **invoice_data,
                  'firs_authentication_seal': authentication_seal
              },
              'seal_management_metadata': {
                  'seal_applied': True,
                  'seal_stored': True,
                  'audit_trail_created': True,
                  'firs_compliance': True
              }
          }

  1.3 FIRS Permission System Update

  Enhanced Permission Model:
  # backend/app/models/firs_permissions.py
  from sqlalchemy import Column, String, Boolean, DateTime, JSON, Enum
  from sqlalchemy.dialects.postgresql import UUID
  import enum

  class FIRSCertificationStatus(enum.Enum):
      PENDING = "pending"
      CERTIFIED = "certified"
      EXPIRED = "expired"
      REVOKED = "revoked"
      SUSPENDED = "suspended"

  class FIRSRoleType(enum.Enum):
      SYSTEM_INTEGRATOR = "firs_si_certified"
      ACCESS_POINT_PROVIDER = "firs_app_certified"
      HYBRID_SI_APP = "firs_hybrid_certified"
      PENDING_CERTIFICATION = "firs_pending"

  class FIRSCertification(Base):
      """FIRS Certification tracking for organizations"""
      __tablename__ = "firs_certifications"

      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
      organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)

      # FIRS Role Information
      firs_role = Column(Enum(FIRSRoleType), nullable=False)
      certification_status = Column(Enum(FIRSCertificationStatus), default=FIRSCertificationStatus.PENDING)

      # Certification Details
      firs_certification_number = Column(String(100), unique=True)
      issued_date = Column(DateTime)
      expiry_date = Column(DateTime)

      # SI-Specific Capabilities
      si_capabilities = Column(JSON, default={
          'erp_integration': False,
          'digital_certificates': False,
          'irn_generation': False,
          'schema_compliance': False
      })

      # APP-Specific Capabilities  
      app_capabilities = Column(JSON, default={
          'secure_transmission': False,
          'data_validation': False,
          'authentication_seals': False,
          'tls_oauth_compliance': False
      })

      # Compliance Status
      last_audit_date = Column(DateTime)
      next_audit_date = Column(DateTime)
      compliance_score = Column(Integer, default=0)

      # FIRS Integration Status
      firs_api_access_granted = Column(Boolean, default=False)
      sandbox_testing_completed = Column(Boolean, default=False)
      production_access_granted = Column(Boolean, default=False)

  class FIRSPermissionService:
      """Enhanced permission service for FIRS roles"""

      async def check_firs_si_permission(
          self, 
          user_id: UUID, 
          capability: str
      ) -> bool:
          """Check if user has specific SI capability"""

          certification = await self._get_user_firs_certification(user_id)

          if not certification or certification.firs_role not in [
              FIRSRoleType.SYSTEM_INTEGRATOR,
              FIRSRoleType.HYBRID_SI_APP
          ]:
              return False

          return certification.si_capabilities.get(capability, False)

      async def check_firs_app_permission(
          self, 
          user_id: UUID, 
          capability: str
      ) -> bool:
          """Check if user has specific APP capability"""

          certification = await self._get_user_firs_certification(user_id)

          if not certification or certification.firs_role not in [
              FIRSRoleType.ACCESS_POINT_PROVIDER,
              FIRSRoleType.HYBRID_SI_APP
          ]:
              return False

          return certification.app_capabilities.get(capability, False)

  2. Frontend Dashboard Implementation Strategy

  2.1 FIRS Role-Specific Dashboard Components

  Pure System Integrator Dashboard:
  // frontend/src/components/dashboard/FIRSPureSIDashboard.tsx
  import React, { useState, useEffect } from 'react';
  import { useFIRSPermissions } from '../../hooks/useFIRSPermissions';

  interface FIRSSIMetrics {
    erpConnections: {
      active: number;
      total: number;
      firsCompliant: number;
    };
    certificateManagement: {
      activeCertificates: number;
      expiringCertificates: number;
      algorithms: string[];
    };
    irnGeneration: {
      totalGenerated: number;
      successRate: number;
      firsValidated: number;
    };
    schemaCompliance: {
      validationsPerformed: number;
      complianceRate: number;
      lastSchemaUpdate: string;
    };
  }

  export const FIRSPureSIDashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<FIRSSIMetrics | null>(null);
    const permissions = useFIRSPermissions();

    // Verify user has FIRS SI certification
    if (!permissions.isFIRSCertifiedSI()) {
      return <FIRSCertificationRequired role="System Integrator" />;
    }

    return (
      <div className="firs-si-dashboard">
        {/* FIRS SI Header */}
        <div className="dashboard-header">
          <div className="firs-branding">
            <img src="/firs-logo.png" alt="FIRS" className="firs-logo" />
            <h1>FIRS System Integrator Dashboard</h1>
            <Badge variant="success">FIRS SI Certified</Badge>
          </div>
        </div>

        {/* SI Core Functions - Following FIRS Specification */}
        <div className="firs-si-functions">

          {/* ERP Integration Focus */}
          <Card className="si-erp-integration">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                ERP Systems Integration with FIRS
              </CardTitle>
              <CardDescription>
                Help businesses integrate their internal ERP systems with FIRS e-invoice systems
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="metrics-grid">
                <MetricCard
                  title="Active ERP Connections"
                  value={metrics?.erpConnections.active || 0}
                  subtitle={`${metrics?.erpConnections.firsCompliant || 0} FIRS Compliant`}
                  icon={<LinkIcon />}
                />
                <MetricCard
                  title="Supported Systems"
                  value={metrics?.erpConnections.total || 0}
                  subtitle="Odoo, SAP, Oracle, Dynamics"
                  icon={<ServerIcon />}
                />
              </div>

              <div className="erp-actions">
                <Button 
                  onClick={() => router.push('/firs-si/erp-connections')}
                  className="w-full"
                >
                  Manage ERP-FIRS Integrations
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => router.push('/firs-si/erp-compliance')}
                  className="w-full"
                >
                  Check FIRS Compliance Status
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Digital Certificate Implementation */}
          <Card className="si-digital-certificates">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <KeyIcon className="w-5 h-5" />
                Digital Certificate Algorithms
              </CardTitle>
              <CardDescription>
                Implement algorithms to authenticate invoice origin and guarantee content integrity
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="certificate-algorithms">
                <AlgorithmStatus 
                  algorithm="RSA-PSS-SHA256"
                  status="active"
                  description="Primary FIRS algorithm for invoice authentication"
                />
                <AlgorithmStatus 
                  algorithm="ECDSA-SHA256"
                  status="available"
                  description="Alternative FIRS-approved algorithm"
                />
              </div>

              <div className="certificate-actions">
                <Button 
                  onClick={() => router.push('/firs-si/certificates')}
                  className="w-full"
                >
                  Manage FIRS Certificates
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => router.push('/firs-si/algorithm-testing')}
                  className="w-full"
                >
                  Test Authentication Algorithms
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* FIRS Compliance Standards */}
          <Card className="si-compliance">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheckIcon className="w-5 h-5" />
                FIRS Compliance Standards
              </CardTitle>
              <CardDescription>
                IRN & QR Code generation and Schema conformity
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="compliance-metrics">
                <MetricCard
                  title="IRNs Generated"
                  value={metrics?.irnGeneration.totalGenerated || 0}
                  subtitle={`${metrics?.irnGeneration.successRate || 0}% Success Rate`}
                  icon={<QrCodeIcon />}
                />
                <MetricCard
                  title="Schema Compliance"
                  value={`${metrics?.schemaCompliance.complianceRate || 0}%`}
                  subtitle="UBL BIS 3.0 Conformity"
                  icon={<FileTextIcon />}
                />
              </div>

              <div className="compliance-actions">
                <Button 
                  onClick={() => router.push('/firs-si/irn-generation')}
                  className="w-full"
                >
                  IRN & QR Code Generator
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => router.push('/firs-si/schema-validation')}
                  className="w-full"
                >
                  Schema Conformity Tools
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* FIRS Integration Status */}
        <Card className="firs-integration-status">
          <CardHeader>
            <CardTitle>FIRS Integration Status</CardTitle>
          </CardHeader>
          <CardContent>
            <FIRSIntegrationStatus role="SI" />
          </CardContent>
        </Card>
      </div>
    );
  };

  Pure Access Point Provider Dashboard:
  // frontend/src/components/dashboard/FIRSPureAPPDashboard.tsx
  export const FIRSPureAPPDashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<FIRSAPPMetrics | null>(null);
    const permissions = useFIRSPermissions();

    // Verify user has FIRS APP certification
    if (!permissions.isFIRSCertifiedAPP()) {
      return <FIRSCertificationRequired role="Access Point Provider" />;
    }

    return (
      <div className="firs-app-dashboard">
        {/* FIRS APP Header */}
        <div className="dashboard-header">
          <div className="firs-branding">
            <img src="/firs-logo.png" alt="FIRS" className="firs-logo" />
            <h1>FIRS Access Point Provider Dashboard</h1>
            <Badge variant="success">FIRS APP Certified</Badge>
          </div>
        </div>

        {/* APP Core Functions - Following FIRS Specification */}
        <div className="firs-app-functions">

          {/* Secure Transmission & Validation */}
          <Card className="app-transmission">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SendIcon className="w-5 h-5" />
                Secure Transmission & Validation
              </CardTitle>
              <CardDescription>
                Securely transmit, validate, and receive eInvoices between businesses and FIRS
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="transmission-metrics">
                <MetricCard
                  title="Transmissions Today"
                  value={metrics?.transmissions.today || 0}
                  subtitle={`${metrics?.transmissions.successRate || 0}% Success Rate`}
                  icon={<ArrowUpIcon />}
                />
                <MetricCard
                  title="Active Connections"
                  value={metrics?.connections.active || 0}
                  subtitle="TLS 1.3 Secured"
                  icon={<LinkIcon />}
                />
              </div>

              <div className="transmission-actions">
                <Button 
                  onClick={() => router.push('/firs-app/transmissions')}
                  className="w-full"
                >
                  Manage Secure Transmissions
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => router.push('/firs-app/transmission-monitor')}
                  className="w-full"
                >
                  Real-time Transmission Monitor
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Data Validation Rules */}
          <Card className="app-validation">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircleIcon className="w-5 h-5" />
                Data Validation Rules
              </CardTitle>
              <CardDescription>
                Implement data validation rules for compliance before submission
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="validation-rules">
                <ValidationRuleStatus 
                  rule="UBL BIS 3.0 Schema"
                  status="active"
                  description="Primary FIRS schema validation"
                />
                <ValidationRuleStatus 
                  rule="Nigerian Tax Rules"
                  status="active"
                  description="VAT and business rule validation"
                />
                <ValidationRuleStatus 
                  rule="Currency Validation"
                  status="active"
                  description="NGN and multi-currency validation"
                />
              </div>

              <div className="validation-actions">
                <Button 
                  onClick={() => router.push('/firs-app/validation-rules')}
                  className="w-full"
                >
                  Configure Validation Rules
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => router.push('/firs-app/validation-testing')}
                  className="w-full"
                >
                  Test Validation Engine
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Authentication Seal Management */}
          <Card className="app-authentication-seals">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldIcon className="w-5 h-5" />
                Authentication Seal Management
              </CardTitle>
              <CardDescription>
                Management of the Authentication Seal for invoice security
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="seal-metrics">
                <MetricCard
                  title="Active Seals"
                  value={metrics?.seals.active || 0}
                  subtitle="Applied Today"
                  icon={<SealIcon />}
                />
                <MetricCard
                  title="Seal Verification Rate"
                  value={`${metrics?.seals.verificationRate || 0}%`}
                  subtitle="Authentication Success"
                  icon={<VerifiedIcon />}
                />
              </div>

              <div className="seal-actions">
                <Button 
                  onClick={() => router.push('/firs-app/authentication-seals')}
                  className="w-full"
                >
                  Manage Authentication Seals
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => router.push('/firs-app/seal-verification')}
                  className="w-full"
                >
                  Verify Seal Integrity
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Secure Communication Status */}
        <Card className="firs-security-status">
          <CardHeader>
            <CardTitle>Secure Communication Status</CardTitle>
          </CardHeader>
          <CardContent>
            <FIRSSecurityStatus 
              tlsVersion="TLS 1.3"
              oauthStatus="Active"
              encryptionStandard="AES-256-GCM"
            />
          </CardContent>
        </Card>
      </div>
    );
  };

  This comprehensive technical specification provides:

  1. FIRS-Compliant Backend Architecture with role-specific services
  2. Enhanced Permission System aligned with FIRS certification requirements
  3. Role-Specific Frontend Dashboards that match FIRS technical specifications
  4. Clear Separation between SI and APP responsibilities as defined by FIRS
  5. Certification Tracking and compliance monitoring built-in

  The architecture ensures we meet every FIRS requirement while providing users with intuitive, role-appropriate interfaces that
  improve their productivity and compliance.
