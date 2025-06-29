import React, { useState, useEffect } from 'react';
import { useLocalization, useBusinessTerms, useCommonPhrases } from '../../context/LocalizationContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Alert, AlertDescription } from '../ui/Alert';
import { Badge } from '../ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { 
  Phone, 
  MessageSquare, 
  CreditCard, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Copy,
  RefreshCw,
  HelpCircle,
  Smartphone
} from 'lucide-react';

interface Bank {
  code: string;
  name: string;
  ussd_code: string;
  logo?: string;
  daily_limit: number;
  single_limit: number;
  features: string[];
}

interface USSDPaymentProps {
  amount: number;
  reference: string;
  customerEmail: string;
  customerPhone?: string;
  onPaymentComplete?: (reference: string, status: string) => void;
  onPaymentCancel?: () => void;
}

const NIGERIAN_BANKS: Bank[] = [
  {
    code: 'GTB',
    name: 'Guaranty Trust Bank',
    ussd_code: '*737#',
    daily_limit: 1000000,
    single_limit: 200000,
    features: ['Instant Transfer', 'Bill Payment', 'Airtime']
  },
  {
    code: 'UBA',
    name: 'United Bank for Africa',
    ussd_code: '*919#',
    daily_limit: 500000,
    single_limit: 100000,
    features: ['Leo Savings', 'Quick Transfer', 'Bill Payment']
  },
  {
    code: 'FIRST_BANK',
    name: 'First Bank of Nigeria',
    ussd_code: '*894#',
    daily_limit: 1000000,
    single_limit: 200000,
    features: ['FirstMobile', 'Quick Transfer', 'Cardless Withdrawal']
  },
  {
    code: 'ZENITH',
    name: 'Zenith Bank',
    ussd_code: '*966#',
    daily_limit: 1000000,
    single_limit: 200000,
    features: ['Zenith Beta', 'EazyBanking', 'Bill Payment']
  },
  {
    code: 'ACCESS',
    name: 'Access Bank',
    ussd_code: '*901#',
    daily_limit: 1000000,
    single_limit: 200000,
    features: ['PayWithCapture', 'Quick Transfer', 'Payday Loans']
  },
  {
    code: 'STANBIC',
    name: 'Stanbic IBTC Bank',
    ussd_code: '*909#',
    daily_limit: 500000,
    single_limit: 100000,
    features: ['Instant Transfer', 'Bill Payment', 'Investment']
  }
];

