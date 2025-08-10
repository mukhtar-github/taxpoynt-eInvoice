"""
PEPPOL Standard Business Document Header (SBDH) Handler
======================================================
Implementation of PEPPOL envelope specification (SBDH) for message routing
and participant identification. Every PEPPOL message must be wrapped in SBDH envelope.
"""
import logging
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from decimal import Decimal

from .models import PEPPOLDocument, PEPPOLParticipant, DocumentType


class SBDHProcessor:
    """
    Standard Business Document Header processor for PEPPOL message enveloping
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sbdh_version = "1.3"
        self.standard_business_document_ns = "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader"
        
    def create_sbdh_envelope(self, peppol_document: PEPPOLDocument,
                           routing_metadata: Dict[str, Any]) -> str:
        """
        Create SBDH envelope wrapper for PEPPOL document
        
        Args:
            peppol_document: PEPPOL document to wrap
            routing_metadata: PEPPOL routing and delivery information
            
        Returns:
            Complete SBDH-wrapped XML document
        """
        try:
            # Generate unique instance identifier
            instance_identifier = str(uuid.uuid4())
            creation_timestamp = datetime.now().isoformat()
            
            # Build SBDH header
            sbdh_header = self._build_sbdh_header(
                peppol_document, routing_metadata, instance_identifier, creation_timestamp
            )
            
            # Wrap document content
            document_content = self._prepare_document_content(peppol_document)
            
            # Create complete envelope
            sbdh_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<StandardBusinessDocument xmlns="{self.standard_business_document_ns}">
    {sbdh_header}
    {document_content}
</StandardBusinessDocument>"""
            
            self.logger.info(f"Created SBDH envelope for document {peppol_document.document_id}")
            return sbdh_envelope
            
        except Exception as e:
            self.logger.error(f"SBDH envelope creation failed: {str(e)}")
            raise
    
    def _build_sbdh_header(self, peppol_document: PEPPOLDocument,
                          routing_metadata: Dict[str, Any],
                          instance_identifier: str,
                          creation_timestamp: str) -> str:
        """Build the Standard Business Document Header"""
        
        # Extract participant information
        sender = peppol_document.sender_participant
        receiver = peppol_document.receiver_participant
        
        # Build header XML
        header = f"""<StandardBusinessDocumentHeader>
        <HeaderVersion>{self.sbdh_version}</HeaderVersion>
        <Sender>
            <Identifier Authority="{sender.scheme_id.value}">{sender.participant_id}</Identifier>
            <ContactInformation>
                <Contact>{sender.participant_name}</Contact>
                <EmailAddress>{sender.contact_info.get('email', '')}</EmailAddress>
                <TelephoneNumber>{sender.contact_info.get('phone', '')}</TelephoneNumber>
            </ContactInformation>
        </Sender>
        <Receiver>
            <Identifier Authority="{receiver.scheme_id.value}">{receiver.participant_id}</Identifier>
            <ContactInformation>
                <Contact>{receiver.participant_name}</Contact>
                <EmailAddress>{receiver.contact_info.get('email', '')}</EmailAddress>
                <TelephoneNumber>{receiver.contact_info.get('phone', '')}</TelephoneNumber>
            </ContactInformation>
        </Receiver>
        <DocumentIdentification>
            <Standard>{self._get_document_standard(peppol_document.document_type)}</Standard>
            <TypeVersion>{self._get_document_version(peppol_document.document_type)}</TypeVersion>
            <InstanceIdentifier>{instance_identifier}</InstanceIdentifier>
            <Type>{self._get_document_type_name(peppol_document.document_type)}</Type>
            <CreationDateAndTime>{creation_timestamp}</CreationDateAndTime>
        </DocumentIdentification>
        <BusinessScope>
            <Scope>
                <Type>DOCUMENTID</Type>
                <InstanceIdentifier>{self._get_peppol_document_id(peppol_document.document_type)}</InstanceIdentifier>
            </Scope>
            <Scope>
                <Type>PROCESSID</Type>
                <InstanceIdentifier>{peppol_document.profile_id}</InstanceIdentifier>
            </Scope>
            <Scope>
                <Type>COUNTRY_C1</Type>
                <InstanceIdentifier>{sender.country_code}</InstanceIdentifier>
            </Scope>
            <Scope>
                <Type>COUNTRY_C4</Type>
                <InstanceIdentifier>{receiver.country_code}</InstanceIdentifier>
            </Scope>
        </BusinessScope>
    </StandardBusinessDocumentHeader>"""
        
        return header
    
    def _get_document_standard(self, document_type: DocumentType) -> str:
        """Get document standard identifier"""
        standards_map = {
            DocumentType.INVOICE: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            DocumentType.CREDIT_NOTE: "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
            DocumentType.ORDER: "urn:oasis:names:specification:ubl:schema:xsd:Order-2",
            DocumentType.ORDER_RESPONSE: "urn:oasis:names:specification:ubl:schema:xsd:OrderResponse-2",
            DocumentType.DESPATCH_ADVICE: "urn:oasis:names:specification:ubl:schema:xsd:DespatchAdvice-2",
            DocumentType.RECEIPT_ADVICE: "urn:oasis:names:specification:ubl:schema:xsd:ReceiptAdvice-2",
            DocumentType.CATALOGUE: "urn:oasis:names:specification:ubl:schema:xsd:Catalogue-2",
            DocumentType.CATALOGUE_RESPONSE: "urn:oasis:names:specification:ubl:schema:xsd:CatalogueResponse-2"
        }
        return standards_map.get(document_type, "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    
    def _get_document_version(self, document_type: DocumentType) -> str:
        """Get document version"""
        return "2.1"  # UBL 2.1 is standard for PEPPOL
    
    def _get_document_type_name(self, document_type: DocumentType) -> str:
        """Get human-readable document type name"""
        type_names = {
            DocumentType.INVOICE: "Invoice",
            DocumentType.CREDIT_NOTE: "CreditNote", 
            DocumentType.ORDER: "Order",
            DocumentType.ORDER_RESPONSE: "OrderResponse",
            DocumentType.DESPATCH_ADVICE: "DespatchAdvice",
            DocumentType.RECEIPT_ADVICE: "ReceiptAdvice",
            DocumentType.CATALOGUE: "Catalogue",
            DocumentType.CATALOGUE_RESPONSE: "CatalogueResponse"
        }
        return type_names.get(document_type, "Invoice")
    
    def _get_peppol_document_id(self, document_type: DocumentType) -> str:
        """Get PEPPOL document identifier"""
        peppol_ids = {
            DocumentType.INVOICE: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1",
            DocumentType.CREDIT_NOTE: "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2::CreditNote##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1",
            DocumentType.ORDER: "urn:oasis:names:specification:ubl:schema:xsd:Order-2::Order##urn:fdc:peppol.eu:2017:poacc:ordering:3.0::2.1",
            DocumentType.ORDER_RESPONSE: "urn:oasis:names:specification:ubl:schema:xsd:OrderResponse-2::OrderResponse##urn:fdc:peppol.eu:2017:poacc:ordering:3.0::2.1",
            DocumentType.DESPATCH_ADVICE: "urn:oasis:names:specification:ubl:schema:xsd:DespatchAdvice-2::DespatchAdvice##urn:fdc:peppol.eu:2017:poacc:despatchadvice:3.0::2.1",
            DocumentType.RECEIPT_ADVICE: "urn:oasis:names:specification:ubl:schema:xsd:ReceiptAdvice-2::ReceiptAdvice##urn:fdc:peppol.eu:2017:poacc:receiptadvice:3.0::2.1",
            DocumentType.CATALOGUE: "urn:oasis:names:specification:ubl:schema:xsd:Catalogue-2::Catalogue##urn:fdc:peppol.eu:2017:poacc:catalogue:3.0::2.1",
            DocumentType.CATALOGUE_RESPONSE: "urn:oasis:names:specification:ubl:schema:xsd:CatalogueResponse-2::CatalogueResponse##urn:fdc:peppol.eu:2017:poacc:catalogue:3.0::2.1"
        }
        return peppol_ids.get(document_type, peppol_ids[DocumentType.INVOICE])
    
    def _prepare_document_content(self, peppol_document: PEPPOLDocument) -> str:
        """Prepare document content for SBDH envelope"""
        
        # Extract UBL document from content
        if isinstance(peppol_document.document_content, dict):
            xml_content = peppol_document.document_content.get('xml_content', '')
            if xml_content:
                # Clean and validate XML
                try:
                    # Parse to ensure valid XML
                    root = ET.fromstring(xml_content)
                    # Return cleaned XML
                    return ET.tostring(root, encoding='unicode')
                except ET.ParseError:
                    # If XML is invalid, create basic structure
                    return self._create_basic_document_structure(peppol_document)
            else:
                return self._create_basic_document_structure(peppol_document)
        else:
            return str(peppol_document.document_content)
    
    def _create_basic_document_structure(self, peppol_document: PEPPOLDocument) -> str:
        """Create basic UBL document structure if none provided"""
        
        document_type_name = self._get_document_type_name(peppol_document.document_type)
        
        basic_structure = f"""<{document_type_name} xmlns="urn:oasis:names:specification:ubl:schema:xsd:{document_type_name}-2"
                         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>{peppol_document.customization_id}</cbc:CustomizationID>
    <cbc:ProfileID>{peppol_document.profile_id}</cbc:ProfileID>
    <cbc:ID>{peppol_document.document_id}</cbc:ID>
    <cbc:IssueDate>{peppol_document.document_date}</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>{peppol_document.currency_code}</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cbc:EndpointID schemeID="{peppol_document.sender_participant.scheme_id.value}">{peppol_document.sender_participant.participant_id}</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>{peppol_document.sender_participant.participant_name}</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cbc:EndpointID schemeID="{peppol_document.receiver_participant.scheme_id.value}">{peppol_document.receiver_participant.participant_id}</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>{peppol_document.receiver_participant.participant_name}</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <cac:LegalMonetaryTotal>
        <cbc:TaxExclusiveAmount currencyID="{peppol_document.currency_code}">{peppol_document.total_amount}</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="{peppol_document.currency_code}">{peppol_document.total_amount + peppol_document.tax_amount}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{peppol_document.currency_code}">{peppol_document.payable_amount}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</{document_type_name}>"""
        
        return basic_structure
    
    def parse_sbdh_envelope(self, sbdh_xml: str) -> Dict[str, Any]:
        """
        Parse SBDH envelope to extract routing and document information
        
        Args:
            sbdh_xml: SBDH-wrapped XML document
            
        Returns:
            Parsed SBDH information and document content
        """
        try:
            root = ET.fromstring(sbdh_xml)
            
            # Extract SBDH header information
            sbdh_info = {
                "header_version": None,
                "sender": {},
                "receiver": {},
                "document_identification": {},
                "business_scope": {},
                "document_content": None
            }
            
            # Parse header version
            version_elem = root.find(f'.//{{{self.standard_business_document_ns}}}HeaderVersion')
            if version_elem is not None:
                sbdh_info["header_version"] = version_elem.text
            
            # Parse sender information
            sender_elem = root.find(f'.//{{{self.standard_business_document_ns}}}Sender')
            if sender_elem is not None:
                identifier_elem = sender_elem.find(f'.//{{{self.standard_business_document_ns}}}Identifier')
                if identifier_elem is not None:
                    sbdh_info["sender"] = {
                        "identifier": identifier_elem.text,
                        "authority": identifier_elem.get('Authority', ''),
                    }
                
                contact_elem = sender_elem.find(f'.//{{{self.standard_business_document_ns}}}Contact')
                if contact_elem is not None:
                    sbdh_info["sender"]["name"] = contact_elem.text
            
            # Parse receiver information
            receiver_elem = root.find(f'.//{{{self.standard_business_document_ns}}}Receiver')
            if receiver_elem is not None:
                identifier_elem = receiver_elem.find(f'.//{{{self.standard_business_document_ns}}}Identifier')
                if identifier_elem is not None:
                    sbdh_info["receiver"] = {
                        "identifier": identifier_elem.text,
                        "authority": identifier_elem.get('Authority', ''),
                    }
                
                contact_elem = receiver_elem.find(f'.//{{{self.standard_business_document_ns}}}Contact')
                if contact_elem is not None:
                    sbdh_info["receiver"]["name"] = contact_elem.text
            
            # Parse document identification
            doc_id_elem = root.find(f'.//{{{self.standard_business_document_ns}}}DocumentIdentification')
            if doc_id_elem is not None:
                for child in doc_id_elem:
                    tag_name = child.tag.replace(f'{{{self.standard_business_document_ns}}}', '')
                    sbdh_info["document_identification"][tag_name.lower()] = child.text
            
            # Parse business scope
            business_scope_elem = root.find(f'.//{{{self.standard_business_document_ns}}}BusinessScope')
            if business_scope_elem is not None:
                scopes = []
                for scope_elem in business_scope_elem.findall(f'.//{{{self.standard_business_document_ns}}}Scope'):
                    scope_type_elem = scope_elem.find(f'.//{{{self.standard_business_document_ns}}}Type')
                    scope_instance_elem = scope_elem.find(f'.//{{{self.standard_business_document_ns}}}InstanceIdentifier')
                    
                    if scope_type_elem is not None and scope_instance_elem is not None:
                        scopes.append({
                            "type": scope_type_elem.text,
                            "instance_identifier": scope_instance_elem.text
                        })
                
                sbdh_info["business_scope"]["scopes"] = scopes
            
            # Extract document content (everything outside SBDH header)
            # Find all children that are not StandardBusinessDocumentHeader
            for child in root:
                if child.tag != f'{{{self.standard_business_document_ns}}}StandardBusinessDocumentHeader':
                    sbdh_info["document_content"] = ET.tostring(child, encoding='unicode')
                    break
            
            return sbdh_info
            
        except Exception as e:
            self.logger.error(f"SBDH parsing failed: {str(e)}")
            raise
    
    def validate_sbdh_compliance(self, sbdh_xml: str) -> Dict[str, Any]:
        """
        Validate SBDH envelope compliance with PEPPOL requirements
        
        Args:
            sbdh_xml: SBDH envelope to validate
            
        Returns:
            Validation results
        """
        try:
            validation_result = {
                "is_compliant": True,
                "compliance_score": 0.0,
                "passed_checks": [],
                "failed_checks": [],
                "warnings": [],
                "recommendations": []
            }
            
            total_checks = 0
            passed_checks = 0
            
            try:
                root = ET.fromstring(sbdh_xml)
                
                # Check 1: Valid XML structure
                total_checks += 1
                validation_result["passed_checks"].append("Valid XML structure")
                passed_checks += 1
                
                # Check 2: SBDH namespace
                total_checks += 1
                if root.tag == f'{{{self.standard_business_document_ns}}}StandardBusinessDocument':
                    validation_result["passed_checks"].append("Correct SBDH namespace")
                    passed_checks += 1
                else:
                    validation_result["failed_checks"].append("Incorrect SBDH root element")
                    validation_result["is_compliant"] = False
                
                # Check 3: Header version
                total_checks += 1
                version_elem = root.find(f'.//{{{self.standard_business_document_ns}}}HeaderVersion')
                if version_elem is not None and version_elem.text == self.sbdh_version:
                    validation_result["passed_checks"].append(f"Correct header version: {self.sbdh_version}")
                    passed_checks += 1
                else:
                    validation_result["failed_checks"].append("Missing or incorrect header version")
                    validation_result["warnings"].append(f"Expected version {self.sbdh_version}")
                
                # Check 4: Sender information
                total_checks += 1
                sender_elem = root.find(f'.//{{{self.standard_business_document_ns}}}Sender')
                if sender_elem is not None:
                    sender_id = sender_elem.find(f'.//{{{self.standard_business_document_ns}}}Identifier')
                    if sender_id is not None and sender_id.text:
                        validation_result["passed_checks"].append("Valid sender information")
                        passed_checks += 1
                    else:
                        validation_result["failed_checks"].append("Missing sender identifier")
                        validation_result["is_compliant"] = False
                else:
                    validation_result["failed_checks"].append("Missing sender information")
                    validation_result["is_compliant"] = False
                
                # Check 5: Receiver information
                total_checks += 1
                receiver_elem = root.find(f'.//{{{self.standard_business_document_ns}}}Receiver')
                if receiver_elem is not None:
                    receiver_id = receiver_elem.find(f'.//{{{self.standard_business_document_ns}}}Identifier')
                    if receiver_id is not None and receiver_id.text:
                        validation_result["passed_checks"].append("Valid receiver information")
                        passed_checks += 1
                    else:
                        validation_result["failed_checks"].append("Missing receiver identifier")
                        validation_result["is_compliant"] = False
                else:
                    validation_result["failed_checks"].append("Missing receiver information")
                    validation_result["is_compliant"] = False
                
                # Check 6: Document identification
                total_checks += 1
                doc_id_elem = root.find(f'.//{{{self.standard_business_document_ns}}}DocumentIdentification')
                if doc_id_elem is not None:
                    instance_id = doc_id_elem.find(f'.//{{{self.standard_business_document_ns}}}InstanceIdentifier')
                    if instance_id is not None and instance_id.text:
                        validation_result["passed_checks"].append("Valid document identification")
                        passed_checks += 1
                    else:
                        validation_result["failed_checks"].append("Missing document instance identifier")
                        validation_result["is_compliant"] = False
                else:
                    validation_result["failed_checks"].append("Missing document identification")
                    validation_result["is_compliant"] = False
                
                # Check 7: Business scope with PEPPOL identifiers
                total_checks += 1
                business_scope_elem = root.find(f'.//{{{self.standard_business_document_ns}}}BusinessScope')
                if business_scope_elem is not None:
                    scopes = business_scope_elem.findall(f'.//{{{self.standard_business_document_ns}}}Scope')
                    required_scopes = {'DOCUMENTID', 'PROCESSID'}
                    found_scopes = set()
                    
                    for scope in scopes:
                        scope_type = scope.find(f'.//{{{self.standard_business_document_ns}}}Type')
                        if scope_type is not None:
                            found_scopes.add(scope_type.text)
                    
                    if required_scopes.issubset(found_scopes):
                        validation_result["passed_checks"].append("Required PEPPOL business scopes present")
                        passed_checks += 1
                    else:
                        missing_scopes = required_scopes - found_scopes
                        validation_result["failed_checks"].append(f"Missing business scopes: {', '.join(missing_scopes)}")
                        validation_result["is_compliant"] = False
                else:
                    validation_result["failed_checks"].append("Missing business scope")
                    validation_result["is_compliant"] = False
                
                # Check 8: Document content present
                total_checks += 1
                has_content = False
                for child in root:
                    if child.tag != f'{{{self.standard_business_document_ns}}}StandardBusinessDocumentHeader':
                        has_content = True
                        break
                
                if has_content:
                    validation_result["passed_checks"].append("Document content present")
                    passed_checks += 1
                else:
                    validation_result["failed_checks"].append("No document content found")
                    validation_result["warnings"].append("SBDH envelope is empty")
                
            except ET.ParseError as e:
                validation_result["failed_checks"].append(f"XML parsing error: {str(e)}")
                validation_result["is_compliant"] = False
                total_checks += 1
            
            # Calculate compliance score
            validation_result["compliance_score"] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            # Generate recommendations
            if not validation_result["is_compliant"]:
                validation_result["recommendations"].append("Address all failed checks for PEPPOL compliance")
            
            if validation_result["warnings"]:
                validation_result["recommendations"].append("Review warnings for completeness")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"SBDH validation failed: {str(e)}")
            raise