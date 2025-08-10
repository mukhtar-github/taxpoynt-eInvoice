# TaxPoynt Localization System

## Overview

Multi-language support system for TaxPoynt Platform, designed to serve Nigerian markets with inclusive language options. Supports English as default and major Nigerian languages for enhanced user accessibility.

## Status: 🚧 **FOUNDATION READY** - Implementation Pending

The localization architecture and directory structure are complete and ready for translation implementation.

## Supported Languages

| Language | Code | Native Name | Status | Priority |
|----------|------|-------------|--------|----------|
| English | `en` | English | ✅ **Complete** | Primary |
| Nigerian Pidgin | `pcn` | Naija | 🚧 **Placeholder** | High |
| Yoruba | `yo` | Yorùbá | 🚧 **Placeholder** | High |
| Igbo | `ig` | Igbo | 🚧 **Placeholder** | High |
| Hausa | `ha` | Hausa | 🚧 **Placeholder** | High |

## Architecture

```
localization/
├── index.ts                 # ✅ Configuration and utilities
├── english/                 # ✅ Default language (complete)
│   ├── common.json         # UI elements, actions, status
│   └── roles.json          # Role-specific terminology
├── nigerian_pidgin/         # 🚧 Placeholder structure
│   └── common.json         # Ready for translation
├── yoruba/                  # 🚧 Placeholder structure  
│   └── common.json         # Ready for translation
├── igbo/                    # 🚧 Placeholder structure
│   └── common.json         # Ready for translation
├── hausa/                   # 🚧 Placeholder structure
│   └── common.json         # Ready for translation
└── README.md               # This documentation
```

## Translation Namespaces

The system is organized into logical namespaces for better management:

### Core Namespaces (Implemented)
- **`common`**: UI elements, actions, status messages
- **`roles`**: Role-specific terminology (SI, APP, Hybrid, Admin)

### Future Namespaces (Planned)
- **`navigation`**: Menu items, breadcrumbs, links
- **`forms`**: Field labels, validation messages, placeholders
- **`tables`**: Column headers, sorting, pagination
- **`charts`**: Chart labels, legends, tooltips
- **`auth`**: Login, registration, password flows
- **`compliance`**: Legal text, FIRS terminology, regulations
- **`billing`**: Payment terms, invoice descriptions
- **`errors`**: Error messages, troubleshooting
- **`success`**: Success messages, confirmations

## Role-Based Terminology

### System Integrator (SI)
- **Focus**: Technical integration terminology
- **Audience**: Developers, IT teams
- **Content**: API documentation, schema validation, data mapping

### Access Point Provider (APP)  
- **Focus**: Compliance and regulatory terminology
- **Audience**: Business owners, compliance officers
- **Content**: FIRS processes, tax compliance, transmission status

### Hybrid Users
- **Focus**: Unified terminology across roles
- **Audience**: Power users, consultants
- **Content**: Cross-role workflows, advanced analytics

### Administrators
- **Focus**: Platform management terminology
- **Audience**: TaxPoynt staff, system administrators
- **Content**: User management, system configuration, monitoring

## Cultural Adaptation Features

### Nigerian Market Focus
- **Currency**: Nigerian Naira (₦) formatting
- **Date/Time**: Nigerian timezone (WAT) and formats
- **Legal References**: Nigerian tax law, FIRS regulations
- **Cultural Context**: Local business practices and terminology

### Regional Language Support
- **Northern Nigeria**: Hausa language support
- **Western Nigeria**: Yoruba language support  
- **Eastern Nigeria**: Igbo language support
- **National**: Nigerian Pidgin for broader accessibility

## Implementation Plan

### Phase 1: Foundation (✅ Complete)
- [x] Directory structure created
- [x] Configuration system setup
- [x] English translations complete
- [x] Placeholder files for Nigerian languages
- [x] TypeScript interfaces defined

### Phase 2: Core Translation (🚧 Pending)
- [ ] Nigerian Pidgin translations
- [ ] Professional translators engagement
- [ ] Cultural review and adaptation
- [ ] Role-specific terminology validation

### Phase 3: Advanced Features (🚧 Pending) 
- [ ] React integration (Context, hooks)
- [ ] Dynamic language switching
- [ ] RTL support (future Arabic support)
- [ ] Pluralization rules
- [ ] Number and date formatting

### Phase 4: Quality Assurance (🚧 Pending)
- [ ] Native speaker reviews
- [ ] Cultural appropriateness validation
- [ ] User testing with target audiences
- [ ] Performance optimization

## Usage Examples (Future Implementation)

### Basic Translation
```tsx
import { useLocalization } from '../localization';

const MyComponent = () => {
  const { t } = useLocalization();
  
  return (
    <button>{t('actions.submit')}</button>
  );
};
```

### Role-Specific Translation
```tsx
const RoleSpecificContent = () => {
  const { t, currentRole } = useLocalization();
  
  return (
    <h1>{t(`roles.${currentRole}.dashboard`)}</h1>
  );
};
```

### Language Switching
```tsx
const LanguageSwitcher = () => {
  const { currentLanguage, setLanguage } = useLocalization();
  
  return (
    <select value={currentLanguage} onChange={(e) => setLanguage(e.target.value)}>
      <option value="en">English</option>
      <option value="pcn">Naija</option>
      <option value="yo">Yorùbá</option>
      <option value="ig">Igbo</option>
      <option value="ha">Hausa</option>
    </select>
  );
};
```

## Integration Requirements

### Dependencies (To be added)
```json
{
  "react-i18next": "^13.0.0",
  "i18next": "^23.0.0",
  "i18next-browser-languagedetector": "^7.0.0"
}
```

### TailwindCSS RTL Support (Future)
```js
module.exports = {
  plugins: [
    require('@tailwindcss/rtl')
  ]
}
```

## Translation Guidelines

### Key Principles
1. **Cultural Sensitivity**: Respect Nigerian cultural contexts
2. **Role Appropriateness**: Match terminology to user expertise level
3. **Consistency**: Use consistent terminology across interfaces
4. **Clarity**: Prioritize understanding over literal translation

### Nigerian Language Considerations
- **Pidgin**: Use widely understood terms, avoid complex grammar
- **Yoruba**: Include proper tone marks and diacritics where needed
- **Igbo**: Consider dialectal variations (Standard Igbo recommended)
- **Hausa**: Use standard orthography with proper markings

## Future Enhancements

### Planned Features
- **Voice Interface**: Audio pronunciation for accessibility
- **Cultural Themes**: Visual themes matching language/region
- **Contextual Help**: Language-specific help documentation
- **Compliance Docs**: Multi-language legal documentation
- **AI Translation**: Machine translation with human review

### Expansion Opportunities
- **French**: For West African expansion
- **Arabic**: For Northern Nigeria Muslim communities  
- **Portuguese**: For regional trade relationships

## Contributing

### Translation Workflow (Future)
1. **Professional Translation**: Engage certified translators
2. **Cultural Review**: Local cultural experts validate content
3. **Technical Review**: Ensure technical accuracy
4. **User Testing**: Test with native speakers
5. **Quality Assurance**: Final review and approval

### File Organization
- Each language has dedicated directory
- Namespaces organized by feature area
- JSON format for easy editing and version control
- Consistent key naming across all languages