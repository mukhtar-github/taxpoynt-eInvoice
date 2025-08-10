"""
PEPPOL Message Level Response (MLR) Processor
============================================
Implementation of Message Level Response signaling for PEPPOL transport reliability.
MLR is mandatory for PEPPOL Access Point certification to ensure reliable message delivery.
"""
import logging
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

from .models import PEPPOLMessage, MessageStatus


class MLRSignalType(str, Enum):
    """MLR signal types"""
    RECEIPT = "Receipt"
    ERROR = "Error"
    PULL_REQUEST = "PullRequest"


class MLRErrorCode(str, Enum):
    """Standard MLR error codes"""
    VALUE_NOT_RECOGNIZED = "EBMS:0001"
    FEATURE_NOT_SUPPORTED = "EBMS:0002"
    VALUE_INCONSISTENT = "EBMS:0003"
    OTHER = "EBMS:0004"
    CONNECTION_FAILURE = "EBMS:0005"
    EMPTY_MESSAGE_PARTITION_CHANNEL = "EBMS:0006"
    MIME_INCONSISTENCY = "EBMS:0007"
    INVALID_HEADER = "EBMS:0008"
    UNKNOWN_ENDPOINT = "EBMS:0009"
    MESSAGE_TOO_LARGE = "EBMS:0010"
    EXTERNAL_PAYLOAD_ERROR = "EBMS:0011"
    INVALID_URI = "EBMS:0101"
    DELIVERY_FAILURE = "EBMS:0201"
    TIME_TO_LIVE_EXPIRED = "EBMS:0202"
    SECURITY_FAILURE = "EBMS:0301"
    AUTHORIZATION_FAILURE = "EBMS:0302"
    AUTHENTICATION_FAILURE = "EBMS:0303"


class MLRProcessor:
    """
    Message Level Response processor for PEPPOL reliable messaging
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mlr_namespace = "http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/"
        self.soap_namespace = "http://www.w3.org/2003/05/soap-envelope"
        self.pending_receipts = {}  # Track pending receipt requests
        
    def generate_receipt_signal(self, original_message: PEPPOLMessage,
                              non_repudiation_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate MLR receipt signal for successful message delivery
        
        Args:
            original_message: Original message to acknowledge
            non_repudiation_info: Non-repudiation information for security
            
        Returns:
            MLR receipt signal message
        """
        try:
            receipt_id = f"uuid:{uuid.uuid4()}"
            timestamp = datetime.now().isoformat()
            
            # Build receipt signal XML
            receipt_xml = self._build_receipt_signal_xml(
                receipt_id, timestamp, original_message, non_repudiation_info
            )
            
            # Create MLR response structure
            mlr_response = {
                "signal_type": MLRSignalType.RECEIPT,
                "message_id": receipt_id,
                "timestamp": timestamp,
                "ref_to_message_id": original_message.message_id,
                "from_party": original_message.receiver_id,
                "to_party": original_message.sender_id,
                "xml_content": receipt_xml,
                "content_type": "application/soap+xml",
                "status": "generated"
            }
            
            self.logger.info(f"Generated receipt signal {receipt_id} for message {original_message.message_id}")
            return mlr_response
            
        except Exception as e:
            self.logger.error(f"Receipt signal generation failed: {str(e)}")
            raise
    
    def _build_receipt_signal_xml(self, receipt_id: str, timestamp: str,
                                 original_message: PEPPOLMessage,
                                 non_repudiation_info: Optional[Dict[str, Any]]) -> str:
        """Build receipt signal XML structure"""
        
        # Build non-repudiation information if provided
        non_repudiation_xml = ""
        if non_repudiation_info:
            non_repudiation_xml = f"""
                <eb:NonRepudiationInformation>
                    <eb:MessagePartNRInformation>
                        <eb:Reference URI="#{original_message.message_id}"/>
                        <ds:Transforms xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                            <ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116">
                                <ds:XPath>//soap:Body</ds:XPath>
                            </ds:Transform>
                        </ds:Transforms>
                        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                        <ds:DigestValue>{non_repudiation_info.get('digest_value', '')}</ds:DigestValue>
                    </eb:MessagePartNRInformation>
                </eb:NonRepudiationInformation>"""
        
        receipt_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.soap_namespace}"
               xmlns:eb="{self.mlr_namespace}">
    <soap:Header>
        <eb:Messaging soap:mustUnderstand="true">
            <eb:SignalMessage>
                <eb:MessageInfo>
                    <eb:Timestamp>{timestamp}</eb:Timestamp>
                    <eb:MessageId>{receipt_id}</eb:MessageId>
                    <eb:RefToMessageId>{original_message.message_id}</eb:RefToMessageId>
                </eb:MessageInfo>
                <eb:Receipt>{non_repudiation_xml}
                </eb:Receipt>
            </eb:SignalMessage>
        </eb:Messaging>
    </soap:Header>
    <soap:Body/>
