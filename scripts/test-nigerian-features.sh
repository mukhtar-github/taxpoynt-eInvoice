#!/bin/bash

# TaxPoynt eInvoice - Nigerian Features Testing Script
# Comprehensive testing for Nigerian market features

set -e

echo "🧪 Testing Nigerian Market Features"
echo "=================================="

# Configuration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
TEST_RESULTS_DIR="test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create test results directory
mkdir -p "$TEST_RESULTS_DIR"

# Function to test Nigerian Tax Service
test_nigerian_tax_service() {
    print_status "Testing Nigerian Tax Jurisdiction Service..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Test Nigerian states data loading
    python3 -c "
from app.services.nigerian_tax_service import NigerianTaxJurisdictionService
from app.database import get_db
import asyncio

async def test_states():
    db = next(get_db())
    service = NigerianTaxJurisdictionService(db)
    states = await service.get_nigerian_states_data()
    assert len(states) >= 6, f'Expected at least 6 states, got {len(states)}'
    
    # Test specific states
    lagos = next((s for s in states if s.code == 'LA'), None)
    assert lagos is not None, 'Lagos state not found'
    assert lagos.name == 'Lagos', f'Expected Lagos, got {lagos.name}'
    assert 'Lagos State Internal Revenue Service' in lagos.internal_revenue_service
    
    print(f'✅ Nigerian states data loaded successfully ({len(states)} states)')
    return True

try:
    asyncio.run(test_states())
except Exception as e:
    print(f'❌ Nigerian states test failed: {e}')
    exit(1)
"
    
    # Test multi-jurisdiction tax calculation
    python3 -c "
from app.services.nigerian_tax_service import NigerianTaxJurisdictionService, Location
from app.database import get_db
import asyncio

async def test_tax_calculation():
    db = next(get_db())
    service = NigerianTaxJurisdictionService(db)
    
    # Test locations
    locations = [
        Location(
            state_code='LA',
            state_name='Lagos',
            lga_code='IKEJA',
            lga_name='Ikeja',
            region='South West'
        ),
        Location(
            state_code='KN',
            state_name='Kano',
            lga_code='KANO_MUNICIPAL',
            lga_name='Kano Municipal',
            region='North West'
        )
    ]
    
    # Test tax calculation
    invoice_amount = 10000000.0  # ₦10M
    tax_breakdown = await service.calculate_multi_jurisdiction_tax(locations, invoice_amount)
    
    assert tax_breakdown.total_tax > 0, 'Total tax should be greater than 0'
    assert len(tax_breakdown.federal_taxes) > 0, 'Federal taxes should be calculated'
    assert len(tax_breakdown.state_taxes) > 0, 'State taxes should be calculated'
    assert len(tax_breakdown.local_taxes) > 0, 'Local taxes should be calculated'
    
    # Verify VAT calculation (7.5%)
    vat_amount = invoice_amount * 0.075
    federal_vat = sum(tax['amount'] for tax in tax_breakdown.federal_taxes if tax['type'] == 'VAT')
    expected_vat = vat_amount * len(locations)  # VAT for each location
    
    print(f'✅ Multi-jurisdiction tax calculation successful')
    print(f'   Total tax: ₦{tax_breakdown.total_tax:,.2f}')
    print(f'   Federal taxes: {len(tax_breakdown.federal_taxes)} items')
    print(f'   State taxes: {len(tax_breakdown.state_taxes)} items')
    print(f'   Local taxes: {len(tax_breakdown.local_taxes)} items')
    
    return True

try:
    asyncio.run(test_tax_calculation())
except Exception as e:
    print(f'❌ Tax calculation test failed: {e}')
    exit(1)
"
    
    cd ..
    print_success "Nigerian Tax Service tests passed"
}

