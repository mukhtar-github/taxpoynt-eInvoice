"""
Activity Service for Dashboard Activity Feed

This service aggregates activities from various sources:
- Transmission audit logs
- IRN generation events
- Integration sync events
- System events and alerts
- User actions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from app.models.transmission_audit_log import TransmissionAuditLog
from app.models.transmission_status_log import TransmissionStatusLog
from app.models.irn import IRNRecord
from app.models.integration import Integration
from app.models.user import User


class ActivityService:
    """Service for managing and retrieving dashboard activities."""
    
    @staticmethod
    def get_activities(
        db: Session,
        organization_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        activity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get paginated activities for the dashboard activity feed.
        
        Args:
            db: Database session
            organization_id: Filter by organization
            limit: Maximum number of activities to return
            offset: Number of activities to skip
            activity_type: Filter by activity type
            
        Returns:
            List of activity items formatted for the frontend
        """
        activities = []
        
        # Get activities from different sources
        activities.extend(ActivityService._get_transmission_activities(
            db, organization_id, limit // 3
        ))
        
        activities.extend(ActivityService._get_irn_activities(
            db, organization_id, limit // 3
        ))
        
        activities.extend(ActivityService._get_integration_activities(
            db, organization_id, limit // 3
        ))
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply filtering
        if activity_type:
            activities = [a for a in activities if a['type'] == activity_type]
        
        # Apply pagination
        return activities[offset:offset + limit]
    
    @staticmethod
    def _get_transmission_activities(
        db: Session,
        organization_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get activities from transmission audit logs."""
        query = db.query(TransmissionAuditLog).order_by(desc(TransmissionAuditLog.timestamp))
        
        if organization_id:
            query = query.filter(TransmissionAuditLog.organization_id == organization_id)
        
        logs = query.limit(limit).all()
        
        activities = []
        for log in logs:
            activity_type = ActivityService._map_transmission_action_to_type(log.action)
            
            activities.append({
                'id': f"transmission_{log.id}",
                'type': activity_type,
                'title': ActivityService._get_transmission_title(log.action),
                'description': log.context.get('description') if log.context else None,
                'timestamp': log.timestamp.isoformat(),
                'metadata': {
                    'user': log.user_email,
                    'status': ActivityService._get_status_from_action(log.action),
                    'transmission_id': str(log.transmission_id) if log.transmission_id else None,
                    'ip_address': log.ip_address
                }
            })
        
        return activities
    
    @staticmethod
    def _get_irn_activities(
        db: Session,
        organization_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get activities from IRN records."""
        query = db.query(IRNRecord).order_by(desc(IRNRecord.created_at))
        
        if organization_id:
            query = query.filter(IRNRecord.organization_id == organization_id)
        
        irn_records = query.limit(limit).all()
        
        activities = []
        for irn in irn_records:
            activities.append({
                'id': f"irn_{irn.id}",
                'type': 'invoice_generated',
                'title': 'Invoice IRN Generated',
                'description': f'IRN {irn.irn_value} generated for invoice',
                'timestamp': irn.created_at.isoformat(),
                'metadata': {
                    'irn_value': irn.irn_value,
                    'status': 'success' if irn.status.value == 'ACTIVE' else 'warning',
                    'invoice_number': irn.invoice_data.get('invoice_number') if irn.invoice_data else None
                }
            })
        
        return activities
    
    @staticmethod
    def _get_integration_activities(
        db: Session,
        organization_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get activities from integration records."""
        query = db.query(Integration).order_by(desc(Integration.updated_at))
        
        if organization_id:
            query = query.filter(Integration.organization_id == organization_id)
        
        integrations = query.limit(limit).all()
        
        activities = []
        for integration in integrations:
            # Check if this is a recent update (within last 24 hours)
            if integration.updated_at > datetime.utcnow() - timedelta(hours=24):
                status = 'success' if integration.is_active else 'warning'
                
                activities.append({
                    'id': f"integration_{integration.id}",
                    'type': 'integration_sync',
                    'title': f'{integration.integration_type.title()} Integration Update',
                    'description': f'Integration status: {"Active" if integration.is_active else "Inactive"}',
                    'timestamp': integration.updated_at.isoformat(),
                    'metadata': {
                        'integration': integration.integration_type,
                        'status': status,
                        'connection_name': integration.name
                    }
                })
        
        return activities
    
    @staticmethod
    def _map_transmission_action_to_type(action: str) -> str:
        """Map transmission action to activity type."""
        action_mapping = {
            'CREATE': 'submission',
            'UPDATE': 'submission',
            'RETRY': 'submission',
            'WEBHOOK': 'system_event',
            'EXPORT': 'user_action',
            'SIGN': 'invoice_generated',
            'ENCRYPT': 'system_event',
            'DECRYPT': 'system_event',
            'DELETE': 'user_action'
        }
        return action_mapping.get(action, 'system_event')
    
    @staticmethod
    def _get_transmission_title(action: str) -> str:
        """Get human-readable title for transmission action."""
        action_titles = {
            'CREATE': 'Transmission Created',
            'UPDATE': 'Transmission Updated',
            'RETRY': 'Transmission Retried',
            'WEBHOOK': 'Webhook Received',
            'EXPORT': 'Data Exported',
            'SIGN': 'Document Signed',
            'ENCRYPT': 'Data Encrypted',
            'DECRYPT': 'Data Decrypted',
            'DELETE': 'Transmission Deleted'
        }
        return action_titles.get(action, f'{action.title()} Action')
    
    @staticmethod
    def _get_status_from_action(action: str) -> str:
        """Get status indicator from action type."""
        if action in ['CREATE', 'UPDATE', 'SIGN', 'ENCRYPT']:
            return 'success'
        elif action in ['RETRY', 'WEBHOOK']:
            return 'warning'
        elif action in ['DELETE']:
            return 'error'
        else:
            return 'info'
    
    @staticmethod
    def get_activity_count_by_type(
        db: Session,
        organization_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, int]:
        """
        Get count of activities by type for the last N hours.
        
        Args:
            db: Database session
            organization_id: Filter by organization
            hours: Number of hours to look back
            
        Returns:
            Dictionary with activity type counts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Count transmission activities
        transmission_query = db.query(TransmissionAuditLog).filter(
            TransmissionAuditLog.timestamp > cutoff_time
        )
        if organization_id:
            transmission_query = transmission_query.filter(
                TransmissionAuditLog.organization_id == organization_id
            )
        
        # Count IRN activities
        irn_query = db.query(IRNRecord).filter(
            IRNRecord.created_at > cutoff_time
        )
        if organization_id:
            irn_query = irn_query.filter(
                IRNRecord.organization_id == organization_id
            )
        
        # Count integration activities
        integration_query = db.query(Integration).filter(
            Integration.updated_at > cutoff_time
        )
        if organization_id:
            integration_query = integration_query.filter(
                Integration.organization_id == organization_id
            )
        
        return {
            'total_transmissions': transmission_query.count(),
            'total_irn_generated': irn_query.count(),
            'total_integrations': integration_query.count(),
            'total_activities': (
                transmission_query.count() + 
                irn_query.count() + 
                integration_query.count()
            )
        }