"""
Deployment Manager - Core Platform Infrastructure
Comprehensive deployment automation system for the TaxPoynt platform.
Manages deployment procedures, rollouts, rollbacks, and environment management.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DeploymentStrategy(Enum):
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"
    A_B_TESTING = "ab_testing"

class DeploymentStatus(Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    DEPLOYING = "deploying"
    TESTING = "testing"
    PROMOTING = "promoting"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    ABORTED = "aborted"

class EnvironmentType(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    UAT = "uat"
    DR = "disaster_recovery"

class ServiceType(Enum):
    WEB_SERVICE = "web_service"
    API_SERVICE = "api_service"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    WORKER = "worker"
    CRON_JOB = "cron_job"

@dataclass
class Environment:
    id: str
    name: str
    environment_type: EnvironmentType
    region: str
    namespace: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    health_check_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ServiceSpec:
    id: str
    name: str
    service_type: ServiceType
    image: str
    tag: str
    port: int
    replicas: int = 1
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    health_check: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentConfig:
    id: str
    name: str
    environment_id: str
    services: List[ServiceSpec]
    strategy: DeploymentStrategy
    rollout_config: Dict[str, Any] = field(default_factory=dict)
    health_checks: List[Dict[str, Any]] = field(default_factory=list)
    pre_deploy_hooks: List[str] = field(default_factory=list)
    post_deploy_hooks: List[str] = field(default_factory=list)
    rollback_config: Dict[str, Any] = field(default_factory=dict)
    notifications: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentStep:
    id: str
    deployment_id: str
    step_name: str
    step_type: str
    parameters: Dict[str, Any]
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class Deployment:
    id: str
    config_id: str
    environment_id: str
    triggered_by: str
    status: DeploymentStatus
    strategy: DeploymentStrategy
    version: str
    steps: List[DeploymentStep] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    previous_deployment_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RollbackPlan:
    id: str
    deployment_id: str
    target_deployment_id: str
    strategy: DeploymentStrategy
    steps: List[Dict[str, Any]]
    estimated_duration: int
    risk_level: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)

class DeploymentProvider(ABC):
    @abstractmethod
    async def deploy_service(self, service_spec: ServiceSpec, environment: Environment) -> bool:
        pass
    
    @abstractmethod
    async def rollback_service(self, service_id: str, target_version: str, environment: Environment) -> bool:
        pass
    
    @abstractmethod
    async def health_check_service(self, service_id: str, environment: Environment) -> bool:
        pass
    
    @abstractmethod
    async def scale_service(self, service_id: str, replicas: int, environment: Environment) -> bool:
        pass
    
    @abstractmethod
    async def get_service_status(self, service_id: str, environment: Environment) -> Dict[str, Any]:
        pass

class KubernetesProvider(DeploymentProvider):
    async def deploy_service(self, service_spec: ServiceSpec, environment: Environment) -> bool:
        try:
            logger.info(f"Deploying service {service_spec.name} to Kubernetes in {environment.name}")
            
            # Simulate Kubernetes deployment
            # In real implementation, this would use kubectl or Kubernetes Python client
            deployment_manifest = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": service_spec.name,
                    "namespace": environment.namespace
                },
                "spec": {
                    "replicas": service_spec.replicas,
                    "selector": {
                        "matchLabels": {"app": service_spec.name}
                    },
                    "template": {
                        "metadata": {
                            "labels": {"app": service_spec.name}
                        },
                        "spec": {
                            "containers": [{
                                "name": service_spec.name,
                                "image": f"{service_spec.image}:{service_spec.tag}",
                                "ports": [{"containerPort": service_spec.port}],
                                "env": [
                                    {"name": k, "value": v} 
                                    for k, v in service_spec.environment_variables.items()
                                ]
                            }]
                        }
                    }
                }
            }
            
            logger.info(f"Kubernetes deployment manifest created for {service_spec.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy service to Kubernetes: {e}")
            return False
    
    async def rollback_service(self, service_id: str, target_version: str, environment: Environment) -> bool:
        try:
            logger.info(f"Rolling back service {service_id} to version {target_version} in {environment.name}")
            # Kubernetes rollback implementation
            return True
        except Exception as e:
            logger.error(f"Failed to rollback service in Kubernetes: {e}")
            return False
    
    async def health_check_service(self, service_id: str, environment: Environment) -> bool:
        try:
            # Simulate Kubernetes health check
            logger.info(f"Health checking service {service_id} in {environment.name}")
            return True
        except Exception as e:
            logger.error(f"Health check failed for Kubernetes service: {e}")
            return False
    
    async def scale_service(self, service_id: str, replicas: int, environment: Environment) -> bool:
        try:
            logger.info(f"Scaling service {service_id} to {replicas} replicas in {environment.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to scale Kubernetes service: {e}")
            return False
    
    async def get_service_status(self, service_id: str, environment: Environment) -> Dict[str, Any]:
        try:
            # Simulate Kubernetes service status
            return {
                "status": "running",
                "replicas": 3,
                "ready_replicas": 3,
                "version": "1.2.3",
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get Kubernetes service status: {e}")
            return {}

class DockerProvider(DeploymentProvider):
    async def deploy_service(self, service_spec: ServiceSpec, environment: Environment) -> bool:
        try:
            logger.info(f"Deploying service {service_spec.name} to Docker in {environment.name}")
            
            # Simulate Docker deployment
            docker_run_command = [
                "docker", "run", "-d",
                "--name", service_spec.name,
                "-p", f"{service_spec.port}:{service_spec.port}",
                f"{service_spec.image}:{service_spec.tag}"
            ]
            
            # Add environment variables
            for key, value in service_spec.environment_variables.items():
                docker_run_command.extend(["-e", f"{key}={value}"])
            
            logger.info(f"Docker command: {' '.join(docker_run_command)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy service to Docker: {e}")
            return False
    
    async def rollback_service(self, service_id: str, target_version: str, environment: Environment) -> bool:
        try:
            logger.info(f"Rolling back Docker service {service_id} to version {target_version}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback Docker service: {e}")
            return False
    
    async def health_check_service(self, service_id: str, environment: Environment) -> bool:
        try:
            logger.info(f"Health checking Docker service {service_id}")
            return True
        except Exception as e:
            logger.error(f"Health check failed for Docker service: {e}")
            return False
    
    async def scale_service(self, service_id: str, replicas: int, environment: Environment) -> bool:
        try:
            logger.info(f"Scaling Docker service {service_id} to {replicas} instances")
            return True
        except Exception as e:
            logger.error(f"Failed to scale Docker service: {e}")
            return False
    
    async def get_service_status(self, service_id: str, environment: Environment) -> Dict[str, Any]:
        try:
            return {
                "status": "running",
                "container_id": "abc123def456",
                "version": "1.2.3",
                "started_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get Docker service status: {e}")
            return {}

class DeploymentManager:
    def __init__(self):
        self.environments: Dict[str, Environment] = {}
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        self.deployments: Dict[str, Deployment] = {}
        self.rollback_plans: Dict[str, RollbackPlan] = {}
        self.providers: Dict[str, DeploymentProvider] = {}
        
        # Initialize providers
        self._initialize_providers()
        
        # Setup default environments
        self._setup_default_environments()
    
    def _initialize_providers(self):
        """Initialize deployment providers"""
        self.providers = {
            'kubernetes': KubernetesProvider(),
            'docker': DockerProvider()
        }
    
    def _setup_default_environments(self):
        """Setup default deployment environments"""
        default_environments = [
            Environment(
                id="dev_env",
                name="Development",
                environment_type=EnvironmentType.DEVELOPMENT,
                region="local",
                namespace="taxpoynt-dev",
                configuration={
                    "debug": True,
                    "log_level": "DEBUG",
                    "database_pool_size": 5
                },
                resource_limits={
                    "cpu": "1",
                    "memory": "2Gi"
                },
                health_check_config={
                    "enabled": True,
                    "path": "/health",
                    "interval": 30,
                    "timeout": 5
                }
            ),
            Environment(
                id="staging_env",
                name="Staging",
                environment_type=EnvironmentType.STAGING,
                region="us-east-1",
                namespace="taxpoynt-staging",
                configuration={
                    "debug": False,
                    "log_level": "INFO",
                    "database_pool_size": 10
                },
                resource_limits={
                    "cpu": "2",
                    "memory": "4Gi"
                },
                health_check_config={
                    "enabled": True,
                    "path": "/health",
                    "interval": 30,
                    "timeout": 10
                }
            ),
            Environment(
                id="prod_env",
                name="Production",
                environment_type=EnvironmentType.PRODUCTION,
                region="us-east-1",
                namespace="taxpoynt-prod",
                configuration={
                    "debug": False,
                    "log_level": "WARN",
                    "database_pool_size": 20
                },
                resource_limits={
                    "cpu": "4",
                    "memory": "8Gi"
                },
                health_check_config={
                    "enabled": True,
                    "path": "/health",
                    "interval": 15,
                    "timeout": 5
                }
            )
        ]
        
        for env in default_environments:
            self.environments[env.id] = env
    
    async def create_deployment_config(self, config_data: Dict[str, Any]) -> Optional[DeploymentConfig]:
        """Create a new deployment configuration"""
        try:
            # Parse service specifications
            services = []
            for service_data in config_data.get('services', []):
                service_spec = ServiceSpec(
                    id=service_data.get('id', f"service_{int(time.time())}"),
                    name=service_data['name'],
                    service_type=ServiceType(service_data['service_type']),
                    image=service_data['image'],
                    tag=service_data.get('tag', 'latest'),
                    port=service_data['port'],
                    replicas=service_data.get('replicas', 1),
                    resource_requirements=service_data.get('resource_requirements', {}),
                    environment_variables=service_data.get('environment_variables', {}),
                    volumes=service_data.get('volumes', []),
                    health_check=service_data.get('health_check', {}),
                    dependencies=service_data.get('dependencies', []),
                    metadata=service_data.get('metadata', {})
                )
                services.append(service_spec)
            
            config = DeploymentConfig(
                id=config_data.get('id', f"config_{int(time.time())}"),
                name=config_data['name'],
                environment_id=config_data['environment_id'],
                services=services,
                strategy=DeploymentStrategy(config_data.get('strategy', 'rolling')),
                rollout_config=config_data.get('rollout_config', {}),
                health_checks=config_data.get('health_checks', []),
                pre_deploy_hooks=config_data.get('pre_deploy_hooks', []),
                post_deploy_hooks=config_data.get('post_deploy_hooks', []),
                rollback_config=config_data.get('rollback_config', {}),
                notifications=config_data.get('notifications', {}),
                metadata=config_data.get('metadata', {})
            )
            
            self.deployment_configs[config.id] = config
            logger.info(f"Created deployment config: {config.id}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create deployment config: {e}")
            return None
    
    async def deploy(self, config_id: str, triggered_by: str, version: str = None) -> Optional[Deployment]:
        """Deploy services based on configuration"""
        try:
            if config_id not in self.deployment_configs:
                logger.error(f"Deployment config not found: {config_id}")
                return None
            
            config = self.deployment_configs[config_id]
            
            if config.environment_id not in self.environments:
                logger.error(f"Environment not found: {config.environment_id}")
                return None
            
            environment = self.environments[config.environment_id]
            
            # Create deployment
            deployment = Deployment(
                id=f"deploy_{int(time.time())}_{config_id}",
                config_id=config_id,
                environment_id=config.environment_id,
                triggered_by=triggered_by,
                status=DeploymentStatus.PENDING,
                strategy=config.strategy,
                version=version or f"v{int(time.time())}",
                started_at=datetime.utcnow()
            )
            
            self.deployments[deployment.id] = deployment
            
            # Execute deployment based on strategy
            success = await self._execute_deployment(deployment, config, environment)
            
            if success:
                deployment.status = DeploymentStatus.COMPLETED
                deployment.completed_at = datetime.utcnow()
                logger.info(f"Deployment completed successfully: {deployment.id}")
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.completed_at = datetime.utcnow()
                logger.error(f"Deployment failed: {deployment.id}")
            
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to execute deployment: {e}")
            return None
    
    async def _execute_deployment(self, deployment: Deployment, config: DeploymentConfig, environment: Environment) -> bool:
        """Execute deployment using specified strategy"""
        try:
            deployment.status = DeploymentStatus.PREPARING
            
            # Execute pre-deploy hooks
            for hook in config.pre_deploy_hooks:
                if not await self._execute_hook(hook, deployment, "pre_deploy"):
                    return False
            
            deployment.status = DeploymentStatus.DEPLOYING
            
            # Execute deployment based on strategy
            if config.strategy == DeploymentStrategy.ROLLING:
                success = await self._rolling_deployment(deployment, config, environment)
            elif config.strategy == DeploymentStrategy.BLUE_GREEN:
                success = await self._blue_green_deployment(deployment, config, environment)
            elif config.strategy == DeploymentStrategy.CANARY:
                success = await self._canary_deployment(deployment, config, environment)
            else:
                success = await self._recreate_deployment(deployment, config, environment)
            
            if not success:
                return False
            
            deployment.status = DeploymentStatus.TESTING
            
            # Execute health checks
            if not await self._execute_health_checks(deployment, config, environment):
                return False
            
            # Execute post-deploy hooks
            for hook in config.post_deploy_hooks:
                if not await self._execute_hook(hook, deployment, "post_deploy"):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute deployment: {e}")
            return False
    
    async def _rolling_deployment(self, deployment: Deployment, config: DeploymentConfig, environment: Environment) -> bool:
        """Execute rolling deployment strategy"""
        try:
            logger.info(f"Executing rolling deployment for {deployment.id}")
            
            provider_name = config.rollout_config.get('provider', 'kubernetes')
            if provider_name not in self.providers:
                logger.error(f"Unknown provider: {provider_name}")
                return False
            
            provider = self.providers[provider_name]
            
            # Deploy services one by one with rolling updates
            for service_spec in config.services:
                step = DeploymentStep(
                    id=f"step_{len(deployment.steps)}",
                    deployment_id=deployment.id,
                    step_name=f"Deploy {service_spec.name}",
                    step_type="service_deployment",
                    parameters={"service_id": service_spec.id}
                )
                deployment.steps.append(step)
                
                step.started_at = datetime.utcnow()
                step.status = "running"
                
                success = await provider.deploy_service(service_spec, environment)
                
                step.completed_at = datetime.utcnow()
                if success:
                    step.status = "completed"
                    step.result = {"deployed": True}
                else:
                    step.status = "failed"
                    step.error_message = "Service deployment failed"
                    return False
                
                # Wait between deployments
                rollout_delay = config.rollout_config.get('delay_seconds', 30)
                await asyncio.sleep(rollout_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Rolling deployment failed: {e}")
            return False
    
    async def _blue_green_deployment(self, deployment: Deployment, config: DeploymentConfig, environment: Environment) -> bool:
        """Execute blue-green deployment strategy"""
        try:
            logger.info(f"Executing blue-green deployment for {deployment.id}")
            
            provider_name = config.rollout_config.get('provider', 'kubernetes')
            provider = self.providers[provider_name]
            
            # Deploy to green environment
            green_env = Environment(
                id=f"{environment.id}_green",
                name=f"{environment.name}_green",
                environment_type=environment.environment_type,
                region=environment.region,
                namespace=f"{environment.namespace}-green",
                configuration=environment.configuration.copy(),
                resource_limits=environment.resource_limits.copy()
            )
            
            # Deploy all services to green environment
            for service_spec in config.services:
                step = DeploymentStep(
                    id=f"step_{len(deployment.steps)}",
                    deployment_id=deployment.id,
                    step_name=f"Deploy {service_spec.name} to green",
                    step_type="green_deployment",
                    parameters={"service_id": service_spec.id}
                )
                deployment.steps.append(step)
                
                step.started_at = datetime.utcnow()
                step.status = "running"
                
                success = await provider.deploy_service(service_spec, green_env)
                
                step.completed_at = datetime.utcnow()
                if success:
                    step.status = "completed"
                else:
                    step.status = "failed"
                    return False
            
            # Switch traffic to green (simulated)
            deployment.status = DeploymentStatus.PROMOTING
            logger.info(f"Switching traffic to green environment for {deployment.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Blue-green deployment failed: {e}")
            return False
    
    async def _canary_deployment(self, deployment: Deployment, config: DeploymentConfig, environment: Environment) -> bool:
        """Execute canary deployment strategy"""
        try:
            logger.info(f"Executing canary deployment for {deployment.id}")
            
            provider_name = config.rollout_config.get('provider', 'kubernetes')
            provider = self.providers[provider_name]
            
            canary_percentage = config.rollout_config.get('canary_percentage', 10)
            
            # Deploy canary version
            for service_spec in config.services:
                # Calculate canary replicas
                canary_replicas = max(1, int(service_spec.replicas * canary_percentage / 100))
                
                canary_spec = ServiceSpec(
                    id=f"{service_spec.id}_canary",
                    name=f"{service_spec.name}-canary",
                    service_type=service_spec.service_type,
                    image=service_spec.image,
                    tag=service_spec.tag,
                    port=service_spec.port,
                    replicas=canary_replicas,
                    resource_requirements=service_spec.resource_requirements,
                    environment_variables=service_spec.environment_variables,
                    health_check=service_spec.health_check
                )
                
                step = DeploymentStep(
                    id=f"step_{len(deployment.steps)}",
                    deployment_id=deployment.id,
                    step_name=f"Deploy {service_spec.name} canary ({canary_percentage}%)",
                    step_type="canary_deployment",
                    parameters={"service_id": service_spec.id, "canary_percentage": canary_percentage}
                )
                deployment.steps.append(step)
                
                step.started_at = datetime.utcnow()
                step.status = "running"
                
                success = await provider.deploy_service(canary_spec, environment)
                
                step.completed_at = datetime.utcnow()
                if success:
                    step.status = "completed"
                else:
                    step.status = "failed"
                    return False
            
            # Monitor canary for specified duration
            canary_duration = config.rollout_config.get('canary_duration_minutes', 10)
            logger.info(f"Monitoring canary for {canary_duration} minutes")
            await asyncio.sleep(canary_duration * 60)  # Convert to seconds
            
            # Promote canary if healthy
            deployment.status = DeploymentStatus.PROMOTING
            logger.info(f"Promoting canary to full deployment for {deployment.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Canary deployment failed: {e}")
            return False
    
    async def _recreate_deployment(self, deployment: Deployment, config: DeploymentConfig, environment: Environment) -> bool:
        """Execute recreate deployment strategy"""
        try:
            logger.info(f"Executing recreate deployment for {deployment.id}")
            
            provider_name = config.rollout_config.get('provider', 'kubernetes')
            provider = self.providers[provider_name]
            
            # Stop all current services first
            for service_spec in config.services:
                logger.info(f"Stopping service {service_spec.name}")
                # In real implementation, this would stop the existing service
            
            # Deploy new versions
            for service_spec in config.services:
                step = DeploymentStep(
                    id=f"step_{len(deployment.steps)}",
                    deployment_id=deployment.id,
                    step_name=f"Recreate {service_spec.name}",
                    step_type="recreate_deployment",
                    parameters={"service_id": service_spec.id}
                )
                deployment.steps.append(step)
                
                step.started_at = datetime.utcnow()
                step.status = "running"
                
                success = await provider.deploy_service(service_spec, environment)
                
                step.completed_at = datetime.utcnow()
                if success:
                    step.status = "completed"
                else:
                    step.status = "failed"
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Recreate deployment failed: {e}")
            return False
    
    async def _execute_hook(self, hook: str, deployment: Deployment, hook_type: str) -> bool:
        """Execute a deployment hook"""
        try:
            logger.info(f"Executing {hook_type} hook: {hook}")
            
            step = DeploymentStep(
                id=f"step_{len(deployment.steps)}",
                deployment_id=deployment.id,
                step_name=f"Execute {hook_type} hook",
                step_type="hook",
                parameters={"hook": hook, "hook_type": hook_type}
            )
            deployment.steps.append(step)
            
            step.started_at = datetime.utcnow()
            step.status = "running"
            
            # Simulate hook execution
            await asyncio.sleep(2)  # Simulate hook execution time
            
            step.completed_at = datetime.utcnow()
            step.status = "completed"
            step.result = {"executed": True}
            
            return True
            
        except Exception as e:
            logger.error(f"Hook execution failed: {e}")
            return False
    
    async def _execute_health_checks(self, deployment: Deployment, config: DeploymentConfig, environment: Environment) -> bool:
        """Execute health checks for deployed services"""
        try:
            logger.info(f"Executing health checks for deployment {deployment.id}")
            
            provider_name = config.rollout_config.get('provider', 'kubernetes')
            provider = self.providers[provider_name]
            
            for service_spec in config.services:
                step = DeploymentStep(
                    id=f"step_{len(deployment.steps)}",
                    deployment_id=deployment.id,
                    step_name=f"Health check {service_spec.name}",
                    step_type="health_check",
                    parameters={"service_id": service_spec.id}
                )
                deployment.steps.append(step)
                
                step.started_at = datetime.utcnow()
                step.status = "running"
                
                # Retry health checks
                max_attempts = 5
                for attempt in range(max_attempts):
                    if await provider.health_check_service(service_spec.id, environment):
                        step.status = "completed"
                        step.result = {"healthy": True, "attempts": attempt + 1}
                        break
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(10)  # Wait before retry
                
                step.completed_at = datetime.utcnow()
                if step.status != "completed":
                    step.status = "failed"
                    step.error_message = f"Health check failed after {max_attempts} attempts"
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health checks failed: {e}")
            return False
    
    async def rollback_deployment(self, deployment_id: str, target_deployment_id: Optional[str] = None) -> bool:
        """Rollback a deployment"""
        try:
            if deployment_id not in self.deployments:
                logger.error(f"Deployment not found: {deployment_id}")
                return False
            
            deployment = self.deployments[deployment_id]
            deployment.status = DeploymentStatus.ROLLING_BACK
            
            # Find target deployment
            if target_deployment_id:
                if target_deployment_id not in self.deployments:
                    logger.error(f"Target deployment not found: {target_deployment_id}")
                    return False
                target_deployment = self.deployments[target_deployment_id]
            else:
                # Find previous successful deployment
                target_deployment = None
                for dep_id, dep in self.deployments.items():
                    if (dep.environment_id == deployment.environment_id and 
                        dep.status == DeploymentStatus.COMPLETED and 
                        dep.created_at < deployment.created_at):
                        if not target_deployment or dep.created_at > target_deployment.created_at:
                            target_deployment = dep
                
                if not target_deployment:
                    logger.error("No previous successful deployment found for rollback")
                    return False
            
            # Create rollback plan
            rollback_plan = RollbackPlan(
                id=f"rollback_{int(time.time())}",
                deployment_id=deployment_id,
                target_deployment_id=target_deployment.id,
                strategy=deployment.strategy,
                steps=[
                    {"action": "restore_services", "target_version": target_deployment.version},
                    {"action": "verify_rollback", "health_checks": True}
                ],
                estimated_duration=300  # 5 minutes
            )
            
            self.rollback_plans[rollback_plan.id] = rollback_plan
            
            # Execute rollback
            config = self.deployment_configs[deployment.config_id]
            environment = self.environments[deployment.environment_id]
            provider_name = config.rollout_config.get('provider', 'kubernetes')
            provider = self.providers[provider_name]
            
            for service_spec in config.services:
                success = await provider.rollback_service(
                    service_spec.id, 
                    target_deployment.version, 
                    environment
                )
                if not success:
                    deployment.status = DeploymentStatus.FAILED
                    return False
            
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.completed_at = datetime.utcnow()
            
            logger.info(f"Deployment rollback completed: {deployment_id} -> {target_deployment.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback deployment: {e}")
            return False
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed deployment status"""
        try:
            if deployment_id not in self.deployments:
                return None
            
            deployment = self.deployments[deployment_id]
            
            # Calculate deployment duration
            duration = None
            if deployment.started_at:
                end_time = deployment.completed_at or datetime.utcnow()
                duration = (end_time - deployment.started_at).total_seconds()
            
            # Get step details
            steps_info = []
            for step in deployment.steps:
                step_duration = None
                if step.started_at:
                    step_end_time = step.completed_at or datetime.utcnow()
                    step_duration = (step_end_time - step.started_at).total_seconds()
                
                steps_info.append({
                    'id': step.id,
                    'name': step.step_name,
                    'type': step.step_type,
                    'status': step.status,
                    'duration_seconds': step_duration,
                    'retry_count': step.retry_count,
                    'error_message': step.error_message
                })
            
            return {
                'deployment_id': deployment.id,
                'config_id': deployment.config_id,
                'environment_id': deployment.environment_id,
                'status': deployment.status.value,
                'strategy': deployment.strategy.value,
                'version': deployment.version,
                'triggered_by': deployment.triggered_by,
                'started_at': deployment.started_at.isoformat() if deployment.started_at else None,
                'completed_at': deployment.completed_at.isoformat() if deployment.completed_at else None,
                'duration_seconds': duration,
                'total_steps': len(deployment.steps),
                'completed_steps': len([s for s in deployment.steps if s.status == "completed"]),
                'failed_steps': len([s for s in deployment.steps if s.status == "failed"]),
                'steps': steps_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return None
    
    def get_deployment_statistics(self) -> Dict[str, Any]:
        """Get deployment statistics"""
        try:
            total_deployments = len(self.deployments)
            
            # Status distribution
            status_counts = {}
            for status in DeploymentStatus:
                status_counts[status.value] = len([
                    d for d in self.deployments.values()
                    if d.status == status
                ])
            
            # Strategy distribution
            strategy_counts = {}
            for strategy in DeploymentStrategy:
                strategy_counts[strategy.value] = len([
                    d for d in self.deployments.values()
                    if d.strategy == strategy
                ])
            
            # Success rate
            completed_deployments = len([
                d for d in self.deployments.values()
                if d.status == DeploymentStatus.COMPLETED
            ])
            success_rate = (completed_deployments / total_deployments * 100) if total_deployments > 0 else 0
            
            # Average deployment time
            completed_with_duration = [
                d for d in self.deployments.values()
                if d.status == DeploymentStatus.COMPLETED and d.started_at and d.completed_at
            ]
            
            avg_duration = 0
            if completed_with_duration:
                total_duration = sum([
                    (d.completed_at - d.started_at).total_seconds()
                    for d in completed_with_duration
                ])
                avg_duration = total_duration / len(completed_with_duration)
            
            return {
                'total_deployments': total_deployments,
                'status_distribution': status_counts,
                'strategy_distribution': strategy_counts,
                'success_rate_percent': success_rate,
                'average_duration_seconds': avg_duration,
                'total_environments': len(self.environments),
                'total_configs': len(self.deployment_configs),
                'total_rollback_plans': len(self.rollback_plans)
            }
        except Exception as e:
            logger.error(f"Failed to get deployment statistics: {e}")
            return {}

# Global deployment manager instance
deployment_manager = DeploymentManager()

async def initialize_deployment_manager():
    """Initialize the deployment manager"""
    try:
        logger.info("Deployment manager initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize deployment manager: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_deployment_manager()
        
        # Example usage
        # Create deployment config
        config_data = {
            'name': 'EInvoice Service Deployment',
            'environment_id': 'staging_env',
            'strategy': 'rolling',
            'services': [
                {
                    'name': 'einvoice-api',
                    'service_type': 'api_service',
                    'image': 'taxpoynt/einvoice-api',
                    'tag': '1.2.3',
                    'port': 8080,
                    'replicas': 3,
                    'environment_variables': {
                        'DATABASE_URL': 'postgresql://...',
                        'REDIS_URL': 'redis://...'
                    }
                }
            ],
            'rollout_config': {
                'provider': 'kubernetes',
                'delay_seconds': 30
            }
        }
        
        config = await deployment_manager.create_deployment_config(config_data)
        if config:
            print(f"Created deployment config: {config.id}")
            
            # Deploy
            deployment = await deployment_manager.deploy(config.id, "admin", "v1.2.3")
            if deployment:
                print(f"Started deployment: {deployment.id}")
                
                # Get status
                status = await deployment_manager.get_deployment_status(deployment.id)
                print(f"Deployment status: {json.dumps(status, indent=2)}")
                
                # Get statistics
                stats = deployment_manager.get_deployment_statistics()
                print(f"Deployment statistics: {json.dumps(stats, indent=2)}")
    
    asyncio.run(main())