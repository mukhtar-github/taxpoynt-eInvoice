/**
 * Deal to Invoice Conversion Component
 * 
 * This component provides a comprehensive interface for converting CRM deals
 * into invoices, including batch processing, preview, and status tracking.
 */

import React, { useState, useEffect } from 'react';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import {
  FileText,
  DollarSign,
  User,
  Calendar,
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  Download,
  Send,
  Eye,
  Settings,
  Loader2,
  ArrowRight,
  Copy
} from 'lucide-react';

import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { FormField } from '@/components/ui/FormField';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { Alert } from '@/components/ui/Alert';
import { Modal } from '@/components/ui/Modal';
import { Tabs } from '@/components/ui/Tabs';
import { Switch } from '@/components/ui/Switch';
import { LegacySelect } from '@/components/ui/Select';

import CRMService from '@/services/crmService';
import {
  CRMDeal,
  CRMConnection,
  HubSpotDealInvoice,
  InvoiceGenerationState
} from '@/types/crm';

// ==================== VALIDATION SCHEMA ====================

const invoiceLineSchema = yup.object().shape({
  description: yup.string().required('Description is required'),
  quantity: yup.number().min(0.01, 'Quantity must be greater than 0').required('Quantity is required'),
  unit_price: yup.number().min(0.01, 'Unit price must be greater than 0').required('Unit price is required'),
  amount: yup.number().min(0.01, 'Amount must be greater than 0').required()
});

const invoiceFormSchema = yup.object().shape({
  invoice_number: yup.string().required('Invoice number is required'),
  invoice_date: yup.string().required('Invoice date is required'),
  due_date: yup.string().required('Due date is required'),
  currency: yup.string().required('Currency is required'),
  description: yup.string().optional(),
  customer: yup.object().shape({
    name: yup.string().required('Customer name is required'),
    email: yup.string().email('Invalid email format').optional(),
    phone: yup.string().optional(),
    address: yup.string().optional()
  }),
  line_items: yup.array().of(invoiceLineSchema).min(1, 'At least one line item is required')
});

type InvoiceFormData = yup.InferType<typeof invoiceFormSchema>;

// ==================== INTERFACES ====================

interface DealToInvoiceConverterProps {
  connection: CRMConnection;
  deals: CRMDeal[];
  onInvoiceGenerated?: (results: any[]) => void;
  onClose?: () => void;
  className?: string;
}

interface InvoicePreview {
  deal: CRMDeal;
  invoice: InvoiceFormData;
  status: 'draft' | 'validating' | 'ready' | 'generating' | 'success' | 'error';
  error?: string;
  invoice_id?: string;
}

// ==================== CONSTANTS ====================

const CURRENCIES = [
  { value: 'NGN', label: '₦ Nigerian Naira (NGN)' },
  { value: 'USD', label: '$ US Dollar (USD)' },
  { value: 'EUR', label: '€ Euro (EUR)' },
  { value: 'GBP', label: '£ British Pound (GBP)' }
];

const TAX_RATES = [
  { value: 0, label: 'No Tax (0%)' },
  { value: 7.5, label: 'VAT (7.5%)' },
  { value: 10, label: 'Service Tax (10%)' },
  { value: 15, label: 'Luxury Tax (15%)' }
];

// ==================== MAIN COMPONENT ====================