</soap:Envelope>"""
        
        return receipt_xml
    
    def generate_error_signal(self, original_message: Optional[PEPPOLMessage],
                            error_code: MLRErrorCode, error_detail: str,
                            severity: str = "failure") -> Dict[str, Any]:
        """
        Generate MLR error signal for message processing failures
        
        Args:
            original_message: Original message that caused error (if available)
            error_code: Standard MLR error code
            error_detail: Detailed error description
            severity: Error severity (failure, warning)
            
        Returns:
            MLR error signal message
        """
        try:
            error_id = f"uuid:{uuid.uuid4()}"
            timestamp = datetime.now().isoformat()
            
            # Build error signal XML
            error_xml = self._build_error_signal_xml(
                error_id, timestamp, original_message, error_code, error_detail, severity
            )
            
            # Create MLR error response structure
            mlr_response = {
                "signal_type": MLRSignalType.ERROR,
                "message_id": error_id,
                "timestamp": timestamp,
                "ref_to_message_id": original_message.message_id if original_message else None,
                "error_code": error_code.value,
                "error_detail": error_detail,
                "severity": severity,
                "xml_content": error_xml,
                "content_type": "application/soap+xml",
                "status": "generated"
            }
            
            self.logger.error(f"Generated error signal {error_id}: {error_code} - {error_detail}")
            return mlr_response
            
        except Exception as e:
            self.logger.error(f"Error signal generation failed: {str(e)}")
            raise
    
    def _build_error_signal_xml(self, error_id: str, timestamp: str,
                               original_message: Optional[PEPPOLMessage],
                               error_code: MLRErrorCode, error_detail: str,
                               severity: str) -> str:
        """Build error signal XML structure"""
        
        ref_to_message = original_message.message_id if original_message else ""
        
        error_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.soap_namespace}"
               xmlns:eb="{self.mlr_namespace}">
    <soap:Header>
        <eb:Messaging soap:mustUnderstand="true">
            <eb:SignalMessage>
                <eb:MessageInfo>
                    <eb:Timestamp>{timestamp}</eb:Timestamp>
                    <eb:MessageId>{error_id}</eb:MessageId>
                    {f'<eb:RefToMessageId>{ref_to_message}</eb:RefToMessageId>' if ref_to_message else ''}
                </eb:MessageInfo>
                <eb:Error errorCode="{error_code.value}" 
                         severity="{severity}"
                         shortDescription="{error_code.name}"
                         category="Communication"
                         refToMessageInError="{ref_to_message}"
                         errorDetail="{error_detail}">
                    <eb:Description xml:lang="en">{error_detail}</eb:Description>
                    <eb:ErrorDetail>{error_detail}</eb:ErrorDetail>
                </eb:Error>
            </eb:SignalMessage>
        </eb:Messaging>
    </soap:Header>
    <soap:Body/>
</soap:Envelope>"""
        
        return error_xml
    
    def process_incoming_signal(self, signal_xml: str) -> Dict[str, Any]:
        """
        Process incoming MLR signal (receipt or error)
        
        Args:
            signal_xml: MLR signal XML content
            
        Returns:
            Processed signal information
        """
        try:
            signal_info = {
                "signal_type": None,
                "message_id": None,
                "ref_to_message_id": None,
                "timestamp": None,
                "processing_status": "unknown",
                "errors": [],
                "details": {}
            }
            
            # Parse XML
            try:
                root = ET.fromstring(signal_xml)
            except ET.ParseError as e:
                signal_info["errors"].append(f"Invalid XML: {str(e)}")
                signal_info["processing_status"] = "parse_error"
                return signal_info
            
            # Extract message info
            message_info = root.find(f'.//{{{self.mlr_namespace}}}MessageInfo')
            if message_info is not None:
                timestamp_elem = message_info.find(f'.//{{{self.mlr_namespace}}}Timestamp')
                if timestamp_elem is not None:
                    signal_info["timestamp"] = timestamp_elem.text
                
                message_id_elem = message_info.find(f'.//{{{self.mlr_namespace}}}MessageId')
                if message_id_elem is not None:
                    signal_info["message_id"] = message_id_elem.text
                
                ref_to_message_id_elem = message_info.find(f'.//{{{self.mlr_namespace}}}RefToMessageId')
                if ref_to_message_id_elem is not None:
                    signal_info["ref_to_message_id"] = ref_to_message_id_elem.text
            
            # Check for receipt signal
            receipt_elem = root.find(f'.//{{{self.mlr_namespace}}}Receipt')
            if receipt_elem is not None:
                signal_info["signal_type"] = MLRSignalType.RECEIPT
                signal_info["processing_status"] = "receipt_received"
                signal_info["details"]["receipt_info"] = "Message delivery confirmed"
                
                # Process non-repudiation information if present
                nr_info = receipt_elem.find(f'.//{{{self.mlr_namespace}}}NonRepudiationInformation')
                if nr_info is not None:
                    signal_info["details"]["non_repudiation"] = "Present"
            
            # Check for error signal
            error_elem = root.find(f'.//{{{self.mlr_namespace}}}Error')
            if error_elem is not None:
                signal_info["signal_type"] = MLRSignalType.ERROR
                signal_info["processing_status"] = "error_received"
                
                error_details = {
                    "error_code": error_elem.get('errorCode', ''),
                    "severity": error_elem.get('severity', ''),
                    "short_description": error_elem.get('shortDescription', ''),
                    "category": error_elem.get('category', ''),
                    "error_detail": error_elem.get('errorDetail', '')
                }
                
                # Extract error description
                desc_elem = error_elem.find(f'.//{{{self.mlr_namespace}}}Description')
                if desc_elem is not None:
                    error_details["description"] = desc_elem.text
                
                signal_info["details"]["error_info"] = error_details
                signal_info["errors"].append(f"Error {error_details['error_code']}: {error_details['description']}")
            
            # Update message status based on signal
            if signal_info["ref_to_message_id"]:
                self._update_message_status(signal_info)
            
            return signal_info
            
        except Exception as e:
            self.logger.error(f"MLR signal processing failed: {str(e)}")
            raise
    
    def _update_message_status(self, signal_info: Dict[str, Any]):
        """Update original message status based on received signal"""
        try:
            ref_message_id = signal_info["ref_to_message_id"]
            
            if signal_info["signal_type"] == MLRSignalType.RECEIPT:
                # Mark message as delivered
                self.logger.info(f"Message {ref_message_id} delivery confirmed by receipt")
                # Here you would update your message tracking system
                
            elif signal_info["signal_type"] == MLRSignalType.ERROR:
                # Mark message as failed
                error_info = signal_info["details"].get("error_info", {})
                self.logger.error(f"Message {ref_message_id} failed: {error_info.get('description', 'Unknown error')}")
                # Here you would update your message tracking system with error details
                
        except Exception as e:
            self.logger.error(f"Message status update failed: {str(e)}")
    
    def validate_mlr_compliance(self, signal_xml: str) -> Dict[str, Any]:
        """
        Validate MLR signal compliance with PEPPOL requirements
        
        Args:
            signal_xml: MLR signal to validate
            
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
            
            try:
                root = ET.fromstring(signal_xml)
                
                # Check 1: Valid XML structure
                total_checks += 1
                validation_result["passed_checks"].append("Valid XML structure")
                passed_checks += 1
                
                # Check 2: SOAP envelope structure
                total_checks += 1
                if root.tag == f'{{{self.soap_namespace}}}Envelope':
                    validation_result["passed_checks"].append("Valid SOAP envelope")
                    passed_checks += 1
                else:
                    validation_result["failed_checks"].append("Invalid SOAP envelope structure")
                    validation_result["is_compliant"] = False
                
                # Check 3: ebMS messaging header
                total_checks += 1
                messaging_elem = root.find(f'.//{{{self.mlr_namespace}}}Messaging')
                if messaging_elem is not None:
                    validation_result["passed_checks"].append("ebMS messaging header present")
                    passed_checks += 1
                else:
                    validation_result["failed_checks"].append("Missing ebMS messaging header")
                    validation_result["is_compliant"] = False
                
                # Check 4: Signal message structure
                total_checks += 1
                signal_elem = root.find(f'.//{{{self.mlr_namespace}}}SignalMessage')
                if signal_elem is not None:
                    validation_result["passed_checks"].append("Signal message structure present")
                    passed_checks += 1
                else:
                    validation_result["failed_checks"].append("Missing signal message structure")
                    validation_result["is_compliant"] = False
                
                # Check 5: Message identification
                total_checks += 1
                message_info = root.find(f'.//{{{self.mlr_namespace}}}MessageInfo')
                if message_info is not None:
                    message_id = message_info.find(f'.//{{{self.mlr_namespace}}}MessageId')
                    timestamp = message_info.find(f'.//{{{self.mlr_namespace}}}Timestamp')
                    
                    if message_id is not None and timestamp is not None:
                        validation_result["passed_checks"].append("Message identification complete")
                        passed_checks += 1
                    else:
                        validation_result["failed_checks"].append("Incomplete message identification")
                        validation_result["is_compliant"] = False
                else:
                    validation_result["failed_checks"].append("Missing message info")
                    validation_result["is_compliant"] = False
                
                # Check 6: Signal type (receipt or error)
                total_checks += 1
                receipt_elem = root.find(f'.//{{{self.mlr_namespace}}}Receipt')
                error_elem = root.find(f'.//{{{self.mlr_namespace}}}Error')
                
                if receipt_elem is not None or error_elem is not None:
                    signal_type = "Receipt" if receipt_elem is not None else "Error"
                    validation_result["passed_checks"].append(f"Valid signal type: {signal_type}")
                    passed_checks += 1
                else:
                    validation_result["failed_checks"].append("No valid signal type found")
                    validation_result["is_compliant"] = False
                
                # Check 7: Reference to original message (if applicable)
                ref_to_message = root.find(f'.//{{{self.mlr_namespace}}}RefToMessageId')
                if ref_to_message is not None and ref_to_message.text:
                    validation_result["passed_checks"].append("Reference to original message present")
                else:
                    validation_result["warnings"].append("No reference to original message")
                
            except ET.ParseError as e:
                validation_result["failed_checks"].append(f"XML parsing failed: {str(e)}")
                validation_result["is_compliant"] = False
                total_checks += 1
            
            # Calculate compliance score
            validation_result["compliance_score"] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            # Generate recommendations
            if not validation_result["is_compliant"]:
                validation_result["recommendations"].append("Address all failed checks for MLR compliance")
            
            if validation_result["warnings"]:
                validation_result["recommendations"].append("Review warnings for completeness")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"MLR compliance validation failed: {str(e)}")
            raise
    
    def track_message_delivery(self, message_id: str, timeout_minutes: int = 30) -> Dict[str, Any]:
        """
        Track message delivery status and manage timeout
        
        Args:
            message_id: Message ID to track
            timeout_minutes: Timeout in minutes for delivery confirmation
            
        Returns:
            Tracking information
        """
        try:
            tracking_info = {
                "message_id": message_id,
                "tracking_started": datetime.now().isoformat(),
                "timeout_at": (datetime.now() + timedelta(minutes=timeout_minutes)).isoformat(),
                "status": "pending",
                "receipts_received": [],
                "errors_received": []
            }
            
            # Store in pending receipts
            self.pending_receipts[message_id] = tracking_info
            
            self.logger.info(f"Started tracking message {message_id} with {timeout_minutes} minute timeout")
            return tracking_info
            
        except Exception as e:
            self.logger.error(f"Message delivery tracking failed: {str(e)}")
            raise
    
    def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get current delivery status for a message
        
        Args:
            message_id: Message ID to check
            
        Returns:
            Current delivery status
        """
        try:
            if message_id not in self.pending_receipts:
                return {
                    "message_id": message_id,
                    "status": "not_tracked",
                    "message": "Message is not being tracked"
                }
            
            tracking_info = self.pending_receipts[message_id]
            
            # Check for timeout
            timeout_time = datetime.fromisoformat(tracking_info["timeout_at"].replace('Z', ''))
            if datetime.now() > timeout_time and tracking_info["status"] == "pending":
                tracking_info["status"] = "timeout"
                tracking_info["timeout_occurred"] = datetime.now().isoformat()
            
            return tracking_info
            
        except Exception as e:
            self.logger.error(f"Delivery status check failed: {str(e)}")
            raise
    
    def cleanup_expired_tracking(self):
        """Clean up expired message tracking entries"""
        try:
            current_time = datetime.now()
            expired_messages = []
            
            for message_id, tracking_info in self.pending_receipts.items():
                timeout_time = datetime.fromisoformat(tracking_info["timeout_at"].replace('Z', ''))
                if current_time > timeout_time + timedelta(hours=24):  # Keep for 24 hours after timeout
                    expired_messages.append(message_id)
            
            for message_id in expired_messages:
                del self.pending_receipts[message_id]
                self.logger.info(f"Cleaned up expired tracking for message {message_id}")
            
        except Exception as e:
            self.logger.error(f"Tracking cleanup failed: {str(e)}")
    
    def generate_mlr_statistics(self) -> Dict[str, Any]:
        """
        Generate MLR processing statistics
        
        Returns:
            MLR statistics and metrics
        """
        try:
            stats = {
                "timestamp": datetime.now().isoformat(),
                "tracked_messages": len(self.pending_receipts),
                "status_breakdown": {
                    "pending": 0,
                    "delivered": 0,
                    "failed": 0,
                    "timeout": 0
                },
                "average_delivery_time": None,
                "error_summary": {}
            }
            
            delivery_times = []
            error_codes = {}
            
            for tracking_info in self.pending_receipts.values():
                status = tracking_info["status"]
                stats["status_breakdown"][status] = stats["status_breakdown"].get(status, 0) + 1
                
                # Calculate delivery time for completed messages
                if status in ["delivered", "failed"] and "completion_time" in tracking_info:
                    start_time = datetime.fromisoformat(tracking_info["tracking_started"])
                    completion_time = datetime.fromisoformat(tracking_info["completion_time"])
                    delivery_time = (completion_time - start_time).total_seconds()
                    delivery_times.append(delivery_time)
                
                # Count error codes
                for error in tracking_info.get("errors_received", []):
                    error_code = error.get("error_code", "unknown")
                    error_codes[error_code] = error_codes.get(error_code, 0) + 1
            
            # Calculate average delivery time
            if delivery_times:
                stats["average_delivery_time"] = sum(delivery_times) / len(delivery_times)
            
            stats["error_summary"] = error_codes
            
            return stats
            
        except Exception as e:
            self.logger.error(f"MLR statistics generation failed: {str(e)}")
            raise