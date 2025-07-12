"""
Client Integration Templates and Communication Scripts

This module provides professional templates for client communication,
discovery questionnaires, and integration specifications that adapt
to any ERP system without requiring deep technical knowledge.

Focus: Business value and flexibility, not technical complexity
"""

from typing import Dict, Any, List
from datetime import datetime
import json


class ClientCommunicationTemplates:
    """Professional communication templates for ERP integration"""
    
    @staticmethod
    def get_initial_capability_statement() -> str:
        """Initial capability statement for any ERP"""
        return """
        TaxPoynt seamlessly integrates with all major ERP systems including SAP, Oracle, 
        Microsoft Dynamics, Odoo, NetSuite, and others. Our integration approach adapts 
        to your existing system architecture and security requirements.
        
        During implementation, we work with your technical team to:
        • Use your preferred integration methods and protocols
        • Maintain your existing security and access controls
        • Ensure zero disruption to your current processes
        • Deliver FIRS-compliant e-invoicing within weeks, not months
        
        Your ERP data flows automatically to FIRS while you maintain full control 
        of your system and data.
        """
    
    @staticmethod
    def get_discovery_email_template() -> str:
        """Email template for ERP discovery"""
        return """
        Subject: ERP Integration Discovery - TaxPoynt FIRS Compliance Setup
        
        Dear [CLIENT_NAME] Team,
        
        Thank you for choosing TaxPoynt for your FIRS e-invoicing compliance. To ensure 
        a smooth integration with your ERP system, we need to understand your current 
        setup and preferences.
        
        Please have your IT/ERP team review the attached discovery questionnaire. 
        This helps us:
        • Adapt our integration to your existing architecture
        • Use your preferred security and access methods  
        • Minimize implementation time and complexity
        • Ensure compliance with your internal policies
        
        Key benefits of our approach:
        ✓ Works with your existing ERP setup (no changes required)
        ✓ Uses your standard integration patterns
        ✓ Your team maintains full control and oversight
        ✓ Proven success with [ERP_TYPE] systems like yours
        
        Next Steps:
        1. Complete the attached questionnaire (15-20 minutes)
        2. Schedule technical alignment call (30 minutes)
        3. Begin integration setup within 48 hours
        
        We look forward to delivering seamless FIRS compliance for your organization.
        
        Best regards,
        TaxPoynt Integration Team
        """
    
    @staticmethod
    def get_technical_workshop_agenda() -> Dict[str, Any]:
        """Agenda for technical discovery workshop"""
        return {
            "workshop_title": "ERP Integration Technical Alignment Workshop",
            "duration": "60 minutes",
            "objectives": [
                "Understand your ERP landscape and architecture",
                "Identify optimal integration approach",
                "Define security requirements and access methods",
                "Establish implementation timeline and milestones"
            ],
            "agenda": {
                "0-10_min": {
                    "topic": "Introductions and Overview",
                    "content": [
                        "TaxPoynt integration team introductions",
                        "Client technical team introductions", 
                        "Workshop objectives and expected outcomes"
                    ]
                },
                "10-25_min": {
                    "topic": "ERP System Architecture Review",
                    "content": [
                        "Current ERP version and deployment model",
                        "Existing integration patterns and middleware",
                        "Data access methods and preferences",
                        "Security requirements and constraints"
                    ]
                },
                "25-40_min": {
                    "topic": "Integration Approach Definition",
                    "content": [
                        "Recommended integration method based on your setup",
                        "Data mapping and transformation requirements",
                        "Authentication and access control design",
                        "Testing and validation approach"
                    ]
                },
                "40-55_min": {
                    "topic": "Implementation Planning",
                    "content": [
                        "Project timeline and key milestones",
                        "Roles and responsibilities (client vs TaxPoynt)",
                        "Testing phases and go-live approach",
                        "Support and maintenance model"
                    ]
                },
                "55-60_min": {
                    "topic": "Next Steps and Action Items",
                    "content": [
                        "Integration specification document",
                        "Access requirements and approval process",
                        "Development environment setup",
                        "Next meeting scheduling"
                    ]
                }
            }
        }
    
    @staticmethod
    def get_security_comfort_script() -> str:
        """Script for addressing security concerns"""
        return """
        "We completely understand your security concerns. Let me clarify our approach:
        
        WHAT WE DON'T NEED:
        • Direct developer access to your production system
        • Administrative privileges or write access
        • Access to sensitive financial or customer data beyond invoices
        
        WHAT WE DO NEED:
        • A technical service account (similar to how your other integrations work)
        • Read-only access to invoice and basic customer data
        • Connection through your standard security protocols
        
        YOU REMAIN IN CONTROL:
        • Your team creates and manages the service account
        • You define exactly what data we can access
        • All activities are logged and auditable
        • Access can be revoked instantly if needed
        
        This is the same approach used by your other enterprise integrations. 
        We follow SAP/Oracle/Microsoft best practices for external system connectivity.
        
        Would you like to see our standard security documentation, or shall we 
        schedule a call with your security team to address specific concerns?"
        """
    
    @staticmethod
    def get_integration_specification_template() -> Dict[str, Any]:
        """Template for integration specification document"""
        return {
            "document_info": {
                "title": "ERP Integration Specification",
                "client": "[CLIENT_NAME]",
                "erp_system": "[ERP_TYPE] [VERSION]",
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0",
                "status": "Draft"
            },
            "executive_summary": {
                "objective": "Enable automated FIRS e-invoicing compliance through secure integration with client's ERP system",
                "approach": "Leverage client's existing integration patterns and security framework",
                "timeline": "2-4 weeks implementation, 1 week testing, go-live",
                "benefits": [
                    "Automated FIRS compliance with zero manual intervention",
                    "Seamless integration with existing ERP workflows", 
                    "Maintained security and data governance standards",
                    "Scalable solution for future regulatory requirements"
                ]
            },
            "system_architecture": {
                "client_erp": {
                    "system": "[ERP_TYPE]",
                    "version": "[VERSION]",
                    "deployment": "[CLOUD/ON_PREMISE/HYBRID]",
                    "environment": "[PRODUCTION/UAT/DEVELOPMENT]"
                },
                "integration_pattern": {
                    "method": "[REST_API/SOAP/DATABASE/FILE_BASED/MIDDLEWARE]",
                    "protocol": "[HTTPS/SFTP/VPN/OTHER]",
                    "authentication": "[OAUTH2/BASIC/API_KEY/CERTIFICATE]",
                    "data_format": "[JSON/XML/CSV/CUSTOM]"
                },
                "data_flow": {
                    "direction": "Outbound from ERP to TaxPoynt",
                    "frequency": "[REAL_TIME/HOURLY/DAILY/BATCH]",
                    "volume": "[INVOICES_PER_MONTH]",
                    "retention": "Data processed immediately, not stored permanently"
                }
            },
            "security_framework": {
                "access_control": {
                    "account_type": "Technical service account (non-human)",
                    "permissions": "Read-only access to invoice and customer master data",
                    "scope": "Limited to FIRS-required data fields only",
                    "approval_process": "Client IT team creates and manages account"
                },
                "network_security": {
                    "connectivity": "[VPN/API_GATEWAY/DIRECT/PROXY]",
                    "ip_restrictions": "TaxPoynt production IP addresses whitelisted",
                    "encryption": "TLS 1.3 for all data in transit",
                    "monitoring": "All access logged and available for audit"
                },
                "compliance": {
                    "standards": "SOC 2 Type II, ISO 27001 compliant processing",
                    "data_residency": "Nigeria-based processing when required",
                    "gdpr_compliance": "Data minimization and purpose limitation applied"
                }
            },
            "implementation_phases": {
                "phase_1_discovery": {
                    "duration": "1 week",
                    "activities": [
                        "Technical architecture review",
                        "Integration specification finalization",
                        "Security requirements validation",
                        "Access approval process initiation"
                    ],
                    "deliverables": [
                        "Finalized integration specification",
                        "Security assessment report",
                        "Implementation project plan"
                    ]
                },
                "phase_2_development": {
                    "duration": "2-3 weeks", 
                    "activities": [
                        "Integration connector development",
                        "Data mapping and transformation setup",
                        "Security implementation and testing",
                        "Initial connectivity testing"
                    ],
                    "deliverables": [
                        "Configured integration connector",
                        "Data mapping documentation",
                        "Security implementation report"
                    ]
                },
                "phase_3_testing": {
                    "duration": "1 week",
                    "activities": [
                        "End-to-end integration testing",
                        "FIRS compliance validation",
                        "Performance and security testing", 
                        "User acceptance testing support"
                    ],
                    "deliverables": [
                        "Test results and validation report",
                        "Performance benchmarks",
                        "Go-live readiness assessment"
                    ]
                },
                "phase_4_deployment": {
                    "duration": "3-5 days",
                    "activities": [
                        "Production environment setup",
                        "Go-live coordination and monitoring",
                        "Issue resolution and optimization",
                        "Knowledge transfer and training"
                    ],
                    "deliverables": [
                        "Live production integration",
                        "Operations handbook",
                        "Support team training completion"
                    ]
                }
            },
            "roles_responsibilities": {
                "client_team": {
                    "it_operations": [
                        "Provide ERP system access and documentation",
                        "Create and manage technical service accounts",
                        "Configure network access and security settings",
                        "Approve and monitor integration activities"
                    ],
                    "business_users": [
                        "Validate invoice data accuracy and completeness",
                        "Participate in user acceptance testing",
                        "Provide feedback on FIRS compliance reports"
                    ],
                    "project_management": [
                        "Coordinate internal approvals and resources",
                        "Manage project timeline and milestones",
                        "Facilitate communication between teams"
                    ]
                },
                "taxpoynt_team": {
                    "integration_engineers": [
                        "Develop and configure ERP connector",
                        "Implement data mapping and transformations",
                        "Conduct technical testing and validation"
                    ],
                    "firs_specialists": [
                        "Ensure FIRS compliance of all invoice data",
                        "Validate tax calculations and classifications",
                        "Support FIRS submission and status tracking"
                    ],
                    "project_management": [
                        "Manage TaxPoynt delivery timeline",
                        "Coordinate with client project team",
                        "Provide regular status updates and reporting"
                    ]
                }
            },
            "success_metrics": {
                "technical_kpis": [
                    "99.9% uptime and availability",
                    "< 5 minute data processing time",
                    "100% FIRS compliance validation rate",
                    "Zero security incidents or data breaches"
                ],
                "business_kpis": [
                    "100% automated invoice processing",
                    "< 24 hour FIRS submission time",
                    "Zero manual intervention required",
                    "Full audit trail and compliance reporting"
                ]
            },
            "support_model": {
                "production_support": {
                    "availability": "24/7 monitoring with business hours response",
                    "response_times": "Critical: 1 hour, High: 4 hours, Medium: 24 hours",
                    "escalation": "Clear escalation path to senior technical team",
                    "communication": "Dedicated Slack channel and email support"
                },
                "ongoing_maintenance": {
                    "updates": "Regular connector updates for ERP system changes",
                    "compliance": "Automatic updates for FIRS regulatory changes",
                    "optimization": "Quarterly performance review and optimization",
                    "reporting": "Monthly integration health and compliance reports"
                }
            }
        }
    
    @staticmethod
    def get_alternative_approaches_guide() -> Dict[str, Any]:
        """Guide for alternative integration approaches for high-security clients"""
        return {
            "title": "Alternative Integration Approaches for High-Security Environments",
            "approaches": {
                "client_managed_deployment": {
                    "description": "TaxPoynt provides connector package, client team deploys and manages",
                    "benefits": [
                        "Client maintains complete control over deployment",
                        "No external access to client systems required", 
                        "Integrates with existing change management processes",
                        "Full compliance with internal security policies"
                    ],
                    "requirements": [
                        "Client team with technical integration capability",
                        "Access to deployment documentation and support",
                        "Remote troubleshooting and guidance from TaxPoynt team"
                    ],
                    "timeline": "Additional 1-2 weeks for knowledge transfer and support"
                },
                "partner_channel_integration": {
                    "description": "Work through client's existing SAP/Oracle/ERP implementation partner",
                    "benefits": [
                        "Leverages existing trusted relationship",
                        "Partner already has appropriate system access",
                        "Familiar with client's architecture and constraints",
                        "Established security and approval processes"
                    ],
                    "requirements": [
                        "Partner willingness to support TaxPoynt integration",
                        "Technical handoff and specification documents",
                        "Three-way coordination between client, partner, and TaxPoynt"
                    ],
                    "timeline": "May add 1 week for partner coordination and briefing"
                },
                "secure_gateway_deployment": {
                    "description": "Install TaxPoynt gateway appliance in client's network environment",
                    "benefits": [
                        "Data never leaves client's network perimeter",
                        "Client-controlled outbound-only data flow",
                        "Integration processing happens on-premises",
                        "Maximum security and data sovereignty"
                    ],
                    "requirements": [
                        "Dedicated server or VM for gateway deployment",
                        "Network configuration for outbound FIRS connectivity",
                        "Local technical support for gateway management"
                    ],
                    "timeline": "Additional 1 week for gateway setup and configuration"
                },
                "scheduled_batch_processing": {
                    "description": "Periodic batch export and processing model",
                    "benefits": [
                        "Minimal real-time connectivity requirements",
                        "Client controls timing and frequency of data sharing",
                        "Compatible with most ERP export capabilities",
                        "Lower technical complexity and risk"
                    ],
                    "requirements": [
                        "ERP system capable of automated invoice export",
                        "Secure file transfer mechanism (SFTP, cloud storage)",
                        "Acceptance of non-real-time processing model"
                    ],
                    "timeline": "Fastest implementation, usually 1-2 weeks"
                }
            },
            "selection_criteria": {
                "high_security_low_volume": "Secure gateway or client-managed deployment",
                "established_partner_relationship": "Partner channel integration",
                "minimal_technical_resources": "Scheduled batch processing",
                "maximum_control_required": "Client-managed deployment",
                "fastest_implementation": "Scheduled batch processing",
                "real_time_requirements": "Secure gateway deployment"
            }
        }
    
    @staticmethod
    def get_client_faq() -> Dict[str, str]:
        """Frequently asked questions from clients"""
        return {
            "q_what_erp_access_needed": {
                "question": "What level of access do you need to our ERP system?",
                "answer": "We need read-only access to invoice and basic customer data through a technical service account. This is similar to how your other business applications integrate - no human access, no administrative privileges, and you maintain complete control over the account and its permissions."
            },
            "q_security_risks": {
                "question": "What are the security risks of giving external access?",
                "answer": "The security risk is minimal because: (1) We only get read-only access to invoice data, (2) All access is through a service account you create and control, (3) All activities are logged and auditable, (4) Access can be revoked instantly, and (5) We follow SOC 2 and ISO 27001 security standards."
            },
            "q_system_changes_required": {
                "question": "Do we need to make changes to our ERP system?",
                "answer": "Typically no. We adapt to your existing ERP configuration and use your standard integration methods. In rare cases, we might need to enable an existing API or create a simple data export, but we avoid any changes to your core business processes."
            },
            "q_implementation_disruption": {
                "question": "Will implementation disrupt our current operations?",
                "answer": "No. Integration happens alongside your existing processes without any interruption. We do most development and testing in non-production environments, and the go-live is typically just a configuration change that takes minutes."
            },
            "q_if_something_goes_wrong": {
                "question": "What happens if something goes wrong with the integration?",
                "answer": "We have multiple safeguards: (1) All integrations are thoroughly tested before go-live, (2) We can disable the integration instantly without affecting your ERP, (3) All invoice data is validated before FIRS submission, and (4) We maintain 24/7 monitoring with immediate alert capabilities."
            },
            "q_ongoing_maintenance": {
                "question": "What ongoing maintenance is required?",
                "answer": "Minimal. The integration is designed to be self-maintaining. We handle FIRS regulatory updates automatically, and ERP system updates rarely affect the integration. We provide quarterly health checks and are available for any optimization or troubleshooting needs."
            },
            "q_data_privacy": {
                "question": "How do you handle our sensitive business data?",
                "answer": "We follow strict data minimization principles - we only access invoice data required for FIRS compliance, process it immediately for tax submission, and don't store sensitive business information permanently. All data handling complies with Nigerian data protection requirements."
            },
            "q_contract_terms": {
                "question": "What should we include in our contract regarding system access?",
                "answer": "Standard terms should cover: (1) Scope of data access and usage rights, (2) Security requirements and compliance standards, (3) Access termination procedures, (4) Audit and monitoring requirements, and (5) Data handling and privacy obligations. We're happy to work with your legal team on appropriate language."
            }
        }
    
    @staticmethod
    def generate_client_presentation(client_name: str, erp_type: str) -> Dict[str, Any]:
        """Generate customized client presentation"""
        return {
            "title": f"FIRS E-Invoicing Integration for {client_name}",
            "subtitle": f"Seamless {erp_type} Integration Strategy",
            "slides": {
                "slide_1_overview": {
                    "title": "TaxPoynt FIRS Integration Overview",
                    "content": [
                        f"Automated FIRS compliance for your {erp_type} system",
                        "Zero disruption to existing business processes",
                        "Enterprise-grade security and reliability",
                        "Proven success with similar organizations"
                    ]
                },
                "slide_2_integration_approach": {
                    "title": f"Our {erp_type} Integration Approach",
                    "content": [
                        "Adapts to your existing system architecture",
                        "Uses your preferred security and access methods",
                        "Maintains your data governance standards",
                        "Leverages industry best practices"
                    ]
                },
                "slide_3_implementation_timeline": {
                    "title": "Implementation Timeline",
                    "content": [
                        "Week 1: Technical discovery and specification",
                        "Week 2-3: Integration development and configuration",
                        "Week 4: Testing and validation",
                        "Week 5: Go-live and support"
                    ]
                },
                "slide_4_security_framework": {
                    "title": "Security and Compliance",
                    "content": [
                        "Read-only access through service account",
                        "Your team maintains complete control",
                        "SOC 2 and ISO 27001 compliant processing",
                        "Full audit trail and monitoring"
                    ]
                },
                "slide_5_business_value": {
                    "title": "Business Value and Benefits",
                    "content": [
                        "100% automated FIRS compliance",
                        "Eliminate manual invoice processing",
                        "Reduce compliance risk and penalties",
                        "Focus your team on core business activities"
                    ]
                },
                "slide_6_next_steps": {
                    "title": "Next Steps",
                    "content": [
                        "Complete technical discovery questionnaire",
                        "Schedule alignment workshop with your IT team",
                        "Begin integration specification and planning",
                        "Target go-live within 4-5 weeks"
                    ]
                }
            }
        }