const DealToInvoiceConverter: React.FC<DealToInvoiceConverterProps> = ({
  connection,
  deals,
  onInvoiceGenerated,
  onClose,
  className = ''
}) => {
  // ==================== STATE MANAGEMENT ====================
  
  const [activeTab, setActiveTab] = useState('batch');
  const [invoicePreviews, setInvoicePreviews] = useState<InvoicePreview[]>([]);
  const [selectedDealIndex, setSelectedDealIndex] = useState(0);
  const [generationState, setGenerationState] = useState<InvoiceGenerationState>({
    isGenerating: false,
    generatedInvoices: []
  });
  const [batchSettings, setBatchSettings] = useState({
    auto_generate_numbers: true,
    default_currency: 'NGN',
    default_tax_rate: 7.5,
    due_days: 30,
    auto_submit_to_firs: false
  });

  // ==================== FORM SETUP ====================

  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    watch,
    setValue,
    reset
  } = useForm<InvoiceFormData>({
    resolver: yupResolver(invoiceFormSchema),
    mode: 'onChange'
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'line_items'
  });

  // ==================== INITIALIZATION ====================

  useEffect(() => {
    initializeInvoicePreviews();
  }, [deals]);

  const initializeInvoicePreviews = () => {
    const previews: InvoicePreview[] = deals.map((deal, index) => {
      const invoiceNumber = batchSettings.auto_generate_numbers 
        ? `HUB-${deal.external_deal_id}-${new Date().getFullYear()}`
        : '';

      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + batchSettings.due_days);

      const invoice: InvoiceFormData = {
        invoice_number: invoiceNumber,
        invoice_date: new Date().toISOString().split('T')[0],
        due_date: dueDate.toISOString().split('T')[0],
        currency: batchSettings.default_currency,
        description: deal.deal_title || `Services for Deal ${deal.external_deal_id}`,
        customer: {
          name: deal.customer_data?.name || deal.customer_data?.company || 'Unknown Customer',
          email: deal.customer_data?.email || '',
          phone: deal.customer_data?.phone || '',
          address: deal.customer_data?.address || ''
        },
        line_items: [
          {
            description: deal.deal_title || 'Professional Services',
            quantity: 1,
            unit_price: deal.deal_amount || 0,
            amount: deal.deal_amount || 0
          }
        ]
      };

      return {
        deal,
        invoice,
        status: 'draft' as const
      };
    });

    setInvoicePreviews(previews);
    
    if (previews.length > 0) {
      loadInvoiceToForm(previews[0].invoice);
    }
  };

  const loadInvoiceToForm = (invoice: InvoiceFormData) => {
    reset(invoice);
  };

  // ==================== INVOICE GENERATION ====================

  const generateSingleInvoice = async (dealIndex: number) => {
    try {
      const preview = invoicePreviews[dealIndex];
      updatePreviewStatus(dealIndex, 'generating');

      const result = await CRMService.processDeal(
        connection.id,
        preview.deal.id,
        { action: 'generate_invoice' }
      );

      updatePreviewStatus(dealIndex, 'success', undefined, result.invoice_id);

    } catch (error: any) {
      console.error('Error generating invoice:', error);
      updatePreviewStatus(dealIndex, 'error', error.message);
    }
  };

  const generateBatchInvoices = async () => {
    try {
      setGenerationState(prev => ({ ...prev, isGenerating: true }));

      const dealIds = deals.map(deal => deal.id);
      const results = await CRMService.batchGenerateInvoices(connection.id, dealIds);

      const updatedPreviews = [...invoicePreviews];
      const generatedInvoices: any[] = [];

      results.forEach((result, index) => {
        if (result.success) {
          updatedPreviews[index].status = 'success';
          updatedPreviews[index].invoice_id = result.invoice_id;
          generatedInvoices.push({
            deal_id: result.deal_id,
            invoice_id: result.invoice_id,
            status: 'success'
          });
        } else {
          updatedPreviews[index].status = 'error';
          updatedPreviews[index].error = result.error;
          generatedInvoices.push({
            deal_id: result.deal_id,
            status: 'error',
            error: result.error
          });
        }
      });

      setInvoicePreviews(updatedPreviews);
      setGenerationState(prev => ({
        ...prev,
        generatedInvoices
      }));

      onInvoiceGenerated?.(results);

    } catch (error: any) {
      console.error('Error generating batch invoices:', error);
      setGenerationState(prev => ({
        ...prev,
        error: error.message
      }));
    } finally {
      setGenerationState(prev => ({ ...prev, isGenerating: false }));
    }
  };

  const updatePreviewStatus = (
    index: number, 
    status: InvoicePreview['status'], 
    error?: string, 
    invoiceId?: string
  ) => {
    setInvoicePreviews(prev => prev.map((preview, i) => 
      i === index 
        ? { ...preview, status, error, invoice_id: invoiceId }
        : preview
    ));
  };

  // ==================== FORM HANDLERS ====================

  const onSubmit = (data: InvoiceFormData) => {
    const updatedPreviews = [...invoicePreviews];
    updatedPreviews[selectedDealIndex].invoice = data;
    updatedPreviews[selectedDealIndex].status = 'ready';
    setInvoicePreviews(updatedPreviews);
  };

  const addLineItem = () => {
    append({
      description: '',
      quantity: 1,
      unit_price: 0,
      amount: 0
    });
  };

  const updateLineItemAmount = (index: number) => {
    const quantity = watch(`line_items.${index}.quantity`);
    const unitPrice = watch(`line_items.${index}.unit_price`);
    const amount = quantity * unitPrice;
    setValue(`line_items.${index}.amount`, amount);
  };

  // ==================== RENDER HELPERS ====================

  const renderBatchOverview = () => {
    const statusCounts = invoicePreviews.reduce((acc, preview) => {
      acc[preview.status] = (acc[preview.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <Card className="mb-6">
        <CardHeader title="Batch Conversion Overview" />
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{deals.length}</div>
              <div className="text-sm text-gray-600">Total Deals</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{statusCounts.success || 0}</div>
              <div className="text-sm text-gray-600">Generated</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{statusCounts.error || 0}</div>
              <div className="text-sm text-gray-600">Failed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{statusCounts.draft + statusCounts.ready || 0}</div>
              <div className="text-sm text-gray-600">Pending</div>
            </div>
          </div>

          <div className="space-y-3">
            {invoicePreviews.map((preview, index) => (
              <div key={preview.deal.id} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium">{preview.deal.deal_title || 'Untitled Deal'}</p>
                    <p className="text-sm text-gray-600">
                      {CRMService.formatCurrency(preview.deal.deal_amount || 0)}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <Badge 
                    variant={
                      preview.status === 'success' ? 'success' :
                      preview.status === 'error' ? 'error' :
                      preview.status === 'generating' ? 'warning' : 'secondary'
                    }
                  >
                    {preview.status === 'success' && <CheckCircle className="w-3 h-3 mr-1" />}
                    {preview.status === 'error' && <AlertCircle className="w-3 h-3 mr-1" />}
                    {preview.status === 'generating' && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                    {preview.status}
                  </Badge>

                  {preview.status === 'success' && preview.invoice_id && (
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4 mr-1" />
                      View
                    </Button>
                  )}

                  {preview.status === 'draft' && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => generateSingleInvoice(index)}
                    >
                      Generate
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderInvoiceEditor = () => {
    const currentDeal = deals[selectedDealIndex];
    
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader 
            title="Deal Information"
            subtitle={`Converting: ${currentDeal?.deal_title || 'Untitled Deal'}`}
          />
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Deal Amount:</span>
                <p className="font-medium">{CRMService.formatCurrency(currentDeal?.deal_amount || 0)}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Deal Stage:</span>
                <p className="font-medium">{CRMService.formatDealStage(currentDeal?.deal_stage || '')}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader title="Invoice Details" />
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  label="Invoice Number"
                  error={errors.invoice_number?.message}
                  required
                >
                  <Controller
                    name="invoice_number"
                    control={control}
                    render={({ field }) => (
                      <Input {...field} placeholder="INV-001" />
                    )}
                  />
                </FormField>

                <FormField
                  label="Currency"
                  error={errors.currency?.message}
                  required
                >
                  <Controller
                    name="currency"
                    control={control}
                    render={({ field }) => (
                      <LegacySelect {...field} options={CURRENCIES} />
                    )}
                  />
                </FormField>

                <FormField
                  label="Invoice Date"
                  error={errors.invoice_date?.message}
                  required
                >
                  <Controller
                    name="invoice_date"
                    control={control}
                    render={({ field }) => (
                      <Input {...field} type="date" />
                    )}
                  />
                </FormField>

                <FormField
                  label="Due Date"
                  error={errors.due_date?.message}
                  required
                >
                  <Controller
                    name="due_date"
                    control={control}
                    render={({ field }) => (
                      <Input {...field} type="date" />
                    )}
                  />
                </FormField>
              </div>

              <FormField
                label="Description"
                error={errors.description?.message}
              >
                <Controller
                  name="description"
                  control={control}
                  render={({ field }) => (
                    <Textarea {...field} placeholder="Invoice description" rows={3} />
                  )}
                />
              </FormField>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title="Customer Information" />
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  label="Customer Name"
                  error={errors.customer?.name?.message}
                  required
                >
                  <Controller
                    name="customer.name"
                    control={control}
                    render={({ field }) => (
                      <Input {...field} placeholder="Customer name" />
                    )}
                  />
                </FormField>

                <FormField
                  label="Email"
                  error={errors.customer?.email?.message}
                >
                  <Controller
                    name="customer.email"
                    control={control}
                    render={({ field }) => (
                      <Input {...field} type="email" placeholder="customer@example.com" />
                    )}
                  />
                </FormField>

                <FormField
                  label="Phone"
                  error={errors.customer?.phone?.message}
                >
                  <Controller
                    name="customer.phone"
                    control={control}
                    render={({ field }) => (
                      <Input {...field} placeholder="+234 xxx xxx xxxx" />
                    )}
                  />
                </FormField>

                <FormField
                  label="Address"
                  error={errors.customer?.address?.message}
                >
                  <Controller
                    name="customer.address"
                    control={control}
                    render={({ field }) => (
                      <Textarea {...field} placeholder="Customer address" rows={2} />
                    )}
                  />
                </FormField>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader 
              title="Line Items"
              action={
                <Button type="button" variant="outline" size="sm" onClick={addLineItem}>
                  <Plus className="w-4 h-4 mr-1" />
                  Add Item
                </Button>
              }
            />
            <CardContent>
              {fields.map((field, index) => (
                <div key={field.id} className="grid grid-cols-12 gap-2 items-end mb-4">
                  <div className="col-span-4">
                    <FormField
                      label={index === 0 ? "Description" : ""}
                      error={errors.line_items?.[index]?.description?.message}
                    >
                      <Controller
                        name={`line_items.${index}.description`}
                        control={control}
                        render={({ field }) => (
                          <Input {...field} placeholder="Item description" />
                        )}
                      />
                    </FormField>
                  </div>

                  <div className="col-span-2">
                    <FormField
                      label={index === 0 ? "Quantity" : ""}
                      error={errors.line_items?.[index]?.quantity?.message}
                    >
                      <Controller
                        name={`line_items.${index}.quantity`}
                        control={control}
                        render={({ field }) => (
                          <Input 
                            {...field} 
                            type="number" 
                            step="0.01"
                            onChange={(e) => {
                              field.onChange(parseFloat(e.target.value) || 0);
                              updateLineItemAmount(index);
                            }}
                          />
                        )}
                      />
                    </FormField>
                  </div>

                  <div className="col-span-2">
                    <FormField
                      label={index === 0 ? "Unit Price" : ""}
                      error={errors.line_items?.[index]?.unit_price?.message}
                    >
                      <Controller
                        name={`line_items.${index}.unit_price`}
                        control={control}
                        render={({ field }) => (
                          <Input 
                            {...field} 
                            type="number" 
                            step="0.01"
                            onChange={(e) => {
                              field.onChange(parseFloat(e.target.value) || 0);
                              updateLineItemAmount(index);
                            }}
                          />
                        )}
                      />
                    </FormField>
                  </div>

                  <div className="col-span-3">
                    <FormField
                      label={index === 0 ? "Amount" : ""}
                      error={errors.line_items?.[index]?.amount?.message}
                    >
                      <Controller
                        name={`line_items.${index}.amount`}
                        control={control}
                        render={({ field }) => (
                          <Input {...field} type="number" step="0.01" readOnly />
                        )}
                      />
                    </FormField>
                  </div>

                  <div className="col-span-1">
                    {fields.length > 1 && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => remove(index)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="flex justify-between">
            <div className="flex gap-2">
              {selectedDealIndex > 0 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setSelectedDealIndex(selectedDealIndex - 1);
                    loadInvoiceToForm(invoicePreviews[selectedDealIndex - 1].invoice);
                  }}
                >
                  Previous Deal
                </Button>
              )}
              
              {selectedDealIndex < deals.length - 1 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setSelectedDealIndex(selectedDealIndex + 1);
                    loadInvoiceToForm(invoicePreviews[selectedDealIndex + 1].invoice);
                  }}
                >
                  Next Deal
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              )}
            </div>

            <div className="flex gap-2">
              <Button type="submit" variant="outline" disabled={!isValid}>
                Save Changes
              </Button>
              
              <Button 
                type="button" 
                onClick={() => generateSingleInvoice(selectedDealIndex)}
                disabled={!isValid}
              >
                <Send className="w-4 h-4 mr-2" />
                Generate Invoice
              </Button>
            </div>
          </div>
        </form>
      </div>
    );
  };

  // ==================== MAIN RENDER ====================

  return (
    <div className={className}>
      <Card>
        <CardHeader
          title="Convert Deals to Invoices"
          subtitle={`${deals.length} deal${deals.length !== 1 ? 's' : ''} selected for conversion`}
          action={
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          }
        />

        <CardContent>
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            tabs={[
              { id: 'batch', label: `Batch Processing (${deals.length})` },
              { id: 'individual', label: 'Individual Editing' }
            ]}
          >
            <div className="mt-6">
              {activeTab === 'batch' && (
                <div className="space-y-6">
                  {renderBatchOverview()}
                  
                  <div className="flex justify-center">
                    <Button
                      onClick={generateBatchInvoices}
                      disabled={generationState.isGenerating}
                      loading={generationState.isGenerating}
                      size="lg"
                    >
                      <FileText className="w-5 h-5 mr-2" />
                      Generate All Invoices
                    </Button>
                  </div>
                </div>
              )}

              {activeTab === 'individual' && renderInvoiceEditor()}
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default DealToInvoiceConverter;