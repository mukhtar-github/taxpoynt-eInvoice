# Import Migration & Codebase Cleanup Strategy

## 🎯 **Strategic Approach for Import Cleanup**

### **Phase 1: Immediate Triage (Next 1-2 Days)**
```
Priority 1: Critical Path (DONE ✅)
├── Core services (firs_si, firs_app, firs_core)
├── API routes and routers
└── Main application entry points

Priority 2: Development Blockers (NEXT)
├── Test files that break CI/CD
├── Database initialization scripts
├── Authentication/authorization modules
└── Background workers/tasks

Priority 3: Nice-to-Have (LATER)
├── Utility scripts
├── Development tools
├── Documentation generators
└── Legacy test files
```

### **Phase 2: Systematic Cleanup Plan**

**Create a Migration Tracking Document:**
```markdown
## Import Migration Status
- [x] Core Services (22/22) ✅ COMPLETE
- [ ] API Routes (15/18) 🔄 IN PROGRESS  
- [ ] Test Suites (12/45) ⏳ PENDING
- [ ] Utilities (5/25) ⏳ PENDING
- [ ] Background Jobs (2/8) ⏳ PENDING
```

## 🧹 **Codebase Cleanup Strategy**

### **1. Identify Redundant Files**
```bash
# Run this analysis periodically
find . -name "*.py" -type f | grep -E "(old|backup|deprecated|legacy)" 
find . -name "*.py" -type f -exec grep -l "# TODO: Remove" {} \;
```

### **2. Service Consolidation Rules**
- **Keep**: Files in new package structure (`firs_*`)
- **Deprecate**: Root-level service files that have been migrated
- **Archive**: Old implementation files (move to `archive/` folder)

### **3. File Lifecycle Management**
```python
# Add to migrated files:
"""
MIGRATION STATUS: ✅ MIGRATED to app.services.firs_si.xxx
DEPRECATION: This file will be removed in v2.0
USE: app.services.firs_si.xxx instead
"""
```

## 📋 **Ongoing Development Process**

### **1. Import Guidelines for New Development**
```python
# ✅ CORRECT - Use new structure
from app.services.firs_si.odoo_service import OdooService
from app.services.firs_app.transmission_service import TransmissionService
from app.services.firs_core.audit_service import AuditService

# ❌ AVOID - Old structure
from app.services.odoo_service import OdooService
from app.services.transmission_service import TransmissionService
```

### **2. Pre-Commit Hooks Setup**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-deprecated-imports
        name: Check for deprecated service imports
        entry: python scripts/check_deprecated_imports.py
        language: python
        files: \.py$
```

### **3. Memory/Documentation Strategy**
Update `CLAUDE.md` with:
```markdown
## Import Guidelines (CRITICAL)
- All new code MUST use firs_* package structure
- When modifying existing files, update imports to new structure
- Before adding new services, check if similar exists in packages
- Run `python scripts/validate_imports.py` before committing

## Package Structure Rules
- firs_si: Backend processing, ERP integration, IRN generation
- firs_app: Secure transmission, validation, crypto operations  
- firs_core: Shared services, audit, configuration
- firs_hybrid: Cross-role validation, unified monitoring
```

## 🔄 **Weekly Maintenance Process**

### **Every Sprint/Week:**
1. **Import Health Check** (5 min)
   ```bash
   python scripts/find_broken_imports.py --report
   ```

2. **Redundant File Review** (10 min)
   - Identify files not imported anywhere
   - Check for duplicate functionality
   - Archive old implementations

3. **New Code Review** (ongoing)
   - Ensure new imports follow structure
   - Consolidate similar services
   - Update documentation

## ⚡ **Immediate Action Plan**

### **Today/Tomorrow:**
1. Create `scripts/import_health_check.py` to identify broken imports
2. Fix Priority 2 imports (tests, workers, auth)
3. Add deprecation warnings to old service files

### **This Week:**
1. Create automated import validation
2. Document new import guidelines
3. Archive redundant files to `archive/` folder

### **Ongoing:**
1. Fix 5-10 import issues per development session
2. Consolidate duplicate services when found
3. Remove archived files after 2 sprints

## 🎯 **Success Metrics**

- **Technical Debt**: Reduce import issues by 20% weekly
- **Code Quality**: No new imports using old structure
- **Maintainability**: Clear package boundaries maintained
- **Developer Experience**: Faster development with clear guidelines

## 💡 **Professional Recommendation**

**DO THIS NOW:**
- Fix tests and workers imports (Priority 2) this week
- Create the import validation script
- Update CLAUDE.md with import guidelines

**DON'T DO:**
- Try to fix all 80+ files at once (high risk, low value)
- Delete old files immediately (keep for rollback safety)
- Block new development for cleanup (balance progress vs perfection)

**LONG-TERM VISION:**
- Clean, maintainable package structure
- Clear service boundaries
- Minimal technical debt
- Fast development velocity

## 📊 **Migration Status Tracking**

### **Completed ✅**
- Core services restructuring (22 services)
- Primary API routes import fixes
- Main router import updates
- Critical path service imports

### **In Progress 🔄**
- Test file imports
- Background worker imports
- Utility script imports

### **Pending ⏳**
- Legacy test files
- Development tools
- Documentation generators
- Archive old redundant files

## 🔧 **Tools & Scripts**

### **Import Health Check Script** (To be created)
```python
# scripts/import_health_check.py
"""
Scan codebase for:
- Broken imports
- Old structure usage
- Redundant files
- Missing dependencies
"""
```

### **Validation Commands**
```bash
# Run before committing
python scripts/validate_imports.py

# Weekly health check
python scripts/find_broken_imports.py --report

# Find redundant files
python scripts/find_unused_files.py
```

---

**Last Updated**: December 2024  
**Status**: Phase 1 Complete, Phase 2 In Progress  
**Next Review**: Weekly during development sprints