class IntegrationProjectTemplates:
    """Templates for managing integration projects"""
    
    @staticmethod
    def get_project_kickoff_checklist() -> Dict[str, List[str]]:
        """Project kickoff checklist"""
        return {
            "pre_kickoff": [
                "Discovery questionnaire completed",
                "Technical workshop scheduled",
                "Client project team identified",
                "Integration specification drafted",
                "Security requirements documented"
            ],
            "kickoff_meeting": [
                "Project scope and objectives confirmed",
                "Roles and responsibilities clarified",
                "Communication plan established",
                "Timeline and milestones agreed",
                "Success criteria defined"
            ],
            "post_kickoff": [
                "Integration specification finalized",
                "Access approval process initiated",
                "Development environment prepared",
                "Testing strategy documented",
                "Regular status meetings scheduled"
            ]
        }
    
    @staticmethod
    def get_status_report_template() -> Dict[str, Any]:
        """Weekly status report template"""
        return {
            "report_info": {
                "client": "[CLIENT_NAME]",
                "project": "FIRS ERP Integration",
                "week_ending": "[DATE]",
                "project_manager": "[PM_NAME]"
            },
            "executive_summary": {
                "overall_status": "[GREEN/YELLOW/RED]",
                "completion_percentage": "[X]%",
                "key_accomplishments": [],
                "upcoming_milestones": [],
                "risks_or_issues": []
            },
            "detailed_progress": {
                "discovery_phase": {
                    "status": "[COMPLETE/IN_PROGRESS/NOT_STARTED]",
                    "completion": "[X]%",
                    "activities": []
                },
                "development_phase": {
                    "status": "[COMPLETE/IN_PROGRESS/NOT_STARTED]",
                    "completion": "[X]%",
                    "activities": []
                },
                "testing_phase": {
                    "status": "[COMPLETE/IN_PROGRESS/NOT_STARTED]",
                    "completion": "[X]%",
                    "activities": []
                },
                "deployment_phase": {
                    "status": "[COMPLETE/IN_PROGRESS/NOT_STARTED]",
                    "completion": "[X]%",
                    "activities": []
                }
            },
            "next_week_plan": {
                "objectives": [],
                "key_activities": [],
                "deliverables": [],
                "meetings_required": []
            }
        }
    
    @staticmethod
    def get_go_live_checklist() -> Dict[str, List[str]]:
        """Go-live readiness checklist"""
        return {
            "technical_readiness": [
                "Integration testing completed successfully",
                "Performance testing passed",
                "Security validation completed",
                "FIRS compliance testing verified",
                "Backup and rollback procedures tested",
                "Monitoring and alerting configured"
            ],
            "business_readiness": [
                "User acceptance testing completed",
                "Business process validation confirmed",
                "Training completed for support teams",
                "Documentation delivered and reviewed",
                "Change management communication sent",
                "Support escalation procedures established"
            ],
            "operational_readiness": [
                "Production environment configured",
                "Service accounts created and tested",
                "Network connectivity verified",
                "Support team contact information updated",
                "Incident response procedures documented",
                "Success metrics baseline established"
            ]
        }