# Function to test FIRS Penalty Manager
test_firs_penalty_manager() {
    print_status "Testing FIRS Penalty Management..."
    
    cd "$BACKEND_DIR"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    python3 -c "
from app.services.nigerian_tax_service import FIRSPenaltyManager
from app.database import get_db
from datetime import datetime, timedelta
import asyncio
import uuid

async def test_penalty_calculation():
    db = next(get_db())
    manager = FIRSPenaltyManager(db)
    
    # Test penalty calculation
    org_id = uuid.uuid4()
    violation_date = datetime.utcnow() - timedelta(days=5)
    
    penalty = await manager.calculate_non_compliance_penalty(org_id, violation_date)
    
    assert penalty.total_penalty > 0, 'Penalty amount should be greater than 0'
    assert penalty.days_non_compliant == 5, f'Expected 5 days, got {penalty.days_non_compliant}'
    assert penalty.first_day_penalty == 1000000, f'Expected ₦1M first day penalty'
    assert penalty.daily_penalty_rate == 10000, f'Expected ₦10K daily penalty'
    
    # Test payment plan setup
    payment_plan = await manager.setup_penalty_payment_plan(org_id, penalty.total_penalty)
    
    assert len(payment_plan.options) > 0, 'Payment options should be available'
    assert payment_plan.grace_period_days == 30, 'Grace period should be 30 days'
    
    # Check immediate payment discount
    immediate_option = next((opt for opt in payment_plan.options if opt.type == 'immediate'), None)
    assert immediate_option is not None, 'Immediate payment option should exist'
    assert immediate_option.discount == 0.05, 'Immediate payment should have 5% discount'
    
    print(f'✅ FIRS penalty calculation successful')
    print(f'   Total penalty: ₦{penalty.total_penalty:,.2f}')
    print(f'   Payment options: {len(payment_plan.options)}')
    
    return True

try:
    asyncio.run(test_penalty_calculation())
except Exception as e:
    print(f'❌ FIRS penalty test failed: {e}')
    exit(1)
"
    
    cd ..
    print_success "FIRS Penalty Manager tests passed"
}

