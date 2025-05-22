# TaxPoynt eInvoice Error Handling System

## Overview

The TaxPoynt eInvoice error handling system provides comprehensive management of failed FIRS submissions with automatic retries, detailed failure logging, and configurable alerts. This document outlines the components, configuration options, and usage of the error handling system.

## Components

### 1. Retry Mechanism with Exponential Backoff

The system implements a sophisticated retry mechanism for failed submissions:

- **Exponential Backoff**: Progressively increasing delays between retry attempts to prevent overwhelming the FIRS API
- **Configurable Parameters**: Customizable base delay, backoff factor, and jitter
- **Intelligent Error Classification**: Distinguishes between permanent errors (that shouldn't be retried) and retriable errors
- **Automatic Scheduling**: Background processing of pending retries based on their scheduled times

```python
# Key configuration parameters
MAX_RETRY_ATTEMPTS = 5
BASE_RETRY_DELAY = 60  # seconds
RETRY_BACKOFF_FACTOR = 2.0
RETRY_JITTER = 0.1  # Random jitter factor (0.0-1.0)
```

### 2. Comprehensive Failure Logging

Detailed tracking and logging of all submission failures:

- **Error Details**: Records error type, message, and stack traces
- **Structured Data**: Stores structured error details in JSON format for easy analysis
- **Severity Classification**: Categorizes failures by severity (low, medium, high, critical)
- **Complete History**: Tracks the entire history of retry attempts for each submission

Failure severity levels:
- **Low**: Minor issues, automatic retry should resolve
- **Medium**: Significant issues, may require attention
- **High**: Serious issues, requires immediate attention
- **Critical**: Critical failure, system operations affected

### 3. Alert System for Critical Failures

Configurable alerting system for critical submission failures:

- **Severity-Based Alerts**: Sends alerts based on configurable severity thresholds
- **Multiple Channels**: Support for email and Slack notifications
- **Comprehensive Information**: Includes all relevant error details in alerts
- **Duplicate Prevention**: Prevents sending multiple alerts for the same failure

Alert data includes:
- Event type
- Severity level
- Submission ID and IRN
- Error message and type
- Attempt information
- Timestamp
- Detailed error information

### 4. Management Interface

Administrative interface for monitoring and managing submission failures:

- **Failed Submissions List**: API endpoint to view and filter failed submissions
- **Detailed Error Information**: Complete error details for troubleshooting
- **Manual Retry Triggering**: Ability to manually trigger retries for failed submissions
- **Create New Retries**: Create retry attempts for submissions without active retries

### 5. Background Processing

Background task system for handling retries:

- **Periodic Scanning**: Regular scanning for pending retries
- **Automatic Processing**: Processing of due retries without manual intervention
- **Configurable Intervals**: Adjustable monitoring intervals through settings
- **Application Integration**: Integration with FastAPI's startup event system

## Configuration

The retry system can be configured through environment variables:

| Setting | Description | Default |
|---------|-------------|---------|
| `TAXPOYNT_MAX_RETRY_ATTEMPTS` | Maximum number of retry attempts | 5 |
| `TAXPOYNT_BASE_RETRY_DELAY` | Base delay in seconds | 60 |
| `TAXPOYNT_RETRY_BACKOFF_FACTOR` | Multiplier for exponential backoff | 2.0 |
| `TAXPOYNT_RETRY_JITTER` | Random jitter factor (0.0-1.0) | 0.1 |
| `TAXPOYNT_RETRY_PROCESSOR_INTERVAL` | Interval for checking pending retries (seconds) | 60 |
| `TAXPOYNT_ENABLE_FAILURE_ALERTS` | Enable failure alerting | True |
| `TAXPOYNT_EMAIL_ALERTS_ENABLED` | Enable email alerts | False |
| `TAXPOYNT_SLACK_ALERTS_ENABLED` | Enable Slack alerts | False |
| `TAXPOYNT_ALERT_EMAIL_RECIPIENTS` | List of email recipients | [] |
| `TAXPOYNT_SLACK_WEBHOOK_URL` | Slack webhook URL | None |

## API Endpoints

### Retry Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/retry-management/failed-submissions` | GET | List failed submissions with filtering options |
| `/api/v1/retry-management/retry/{retry_id}` | GET | Get detailed information about a specific retry attempt |
| `/api/v1/retry-management/retry/{retry_id}/trigger` | POST | Manually trigger a retry attempt |
| `/api/v1/retry-management/submission/{submission_id}/retry` | POST | Create a manual retry for a submission |

## Database Models

### SubmissionRetry

Key model for tracking retry attempts:

```python
class SubmissionRetry(Base):
    __tablename__ = "submission_retries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submission_records.id"), nullable=False, index=True)
    
    # Retry tracking
    attempt_number = Column(Integer, nullable=False, default=1)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    last_attempt_at = Column(DateTime, nullable=True)
    backoff_factor = Column(Float, nullable=False, default=2.0)
    base_delay = Column(Integer, nullable=False, default=60)
    jitter = Column(Float, nullable=False, default=0.1)
    
    # Status tracking
    status = Column(SQLEnum(RetryStatus), nullable=False, default=RetryStatus.PENDING)
    
    # Error details
    error_type = Column(String(100), nullable=True)
    error_message = Column(String(1000), nullable=True)
    error_details = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Alert information
    severity = Column(SQLEnum(FailureSeverity), nullable=False, default=FailureSeverity.MEDIUM)
    alert_sent = Column(Boolean, nullable=False, default=False)
```

## Error Classification

The system distinguishes between two types of errors:

1. **RetryableError**: Temporary errors that should be retried (network issues, timeouts, server errors)
2. **PermanentError**: Errors that should not be retried (validation errors, authentication failures, invalid data)

```python
class RetryableError(Exception):
    """Base exception for errors that can be retried."""
    # ...

class PermanentError(Exception):
    """Base exception for errors that should not be retried."""
    # ...
```

## Integration with FIRS Service

The error handling system extends the existing FIRS service:

- `submit_invoice_with_retry`: Enhanced version of the FIRS submission method with retry capabilities
- `check_submission_status_with_logging`: Enhanced status checking with detailed logging
- Background retry processing for failed submissions

## Alert Channels

The system supports multiple alert channels:

- **Email**: HTML-formatted email alerts with complete error details
- **Slack**: Formatted Slack messages with color-coding by severity level

Additional channels can be easily added by implementing new notification methods.

## Usage Examples

### Submitting an Invoice with Retry

```python
response = await submit_invoice_with_retry(
    db=db,
    invoice_data=invoice_data,
    submission_record=submission,
    retry_on_failure=True,
    max_attempts=5
)
```

### Manually Triggering a Retry

```python
# Using the API endpoint
POST /api/v1/retry-management/retry/{retry_id}/trigger

# Or programmatically
await process_submission_retry(db, retry.id)
```