def generate_discovery_questionnaire(erp_type: str = "Generic") -> Dict[str, Any]:
    """Generate ERP-specific discovery questionnaire"""
    base_template = ERPDiscoveryTemplate.get_discovery_questions()
    
    # Customize questions based on ERP type
    if erp_type.lower() == "sap":
        base_template["system_info"]["sap_specific"] = {
            "question": "Which SAP system are you using?",
            "options": ["S/4HANA Cloud", "S/4HANA On-Premise", "ECC", "Business One"],
            "follow_up": "What version and what modules are implemented?"
        }
    elif erp_type.lower() == "oracle":
        base_template["system_info"]["oracle_specific"] = {
            "question": "Which Oracle system are you using?",
            "options": ["Oracle Cloud ERP", "Oracle E-Business Suite", "JD Edwards", "PeopleSoft"],
            "follow_up": "What version and which modules are you using?"
        }
    elif erp_type.lower() == "odoo":
        base_template["system_info"]["odoo_specific"] = {
            "question": "What Odoo deployment do you have?",
            "options": ["Odoo.com (SaaS)", "Odoo.sh", "Self-hosted", "Partner-hosted"],
            "follow_up": "What version and which apps are installed?"
        }
    
    return {
        "questionnaire_title": f"{erp_type} Integration Discovery Questionnaire",
        "instructions": "Please complete this questionnaire to help us design the optimal integration approach for your system.",
        "estimated_time": "15-20 minutes",
        "sections": base_template
    }


if __name__ == "__main__":
    """Example usage of the templates"""
    
    # Generate discovery questionnaire for SAP
    sap_questionnaire = generate_discovery_questionnaire("SAP")
    print("SAP Discovery Questionnaire Generated")
    
    # Generate client presentation
    client_presentation = ClientCommunicationTemplates.generate_client_presentation(
        "Acme Corporation", "SAP S/4HANA"
    )
    print("Client Presentation Generated")
    
    # Get security comfort script
    security_script = ClientCommunicationTemplates.get_security_comfort_script()
    print("Security Script Ready")
    
    print("\nAll templates generated successfully!")