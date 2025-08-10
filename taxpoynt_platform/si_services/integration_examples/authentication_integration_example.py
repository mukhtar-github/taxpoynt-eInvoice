"""
SI Authentication Services Integration Example

This example demonstrates how the newly integrated authentication services
work together to provide secure end-to-end workflows from ERP to FIRS submission.

Example workflows:
1. ERP Connection → Data Extraction → IRN Generation → FIRS Submission
2. Certificate-based Authentication for FIRS
3. Session Management and Token Refresh
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import integrated services
from taxpoynt_platform.si_services.authentication import (
    AuthenticationManager,
    ERPAuthProvider,
    FIRSAuthService,
    CertificateAuth,
    TokenManager,
    CredentialStore,
    AuthMethod,
    ERPSystem
)

from taxpoynt_platform.si_services.erp_integration import (
    create_authenticated_erp_session_manager,
    ERPType,
    SessionManagerConfig
)

from taxpoynt_platform.si_services.certificate_management import (
    CertificateService
)

from taxpoynt_platform.si_services.irn_qr_generation import (
    IRNGenerationService
)

logger = logging.getLogger(__name__)


class AuthenticationIntegrationDemo:
    """
    Demonstration of integrated authentication services across SI components
    """
    
    def __init__(self):
        # Initialize authentication manager
        self.auth_manager = AuthenticationManager()
        
        # Initialize component services with authentication
        self.erp_session_manager = create_authenticated_erp_session_manager()
        self.certificate_service = CertificateService(
            db=None,  # Mock DB for demo
            auth_manager=self.auth_manager
        )
        self.irn_service = IRNGenerationService(auth_manager=self.auth_manager)
        
        # Initialize specialized auth services
        self.erp_auth = ERPAuthProvider()
        self.firs_auth = FIRSAuthService()
        self.cert_auth = CertificateAuth()
        self.token_manager = TokenManager()
        self.credential_store = CredentialStore()
    
    async def start_services(self):
        """Start all authentication and service components"""
        try:
            logger.info("Starting authentication services...")
            
            # Start core authentication services
            await self.auth_manager.start()
            await self.credential_store.initialize()
            await self.token_manager.start()
            
            # Start ERP session manager (includes auth services)
            await self.erp_session_manager.start_session_manager()
            
            logger.info("All authentication services started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            raise
    
    async def stop_services(self):
        """Stop all services gracefully"""
        try:
            logger.info("Stopping authentication services...")
            
            await self.erp_session_manager.stop_session_manager()
            await self.auth_manager.stop()
            await self.token_manager.stop()
            await self.credential_store.cleanup()
            
            logger.info("All services stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
    
    async def demo_erp_to_firs_workflow(self) -> Dict[str, Any]:
        """
        Demonstrate complete ERP to FIRS workflow with authentication
        """
        workflow_result = {
            'started_at': datetime.now().isoformat(),
            'steps': [],
            'success': False
        }
        
        try:
            # Step 1: Register ERP connection with authentication
            logger.info("Step 1: Registering ERP connection...")
            
            erp_config = {
                'host': 'demo-odoo.example.com',
                'port': 443,
                'database': 'demo_db',
                'username': 'demo_user',
                'password': 'demo_password',
                'ssl_enabled': True
            }
            
            # Register ERP with authentication
            registration_success = await self.erp_session_manager.register_erp_connection(
                erp_type=ERPType.ODOO,
                config=erp_config
            )
            
            workflow_result['steps'].append({
                'step': 'erp_registration',
                'success': registration_success,
                'timestamp': datetime.now().isoformat()
            })
            
            if not registration_success:
                workflow_result['error'] = 'ERP registration failed'
                return workflow_result
            
            # Step 2: Create authenticated ERP session
            logger.info("Step 2: Creating authenticated ERP session...")
            
            async with self.erp_session_manager.get_session_context(
                ERPType.ODOO,
                user_context={'workflow': 'invoice_extraction'}
            ) as session:
                
                if not session:
                    workflow_result['error'] = 'Failed to create ERP session'
                    return workflow_result
                
                workflow_result['steps'].append({
                    'step': 'erp_session_created',
                    'success': True,
                    'session_id': session.session_id,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Step 3: Extract invoice data (mock)
                logger.info("Step 3: Extracting invoice data...")
                
                invoice_data = {
                    'seller_gstin': '29ABCDE1234F1Z5',
                    'buyer_gstin': '29FGHIJ5678K2X6',
                    'invoice_number': 'INV-2023-001',
                    'invoice_date': '2023-12-01',
                    'taxable_value': 10000.00,
                    'total_tax': 1800.00,
                    'total_amount': 11800.00
                }
                
                workflow_result['steps'].append({
                    'step': 'data_extraction',
                    'success': True,
                    'invoice_number': invoice_data['invoice_number'],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Step 4: Generate IRN
                logger.info("Step 4: Generating IRN...")
                
                irn, qr_code, verification_code = self.irn_service.generate_irn(invoice_data)
                
                workflow_result['steps'].append({
                    'step': 'irn_generation',
                    'success': bool(irn),
                    'irn': irn,
                    'timestamp': datetime.now().isoformat()
                })
                
                if not irn:
                    workflow_result['error'] = 'IRN generation failed'
                    return workflow_result
                
                # Step 5: Authenticate with FIRS
                logger.info("Step 5: Authenticating with FIRS...")
                
                firs_auth_result = await self.irn_service.authenticate_with_firs(
                    environment='sandbox'
                )
                
                workflow_result['steps'].append({
                    'step': 'firs_authentication',
                    'success': firs_auth_result['success'],
                    'environment': 'sandbox',
                    'timestamp': datetime.now().isoformat()
                })
                
                if not firs_auth_result['success']:
                    workflow_result['error'] = f"FIRS authentication failed: {firs_auth_result.get('error')}"
                    return workflow_result
                
                # Step 6: Submit IRN to FIRS
                logger.info("Step 6: Submitting IRN to FIRS...")
                
                submission_result = await self.irn_service.submit_irn_to_firs(
                    irn_value=irn,
                    invoice_data=invoice_data,
                    environment='sandbox'
                )
                
                workflow_result['steps'].append({
                    'step': 'firs_submission',
                    'success': submission_result['success'],
                    'irn': irn,
                    'timestamp': datetime.now().isoformat()
                })
                
                if submission_result['success']:
                    workflow_result['success'] = True
                    workflow_result['final_result'] = {
                        'irn': irn,
                        'qr_code': qr_code,
                        'verification_code': verification_code,
                        'firs_response': submission_result.get('firs_response')
                    }
                else:
                    workflow_result['error'] = f"FIRS submission failed: {submission_result.get('error')}"
            
            workflow_result['completed_at'] = datetime.now().isoformat()
            return workflow_result
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            workflow_result['error'] = str(e)
            workflow_result['completed_at'] = datetime.now().isoformat()
            return workflow_result
    
    async def demo_certificate_authentication(self) -> Dict[str, Any]:
        """
        Demonstrate certificate-based authentication
        """
        try:
            logger.info("Demonstrating certificate-based authentication...")
            
            # Generate a demo certificate
            subject_info = {
                'common_name': 'demo.taxpoynt.com',
                'organization': 'TaxPoynt Demo',
                'country': 'NG'
            }
            
            cert_id, cert_pem = self.certificate_service.generate_certificate(
                subject_info=subject_info,
                organization_id='demo-org-001',
                validity_days=365,
                certificate_type='ssl_client'
            )
            
            # Authenticate using the certificate
            auth_result = await self.certificate_service.authenticate_with_certificate(
                certificate_data=cert_pem,
                target_service='firs',
                context={
                    'host': 'sandbox.firs.gov.ng',
                    'purpose': 'api_access'
                }
            )
            
            return {
                'certificate_id': cert_id,
                'authentication_success': auth_result['success'],
                'auth_details': auth_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Certificate authentication demo error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def demo_token_management(self) -> Dict[str, Any]:
        """
        Demonstrate token management and refresh
        """
        try:
            logger.info("Demonstrating token management...")
            
            # Generate a mock token
            token_result = await self.token_manager.generate_token(
                token_type='oauth2',
                context={
                    'client_id': 'demo_client',
                    'scope': 'api_access',
                    'expires_in': 3600
                }
            )
            
            if not token_result.success:
                return {
                    'success': False,
                    'error': 'Token generation failed',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate the token
            validation_result = await self.token_manager.validate_token(
                token=token_result.token_data['access_token'],
                context={'expected_scope': 'api_access'}
            )
            
            # Attempt token refresh (will use mock refresh token)
            refresh_result = await self.token_manager.refresh_token(
                token=token_result.token_data['access_token'],
                refresh_token=token_result.token_data.get('refresh_token'),
                context={'client_id': 'demo_client'}
            )
            
            return {
                'token_generation': token_result.success,
                'token_validation': validation_result.success,
                'token_refresh': refresh_result.success,
                'token_details': {
                    'expires_at': token_result.expires_at.isoformat() if token_result.expires_at else None,
                    'scope': token_result.token_data.get('scope')
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Token management demo error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


async def run_authentication_integration_demo():
    """
    Run the complete authentication integration demonstration
    """
    demo = AuthenticationIntegrationDemo()
    
    try:
        print("🚀 Starting TaxPoynt SI Authentication Integration Demo")
        print("=" * 60)
        
        # Start services
        await demo.start_services()
        print("✅ Authentication services started successfully")
        
        # Demo 1: Complete ERP to FIRS workflow
        print("\n📊 Demo 1: Complete ERP to FIRS Workflow")
        print("-" * 40)
        
        workflow_result = await demo.demo_erp_to_firs_workflow()
        
        print(f"Workflow Success: {workflow_result['success']}")
        if workflow_result['success']:
            print(f"✅ IRN Generated: {workflow_result['final_result']['irn']}")
            print(f"✅ FIRS Submission: Successful")
        else:
            print(f"❌ Error: {workflow_result.get('error')}")
        
        for step in workflow_result['steps']:
            status = "✅" if step['success'] else "❌"
            print(f"  {status} {step['step']}: {step.get('timestamp', 'N/A')}")
        
        # Demo 2: Certificate Authentication
        print("\n🔐 Demo 2: Certificate-Based Authentication")
        print("-" * 40)
        
        cert_result = await demo.demo_certificate_authentication()
        if cert_result.get('authentication_success'):
            print("✅ Certificate authentication successful")
            print(f"   Certificate ID: {cert_result['certificate_id']}")
        else:
            print(f"❌ Certificate authentication failed: {cert_result.get('error')}")
        
        # Demo 3: Token Management
        print("\n🎟️ Demo 3: Token Management")
        print("-" * 40)
        
        token_result = await demo.demo_token_management()
        print(f"Token Generation: {'✅' if token_result.get('token_generation') else '❌'}")
        print(f"Token Validation: {'✅' if token_result.get('token_validation') else '❌'}")
        print(f"Token Refresh: {'✅' if token_result.get('token_refresh') else '❌'}")
        
        print("\n🎉 Authentication Integration Demo Completed Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}")
    
    finally:
        # Stop services
        await demo.stop_services()
        print("🛑 Services stopped gracefully")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demo
    asyncio.run(run_authentication_integration_demo())