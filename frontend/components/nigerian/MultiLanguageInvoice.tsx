import React from 'react';
import { useLocalization, useBusinessTerms } from '../../context/LocalizationContext';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Separator } from '../ui/Separator';
import { 
  Download, 
  Print, 
  Share2, 
  Eye,
  Calendar,
  User,
  Building,
  Receipt,
  FileText
} from 'lucide-react';

interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
  tax_rate?: number;
}

interface InvoiceData {
  id: string;
  reference: string;
  date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  
  // Business details
  business: {
    name: string;
    address: string;
    phone: string;
    email: string;
    tax_id?: string;
    logo?: string;
  };
  
  // Customer details
  customer: {
    name: string;
    address: string;
    phone?: string;
    email?: string;
  };
  
  // Invoice items
  items: InvoiceItem[];
  
  // Totals
  subtotal: number;
  tax_amount: number;
  discount_amount?: number;
  total: number;
  
  // Payment details
  payment_terms?: string;
  notes?: string;
}

interface MultiLanguageInvoiceProps {
  invoice: InvoiceData;
  showActions?: boolean;
  onDownload?: () => void;
  onPrint?: () => void;
  onShare?: () => void;
  onView?: () => void;
}

export const MultiLanguageInvoice: React.FC<MultiLanguageInvoiceProps> = ({
  invoice,
  showActions = true,
  onDownload,
  onPrint,
  onShare,
  onView
}) => {
  const { currentLanguage, formatCurrency, formatDate, getCurrentGreeting } = useLocalization();
  const terms = useBusinessTerms();

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { 
        color: 'secondary' as const, 
        labels: {
          'en-NG': 'Draft',
          'ha-NG': 'Daftari',
          'yo-NG': 'Apẹrẹ',
          'ig-NG': 'Nchịkọta'
        }
      },
      sent: { 
        color: 'default' as const, 
        labels: {
          'en-NG': 'Sent',
          'ha-NG': 'An aika',
          'yo-NG': 'Ti fi ranṣẹ',
          'ig-NG': 'Ezigara'
        }
      },
      paid: { 
        color: 'default' as const, 
        labels: {
          'en-NG': 'Paid',
          'ha-NG': 'An biya',
          'yo-NG': 'Ti san',
          'ig-NG': 'Akwụọla'
        }
      },
      overdue: { 
        color: 'destructive' as const, 
        labels: {
          'en-NG': 'Overdue',
          'ha-NG': 'Ya wuce lokaci',
          'yo-NG': 'Ti koja akoko',
          'ig-NG': 'Agafela oge'
        }
      },
      cancelled: { 
        color: 'secondary' as const, 
        labels: {
          'en-NG': 'Cancelled',
          'ha-NG': 'An soke',
          'yo-NG': 'Ti fagile',
          'ig-NG': 'Akagbuola'
        }
      }
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    const label = config?.labels[currentLanguage as keyof typeof config.labels] || status;
    
    return (
      <Badge variant={config?.color || 'secondary'}>
        {label}
      </Badge>
    );
  };

  const getLocalizedLabel = (key: string): string => {
    const labels: Record<string, Record<string, string>> = {
      'invoice_number': {
        'en-NG': 'Invoice Number',
        'ha-NG': 'Lambar Takardayar Biya',
        'yo-NG': 'Nọmba Iwe Owo',
        'ig-NG': 'Nọmba Akwụkwọ Ego'
      },
      'issue_date': {
        'en-NG': 'Issue Date',
        'ha-NG': 'Ranar Fitarwa',
        'yo-NG': 'Ọjọ Ipilẹṣẹ',
        'ig-NG': 'Ụbọchị Ewepụtara'
      },
      'due_date': {
        'en-NG': 'Due Date',
        'ha-NG': 'Ranar Karewa',
        'yo-NG': 'Ọjọ Iyẹ',
        'ig-NG': 'Ụbọchị Nkwụghachi'
      },
      'bill_to': {
        'en-NG': 'Bill To',
        'ha-NG': 'Biyan Zuwa',
        'yo-NG': 'San Fun',
        'ig-NG': 'Kwụọ Nye'
      },
      'bill_from': {
        'en-NG': 'Bill From',
        'ha-NG': 'Biyan Daga',
        'yo-NG': 'Lati Ọdọ',
        'ig-NG': 'Kpọpụta Site Na'
      },
      'payment_terms': {
        'en-NG': 'Payment Terms',
        'ha-NG': 'Sharuɗɗan Biya',
        'yo-NG': 'Awọn Ofin Sisanwo',
        'ig-NG': 'Usoro Ịkwụ Ụgwọ'
      },
      'notes': {
        'en-NG': 'Notes',
        'ha-NG': 'Bayanai',
        'yo-NG': 'Akọsilẹ',
        'ig-NG': 'Ndetu'
      },
      'unit_price': {
        'en-NG': 'Unit Price',
        'ha-NG': 'Farashin Rabi',
        'yo-NG': 'Idiyele Ẹyọ Kan',
        'ig-NG': 'Ọnụahịa Otu'
      }
    };

    return labels[key]?.[currentLanguage] || labels[key]?.['en-NG'] || key;
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white">
      {/* Invoice Header */}
      <div className="flex items-center justify-between p-6 border-b">
        <div className="flex items-center space-x-4">
          {invoice.business.logo && (
            <img 
              src={invoice.business.logo} 
              alt={invoice.business.name}
              className="w-12 h-12 object-contain"
            />
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {terms.invoice}
            </h1>
            <p className="text-sm text-gray-600">
              #{invoice.reference}
            </p>
          </div>
        </div>
        
        <div className="text-right">
          {getStatusBadge(invoice.status)}
          <p className="text-sm text-gray-600 mt-2">
            {formatDate(invoice.date)}
          </p>
        </div>
      </div>

      {/* Invoice Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6 bg-gray-50">
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">
            {getLocalizedLabel('invoice_number')}
          </h3>
          <p className="text-sm font-mono">{invoice.reference}</p>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">
            {getLocalizedLabel('issue_date')}
          </h3>
          <p className="text-sm">{formatDate(invoice.date)}</p>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">
            {getLocalizedLabel('due_date')}
          </h3>
          <p className="text-sm">{formatDate(invoice.due_date)}</p>
        </div>
      </div>

      {/* Business and Customer Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <Building className="w-4 h-4 mr-2" />
            {getLocalizedLabel('bill_from')}
          </h3>
          <div className="space-y-1 text-sm">
            <p className="font-medium">{invoice.business.name}</p>
            <p className="text-gray-600">{invoice.business.address}</p>
            <p className="text-gray-600">{invoice.business.phone}</p>
            <p className="text-gray-600">{invoice.business.email}</p>
            {invoice.business.tax_id && (
              <p className="text-gray-600">Tax ID: {invoice.business.tax_id}</p>
            )}
          </div>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <User className="w-4 h-4 mr-2" />
            {getLocalizedLabel('bill_to')}
          </h3>
          <div className="space-y-1 text-sm">
            <p className="font-medium">{invoice.customer.name}</p>
            <p className="text-gray-600">{invoice.customer.address}</p>
            {invoice.customer.phone && (
              <p className="text-gray-600">{invoice.customer.phone}</p>
            )}
            {invoice.customer.email && (
              <p className="text-gray-600">{invoice.customer.email}</p>
            )}
          </div>
        </div>
      </div>

      {/* Invoice Items Table */}
      <div className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-3 font-semibold text-gray-900">
                  {terms.description}
                </th>
                <th className="text-center py-3 font-semibold text-gray-900">
                  {terms.quantity}
                </th>
                <th className="text-right py-3 font-semibold text-gray-900">
                  {getLocalizedLabel('unit_price')}
                </th>
                <th className="text-right py-3 font-semibold text-gray-900">
                  {terms.total}
                </th>
              </tr>
            </thead>
            <tbody>
              {invoice.items.map((item, index) => (
                <tr key={item.id} className="border-b border-gray-100">
                  <td className="py-3">
                    <div className="text-sm font-medium text-gray-900">
                      {item.description}
                    </div>
                  </td>
                  <td className="text-center py-3 text-sm text-gray-600">
                    {item.quantity.toLocaleString()}
                  </td>
                  <td className="text-right py-3 text-sm text-gray-600">
                    {formatCurrency(item.unit_price)}
                  </td>
                  <td className="text-right py-3 text-sm font-medium text-gray-900">
                    {formatCurrency(item.total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoice Totals */}
      <div className="px-6 pb-6">
        <div className="flex justify-end">
          <div className="w-full max-w-sm space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">{terms.subtotal}:</span>
              <span className="font-medium">{formatCurrency(invoice.subtotal)}</span>
            </div>
            
            {invoice.discount_amount && invoice.discount_amount > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">{terms.discount}:</span>
                <span className="font-medium text-green-600">
                  -{formatCurrency(invoice.discount_amount)}
                </span>
              </div>
            )}
            
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">{terms.tax} ({terms.vat}):</span>
              <span className="font-medium">{formatCurrency(invoice.tax_amount)}</span>
            </div>
            
            <Separator />
            
            <div className="flex justify-between text-lg font-bold">
              <span>{terms.total}:</span>
              <span>{formatCurrency(invoice.total)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Terms and Notes */}
      {(invoice.payment_terms || invoice.notes) && (
        <div className="px-6 pb-6 space-y-4">
          {invoice.payment_terms && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                {getLocalizedLabel('payment_terms')}
              </h4>
              <p className="text-sm text-gray-600">{invoice.payment_terms}</p>
            </div>
          )}
          
          {invoice.notes && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                {getLocalizedLabel('notes')}
              </h4>
              <p className="text-sm text-gray-600">{invoice.notes}</p>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {showActions && (
        <div className="flex flex-wrap gap-3 p-6 bg-gray-50 border-t">
          <Button onClick={onView} variant="outline" size="sm">
            <Eye className="w-4 h-4 mr-2" />
            {currentLanguage === 'ha-NG' && 'Duba'}
            {currentLanguage === 'yo-NG' && 'Wo'}
            {currentLanguage === 'ig-NG' && 'Lee'}
            {currentLanguage === 'en-NG' && 'View'}
          </Button>
          
          <Button onClick={onDownload} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            {currentLanguage === 'ha-NG' && 'Sauke'}
            {currentLanguage === 'yo-NG' && 'Gba sile'}
            {currentLanguage === 'ig-NG' && 'Budata'}
            {currentLanguage === 'en-NG' && 'Download'}
          </Button>
          
          <Button onClick={onPrint} variant="outline" size="sm">
            <Print className="w-4 h-4 mr-2" />
            {currentLanguage === 'ha-NG' && 'Bugawa'}
            {currentLanguage === 'yo-NG' && 'Tẹjade'}
            {currentLanguage === 'ig-NG' && 'Pịnye'}
            {currentLanguage === 'en-NG' && 'Print'}
          </Button>
          
          <Button onClick={onShare} variant="outline" size="sm">
            <Share2 className="w-4 h-4 mr-2" />
            {currentLanguage === 'ha-NG' && 'Raba'}
            {currentLanguage === 'yo-NG' && 'Pin'}
            {currentLanguage === 'ig-NG' && 'Kekọrịta'}
            {currentLanguage === 'en-NG' && 'Share'}
          </Button>
        </div>
      )}
    </div>
  );
};

export default MultiLanguageInvoice;