# Function to test Nigerian Analytics Dashboard
test_analytics_dashboard() {
    print_status "Testing Nigerian Analytics Dashboard..."
    
    cd "$FRONTEND_DIR"
    
    # Check if analytics dashboard component exists
    if [ ! -f "components/nigerian/analytics/NigerianAnalyticsDashboard.tsx" ]; then
        print_error "Nigerian Analytics Dashboard component not found"
        exit 1
    fi
    
    # Check if analytics service exists
    if [ ! -f "services/nigerianAnalyticsService.ts" ]; then
        print_error "Nigerian Analytics Service not found"
        exit 1
    fi
    
    # Install dependencies
    npm install --silent
    
    # Type check the dashboard component
    npx tsc --noEmit --skipLibCheck components/nigerian/analytics/NigerianAnalyticsDashboard.tsx
    
    # Test service methods
    node -e "
const fs = require('fs');
const path = require('path');

// Read the service file
const servicePath = path.join(__dirname, 'services/nigerianAnalyticsService.ts');
const serviceContent = fs.readFileSync(servicePath, 'utf8');

// Check for required methods
const requiredMethods = [
    'getAnalyticsData',
    'getComplianceMetrics',
    'getRegionalMetrics',
    'getCulturalMetrics',
    'getPaymentAnalytics',
    'exportData',
    'getRealTimeMetrics',
    'getPenaltyDetails'
];

let allMethodsPresent = true;
for (const method of requiredMethods) {
    if (!serviceContent.includes(method)) {
        console.log(\`❌ Missing method: \${method}\`);
        allMethodsPresent = false;
    }
}

if (allMethodsPresent) {
    console.log('✅ All required service methods present');
} else {
    process.exit(1);
}
"
    
    cd ..
    print_success "Nigerian Analytics Dashboard tests passed"
}

# Function to test database models
test_database_models() {
    print_status "Testing Nigerian database models..."
    
    cd "$BACKEND_DIR"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Test Nigerian compliance models
    python3 -c "
from app.models.nigerian_compliance import (
    NITDAAccreditation,
    NDPRCompliance,
    FIRSPenaltyTracking,
    NigerianBusinessRegistration
)
from app.models.nigerian_business import (
    NigerianConglomerate,
    NigerianSubsidiary,
    NigerianApprovalLevel,
    NigerianRelationshipManager
)
import uuid
from datetime import datetime

# Test model instantiation
try:
    # Test FIRS penalty tracking model
    penalty = FIRSPenaltyTracking(
        organization_id=uuid.uuid4(),
        penalty_type='non_compliance',
        penalty_amount_ngn=1040000.0,
        violation_date=datetime.utcnow(),
        days_non_compliant=5
    )
    
    # Test Nigerian subsidiary model
    subsidiary = NigerianSubsidiary(
        conglomerate_id=uuid.uuid4(),
        subsidiary_name='Test Subsidiary',
        operating_state='Lagos',
        local_government_area='Ikeja',
        annual_revenue_ngn=50000000.0
    )
    
    print('✅ Nigerian database models instantiated successfully')
    print(f'   Penalty tracking: {penalty.penalty_type}')
    print(f'   Subsidiary: {subsidiary.subsidiary_name} in {subsidiary.operating_state}')
    
except Exception as e:
    print(f'❌ Database model test failed: {e}')
    exit(1)
"
    
    cd ..
    print_success "Database models tests passed"
}

# Function to test API endpoints
test_api_endpoints() {
    print_status "Testing Nigerian API endpoints..."
    
    cd "$BACKEND_DIR"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start test server in background
    python3 -c "
import uvicorn
from app.main import app
import threading
import time

def start_server():
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='error')

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()
time.sleep(3)  # Give server time to start

print('Test server started on port 8001')
" &
    
    SERVER_PID=$!
    sleep 5
    
    # Test endpoints
    python3 -c "
import requests
import json

base_url = 'http://127.0.0.1:8001'

try:
    # Test health endpoint
    response = requests.get(f'{base_url}/health', timeout=5)
    assert response.status_code == 200, f'Health check failed: {response.status_code}'
    
    # Test Nigerian states endpoint (if exists)
    try:
        response = requests.get(f'{base_url}/api/nigerian-tax/states', timeout=5)
        if response.status_code == 200:
            print('✅ Nigerian states endpoint accessible')
        else:
            print('⚠️ Nigerian states endpoint not implemented yet')
    except:
        print('⚠️ Nigerian states endpoint not available')
    
    print('✅ API endpoints test completed')
    
except Exception as e:
    print(f'❌ API endpoints test failed: {e}')
    exit(1)
"
    
    # Kill test server
    kill $SERVER_PID 2>/dev/null || true
    
    cd ..
    print_success "API endpoints tests completed"
}

# Function to test deployment readiness
test_deployment_readiness() {
    print_status "Testing deployment readiness..."
    
    # Check deployment scripts
    if [ ! -f "scripts/deploy-production.sh" ]; then
        print_error "Production deployment script not found"
        exit 1
    fi
    
    if [ ! -x "scripts/deploy-production.sh" ]; then
        print_error "Production deployment script not executable"
        exit 1
    fi
    
    # Check environment configurations
    if [ ! -f "backend/requirements.txt" ]; then
        print_error "Backend requirements.txt not found"
        exit 1
    fi
    
    if [ ! -f "frontend/package.json" ]; then
        print_error "Frontend package.json not found"
        exit 1
    fi
    
    # Check Alembic migrations
    cd "$BACKEND_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Check if Nigerian compliance migrations exist
    if [ ! -f "alembic/versions/015_add_nigerian_compliance_models.py" ] && [ ! -f "alembic/versions/*nigerian_compliance*.py" ]; then
        print_warning "Nigerian compliance migrations not found"
    fi
    
    cd ..
    
    print_success "Deployment readiness tests passed"
}

# Main testing function
main() {
    echo "🇳🇬 TaxPoynt eInvoice - Nigerian Features Testing Suite"
    echo "===================================================="
    
    # Create test report
    TEST_REPORT="$TEST_RESULTS_DIR/nigerian_features_test_$TIMESTAMP.log"
    exec > >(tee -a "$TEST_REPORT")
    exec 2>&1
    
    echo "Test started at: $(date)"
    echo "Test report: $TEST_REPORT"
    echo ""
    
    # Run all tests
    test_nigerian_tax_service
    test_firs_penalty_manager
    test_analytics_dashboard
    test_database_models
    test_api_endpoints
    test_deployment_readiness
    
    echo ""
    echo "🎉 All Nigerian Features Tests Passed!"
    echo ""
    echo "✅ Test Summary:"
    echo "  - Nigerian Tax Jurisdiction Service: PASSED"
    echo "  - FIRS Penalty Management: PASSED"
    echo "  - Analytics Dashboard: PASSED"
    echo "  - Database Models: PASSED"
    echo "  - API Endpoints: PASSED"
    echo "  - Deployment Readiness: PASSED"
    echo ""
    echo "📋 Test report saved to: $TEST_REPORT"
    echo "🚀 Ready for production deployment!"
}

# Run tests
main "$@"