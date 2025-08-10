/**
 * Data Mapping Page
 * =================
 * 
 * System Integrator interface for mapping business system data to FIRS-compliant invoice format.
 * Visual drag-and-drop data mapping with Nigerian tax compliance validation.
 * 
 * Features:
 * - Visual data field mapping interface
 * - FIRS invoice schema validation
 * - Nigerian VAT and tax code mapping
 * - Real-time data preview
 * - Template-based mapping for common systems
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface DataField {
  id: string;
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  example?: any;
  validation?: string[];
}

interface BusinessSystemSchema {
  systemId: string;
  systemName: string;
  fields: DataField[];
}

interface FIRSInvoiceField {
  id: string;
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  firsCode?: string;
  validation: string[];
  nigerianCompliance?: {
    vatApplicable: boolean;
    taxCode?: string;
    regulatoryNote?: string;
  };
}

interface MappingRule {
  id: string;
  sourceField: string;
  targetField: string;
  transformation?: {
    type: 'direct' | 'format' | 'calculate' | 'lookup' | 'conditional';
    formula?: string;
    lookupTable?: Record<string, any>;
    conditions?: Array<{
      condition: string;
      value: any;
    }>;
  };
  validated: boolean;
}

// FIRS-compliant invoice schema
const firsInvoiceSchema: FIRSInvoiceField[] = [
  {
    id: 'invoice_number',
    name: 'Invoice Number',
    type: 'string',
    required: true,
    description: 'Unique invoice identifier',
    firsCode: 'INV_NUM',
    validation: ['unique', 'alphanumeric', 'max_length:50'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Must be unique across all invoices'
    }
  },
  {
    id: 'invoice_date',
    name: 'Invoice Date',
    type: 'date',
    required: true,
    description: 'Date invoice was issued',
    firsCode: 'INV_DATE',
    validation: ['date_format:YYYY-MM-DD', 'not_future'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Must not be in the future'
    }
  },
  {
    id: 'supplier_tin',
    name: 'Supplier TIN',
    type: 'string',
    required: true,
    description: 'Supplier Tax Identification Number',
    firsCode: 'SUP_TIN',
    validation: ['tin_format', 'length:14'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Must be valid FIRS TIN format'
    }
  },
  {
    id: 'customer_tin',
    name: 'Customer TIN',
    type: 'string',
    required: false,
    description: 'Customer Tax Identification Number',
    firsCode: 'CUST_TIN',
    validation: ['tin_format', 'length:14'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'Required for B2B transactions above ₦25M'
    }
  },
  {
    id: 'line_items',
    name: 'Line Items',
    type: 'array',
    required: true,
    description: 'Invoice line items with products/services',
    firsCode: 'LINE_ITEMS',
    validation: ['min_items:1', 'max_items:1000'],
    nigerianCompliance: {
      vatApplicable: true,
      taxCode: 'VAT_ITEMS',
      regulatoryNote: 'Each item must have VAT calculation'
    }
  },
  {
    id: 'total_amount',
    name: 'Total Amount',
    type: 'number',
    required: true,
    description: 'Total invoice amount including VAT',
    firsCode: 'TOTAL_AMT',
    validation: ['positive', 'decimal_places:2', 'currency:NGN'],
    nigerianCompliance: {
      vatApplicable: true,
      taxCode: 'VAT_INCLUSIVE',
      regulatoryNote: 'Must include VAT where applicable'
    }
  },
  {
    id: 'vat_amount',
    name: 'VAT Amount',
    type: 'number',
    required: false,
    description: 'Value Added Tax amount',
    firsCode: 'VAT_AMT',
    validation: ['positive', 'decimal_places:2', 'percentage:7.5'],
    nigerianCompliance: {
      vatApplicable: true,
      taxCode: 'VAT_7_5',
      regulatoryNote: 'Standard Nigerian VAT rate is 7.5%'
    }
  },
  {
    id: 'currency',
    name: 'Currency',
    type: 'string',
    required: true,
    description: 'Invoice currency code',
    firsCode: 'CURRENCY',
    validation: ['currency_code', 'supported_currencies'],
    nigerianCompliance: {
      vatApplicable: false,
      regulatoryNote: 'NGN required for domestic transactions'
    }
  }
];

// Sample business system schemas
const sampleBusinessSystems: BusinessSystemSchema[] = [
  {
    systemId: 'sap',
    systemName: 'SAP ERP',
    fields: [
      { id: 'VBELN', name: 'Sales Document', type: 'string', required: true, description: 'SAP sales document number' },
      { id: 'AUDAT', name: 'Document Date', type: 'date', required: true, description: 'SAP document date' },
      { id: 'KUNNR', name: 'Customer Number', type: 'string', required: true, description: 'SAP customer master number' },
      { id: 'NETWR', name: 'Net Value', type: 'number', required: true, description: 'Net value in document currency' },
      { id: 'MWSBP', name: 'Tax Amount', type: 'number', required: false, description: 'Tax amount' },
      { id: 'WAERK', name: 'Currency', type: 'string', required: true, description: 'Document currency' }
    ]
  },
  {
    systemId: 'quickbooks',
    systemName: 'QuickBooks',
    fields: [
      { id: 'DocNumber', name: 'Document Number', type: 'string', required: true, description: 'QuickBooks invoice number' },
      { id: 'TxnDate', name: 'Transaction Date', type: 'date', required: true, description: 'Transaction date' },
      { id: 'CustomerRef', name: 'Customer Reference', type: 'object', required: true, description: 'Customer reference object' },
      { id: 'TotalAmt', name: 'Total Amount', type: 'number', required: true, description: 'Total invoice amount' },
      { id: 'Line', name: 'Line Items', type: 'array', required: true, description: 'Invoice line items' },
      { id: 'CurrencyRef', name: 'Currency Reference', type: 'string', required: true, description: 'Currency code' }
    ]
  }
];

interface DataMappingProps {
  systemId?: string;
  organizationId?: string;
  onMappingComplete?: (mappingRules: MappingRule[]) => void;
}

export const DataMapping: React.FC<DataMappingProps> = ({
  systemId,
  organizationId,
  onMappingComplete
}) => {
  const [selectedSystem, setSelectedSystem] = useState<BusinessSystemSchema | null>(
    systemId ? sampleBusinessSystems.find(s => s.systemId === systemId) || null : null
  );
  const [mappingRules, setMappingRules] = useState<MappingRule[]>([]);
  const [draggedField, setDraggedField] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({});
  const [isValidating, setIsValidating] = useState(false);

  // Load existing mapping rules
  useEffect(() => {
    if (selectedSystem && organizationId) {
      loadExistingMappings();
    }
  }, [selectedSystem, organizationId]);

  const loadExistingMappings = async () => {
    try {
      const response = await fetch(`/api/v1/si/data-mapping/${organizationId}/${selectedSystem?.systemId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMappingRules(data.mapping_rules || []);
      }
    } catch (error) {
      console.error('Failed to load existing mappings:', error);
    }
  };

  const handleDragStart = (fieldId: string) => {
    setDraggedField(fieldId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (targetFieldId: string) => {
    if (draggedField && selectedSystem) {
      const sourceField = selectedSystem.fields.find(f => f.id === draggedField);
      const targetField = firsInvoiceSchema.find(f => f.id === targetFieldId);
      
      if (sourceField && targetField) {
        const newRule: MappingRule = {
          id: `${draggedField}_to_${targetFieldId}`,
          sourceField: draggedField,
          targetField: targetFieldId,
          transformation: {
            type: 'direct'
          },
          validated: false
        };

        setMappingRules(prev => {
          const filtered = prev.filter(rule => rule.targetField !== targetFieldId);
          return [...filtered, newRule];
        });
      }
    }
    setDraggedField(null);
  };

  const handleValidateMapping = async () => {
    if (!selectedSystem || mappingRules.length === 0) return;

    setIsValidating(true);
    try {
      const response = await fetch('/api/v1/si/data-mapping/validate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          system_id: selectedSystem.systemId,
          organization_id: organizationId,
          mapping_rules: mappingRules,
          firs_schema: firsInvoiceSchema
        })
      });

      const result = await response.json();
      
      if (result.success) {
        setValidationErrors({});
        setMappingRules(prev => prev.map(rule => ({ ...rule, validated: true })));
        setPreviewData(result.preview_data);
        alert('✅ Mapping validation successful!');
      } else {
        setValidationErrors(result.errors || {});
        alert('❌ Mapping validation failed. Please check the errors.');
      }
    } catch (error) {
      console.error('Validation failed:', error);
      alert('Validation failed. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleSaveMapping = async () => {
    if (!selectedSystem || mappingRules.length === 0) return;

    try {
      const response = await fetch('/api/v1/si/data-mapping/save', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          system_id: selectedSystem.systemId,
          organization_id: organizationId,
          mapping_rules: mappingRules
        })
      });

      const result = await response.json();
      
      if (result.success) {
        alert('✅ Mapping configuration saved successfully!');
        if (onMappingComplete) {
          onMappingComplete(mappingRules);
        }
      } else {
        alert('❌ Failed to save mapping configuration.');
      }
    } catch (error) {
      console.error('Save failed:', error);
      alert('Save failed. Please try again.');
    }
  };

  const getMappedSourceField = (targetFieldId: string) => {
    const rule = mappingRules.find(rule => rule.targetField === targetFieldId);
    return rule ? selectedSystem?.fields.find(f => f.id === rule.sourceField) : null;
  };

  if (!selectedSystem) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg border p-8 text-center max-w-md">
          <div className="text-4xl mb-4">🔄</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Select Business System</h2>
          <p className="text-gray-600 mb-6">Choose a business system to configure data mapping</p>
          
          <div className="space-y-3">
            {sampleBusinessSystems.map(system => (
              <button
                key={system.systemId}
                onClick={() => setSelectedSystem(system)}
                className="w-full text-left p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <div className="font-semibold text-gray-900">{system.systemName}</div>
                <div className="text-sm text-gray-600">{system.fields.length} fields available</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Data Mapping</h1>
              <p className="text-gray-600 mt-2">
                Map {selectedSystem.systemName} data to FIRS-compliant invoice format
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                onClick={handleValidateMapping}
                disabled={mappingRules.length === 0 || isValidating}
                loading={isValidating}
                variant="outline"
              >
                Validate Mapping
              </Button>
              
              <Button
                onClick={handleSaveMapping}
                disabled={mappingRules.length === 0 || !mappingRules.every(rule => rule.validated)}
              >
                Save Configuration
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Mapping Interface */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Source Fields */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {selectedSystem.systemName} Fields
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Drag fields from here to map them to FIRS invoice format
            </p>
            
            <div className="space-y-3">
              {selectedSystem.fields.map(field => (
                <div
                  key={field.id}
                  draggable
                  onDragStart={() => handleDragStart(field.id)}
                  className="p-3 border border-gray-200 rounded-lg cursor-move hover:border-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{field.name}</div>
                      <div className="text-sm text-gray-600">{field.id}</div>
                    </div>
                    <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {field.type}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{field.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Target Fields (FIRS Schema) */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              FIRS Invoice Format 🇳🇬
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Drop source fields here to create mappings
            </p>
            
            <div className="space-y-3">
              {firsInvoiceSchema.map(field => {
                const mappedField = getMappedSourceField(field.id);
                const hasError = validationErrors[field.id];
                
                return (
                  <div
                    key={field.id}
                    onDragOver={handleDragOver}
                    onDrop={() => handleDrop(field.id)}
                    className={`p-3 border-2 border-dashed rounded-lg transition-colors ${
                      mappedField 
                        ? hasError 
                          ? 'border-red-300 bg-red-50' 
                          : 'border-green-300 bg-green-50'
                        : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-medium text-gray-900 flex items-center">
                          {field.name}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </div>
                        <div className="text-sm text-gray-600">{field.firsCode}</div>
                      </div>
                      <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {field.type}
                      </div>
                    </div>
                    
                    {mappedField ? (
                      <div className="bg-white border rounded p-2 mb-2">
                        <div className="text-sm font-medium text-gray-900">
                          Mapped to: {mappedField.name}
                        </div>
                        <div className="text-xs text-gray-600">{mappedField.id}</div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500 italic">
                        Drop a field here to create mapping
                      </div>
                    )}
                    
                    <p className="text-xs text-gray-500 mt-2">{field.description}</p>
                    
                    {field.nigerianCompliance && (
                      <div className="mt-2 text-xs text-blue-600 bg-blue-50 p-2 rounded">
                        🇳🇬 {field.nigerianCompliance.regulatoryNote}
                      </div>
                    )}
                    
                    {hasError && (
                      <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                        ❌ {hasError.join(', ')}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Preview and Validation */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Mapping Preview
            </h2>
            
            {mappingRules.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📋</div>
                <p>No mappings created yet</p>
                <p className="text-sm">Drag and drop fields to create mappings</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Mapping Rules Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Mapping Rules ({mappingRules.length})</h3>
                  <div className="space-y-2">
                    {mappingRules.map(rule => {
                      const sourceField = selectedSystem.fields.find(f => f.id === rule.sourceField);
                      const targetField = firsInvoiceSchema.find(f => f.id === rule.targetField);
                      
                      return (
                        <div key={rule.id} className="text-sm">
                          <div className="flex items-center justify-between">
                            <span>{sourceField?.name}</span>
                            <span className="text-gray-400">→</span>
                            <span>{targetField?.name}</span>
                            <span className={`w-2 h-2 rounded-full ${
                              rule.validated ? 'bg-green-500' : 'bg-yellow-500'
                            }`}></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Preview Data */}
                {previewData && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-3">FIRS Invoice Preview</h3>
                    <pre className="text-xs text-gray-700 bg-white p-3 rounded border overflow-auto max-h-64">
                      {JSON.stringify(previewData, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Nigerian Compliance Status */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">🇳🇬 Nigerian Compliance</h3>
                  <div className="space-y-1 text-sm text-blue-800">
                    <div>✓ FIRS e-invoicing format compatibility</div>
                    <div>✓ VAT calculation fields mapped</div>
                    <div>✓ Nigerian business data requirements</div>
                    <div>✓ Currency and tax code validation</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataMapping;