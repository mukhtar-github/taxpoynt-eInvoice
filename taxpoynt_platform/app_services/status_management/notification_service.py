"""
Notification Service for APP Role

This service sends notifications on status changes including:
- Multi-channel notification delivery (email, SMS, webhook, push)
- Notification templates and personalization
- Notification preferences and filtering
- Delivery tracking and retry mechanisms
- Real-time and batch notification processing
"""

import asyncio
import json
import smtplib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import uuid
import re
import aiohttp

from .status_tracker import SubmissionStatus, SubmissionRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    IN_APP = "in_app"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationType(Enum):
    """Types of notifications"""
    STATUS_CHANGE = "status_change"
    ERROR_ALERT = "error_alert"
    SUCCESS_CONFIRMATION = "success_confirmation"
    WARNING = "warning"
    REMINDER = "reminder"
    SUMMARY = "summary"
    SYSTEM_ALERT = "system_alert"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class DeliveryStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class NotificationTemplate:
    """Notification template structure"""
    template_id: str
    template_name: str
    notification_type: NotificationType
    channel: NotificationChannel
    subject_template: str
    body_template: str
    variables: List[str] = field(default_factory=list)
    is_html: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationPreference:
    """User notification preferences"""
    user_id: str
    organization_id: Optional[str] = None
    enabled_channels: Set[NotificationChannel] = field(default_factory=set)
    notification_types: Set[NotificationType] = field(default_factory=set)
    minimum_priority: NotificationPriority = NotificationPriority.NORMAL
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    frequency_limits: Dict[str, int] = field(default_factory=dict)  # type -> max per hour
    contact_info: Dict[str, str] = field(default_factory=dict)  # channel -> contact
    custom_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationRecipient:
    """Notification recipient information"""
    recipient_id: str
    recipient_type: str  # user, group, role
    channels: List[NotificationChannel]
    contact_info: Dict[str, str]  # channel -> contact details
    preferences: Optional[NotificationPreference] = None


@dataclass
class NotificationMessage:
    """Notification message structure"""
    message_id: str
    notification_type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority
    
    # Recipients
    recipients: List[NotificationRecipient]
    
    # Content
    subject: str
    body: str
    html_body: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Context
    submission_id: Optional[str] = None
    document_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    
    # Delivery
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    delivery_attempts: int = 0
    max_delivery_attempts: int = 3
    last_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Template and variables
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    tracking_id: Optional[str] = None
    delivery_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryResult:
    """Notification delivery result"""
    message_id: str
    recipient_id: str
    channel: NotificationChannel
    status: DeliveryStatus
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    response_data: Dict[str, Any] = field(default_factory=dict)
    delivery_time: float = 0.0
    retry_count: int = 0


@dataclass
class NotificationStats:
    """Notification statistics"""
    total_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_channel: Dict[str, int]
    notifications_by_priority: Dict[str, int]
    delivery_success_rate: float
    average_delivery_time: float
    failed_deliveries: int
    bounce_rate: float
    notifications_last_24h: int


class NotificationService:
    """
    Notification service for APP role
    
    Handles:
    - Multi-channel notification delivery
    - Notification templates and personalization
    - Notification preferences and filtering
    - Delivery tracking and retry mechanisms
    - Real-time and batch notification processing
    """
    
    def __init__(self,
                 smtp_config: Optional[Dict[str, Any]] = None,
                 sms_config: Optional[Dict[str, Any]] = None,
                 webhook_timeout: int = 30,
                 batch_size: int = 100,
                 retry_interval: int = 300):  # 5 minutes
        
        self.smtp_config = smtp_config or {}
        self.sms_config = sms_config or {}
        self.webhook_timeout = webhook_timeout
        self.batch_size = batch_size
        self.retry_interval = retry_interval
        
        # Storage
        self.messages: Dict[str, NotificationMessage] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.preferences: Dict[str, NotificationPreference] = {}
        self.delivery_queue: deque = deque()
        self.retry_queue: deque = deque()
        
        # Setup default templates
        self._setup_default_templates()
        
        # Channel handlers
        self.channel_handlers = {
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.SMS: self._send_sms,
            NotificationChannel.WEBHOOK: self._send_webhook,
            NotificationChannel.PUSH: self._send_push_notification,
            NotificationChannel.IN_APP: self._send_in_app,
            NotificationChannel.SLACK: self._send_slack,
            NotificationChannel.TEAMS: self._send_teams
        }
        
        # Background tasks
        self.delivery_task: Optional[asyncio.Task] = None
        self.retry_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
        
        # HTTP session for webhooks
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Metrics
        self.metrics = {
            'total_notifications': 0,
            'delivered_notifications': 0,
            'failed_notifications': 0,
            'bounced_notifications': 0,
            'notifications_by_type': defaultdict(int),
            'notifications_by_channel': defaultdict(int),
            'notifications_by_priority': defaultdict(int),
            'delivery_success_rate': 0.0,
            'average_delivery_time': 0.0,
            'channel_success_rates': defaultdict(float),
            'template_usage': defaultdict(int),
            'delivery_attempts': 0,
            'retry_attempts': 0
        }
    
    async def start(self):
        """Start notification service"""
        self.running = True
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        timeout = aiohttp.ClientTimeout(total=self.webhook_timeout)
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Start background tasks
        self.delivery_task = asyncio.create_task(self._process_delivery_queue())
        self.retry_task = asyncio.create_task(self._process_retry_queue())
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Notification service started")
    
    async def stop(self):
        """Stop notification service"""
        self.running = False
        
        # Cancel background tasks
        if self.delivery_task:
            self.delivery_task.cancel()
        if self.retry_task:
            self.retry_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Close HTTP session
        if self.http_session:
            await self.http_session.close()
        
        logger.info("Notification service stopped")
    
    async def send_notification(self,
                              notification_type: NotificationType,
                              recipients: List[NotificationRecipient],
                              subject: str,
                              body: str,
                              priority: NotificationPriority = NotificationPriority.NORMAL,
                              template_id: Optional[str] = None,
                              template_variables: Optional[Dict[str, Any]] = None,
                              submission_id: Optional[str] = None,
                              document_id: Optional[str] = None,
                              user_id: Optional[str] = None,
                              organization_id: Optional[str] = None,
                              scheduled_at: Optional[datetime] = None,
                              expires_at: Optional[datetime] = None) -> str:
        """
        Send notification to recipients
        
        Args:
            notification_type: Type of notification
            recipients: List of recipients
            subject: Notification subject
            body: Notification body
            priority: Notification priority
            template_id: Template to use
            template_variables: Variables for template
            submission_id: Related submission ID
            document_id: Related document ID
            user_id: Related user ID
            organization_id: Related organization ID
            scheduled_at: Schedule delivery time
            expires_at: Expiration time
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        
        # Apply preferences filtering
        filtered_recipients = await self._filter_recipients(
            recipients, notification_type, priority
        )
        
        if not filtered_recipients:
            logger.info(f"No recipients after filtering for notification {message_id}")
            return message_id
        
        # Create notification message
        message = NotificationMessage(
            message_id=message_id,
            notification_type=notification_type,
            channel=NotificationChannel.EMAIL,  # Will be determined per recipient
            priority=priority,
            recipients=filtered_recipients,
            subject=subject,
            body=body,
            submission_id=submission_id,
            document_id=document_id,
            user_id=user_id,
            organization_id=organization_id,
            scheduled_at=scheduled_at,
            expires_at=expires_at,
            template_id=template_id,
            template_variables=template_variables or {}
        )
        
        # Apply template if specified
        if template_id:
            await self._apply_template(message)
        
        # Store message
        self.messages[message_id] = message
        
        # Queue for delivery
        if scheduled_at and scheduled_at > datetime.utcnow():
            # Schedule for later
            message.delivery_status = DeliveryStatus.QUEUED
        else:
            # Queue for immediate delivery
            self.delivery_queue.append(message_id)
            message.delivery_status = DeliveryStatus.QUEUED
        
        # Update metrics
        self.metrics['total_notifications'] += 1
        self.metrics['notifications_by_type'][notification_type.value] += 1
        self.metrics['notifications_by_priority'][priority.value] += 1
        
        if template_id:
            self.metrics['template_usage'][template_id] += 1
        
        logger.info(f"Queued notification {message_id} for {len(filtered_recipients)} recipients")
        
        return message_id
    
    async def send_status_change_notification(self,
                                            submission: SubmissionRecord,
                                            old_status: Optional[SubmissionStatus],
                                            new_status: SubmissionStatus,
                                            recipients: List[NotificationRecipient]):
        """Send status change notification"""
        # Determine priority based on status
        priority = NotificationPriority.NORMAL
        if new_status in [SubmissionStatus.FAILED, SubmissionStatus.REJECTED]:
            priority = NotificationPriority.HIGH
        elif new_status == SubmissionStatus.ACCEPTED:
            priority = NotificationPriority.NORMAL
        
        # Create subject and body
        subject = f"Submission Status Update: {submission.document_id}"
        body = f"""
Your submission has been updated:

Document ID: {submission.document_id}
Submission ID: {submission.submission_id}
Previous Status: {old_status.value if old_status else 'N/A'}
New Status: {new_status.value}
Updated At: {submission.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Status Description: {self._get_status_description(new_status)}
        """.strip()
        
        # Template variables
        template_variables = {
            'document_id': submission.document_id,
            'submission_id': submission.submission_id,
            'old_status': old_status.value if old_status else 'N/A',
            'new_status': new_status.value,
            'updated_at': submission.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'status_description': self._get_status_description(new_status),
            'firs_reference': submission.firs_reference or 'N/A'
        }
        
        return await self.send_notification(
            notification_type=NotificationType.STATUS_CHANGE,
            recipients=recipients,
            subject=subject,
            body=body,
            priority=priority,
            template_id="status_change_email",
            template_variables=template_variables,
            submission_id=submission.submission_id,
            document_id=submission.document_id,
            user_id=submission.submitted_by,
            organization_id=submission.organization_id
        )
    
    async def _filter_recipients(self,
                               recipients: List[NotificationRecipient],
                               notification_type: NotificationType,
                               priority: NotificationPriority) -> List[NotificationRecipient]:
        """Filter recipients based on preferences"""
        filtered = []
        
        for recipient in recipients:
            # Check if recipient has preferences
            if recipient.preferences:
                prefs = recipient.preferences
                
                # Check if notification type is enabled
                if prefs.notification_types and notification_type not in prefs.notification_types:
                    continue
                
                # Check minimum priority
                priority_order = {
                    NotificationPriority.LOW: 1,
                    NotificationPriority.NORMAL: 2,
                    NotificationPriority.HIGH: 3,
                    NotificationPriority.URGENT: 4,
                    NotificationPriority.CRITICAL: 5
                }
                
                if priority_order[priority] < priority_order[prefs.minimum_priority]:
                    continue
                
                # Check quiet hours
                if self._is_quiet_hours(prefs):
                    # Only allow urgent and critical notifications during quiet hours
                    if priority not in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
                        continue
                
                # Check frequency limits
                if await self._exceeds_frequency_limit(recipient.recipient_id, notification_type, prefs):
                    continue
                
                # Filter channels based on preferences
                enabled_channels = prefs.enabled_channels
                if enabled_channels:
                    recipient.channels = [ch for ch in recipient.channels if ch in enabled_channels]
                
                if not recipient.channels:
                    continue
            
            filtered.append(recipient)
        
        return filtered
    
    def _is_quiet_hours(self, prefs: NotificationPreference) -> bool:
        """Check if current time is within quiet hours"""
        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False
        
        now = datetime.utcnow().time()
        start_time = datetime.strptime(prefs.quiet_hours_start, '%H:%M').time()
        end_time = datetime.strptime(prefs.quiet_hours_end, '%H:%M').time()
        
        if start_time <= end_time:
            # Same day quiet hours
            return start_time <= now <= end_time
        else:
            # Quiet hours span midnight
            return now >= start_time or now <= end_time
    
    async def _exceeds_frequency_limit(self,
                                     recipient_id: str,
                                     notification_type: NotificationType,
                                     prefs: NotificationPreference) -> bool:
        """Check if recipient exceeds frequency limit"""
        if notification_type.value not in prefs.frequency_limits:
            return False
        
        limit = prefs.frequency_limits[notification_type.value]
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        # Count notifications to this recipient in the last hour
        count = sum(1 for message in self.messages.values()
                   if (message.created_at > cutoff_time and
                       message.notification_type == notification_type and
                       any(r.recipient_id == recipient_id for r in message.recipients)))
        
        return count >= limit
    
    async def _apply_template(self, message: NotificationMessage):
        """Apply template to message"""
        if not message.template_id or message.template_id not in self.templates:
            return
        
        template = self.templates[message.template_id]
        variables = message.template_variables
        
        # Apply template to subject
        message.subject = self._render_template(template.subject_template, variables)
        
        # Apply template to body
        message.body = self._render_template(template.body_template, variables)
        
        # Set HTML body if template is HTML
        if template.is_html:
            message.html_body = message.body
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        result = template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def _get_status_description(self, status: SubmissionStatus) -> str:
        """Get human-readable status description"""
        descriptions = {
            SubmissionStatus.PENDING: "Your submission is pending processing",
            SubmissionStatus.VALIDATING: "Your submission is being validated",
            SubmissionStatus.VALIDATED: "Your submission has been validated successfully",
            SubmissionStatus.QUEUED: "Your submission is queued for transmission",
            SubmissionStatus.TRANSMITTING: "Your submission is being transmitted to FIRS",
            SubmissionStatus.TRANSMITTED: "Your submission has been transmitted to FIRS",
            SubmissionStatus.PROCESSING: "FIRS is processing your submission",
            SubmissionStatus.ACKNOWLEDGED: "FIRS has acknowledged your submission",
            SubmissionStatus.ACCEPTED: "Your submission has been accepted by FIRS",
            SubmissionStatus.REJECTED: "Your submission has been rejected by FIRS",
            SubmissionStatus.FAILED: "Your submission has failed processing",
            SubmissionStatus.TIMEOUT: "Your submission has timed out",
            SubmissionStatus.CANCELLED: "Your submission has been cancelled",
            SubmissionStatus.RETRY: "Your submission is being retried"
        }
        
        return descriptions.get(status, "Status update")
    
    async def _process_delivery_queue(self):
        """Process notification delivery queue"""
        while self.running:
            try:
                # Process scheduled notifications first
                await self._process_scheduled_notifications()
                
                # Process immediate delivery queue
                batch = []
                while len(batch) < self.batch_size and self.delivery_queue:
                    message_id = self.delivery_queue.popleft()
                    if message_id in self.messages:
                        batch.append(message_id)
                
                # Deliver batch
                if batch:
                    await self._deliver_batch(batch)
                
                await asyncio.sleep(1)  # Small delay between batches
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing delivery queue: {e}")
                await asyncio.sleep(5)
    
    async def _process_scheduled_notifications(self):
        """Process scheduled notifications"""
        current_time = datetime.utcnow()
        
        scheduled_messages = []
        for message_id, message in self.messages.items():
            if (message.delivery_status == DeliveryStatus.QUEUED and
                message.scheduled_at and
                message.scheduled_at <= current_time):
                scheduled_messages.append(message_id)
        
        for message_id in scheduled_messages:
            self.delivery_queue.append(message_id)
    
    async def _deliver_batch(self, message_ids: List[str]):
        """Deliver batch of notifications"""
        delivery_tasks = []
        
        for message_id in message_ids:
            message = self.messages[message_id]
            message.delivery_status = DeliveryStatus.SENDING
            message.delivery_attempts += 1
            message.last_attempt_at = datetime.utcnow()
            
            # Create delivery task for each recipient and channel
            for recipient in message.recipients:
                for channel in recipient.channels:
                    task = asyncio.create_task(
                        self._deliver_to_recipient(message, recipient, channel)
                    )
                    delivery_tasks.append(task)
        
        # Wait for all deliveries to complete
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)
    
    async def _deliver_to_recipient(self,
                                  message: NotificationMessage,
                                  recipient: NotificationRecipient,
                                  channel: NotificationChannel):
        """Deliver notification to specific recipient via channel"""
        start_time = time.time()
        
        try:
            # Get channel handler
            handler = self.channel_handlers.get(channel)
            if not handler:
                raise ValueError(f"No handler for channel: {channel.value}")
            
            # Get contact info for channel
            contact_info = recipient.contact_info.get(channel.value)
            if not contact_info:
                raise ValueError(f"No contact info for channel: {channel.value}")
            
            # Deliver notification
            result = await handler(message, recipient, contact_info)
            
            delivery_time = time.time() - start_time
            
            # Record successful delivery
            delivery_result = DeliveryResult(
                message_id=message.message_id,
                recipient_id=recipient.recipient_id,
                channel=channel,
                status=DeliveryStatus.DELIVERED,
                delivered_at=datetime.utcnow(),
                delivery_time=delivery_time,
                response_data=result
            )
            
            message.delivery_results.append(delivery_result.__dict__)
            
            # Update metrics
            self.metrics['delivered_notifications'] += 1
            self.metrics['notifications_by_channel'][channel.value] += 1
            self._update_delivery_metrics(delivery_time, True, channel)
            
            logger.info(f"Delivered notification {message.message_id} to {recipient.recipient_id} via {channel.value}")
            
        except Exception as e:
            delivery_time = time.time() - start_time
            
            # Record failed delivery
            delivery_result = DeliveryResult(
                message_id=message.message_id,
                recipient_id=recipient.recipient_id,
                channel=channel,
                status=DeliveryStatus.FAILED,
                error_message=str(e),
                delivery_time=delivery_time
            )
            
            message.delivery_results.append(delivery_result.__dict__)
            
            # Update metrics
            self.metrics['failed_notifications'] += 1
            self._update_delivery_metrics(delivery_time, False, channel)
            
            logger.error(f"Failed to deliver notification {message.message_id} to {recipient.recipient_id} via {channel.value}: {e}")
            
            # Queue for retry if not exceeded max attempts
            if message.delivery_attempts < message.max_delivery_attempts:
                self.retry_queue.append((message.message_id, recipient.recipient_id, channel))
    
    async def _send_email(self,
                        message: NotificationMessage,
                        recipient: NotificationRecipient,
                        email_address: str) -> Dict[str, Any]:
        """Send email notification"""
        if not self.smtp_config:
            raise ValueError("SMTP configuration not provided")
        
        # Create email message
        msg = MimeMultipart('alternative')
        msg['Subject'] = message.subject
        msg['From'] = self.smtp_config.get('from_email', 'noreply@taxpoynt.com')
        msg['To'] = email_address
        
        # Add text part
        text_part = MimeText(message.body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if available
        if message.html_body:
            html_part = MimeText(message.html_body, 'html')
            msg.attach(html_part)
        
        # Send email
        smtp_server = smtplib.SMTP(
            self.smtp_config['host'],
            self.smtp_config.get('port', 587)
        )
        
        if self.smtp_config.get('use_tls', True):
            smtp_server.starttls()
        
        if 'username' in self.smtp_config:
            smtp_server.login(
                self.smtp_config['username'],
                self.smtp_config['password']
            )
        
        smtp_server.send_message(msg)
        smtp_server.quit()
        
        return {'email_sent': True, 'recipient': email_address}
    
    async def _send_sms(self,
                      message: NotificationMessage,
                      recipient: NotificationRecipient,
                      phone_number: str) -> Dict[str, Any]:
        """Send SMS notification"""
        # This would integrate with SMS service provider
        # For now, just log the SMS
        logger.info(f"SMS to {phone_number}: {message.subject} - {message.body}")
        
        return {'sms_sent': True, 'recipient': phone_number}
    
    async def _send_webhook(self,
                          message: NotificationMessage,
                          recipient: NotificationRecipient,
                          webhook_url: str) -> Dict[str, Any]:
        """Send webhook notification"""
        if not self.http_session:
            raise ValueError("HTTP session not initialized")
        
        # Prepare webhook payload
        payload = {
            'message_id': message.message_id,
            'notification_type': message.notification_type.value,
            'priority': message.priority.value,
            'subject': message.subject,
            'body': message.body,
            'submission_id': message.submission_id,
            'document_id': message.document_id,
            'user_id': message.user_id,
            'organization_id': message.organization_id,
            'created_at': message.created_at.isoformat(),
            'recipient_id': recipient.recipient_id
        }
        
        # Send webhook
        async with self.http_session.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        ) as response:
            response_data = await response.text()
            
            if response.status >= 400:
                raise ValueError(f"Webhook failed with status {response.status}: {response_data}")
            
            return {
                'webhook_sent': True,
                'status_code': response.status,
                'response': response_data
            }
    
    async def _send_push_notification(self,
                                    message: NotificationMessage,
                                    recipient: NotificationRecipient,
                                    device_token: str) -> Dict[str, Any]:
        """Send push notification"""
        # This would integrate with push notification service (FCM, APNs)
        # For now, just log the push notification
        logger.info(f"Push notification to {device_token}: {message.subject}")
        
        return {'push_sent': True, 'device_token': device_token}
    
    async def _send_in_app(self,
                         message: NotificationMessage,
                         recipient: NotificationRecipient,
                         user_id: str) -> Dict[str, Any]:
        """Send in-app notification"""
        # This would store notification in database for in-app display
        # For now, just log the in-app notification
        logger.info(f"In-app notification for user {user_id}: {message.subject}")
        
        return {'in_app_sent': True, 'user_id': user_id}
    
    async def _send_slack(self,
                        message: NotificationMessage,
                        recipient: NotificationRecipient,
                        slack_webhook: str) -> Dict[str, Any]:
        """Send Slack notification"""
        if not self.http_session:
            raise ValueError("HTTP session not initialized")
        
        # Prepare Slack payload
        payload = {
            'text': message.subject,
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f"*{message.subject}*\n{message.body}"
                    }
                }
            ]
        }
        
        async with self.http_session.post(slack_webhook, json=payload) as response:
            if response.status >= 400:
                response_text = await response.text()
                raise ValueError(f"Slack webhook failed: {response_text}")
            
            return {'slack_sent': True}
    
    async def _send_teams(self,
                        message: NotificationMessage,
                        recipient: NotificationRecipient,
                        teams_webhook: str) -> Dict[str, Any]:
        """Send Microsoft Teams notification"""
        if not self.http_session:
            raise ValueError("HTTP session not initialized")
        
        # Prepare Teams payload
        payload = {
            '@type': 'MessageCard',
            '@context': 'http://schema.org/extensions',
            'themeColor': '0076D7',
            'summary': message.subject,
            'sections': [
                {
                    'activityTitle': message.subject,
                    'activityText': message.body,
                    'facts': [
                        {'name': 'Type', 'value': message.notification_type.value},
                        {'name': 'Priority', 'value': message.priority.value},
                        {'name': 'Time', 'value': message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
                    ]
                }
            ]
        }
        
        async with self.http_session.post(teams_webhook, json=payload) as response:
            if response.status >= 400:
                response_text = await response.text()
                raise ValueError(f"Teams webhook failed: {response_text}")
            
            return {'teams_sent': True}
    
    def _update_delivery_metrics(self, delivery_time: float, success: bool, channel: NotificationChannel):
        """Update delivery metrics"""
        self.metrics['delivery_attempts'] += 1
        
        # Update average delivery time
        current_avg = self.metrics['average_delivery_time']
        total_attempts = self.metrics['delivery_attempts']
        self.metrics['average_delivery_time'] = (
            (current_avg * (total_attempts - 1) + delivery_time) / total_attempts
        )
        
        # Update channel success rate
        channel_key = channel.value
        current_rate = self.metrics['channel_success_rates'][channel_key]
        
        # Simple moving average for success rate
        if success:
            self.metrics['channel_success_rates'][channel_key] = min(100.0, current_rate + 1.0)
        else:
            self.metrics['channel_success_rates'][channel_key] = max(0.0, current_rate - 1.0)
        
        # Update overall success rate
        total_notifications = self.metrics['total_notifications']
        delivered = self.metrics['delivered_notifications']
        self.metrics['delivery_success_rate'] = (delivered / total_notifications * 100) if total_notifications > 0 else 0
    
    async def _process_retry_queue(self):
        """Process notification retry queue"""
        while self.running:
            try:
                if self.retry_queue:
                    retry_batch = []
                    
                    # Get retry batch
                    while len(retry_batch) < self.batch_size and self.retry_queue:
                        retry_batch.append(self.retry_queue.popleft())
                    
                    # Process retries
                    for message_id, recipient_id, channel in retry_batch:
                        if message_id in self.messages:
                            message = self.messages[message_id]
                            recipient = next((r for r in message.recipients if r.recipient_id == recipient_id), None)
                            
                            if recipient:
                                await self._deliver_to_recipient(message, recipient, channel)
                                self.metrics['retry_attempts'] += 1
                
                await asyncio.sleep(self.retry_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing retry queue: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old notifications"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=24)
                
                # Remove old delivered notifications
                old_messages = []
                for message_id, message in self.messages.items():
                    if (message.delivery_status == DeliveryStatus.DELIVERED and
                        message.delivered_at and
                        message.delivered_at < cutoff_time):
                        old_messages.append(message_id)
                
                for message_id in old_messages:
                    del self.messages[message_id]
                
                if old_messages:
                    logger.info(f"Cleaned up {len(old_messages)} old notifications")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def _setup_default_templates(self):
        """Setup default notification templates"""
        # Status change email template
        self.templates['status_change_email'] = NotificationTemplate(
            template_id='status_change_email',
            template_name='Status Change Email',
            notification_type=NotificationType.STATUS_CHANGE,
            channel=NotificationChannel.EMAIL,
            subject_template='Submission Status Update: {document_id}',
            body_template="""
Dear User,

Your submission has been updated:

Document ID: {document_id}
Submission ID: {submission_id}
Previous Status: {old_status}
New Status: {new_status}
Updated At: {updated_at}
FIRS Reference: {firs_reference}

{status_description}

Best regards,
TaxPoynt Team
            """.strip(),
            variables=['document_id', 'submission_id', 'old_status', 'new_status', 'updated_at', 'firs_reference', 'status_description']
        )
        
        # Error alert template
        self.templates['error_alert_email'] = NotificationTemplate(
            template_id='error_alert_email',
            template_name='Error Alert Email',
            notification_type=NotificationType.ERROR_ALERT,
            channel=NotificationChannel.EMAIL,
            subject_template='Error Alert: {document_id}',
            body_template="""
Dear User,

An error has occurred with your submission:

Document ID: {document_id}
Submission ID: {submission_id}
Error: {error_message}
Occurred At: {occurred_at}

Please review and resubmit if necessary.

Best regards,
TaxPoynt Team
            """.strip(),
            variables=['document_id', 'submission_id', 'error_message', 'occurred_at']
        )
    
    def add_template(self, template: NotificationTemplate):
        """Add notification template"""
        self.templates[template.template_id] = template
    
    def set_user_preferences(self, user_id: str, preferences: NotificationPreference):
        """Set user notification preferences"""
        self.preferences[user_id] = preferences
    
    def get_message(self, message_id: str) -> Optional[NotificationMessage]:
        """Get notification message by ID"""
        return self.messages.get(message_id)
    
    def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """Get delivery status of message"""
        message = self.messages.get(message_id)
        return message.delivery_status if message else None
    
    def get_statistics(self) -> NotificationStats:
        """Get notification statistics"""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=24)
        
        notifications_24h = sum(1 for message in self.messages.values()
                               if message.created_at > cutoff_time)
        
        return NotificationStats(
            total_notifications=self.metrics['total_notifications'],
            notifications_by_type=dict(self.metrics['notifications_by_type']),
            notifications_by_channel=dict(self.metrics['notifications_by_channel']),
            notifications_by_priority=dict(self.metrics['notifications_by_priority']),
            delivery_success_rate=self.metrics['delivery_success_rate'],
            average_delivery_time=self.metrics['average_delivery_time'],
            failed_deliveries=self.metrics['failed_notifications'],
            bounce_rate=0.0,  # Would be calculated from bounced notifications
            notifications_last_24h=notifications_24h
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get notification service metrics"""
        return {
            **self.metrics,
            'active_messages': len(self.messages),
            'templates': len(self.templates),
            'user_preferences': len(self.preferences),
            'delivery_queue_size': len(self.delivery_queue),
            'retry_queue_size': len(self.retry_queue)
        }


# Factory functions for easy setup
def create_notification_service(smtp_config: Optional[Dict[str, Any]] = None,
                              sms_config: Optional[Dict[str, Any]] = None) -> NotificationService:
    """Create notification service instance"""
    return NotificationService(smtp_config=smtp_config, sms_config=sms_config)


def create_notification_recipient(recipient_id: str,
                                recipient_type: str,
                                channels: List[NotificationChannel],
                                contact_info: Dict[str, str],
                                **kwargs) -> NotificationRecipient:
    """Create notification recipient"""
    return NotificationRecipient(
        recipient_id=recipient_id,
        recipient_type=recipient_type,
        channels=channels,
        contact_info=contact_info,
        **kwargs
    )


def create_notification_preferences(user_id: str,
                                  enabled_channels: Set[NotificationChannel],
                                  **kwargs) -> NotificationPreference:
    """Create notification preferences"""
    return NotificationPreference(
        user_id=user_id,
        enabled_channels=enabled_channels,
        **kwargs
    )


async def send_status_notification(submission: SubmissionRecord,
                                 old_status: Optional[SubmissionStatus],
                                 new_status: SubmissionStatus,
                                 recipients: List[NotificationRecipient],
                                 service: Optional[NotificationService] = None) -> str:
    """Send status change notification"""
    if not service:
        service = create_notification_service()
        await service.start()
    
    try:
        return await service.send_status_change_notification(
            submission, old_status, new_status, recipients
        )
    finally:
        if not service.running:
            await service.stop()


def get_notification_summary(service: NotificationService) -> Dict[str, Any]:
    """Get notification service summary"""
    metrics = service.get_metrics()
    stats = service.get_statistics()
    
    return {
        'total_notifications': stats.total_notifications,
        'delivery_success_rate': stats.delivery_success_rate,
        'failed_deliveries': stats.failed_deliveries,
        'average_delivery_time': stats.average_delivery_time,
        'notifications_last_24h': stats.notifications_last_24h,
        'active_messages': metrics['active_messages'],
        'templates': metrics['templates'],
        'user_preferences': metrics['user_preferences'],
        'channel_distribution': dict(stats.notifications_by_channel),
        'type_distribution': dict(stats.notifications_by_type)
    }