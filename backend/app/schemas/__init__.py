from app.schemas.user import User, UserCreate, UserUpdate
from app.schemas.client import Client, ClientCreate, ClientUpdate, ClientInDB
from app.schemas.integration import (
    Integration, IntegrationCreate, IntegrationUpdate, IntegrationInDB,
    IntegrationHistory, IntegrationHistoryCreate, IntegrationHistoryInDB,
    IntegrationTestResult
)

# Add new schemas here when created 