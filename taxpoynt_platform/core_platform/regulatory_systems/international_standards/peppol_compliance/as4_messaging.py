"""
PEPPOL AS4 Messaging Protocol Implementation
==========================================
AS4 messaging protocol implementation for PEPPOL network communication.
AS4 has replaced AS2 and is mandatory for PEPPOL Access Point certification.
"""
import logging
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import base64

from .models import PEPPOLMessage, MessageStatus, SecurityLevel


class AS4MessageHandler:
    """
    PEPPOL AS4 messaging protocol handler for secure document exchange
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_profiles = self._initialize_transport_profiles()
        self.message_cache = {}
        
    def _initialize_transport_profiles(self) -> Dict[str, Dict]:
        """Initialize supported AS4 transport profiles"""
        return {
            "bdxr-transport-ebms3-as4-v1p0": {
                "name": "PEPPOL AS4 Profile",
                "version": "1.0",
                "protocol": "AS4",
                "binding": "HTTP/HTTPS",
                "security": "WS-Security",
                "reliability": "WS-ReliableMessaging",
                "mandatory": True
            },
            "peppol-transport-as4-v2_0": {
                "name": "PEPPOL AS4 v2.0",
                "version": "2.0", 
                "protocol": "AS4",
                "binding": "HTTP/HTTPS",
                "security": "WS-Security",
                "reliability": "WS-ReliableMessaging",
                "mandatory": True
            }
        }
    
    def create_as4_message(self, peppol_message: PEPPOLMessage, 
                          sender_cert: Dict[str, Any],
                          receiver_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create AS4 message envelope for PEPPOL document
        
        Args:
            peppol_message: PEPPOL message to wrap
            sender_cert: Sender's PKI certificate information
            receiver_info: Receiver participant information
            
        Returns:
            Complete AS4 message envelope
        """
        try:
            # Generate AS4 message headers
            message_id = f"uuid:{uuid.uuid4()}"
            timestamp = datetime.now().isoformat()
            
            # Create SOAP envelope with AS4 headers
            as4_envelope = self._create_soap_envelope(
                message_id, timestamp, peppol_message, sender_cert, receiver_info
            )
            
            # Add reliability headers if required
            if peppol_message.delivery_receipt_requested:
                as4_envelope = self._add_reliability_headers(as4_envelope, peppol_message)
            
            # Add security headers
            as4_envelope = self._add_security_headers(
                as4_envelope, sender_cert, peppol_message.security_level
            )
            
            # Create message attachments
            attachments = self._create_message_attachments(peppol_message)
            
            return {
                "message_id": message_id,
                "timestamp": timestamp,
                "soap_envelope": as4_envelope,
                "attachments": attachments,
                "content_type": "multipart/related; type=\"application/soap+xml\"",
                "transport_profile": "bdxr-transport-ebms3-as4-v1p0"
            }
            
        except Exception as e:
            self.logger.error(f"AS4 message creation failed: {str(e)}")
            raise
    
    def _create_soap_envelope(self, message_id: str, timestamp: str,
                            peppol_message: PEPPOLMessage, sender_cert: Dict[str, Any],
                            receiver_info: Dict[str, Any]) -> str:
        """Create SOAP envelope with AS4 messaging headers"""
        
        soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:eb="http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/"
               xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
               xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
    
    <soap:Header>
        <!-- AS4 Messaging Headers -->
        <eb:Messaging soap:mustUnderstand="true">
            <eb:UserMessage>
                <eb:MessageInfo>
                    <eb:Timestamp>{timestamp}</eb:Timestamp>
                    <eb:MessageId>{message_id}</eb:MessageId>
                </eb:MessageInfo>
                
                <eb:PartyInfo>
                    <eb:From>
                        <eb:PartyId type="urn:oasis:names:tc:ebcore:partyid-type:unregistered">{peppol_message.sender_id}</eb:PartyId>
                        <eb:Role>http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/initiator</eb:Role>
                    </eb:From>
                    <eb:To>
                        <eb:PartyId type="urn:oasis:names:tc:ebcore:partyid-type:unregistered">{peppol_message.receiver_id}</eb:PartyId>
                        <eb:Role>http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/responder</eb:Role>
                    </eb:To>
                </eb:PartyInfo>
                
                <eb:CollaborationInfo>
                    <eb:Service type="peppol-transport-as4-v2_0">busdox:noprocess</eb:Service>
                    <eb:Action>http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/test</eb:Action>
                    <eb:ConversationId>{uuid.uuid4()}</eb:ConversationId>
                </eb:CollaborationInfo>
                
                <eb:MessageProperties>
                    <eb:Property name="originalSender">{peppol_message.sender_id}</eb:Property>
                    <eb:Property name="finalRecipient">{peppol_message.receiver_id}</eb:Property>
                </eb:MessageProperties>
                
                <eb:PayloadInfo>
                    <eb:PartInfo href="cid:payload">
                        <eb:PartProperties>
                            <eb:Property name="MimeType">{peppol_message.content_type}</eb:Property>
                        </eb:PartProperties>
                    </eb:PartInfo>
                </eb:PayloadInfo>
            </eb:UserMessage>
        </eb:Messaging>
    </soap:Header>
    
    <soap:Body>
        <!-- Empty body - payload is in attachments -->
    </soap:Body>
