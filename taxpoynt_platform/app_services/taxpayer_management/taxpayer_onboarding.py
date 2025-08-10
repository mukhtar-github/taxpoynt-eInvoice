"""
APP Service: Taxpayer Onboarding
Manages taxpayer onboarding process to meet FIRS KPI requirements
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, Counter


class OnboardingStatus(str, Enum):
    """Taxpayer onboarding status"""
    INITIATED = "initiated"
    DOCUMENTATION_PENDING = "documentation_pending"
    VERIFICATION_IN_PROGRESS = "verification_in_progress"
    TESTING_PHASE = "testing_phase"
    APPROVED = "approved"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class TaxpayerType(str, Enum):
    """Types of taxpayers"""
    LARGE_TAXPAYER = "large_taxpayer"
    MEDIUM_TAXPAYER = "medium_taxpayer"
    SMALL_TAXPAYER = "small_taxpayer"
    MICRO_TAXPAYER = "micro_taxpayer"
    GOVERNMENT_ENTITY = "government_entity"
    NON_PROFIT = "non_profit"
    FOREIGN_ENTITY = "foreign_entity"


class OnboardingStep(str, Enum):
    """Onboarding process steps"""
    INITIAL_APPLICATION = "initial_application"
    DOCUMENT_SUBMISSION = "document_submission"
    DOCUMENT_VERIFICATION = "document_verification"
    TECHNICAL_SETUP = "technical_setup"
    INTEGRATION_TESTING = "integration_testing"
    COMPLIANCE_VALIDATION = "compliance_validation"
    FINAL_APPROVAL = "final_approval"
    ACTIVATION = "activation"


@dataclass
class TaxpayerProfile:
    """Taxpayer profile information"""
    taxpayer_id: str
    tin: str
    business_name: str
    business_registration_number: str
    taxpayer_type: TaxpayerType
    sector: str
    contact_email: str
    contact_phone: str
    address: str
    state: str
    lga: str
    annual_turnover: Optional[float] = None
    employee_count: Optional[int] = None
    business_description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingApplication:
    """Taxpayer onboarding application"""
    application_id: str
    taxpayer_profile: TaxpayerProfile
    status: OnboardingStatus
    current_step: OnboardingStep
    submitted_at: datetime
    assigned_to: Optional[str] = None
    expected_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['submitted_at'] = self.submitted_at.isoformat()
        if self.expected_completion:
            data['expected_completion'] = self.expected_completion.isoformat()
        if self.actual_completion:
            data['actual_completion'] = self.actual_completion.isoformat()
        return data


@dataclass
class OnboardingDocument:
    """Document submitted during onboarding"""
    document_id: str
    application_id: str
    document_type: str
    filename: str
    file_path: str
    uploaded_at: datetime
    verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['uploaded_at'] = self.uploaded_at.isoformat()
        if self.verified_at:
            data['verified_at'] = self.verified_at.isoformat()
        return data


@dataclass
class OnboardingTask:
    """Individual task in the onboarding process"""
    task_id: str
    application_id: str
    step: OnboardingStep
    title: str
    description: str
    assigned_to: str
    due_date: datetime
    status: str
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['due_date'] = self.due_date.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class OnboardingWorkflow:
    """Defines the standard onboarding workflow"""
    
    @staticmethod
    def get_workflow_steps() -> List[Dict[str, Any]]:
        """Get standard onboarding workflow steps"""
        return [
            {
                'step': OnboardingStep.INITIAL_APPLICATION,
                'title': 'Initial Application',
                'description': 'Submit initial application with business details',
                'duration_days': 1,
                'required_documents': ['business_registration', 'tax_certificate'],
                'automated': False
            },
            {
                'step': OnboardingStep.DOCUMENT_SUBMISSION,
                'title': 'Document Submission',
                'description': 'Upload all required documents',
                'duration_days': 3,
                'required_documents': ['cac_certificate', 'tin_certificate', 'bank_statement'],
                'automated': False
            },
            {
                'step': OnboardingStep.DOCUMENT_VERIFICATION,
                'title': 'Document Verification',
                'description': 'Verify submitted documents',
                'duration_days': 5,
                'required_documents': [],
                'automated': False
            },
            {
                'step': OnboardingStep.TECHNICAL_SETUP,
                'title': 'Technical Setup',
                'description': 'Configure technical integration',
                'duration_days': 2,
                'required_documents': ['technical_specification'],
                'automated': True
            },
            {
                'step': OnboardingStep.INTEGRATION_TESTING,
                'title': 'Integration Testing',
                'description': 'Test integration with taxpayer systems',
                'duration_days': 7,
                'required_documents': [],
                'automated': True
            },
            {
                'step': OnboardingStep.COMPLIANCE_VALIDATION,
                'title': 'Compliance Validation',
                'description': 'Validate compliance with FIRS requirements',
                'duration_days': 3,
                'required_documents': [],
                'automated': True
            },
            {
                'step': OnboardingStep.FINAL_APPROVAL,
                'title': 'Final Approval',
                'description': 'Final approval and activation',
                'duration_days': 1,
                'required_documents': [],
                'automated': False
            },
            {
                'step': OnboardingStep.ACTIVATION,
                'title': 'Activation',
                'description': 'Activate taxpayer account',
                'duration_days': 1,
                'required_documents': [],
                'automated': True
            }
        ]
    
    @staticmethod
    def calculate_expected_completion(start_date: datetime) -> datetime:
        """Calculate expected completion date based on workflow"""
        workflow_steps = OnboardingWorkflow.get_workflow_steps()
        total_days = sum(step['duration_days'] for step in workflow_steps)
        return start_date + timedelta(days=total_days)
    
    @staticmethod
    def get_required_documents(step: OnboardingStep) -> List[str]:
        """Get required documents for a specific step"""
        workflow_steps = OnboardingWorkflow.get_workflow_steps()
        for workflow_step in workflow_steps:
            if workflow_step['step'] == step:
                return workflow_step['required_documents']
        return []


class TaxpayerOnboardingService:
    """
    Comprehensive taxpayer onboarding service
    Manages the complete onboarding process to meet FIRS KPI requirements
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage (in production, use database)
        self.applications: Dict[str, OnboardingApplication] = {}
        self.documents: Dict[str, List[OnboardingDocument]] = defaultdict(list)
        self.tasks: Dict[str, List[OnboardingTask]] = defaultdict(list)
        
        # Onboarding statistics
        self.stats = {
            'total_applications': 0,
            'approved_taxpayers': 0,
            'rejected_applications': 0,
            'active_taxpayers': 0,
            'pending_applications': 0,
            'average_onboarding_time': 0.0,
            'monthly_onboarding_count': defaultdict(int),
            'taxpayer_type_distribution': Counter(),
            'sector_distribution': Counter(),
            'last_update': None
        }
        
        # KPI targets
        self.kpi_targets = {
            'taxpayers_per_6_months': 100,
            'max_onboarding_time_days': 30,
            'approval_rate_threshold': 85.0,
            'document_verification_time_days': 5
        }
    
    async def submit_application(self, taxpayer_profile: TaxpayerProfile) -> str:
        """
        Submit new taxpayer onboarding application
        
        Args:
            taxpayer_profile: Taxpayer profile information
            
        Returns:
            Application ID
        """
        try:
            # Generate application ID
            application_id = f"APP_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
            
            # Create application
            application = OnboardingApplication(
                application_id=application_id,
                taxpayer_profile=taxpayer_profile,
                status=OnboardingStatus.INITIATED,
                current_step=OnboardingStep.INITIAL_APPLICATION,
                submitted_at=datetime.now(timezone.utc),
                expected_completion=OnboardingWorkflow.calculate_expected_completion(
                    datetime.now(timezone.utc)
                )
            )
            
            # Store application
            self.applications[application_id] = application
            
            # Create initial tasks
            await self._create_initial_tasks(application_id)
            
            # Update statistics
            self.stats['total_applications'] += 1
            self.stats['pending_applications'] += 1
            self.stats['taxpayer_type_distribution'][taxpayer_profile.taxpayer_type.value] += 1
            self.stats['sector_distribution'][taxpayer_profile.sector] += 1
            
            # Track monthly onboarding
            month_key = datetime.now(timezone.utc).strftime('%Y-%m')
            self.stats['monthly_onboarding_count'][month_key] += 1
            
            self.logger.info(f"New taxpayer application submitted: {application_id}")
            
            return application_id
            
        except Exception as e:
            self.logger.error(f"Error submitting application: {str(e)}")
            raise
    
    async def _create_initial_tasks(self, application_id: str):
        """Create initial onboarding tasks"""
        workflow_steps = OnboardingWorkflow.get_workflow_steps()
        
        for step_info in workflow_steps:
            task = OnboardingTask(
                task_id=f"TASK_{application_id}_{step_info['step'].value}",
                application_id=application_id,
                step=step_info['step'],
                title=step_info['title'],
                description=step_info['description'],
                assigned_to='onboarding_team',
                due_date=datetime.now(timezone.utc) + timedelta(days=step_info['duration_days']),
                status='pending'
            )
            
            self.tasks[application_id].append(task)
    
    async def upload_document(self, 
                             application_id: str,
                             document_type: str,
                             filename: str,
                             file_path: str) -> str:
        """
        Upload document for onboarding application
        
        Args:
            application_id: Application ID
            document_type: Type of document
            filename: Original filename
            file_path: Path to uploaded file
            
        Returns:
            Document ID
        """
        try:
            if application_id not in self.applications:
                raise ValueError(f"Application not found: {application_id}")
            
            document_id = f"DOC_{application_id}_{uuid.uuid4().hex[:8].upper()}"
            
            document = OnboardingDocument(
                document_id=document_id,
                application_id=application_id,
                document_type=document_type,
                filename=filename,
                file_path=file_path,
                uploaded_at=datetime.now(timezone.utc)
            )
            
            self.documents[application_id].append(document)
            
            # Check if all required documents are uploaded
            await self._check_document_completeness(application_id)
            
            self.logger.info(f"Document uploaded: {document_id} for application {application_id}")
            
            return document_id
            
        except Exception as e:
            self.logger.error(f"Error uploading document: {str(e)}")
            raise
    
    async def _check_document_completeness(self, application_id: str):
        """Check if all required documents are uploaded"""
        application = self.applications[application_id]
        current_step = application.current_step
        
        required_docs = OnboardingWorkflow.get_required_documents(current_step)
        uploaded_docs = [doc.document_type for doc in self.documents[application_id]]
        
        if all(doc_type in uploaded_docs for doc_type in required_docs):
            # All documents uploaded, move to next step
            await self._advance_to_next_step(application_id)
    
    async def verify_document(self, 
                             document_id: str,
                             verified_by: str,
                             verification_notes: Optional[str] = None) -> bool:
        """
        Verify uploaded document
        
        Args:
            document_id: Document ID
            verified_by: Who verified the document
            verification_notes: Verification notes
            
        Returns:
            True if verification successful
        """
        try:
            # Find document
            document = None
            application_id = None
            
            for app_id, docs in self.documents.items():
                for doc in docs:
                    if doc.document_id == document_id:
                        document = doc
                        application_id = app_id
                        break
                if document:
                    break
            
            if not document:
                raise ValueError(f"Document not found: {document_id}")
            
            # Update verification status
            document.verified = True
            document.verified_at = datetime.now(timezone.utc)
            document.verified_by = verified_by
            document.verification_notes = verification_notes
            
            # Check if all documents for current step are verified
            await self._check_step_completion(application_id)
            
            self.logger.info(f"Document verified: {document_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying document: {str(e)}")
            raise
    
    async def _check_step_completion(self, application_id: str):
        """Check if current step is completed"""
        application = self.applications[application_id]
        current_step = application.current_step
        
        # Check if all tasks for current step are completed
        step_tasks = [task for task in self.tasks[application_id] if task.step == current_step]
        
        if all(task.status == 'completed' for task in step_tasks):
            await self._advance_to_next_step(application_id)
    
    async def _advance_to_next_step(self, application_id: str):
        """Advance application to next step"""
        application = self.applications[application_id]
        workflow_steps = OnboardingWorkflow.get_workflow_steps()
        
        # Find current step index
        current_index = None
        for i, step_info in enumerate(workflow_steps):
            if step_info['step'] == application.current_step:
                current_index = i
                break
        
        if current_index is None or current_index >= len(workflow_steps) - 1:
            # Final step reached
            await self._complete_onboarding(application_id)
            return
        
        # Move to next step
        next_step_info = workflow_steps[current_index + 1]
        application.current_step = next_step_info['step']
        
        # Update status based on step
        if next_step_info['step'] == OnboardingStep.DOCUMENT_VERIFICATION:
            application.status = OnboardingStatus.VERIFICATION_IN_PROGRESS
        elif next_step_info['step'] == OnboardingStep.INTEGRATION_TESTING:
            application.status = OnboardingStatus.TESTING_PHASE
        
        self.logger.info(f"Application {application_id} advanced to step: {next_step_info['step'].value}")
    
    async def _complete_onboarding(self, application_id: str):
        """Complete onboarding process"""
        application = self.applications[application_id]
        
        application.status = OnboardingStatus.ACTIVE
        application.actual_completion = datetime.now(timezone.utc)
        
        # Update statistics
        self.stats['approved_taxpayers'] += 1
        self.stats['active_taxpayers'] += 1
        self.stats['pending_applications'] -= 1
        
        # Calculate onboarding time
        onboarding_time = (application.actual_completion - application.submitted_at).days
        
        # Update average onboarding time
        current_avg = self.stats['average_onboarding_time']
        approved_count = self.stats['approved_taxpayers']
        self.stats['average_onboarding_time'] = (
            (current_avg * (approved_count - 1) + onboarding_time) / approved_count
        )
        
        self.logger.info(f"Onboarding completed for application: {application_id}")
    
    async def reject_application(self, application_id: str, reason: str):
        """Reject onboarding application"""
        if application_id not in self.applications:
            raise ValueError(f"Application not found: {application_id}")
        
        application = self.applications[application_id]
        application.status = OnboardingStatus.REJECTED
        application.rejection_reason = reason
        application.actual_completion = datetime.now(timezone.utc)
        
        # Update statistics
        self.stats['rejected_applications'] += 1
        self.stats['pending_applications'] -= 1
        
        self.logger.info(f"Application rejected: {application_id} - {reason}")
    
    async def get_application_status(self, application_id: str) -> Dict[str, Any]:
        """Get application status and details"""
        if application_id not in self.applications:
            raise ValueError(f"Application not found: {application_id}")
        
        application = self.applications[application_id]
        documents = self.documents[application_id]
        tasks = self.tasks[application_id]
        
        return {
            'application': application.to_dict(),
            'documents': [doc.to_dict() for doc in documents],
            'tasks': [task.to_dict() for task in tasks],
            'progress': self._calculate_progress(application_id)
        }
    
    def _calculate_progress(self, application_id: str) -> Dict[str, Any]:
        """Calculate onboarding progress"""
        application = self.applications[application_id]
        tasks = self.tasks[application_id]
        
        total_tasks = len(tasks)
        completed_tasks = len([task for task in tasks if task.status == 'completed'])
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'percentage': round(progress_percentage, 1),
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'current_step': application.current_step.value,
            'status': application.status.value,
            'days_since_submission': (datetime.now(timezone.utc) - application.submitted_at).days
        }
    
    async def get_onboarding_analytics(self) -> Dict[str, Any]:
        """Get comprehensive onboarding analytics"""
        now = datetime.now(timezone.utc)
        
        # Calculate KPI metrics
        six_months_ago = now - timedelta(days=180)
        recent_applications = [
            app for app in self.applications.values()
            if app.submitted_at >= six_months_ago
        ]
        
        taxpayers_last_6_months = len([
            app for app in recent_applications
            if app.status == OnboardingStatus.ACTIVE
        ])
        
        # Calculate approval rate
        total_completed = self.stats['approved_taxpayers'] + self.stats['rejected_applications']
        approval_rate = (
            (self.stats['approved_taxpayers'] / total_completed * 100) 
            if total_completed > 0 else 0
        )
        
        return {
            'timestamp': now.isoformat(),
            'kpi_metrics': {
                'taxpayers_onboarded_6_months': taxpayers_last_6_months,
                'kpi_target': self.kpi_targets['taxpayers_per_6_months'],
                'kpi_progress': (taxpayers_last_6_months / self.kpi_targets['taxpayers_per_6_months'] * 100),
                'approval_rate': round(approval_rate, 1),
                'average_onboarding_time': round(self.stats['average_onboarding_time'], 1)
            },
            'statistics': self.stats,
            'monthly_trends': dict(self.stats['monthly_onboarding_count']),
            'taxpayer_distribution': {
                'by_type': dict(self.stats['taxpayer_type_distribution']),
                'by_sector': dict(self.stats['sector_distribution'])
            }
        }
    
    async def get_pending_applications(self) -> List[Dict[str, Any]]:
        """Get list of pending applications requiring attention"""
        pending_apps = []
        
        for app in self.applications.values():
            if app.status in [OnboardingStatus.INITIATED, OnboardingStatus.DOCUMENTATION_PENDING, 
                             OnboardingStatus.VERIFICATION_IN_PROGRESS, OnboardingStatus.TESTING_PHASE]:
                
                days_pending = (datetime.now(timezone.utc) - app.submitted_at).days
                
                pending_apps.append({
                    'application_id': app.application_id,
                    'taxpayer_name': app.taxpayer_profile.business_name,
                    'taxpayer_type': app.taxpayer_profile.taxpayer_type.value,
                    'sector': app.taxpayer_profile.sector,
                    'status': app.status.value,
                    'current_step': app.current_step.value,
                    'days_pending': days_pending,
                    'priority': 'high' if days_pending > 20 else 'medium' if days_pending > 10 else 'normal'
                })
        
        # Sort by days pending (most urgent first)
        pending_apps.sort(key=lambda x: x['days_pending'], reverse=True)
        
        return pending_apps
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        pending_count = self.stats['pending_applications']
        overdue_count = len([
            app for app in self.applications.values()
            if (app.status not in [OnboardingStatus.ACTIVE, OnboardingStatus.REJECTED] and
                app.expected_completion and 
                datetime.now(timezone.utc) > app.expected_completion)
        ])
        
        status = "healthy"
        if overdue_count > 5:
            status = "degraded"
        elif pending_count > 50:
            status = "overloaded"
        
        return {
            'status': status,
            'service': 'taxpayer_onboarding',
            'pending_applications': pending_count,
            'overdue_applications': overdue_count,
            'active_taxpayers': self.stats['active_taxpayers'],
            'kpi_progress': self.stats.get('kpi_progress', 0),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Taxpayer onboarding service cleanup initiated")
        
        # Log final statistics
        self.logger.info(f"Final onboarding statistics: {self.stats}")
        
        self.logger.info("Taxpayer onboarding service cleanup completed")


# Factory function
def create_taxpayer_onboarding_service() -> TaxpayerOnboardingService:
    """Create taxpayer onboarding service with standard configuration"""
    return TaxpayerOnboardingService()


# Helper functions
def get_taxpayer_classification(annual_turnover: float) -> TaxpayerType:
    """Classify taxpayer based on annual turnover"""
    if annual_turnover >= 1_000_000_000:  # 1 billion
        return TaxpayerType.LARGE_TAXPAYER
    elif annual_turnover >= 100_000_000:  # 100 million
        return TaxpayerType.MEDIUM_TAXPAYER
    elif annual_turnover >= 10_000_000:  # 10 million
        return TaxpayerType.SMALL_TAXPAYER
    else:
        return TaxpayerType.MICRO_TAXPAYER


def get_required_documents_by_type(taxpayer_type: TaxpayerType) -> List[str]:
    """Get required documents based on taxpayer type"""
    base_documents = [
        'business_registration',
        'tax_certificate',
        'cac_certificate',
        'tin_certificate',
        'bank_statement'
    ]
    
    if taxpayer_type == TaxpayerType.LARGE_TAXPAYER:
        base_documents.extend([
            'audited_financial_statements',
            'tax_clearance_certificate',
            'board_resolution',
            'authorized_signatory_list'
        ])
    elif taxpayer_type == TaxpayerType.MEDIUM_TAXPAYER:
        base_documents.extend([
            'financial_statements',
            'tax_clearance_certificate'
        ])
    
    return base_documents