export const NigerianUSSDPayment: React.FC<USSDPaymentProps> = ({
  amount,
  reference,
  customerEmail,
  customerPhone,
  onPaymentComplete,
  onPaymentCancel
}) => {
  const { currentLanguage, formatCurrency, getCurrentGreeting } = useLocalization();
  const terms = useBusinessTerms();
  const phrases = useCommonPhrases();
  
  const [selectedBank, setSelectedBank] = useState<Bank | null>(null);
  const [phoneNumber, setPhoneNumber] = useState(customerPhone || '');
  const [paymentStep, setPaymentStep] = useState<'select' | 'instructions' | 'verify' | 'complete'>('select');
  const [ussdCode, setUssdCode] = useState('');
  const [instructions, setInstructions] = useState<string[]>([]);
  const [timeRemaining, setTimeRemaining] = useState(1800); // 30 minutes
  const [paymentStatus, setPaymentStatus] = useState<'pending' | 'success' | 'failed'>('pending');
  const [isVerifying, setIsVerifying] = useState(false);

  // Timer for payment expiration
  useEffect(() => {
    if (paymentStep === 'instructions' && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining(prev => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [paymentStep, timeRemaining]);

  const handleBankSelection = (bankCode: string) => {
    const bank = NIGERIAN_BANKS.find(b => b.code === bankCode);
    if (bank) {
      setSelectedBank(bank);
      generateUSSDCode(bank);
    }
  };

  const generateUSSDCode = (bank: Bank) => {
    // Generate USSD code for payment
    const code = `${bank.ussd_code}*${Math.round(amount * 100)}*${reference}#`;
    setUssdCode(code);
    
    // Generate localized instructions
    const stepInstructions = getLocalizedInstructions(bank);
    setInstructions(stepInstructions);
    
    setPaymentStep('instructions');
  };

  const getLocalizedInstructions = (bank: Bank): string[] => {
    if (currentLanguage === 'ha-NG') {
      return [
        `Ka buga ${bank.ussd_code} a wayarka`,
        `Ka zaɓi zaɓi na 'Canja kudi' ko 'Biya'`,
        `Ka shigar da adadin: ₦${amount.toLocaleString()}`,
        `Ka shigar da reference: ${reference}`,
        `Ka shigar da PIN naka na ${bank.name} USSD`,
        `Ka tabbatar da cikakkun bayanai`,
        `Za ka karɓi saƙon tabbatarwa ta SMS`
      ];
    } else if (currentLanguage === 'yo-NG') {
      return [
        `Pe ${bank.ussd_code} lori foonu rẹ`,
        `Yan ẹyan fun 'Gbigbe owo' tabi 'Sisanwo'`,
        `Tẹ iye owo: ₦${amount.toLocaleString()}`,
        `Tẹ reference: ${reference}`,
        `Tẹ PIN USSD ${bank.name} rẹ`,
        `Jẹrisi awọn alaye iṣowo`,
        `Iwọ yoo gba ijẹrisi SMS`
      ];
    } else if (currentLanguage === 'ig-NG') {
      return [
        `Kpọọ ${bank.ussd_code} na ekwentị gị`,
        `Họrọ nhọrọ maka 'Ịnyefe ego' ma ọ bụ 'Ịkwụ ụgwọ'`,
        `Tinye ego: ₦${amount.toLocaleString()}`,
        `Tinye reference: ${reference}`,
        `Tinye PIN USSD ${bank.name} gị`,
        `Kwenye nkọwa azụmahịa`,
        `Ị ga-enweta nkwenye SMS`
      ];
    } else {
      return [
        `Dial ${bank.ussd_code} on your phone`,
        `Select option for 'Transfer' or 'Payment'`,
        `Enter amount: ₦${amount.toLocaleString()}`,
        `Enter reference: ${reference}`,
        `Enter your ${bank.name} USSD PIN`,
        `Confirm transaction details`,
        `You will receive SMS confirmation`
      ];
    }
  };

  const copyUSSDCode = async () => {
    try {
      await navigator.clipboard.writeText(ussdCode);
      // Show success toast
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = ussdCode;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
  };

  const sendSMSInstructions = async () => {
    if (!phoneNumber) return;
    
    try {
      // API call to send SMS instructions
      const response = await fetch('/api/ussd/send-instructions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phoneNumber,
          bank_code: selectedBank?.code,
          amount,
          reference,
          language: currentLanguage
        })
      });
      
      if (response.ok) {
        // Show success message
      }
    } catch (error) {
      console.error('Failed to send SMS:', error);
    }
  };

  const verifyPayment = async () => {
    setIsVerifying(true);
    
    try {
      const response = await fetch(`/api/ussd/verify/${reference}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setPaymentStatus('success');
        setPaymentStep('complete');
        onPaymentComplete?.(reference, 'success');
      } else if (data.status === 'failed') {
        setPaymentStatus('failed');
      }
    } catch (error) {
      console.error('Payment verification failed:', error);
      setPaymentStatus('failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const renderBankSelection = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">{getCurrentGreeting()}</h3>
        <p className="text-gray-600">
          {currentLanguage === 'ha-NG' && 'Ka zaɓi bankin da ka so don biya'}
          {currentLanguage === 'yo-NG' && 'Yan banki ti o fẹ lati san'}
          {currentLanguage === 'ig-NG' && 'Họrọ ụlọ akụ ị chọrọ iji kwụọ ụgwọ'}
          {currentLanguage === 'en-NG' && 'Select your bank to make payment'}
        </p>
      </div>

      <div className="mb-4">
        <Label htmlFor="phone">{terms.customer} Phone</Label>
        <Input
          id="phone"
          type="tel"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          placeholder="+234 xxx xxx xxxx"
          className="mt-1"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {NIGERIAN_BANKS.map((bank) => (
          <Card 
            key={bank.code} 
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedBank?.code === bank.code ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => handleBankSelection(bank.code)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium">{bank.name}</h4>
                <Badge variant="secondary">{bank.ussd_code}</Badge>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Daily Limit:</span>
                  <span>{formatCurrency(bank.daily_limit)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Single Limit:</span>
                  <span>{formatCurrency(bank.single_limit)}</span>
                </div>
              </div>
              
              <div className="mt-3">
                <div className="flex flex-wrap gap-1">
                  {bank.features.slice(0, 2).map((feature) => (
                    <Badge key={feature} variant="outline" className="text-xs">
                      {feature}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderInstructions = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-4">
          <Smartphone className="w-8 h-8 text-blue-600" />
          <h3 className="text-xl font-semibold">{selectedBank?.name}</h3>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-2xl font-bold text-blue-800">{ussdCode}</p>
              <p className="text-sm text-blue-600 mt-1">
                {currentLanguage === 'ha-NG' && 'Ka buga wannan lambar'}
                {currentLanguage === 'yo-NG' && 'Pe nọmba yii'}
                {currentLanguage === 'ig-NG' && 'Kpọọ nọmba a'}
                {currentLanguage === 'en-NG' && 'Dial this code'}
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={copyUSSDCode}>
              <Copy className="w-4 h-4 mr-2" />
              {phrases.copy || 'Copy'}
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center space-x-1">
            <Clock className="w-4 h-4" />
            <span>
              {currentLanguage === 'ha-NG' && `Lokaci: ${formatTime(timeRemaining)}`}
              {currentLanguage === 'yo-NG' && `Akoko: ${formatTime(timeRemaining)}`}
              {currentLanguage === 'ig-NG' && `Oge: ${formatTime(timeRemaining)}`}
              {currentLanguage === 'en-NG' && `Time: ${formatTime(timeRemaining)}`}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <CreditCard className="w-4 h-4" />
            <span>{formatCurrency(amount)}</span>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Phone className="w-5 h-5" />
            <span>
              {currentLanguage === 'ha-NG' && 'Umarnin Biya'}
              {currentLanguage === 'yo-NG' && 'Itọnisọna Sisanwo'}
              {currentLanguage === 'ig-NG' && 'Ntuziaka Ịkwụ Ụgwọ'}
              {currentLanguage === 'en-NG' && 'Payment Instructions'}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-3">
            {instructions.map((instruction, index) => (
              <li key={index} className="flex items-start space-x-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </span>
                <span className="text-sm">{instruction}</span>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>

      <div className="flex space-x-3">
        <Button 
          onClick={sendSMSInstructions} 
          variant="outline" 
          className="flex-1"
          disabled={!phoneNumber}
        >
          <MessageSquare className="w-4 h-4 mr-2" />
          {currentLanguage === 'ha-NG' && 'Aika SMS'}
          {currentLanguage === 'yo-NG' && 'Fi SMS ranṣẹ'}
          {currentLanguage === 'ig-NG' && 'Ziga SMS'}
          {currentLanguage === 'en-NG' && 'Send SMS'}
        </Button>
        
        <Button onClick={() => setPaymentStep('verify')} className="flex-1">
          {currentLanguage === 'ha-NG' && 'Na gama biya'}
          {currentLanguage === 'yo-NG' && 'Mo ti san'}
          {currentLanguage === 'ig-NG' && 'Akwụọla m ụgwọ'}
          {currentLanguage === 'en-NG' && 'I have paid'}
        </Button>
      </div>
    </div>
  );

  const renderVerification = () => (
    <div className="space-y-6 text-center">
      <div className="space-y-4">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
          <RefreshCw className={`w-8 h-8 text-blue-600 ${isVerifying ? 'animate-spin' : ''}`} />
        </div>
        
        <div>
          <h3 className="text-lg font-semibold mb-2">
            {currentLanguage === 'ha-NG' && 'Ana Tabbatar da Biyan Kudi'}
            {currentLanguage === 'yo-NG' && 'N Ṣayẹwo Sisanwo'}
            {currentLanguage === 'ig-NG' && 'Na-achọpụta Ịkwụ Ụgwọ'}
            {currentLanguage === 'en-NG' && 'Verifying Payment'}
          </h3>
          
          <p className="text-gray-600">
            {currentLanguage === 'ha-NG' && 'Da fatan za a jira kaɗan yayin da muke tabbatar da biyan kuɗi naku...'}
            {currentLanguage === 'yo-NG' && 'Jọwọ duro diẹ lakoko ti a ba n ṣayẹwo sisanwo rẹ...'}
            {currentLanguage === 'ig-NG' && 'Biko chere ntakịrị ka anyị na-achọpụta ịkwụ ụgwọ gị...'}
            {currentLanguage === 'en-NG' && 'Please wait while we verify your payment...'}
          </p>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">{terms.reference}:</span>
            <p className="font-mono font-medium">{reference}</p>
          </div>
          <div>
            <span className="text-gray-500">{terms.amount}:</span>
            <p className="font-medium">{formatCurrency(amount)}</p>
          </div>
        </div>
      </div>

      <div className="flex space-x-3">
        <Button 
          onClick={verifyPayment} 
          disabled={isVerifying}
          className="flex-1"
        >
          {isVerifying ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              {phrases.loading}
            </>
          ) : (
            phrases.refresh
          )}
        </Button>
        
        <Button variant="outline" onClick={onPaymentCancel} className="flex-1">
          {phrases.cancel}
        </Button>
      </div>
    </div>
  );

  const renderComplete = () => (
    <div className="space-y-6 text-center">
      <div className="space-y-4">
        <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto ${
          paymentStatus === 'success' ? 'bg-green-100' : 'bg-red-100'
        }`}>
          {paymentStatus === 'success' ? (
            <CheckCircle className="w-8 h-8 text-green-600" />
          ) : (
            <AlertCircle className="w-8 h-8 text-red-600" />
          )}
        </div>
        
        <div>
          <h3 className="text-lg font-semibold mb-2">
            {paymentStatus === 'success' ? (
              <>
                {currentLanguage === 'ha-NG' && 'Biyan Kudi Ya Yi Nasara!'}
                {currentLanguage === 'yo-NG' && 'Sisanwo Ṣaṣeyọri!'}
                {currentLanguage === 'ig-NG' && 'Ịkwụ Ụgwọ Gagara!'}
                {currentLanguage === 'en-NG' && 'Payment Successful!'}
              </>
            ) : (
              <>
                {currentLanguage === 'ha-NG' && 'Biyan Kudi Ya Gaza'}
                {currentLanguage === 'yo-NG' && 'Sisanwo Kuna'}
                {currentLanguage === 'ig-NG' && 'Ịkwụ Ụgwọ Dara'}
                {currentLanguage === 'en-NG' && 'Payment Failed'}
              </>
            )}
          </h3>
          
          <p className="text-gray-600">
            {paymentStatus === 'success' ? (
              <>
                {currentLanguage === 'ha-NG' && 'An karɓi biyan kuɗi naku cikin nasara. Za ka karɓi saƙon tabbatarwa.'}
                {currentLanguage === 'yo-NG' && 'A ti gba sisanwo rẹ ni aṣeyọri. Iwọ yoo gba ijẹrisi.'}
                {currentLanguage === 'ig-NG' && 'Anataala ịkwụ ụgwọ gị nke ọma. Ị ga-enweta nkwenye.'}
                {currentLanguage === 'en-NG' && 'Your payment has been received successfully. You will receive a confirmation.'}
              </>
            ) : (
              <>
                {currentLanguage === 'ha-NG' && 'Ba mu sami biyan kuɗi ba. Ka gwada kuma ko ka tuntube mu.'}
                {currentLanguage === 'yo-NG' && 'A ko gba sisanwo naa. Gbiyanju lẹẹkansi tabi kan si wa.'}
                {currentLanguage === 'ig-NG' && 'Anyị enwetaghị ịkwụ ụgwọ ahụ. Nwaa ọzọ ma ọ bụ kpọtụrụ anyị.'}
                {currentLanguage === 'en-NG' && 'We did not receive your payment. Please try again or contact us.'}
              </>
            )}
          </p>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">{terms.reference}:</span>
            <p className="font-mono font-medium">{reference}</p>
          </div>
          <div>
            <span className="text-gray-500">{terms.amount}:</span>
            <p className="font-medium">{formatCurrency(amount)}</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Phone className="w-6 h-6" />
          <span>
            {currentLanguage === 'ha-NG' && 'Biyan Kudi Ta USSD'}
            {currentLanguage === 'yo-NG' && 'Sisanwo USSD'}
            {currentLanguage === 'ig-NG' && 'Ịkwụ Ụgwọ USSD'}
            {currentLanguage === 'en-NG' && 'USSD Payment'}
          </span>
        </CardTitle>
        <CardDescription>
          {currentLanguage === 'ha-NG' && 'Biya ta amfani da wayar hannu mai sauki'}
          {currentLanguage === 'yo-NG' && 'San pẹlu foonu ti ko ni internet'}
          {currentLanguage === 'ig-NG' && 'Kwụọ ụgwọ site na ekwentị nkịtị'}
          {currentLanguage === 'en-NG' && 'Pay using any basic mobile phone'}
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {paymentStep === 'select' && renderBankSelection()}
        {paymentStep === 'instructions' && renderInstructions()}
        {paymentStep === 'verify' && renderVerification()}
        {paymentStep === 'complete' && renderComplete()}
      </CardContent>
    </Card>
  );
};

export default NigerianUSSDPayment;