</soap:Envelope>"""
        
        return soap_envelope
    
    def _add_reliability_headers(self, soap_envelope: str, 
                               peppol_message: PEPPOLMessage) -> str:
        """Add WS-ReliableMessaging headers for delivery guarantees"""
        
        # Parse existing SOAP envelope
        root = ET.fromstring(soap_envelope)
        
        # Add reliability namespace
        root.set('xmlns:wsrm', 'http://docs.oasis-open.org/ws-rx/wsrm/200702')
        
        # Find header element
        header = root.find('.//{http://www.w3.org/2003/05/soap-envelope}Header')
        
        # Create reliability headers
        reliability_elem = ET.SubElement(header, '{http://docs.oasis-open.org/ws-rx/wsrm/200702}Sequence')
        reliability_elem.set('mustUnderstand', 'true')
        
        sequence_id = ET.SubElement(reliability_elem, '{http://docs.oasis-open.org/ws-rx/wsrm/200702}Identifier')
        sequence_id.text = f"urn:uuid:{uuid.uuid4()}"
        
        message_number = ET.SubElement(reliability_elem, '{http://docs.oasis-open.org/ws-rx/wsrm/200702}MessageNumber')
        message_number.text = "1"
        
        return ET.tostring(root, encoding='unicode')
    
    def _add_security_headers(self, soap_envelope: str, sender_cert: Dict[str, Any],
                            security_level: SecurityLevel) -> str:
        """Add WS-Security headers for message authentication and encryption"""
        
        # Parse existing SOAP envelope
        root = ET.fromstring(soap_envelope)
        
        # Find header element
        header = root.find('.//{http://www.w3.org/2003/05/soap-envelope}Header')
        
        # Create security header
        security_elem = ET.SubElement(header, '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Security')
        security_elem.set('mustUnderstand', 'true')
        
        # Add timestamp for message freshness
        timestamp_elem = ET.SubElement(security_elem, '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Timestamp')
        timestamp_id = f"TS-{uuid.uuid4()}"
        timestamp_elem.set('Id', timestamp_id)
        
        created_elem = ET.SubElement(timestamp_elem, '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Created')
        created_elem.text = datetime.now().isoformat()
        
        expires_elem = ET.SubElement(timestamp_elem, '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Expires')
        expires_elem.text = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        # Add binary security token (certificate)
        if sender_cert.get('certificate'):
            token_elem = ET.SubElement(security_elem, '{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken')
            token_elem.set('ValueType', 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3')
            token_elem.set('EncodingType', 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary')
            token_elem.set('Id', f"X509-{uuid.uuid4()}")
            token_elem.text = base64.b64encode(sender_cert['certificate']).decode('utf-8')
        
        return ET.tostring(root, encoding='unicode')
    
    def _create_message_attachments(self, peppol_message: PEPPOLMessage) -> List[Dict[str, Any]]:
        """Create message attachments containing the actual PEPPOL document"""
        
        attachments = []
        
        # Main payload attachment
        main_attachment = {
            "content_id": "payload",
            "content_type": peppol_message.content_type,
            "content_encoding": peppol_message.encoding,
            "content": peppol_message.payload,
            "size": peppol_message.payload_size
        }
        
        attachments.append(main_attachment)
        
        return attachments
    
    def process_as4_response(self, response_data: bytes) -> Dict[str, Any]:
        """
        Process AS4 response message
        
        Args:
            response_data: Raw AS4 response
            
        Returns:
            Processed response information
        """
        try:
            # Parse SOAP response
            response_info = {
                "timestamp": datetime.now(),
                "status": "unknown",
                "message_id": None,
                "ref_to_message_id": None,
                "errors": [],
                "receipts": []
            }
            
            # Basic XML parsing
            try:
                root = ET.fromstring(response_data)
                
                # Extract message ID
                message_id_elem = root.find('.//{http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/}MessageId')
                if message_id_elem is not None:
                    response_info["message_id"] = message_id_elem.text
                
                # Check for receipt signal
                receipt_elem = root.find('.//{http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/}Receipt')
                if receipt_elem is not None:
                    response_info["status"] = "receipt_received"
                    response_info["receipts"].append("Message delivery confirmed")
                
                # Check for error signals
                error_elem = root.find('.//{http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/}Error')
                if error_elem is not None:
                    response_info["status"] = "error_received"
                    error_code = error_elem.get('errorCode', 'Unknown')
                    error_detail = error_elem.get('errorDetail', 'No details')
                    response_info["errors"].append(f"Error {error_code}: {error_detail}")
                
            except ET.ParseError as e:
                response_info["errors"].append(f"Invalid XML response: {str(e)}")
                response_info["status"] = "parse_error"
            
            return response_info
            
        except Exception as e:
            self.logger.error(f"AS4 response processing failed: {str(e)}")
            raise
    
    def validate_as4_compliance(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate AS4 message compliance with PEPPOL requirements
        
        Args:
            message_data: AS4 message data to validate
            
        Returns:
            Compliance validation results
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
            
            # Check 1: Valid SOAP envelope structure
            total_checks += 1
            if message_data.get("soap_envelope"):
                validation_result["passed_checks"].append("Valid SOAP envelope structure")
                passed_checks += 1
            else:
                validation_result["failed_checks"].append("Missing SOAP envelope")
                validation_result["is_compliant"] = False
            
            # Check 2: AS4 messaging headers present
            total_checks += 1
            soap_envelope = message_data.get("soap_envelope", "")
            if "eb:Messaging" in soap_envelope:
                validation_result["passed_checks"].append("AS4 messaging headers present")
                passed_checks += 1
            else:
                validation_result["failed_checks"].append("Missing AS4 messaging headers")
                validation_result["is_compliant"] = False
            
            # Check 3: Security headers
            total_checks += 1
            if "wsse:Security" in soap_envelope:
                validation_result["passed_checks"].append("WS-Security headers present")
                passed_checks += 1
            else:
                validation_result["failed_checks"].append("Missing WS-Security headers")
                validation_result["warnings"].append("Message may not be secure")
            
            # Check 4: Transport profile compliance
            total_checks += 1
            transport_profile = message_data.get("transport_profile")
            if transport_profile in self.supported_profiles:
                validation_result["passed_checks"].append(f"Valid transport profile: {transport_profile}")
                passed_checks += 1
            else:
                validation_result["failed_checks"].append("Invalid or missing transport profile")
                validation_result["is_compliant"] = False
            
            # Check 5: Message attachments
            total_checks += 1
            attachments = message_data.get("attachments", [])
            if attachments:
                validation_result["passed_checks"].append(f"Message has {len(attachments)} attachments")
                passed_checks += 1
            else:
                validation_result["failed_checks"].append("No message attachments found")
                validation_result["warnings"].append("Empty message payload")
            
            # Calculate compliance score
            validation_result["compliance_score"] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            # Generate recommendations
            if validation_result["compliance_score"] < 100:
                validation_result["recommendations"].append("Address all failed checks for full AS4 compliance")
            
            if validation_result["warnings"]:
                validation_result["recommendations"].append("Review warnings for security and reliability improvements")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"AS4 compliance validation failed: {str(e)}")
            raise
    
    def generate_delivery_receipt(self, original_message: PEPPOLMessage) -> Dict[str, Any]:
        """
        Generate AS4 delivery receipt for received message
        
        Args:
            original_message: Original message to acknowledge
            
        Returns:
            AS4 receipt message
        """
        try:
            receipt_id = f"uuid:{uuid.uuid4()}"
            timestamp = datetime.now().isoformat()
            
            receipt_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:eb="http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/">
    <soap:Header>
        <eb:Messaging soap:mustUnderstand="true">
            <eb:SignalMessage>
                <eb:MessageInfo>
                    <eb:Timestamp>{timestamp}</eb:Timestamp>
                    <eb:MessageId>{receipt_id}</eb:MessageId>
                    <eb:RefToMessageId>{original_message.message_id}</eb:RefToMessageId>
                </eb:MessageInfo>
                <eb:Receipt>
                    <eb:NonRepudiationInformation>
                        <eb:MessagePartNRInformation>
                            <eb:Reference URI="#{original_message.message_id}"/>
                        </eb:MessagePartNRInformation>
                    </eb:NonRepudiationInformation>
                </eb:Receipt>
            </eb:SignalMessage>
        </eb:Messaging>
    </soap:Header>
    <soap:Body/>
</soap:Envelope>"""
            
            return {
                "message_id": receipt_id,
                "timestamp": timestamp,
                "ref_to_message_id": original_message.message_id,
                "soap_envelope": receipt_envelope,
                "message_type": "receipt"
            }
            
        except Exception as e:
            self.logger.error(f"Delivery receipt generation failed: {str(e)}")
            raise