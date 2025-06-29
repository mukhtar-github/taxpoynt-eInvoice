/**
 * Nigerian Language Localization System
 * Supports English (Nigeria), Hausa, Yoruba, and Igbo
 */

export interface LocalizedBusinessTerms {
  invoice: string;
  receipt: string;
  payment: string;
  tax: string;
  vat: string;
  total: string;
  subtotal: string;
  discount: string;
  customer: string;
  business: string;
  date: string;
  amount: string;
  description: string;
  quantity: string;
  price: string;
  status: string;
  pending: string;
  completed: string;
  failed: string;
  cancelled: string;
  refunded: string;
}

export interface LanguageConfig {
  name: string;
  currency: string;
  date_format: string;
  number_format: string;
  business_terminology: LocalizedBusinessTerms;
  greetings: {
    morning: string;
    afternoon: string;
    evening: string;
    formal: string;
    casual: string;
  };
  common_phrases: {
    thank_you: string;
    please: string;
    welcome: string;
    goodbye: string;
    yes: string;
    no: string;
    ok: string;
    cancel: string;
    confirm: string;
    save: string;
    delete: string;
    edit: string;
    view: string;
    download: string;
    upload: string;
    search: string;
    filter: string;
    sort: string;
    refresh: string;
    loading: string;
    error: string;
    success: string;
    warning: string;
    info: string;
  };
  business_messages: {
    invoice_sent: string;
    payment_received: string;
    payment_pending: string;
    payment_failed: string;
    invoice_overdue: string;
    welcome_message: string;
    transaction_complete: string;
    verification_required: string;
  };
}

export const NigerianLocalization = {
  languages: {
    'en-NG': {
      name: 'English (Nigeria)',
      currency: 'NGN',
      date_format: 'DD/MM/YYYY',
      number_format: '#,##0.00',
      business_terminology: {
        invoice: 'Invoice',
        receipt: 'Receipt',
        payment: 'Payment',
        tax: 'Tax',
        vat: 'VAT',
        total: 'Total',
        subtotal: 'Subtotal',
        discount: 'Discount',
        customer: 'Customer',
        business: 'Business',
        date: 'Date',
        amount: 'Amount',
        description: 'Description',
        quantity: 'Quantity',
        price: 'Price',
        status: 'Status',
        pending: 'Pending',
        completed: 'Completed',
        failed: 'Failed',
        cancelled: 'Cancelled',
        refunded: 'Refunded'
      },
      greetings: {
        morning: 'Good morning',
        afternoon: 'Good afternoon',
        evening: 'Good evening',
        formal: 'Good day, Sir/Madam',
        casual: 'Hello'
      },
      common_phrases: {
        thank_you: 'Thank you',
        please: 'Please',
        welcome: 'Welcome',
        goodbye: 'Goodbye',
        yes: 'Yes',
        no: 'No',
        ok: 'OK',
        cancel: 'Cancel',
        confirm: 'Confirm',
        save: 'Save',
        delete: 'Delete',
        edit: 'Edit',
        view: 'View',
        download: 'Download',
        upload: 'Upload',
        search: 'Search',
        filter: 'Filter',
        sort: 'Sort',
        refresh: 'Refresh',
        loading: 'Loading...',
        error: 'Error',
        success: 'Success',
        warning: 'Warning',
        info: 'Information'
      },
      business_messages: {
        invoice_sent: 'Invoice has been sent successfully',
        payment_received: 'Payment received successfully',
        payment_pending: 'Payment is pending',
        payment_failed: 'Payment failed. Please try again',
        invoice_overdue: 'Invoice is overdue',
        welcome_message: 'Welcome to TaxPoynt eInvoice',
        transaction_complete: 'Transaction completed successfully',
        verification_required: 'Verification required'
      }
    } as LanguageConfig,
    
    'ha-NG': {
      name: 'Hausa (Nigeria)',
      currency: 'NGN',
      date_format: 'DD/MM/YYYY',
      number_format: '#,##0.00',
      business_terminology: {
        invoice: 'Takardar biyan kudi',
        receipt: 'Rasit',
        payment: 'Biya',
        tax: 'Haraji',
        vat: 'VAT',
        total: 'Jimla',
        subtotal: 'Jimlar kasa',
        discount: 'Rangwame',
        customer: 'Abokin ciniki',
        business: 'Kasuwanci',
        date: 'Kwanan wata',
        amount: 'Adadi',
        description: 'Bayani',
        quantity: 'Yawa',
        price: 'Farashi',
        status: 'Matsayi',
        pending: 'Ana jira',
        completed: 'An gama',
        failed: 'Ya gaza',
        cancelled: 'An soke',
        refunded: 'An mayar'
      },
      greetings: {
        morning: 'Ina kwana',
        afternoon: 'Ina yini',
        evening: 'Ina yamma',
        formal: 'Sannu, Malam/Madam',
        casual: 'Sannu'
      },
      common_phrases: {
        thank_you: 'Na gode',
        please: 'Don Allah',
        welcome: 'Maraba',
        goodbye: 'Sai anjima',
        yes: 'Ee',
        no: 'A\'a',
        ok: 'To',
        cancel: 'Soke',
        confirm: 'Tabbatar',
        save: 'Ajiye',
        delete: 'Share',
        edit: 'Gyara',
        view: 'Duba',
        download: 'Sauke',
        upload: 'Tura',
        search: 'Nemo',
        filter: 'Tace',
        sort: 'Jera',
        refresh: 'Sabunta',
        loading: 'Ana lodawa...',
        error: 'Kuskure',
        success: 'Nasara',
        warning: 'Gargadi',
        info: 'Bayani'
      },
      business_messages: {
        invoice_sent: 'An aika takardayar biya cikin nasara',
        payment_received: 'An karbi biya cikin nasara',
        payment_pending: 'Biya yana jira',
        payment_failed: 'Biya ya gaza. Don Allah sake gwadawa',
        invoice_overdue: 'Takardayar biya ta wuce lokaci',
        welcome_message: 'Maraba zuwa TaxPoynt eInvoice',
        transaction_complete: 'An gama mu\'amala cikin nasara',
        verification_required: 'Ana bukatar tabbatarwa'
      }
    } as LanguageConfig,
    
    'yo-NG': {
      name: 'Yoruba (Nigeria)',
      currency: 'NGN',
      date_format: 'DD/MM/YYYY',
      number_format: '#,##0.00',
      business_terminology: {
        invoice: 'Iwe owo',
        receipt: 'Iwe eri',
        payment: 'Sisanwo',
        tax: 'Owo ori',
        vat: 'VAT',
        total: 'Lapapọ',
        subtotal: 'Apọ kekere',
        discount: 'Owo dinku',
        customer: 'Onibara',
        business: 'Iṣowo',
        date: 'Ọjọ',
        amount: 'Iye owo',
        description: 'Alaye',
        quantity: 'Iye',
        price: 'Idiyele',
        status: 'Ipo',
        pending: 'Ti nduro',
        completed: 'Ti pari',
        failed: 'Ti kuna',
        cancelled: 'Ti fagile',
        refunded: 'Ti pada'
      },
      greetings: {
        morning: 'E kaaro',
        afternoon: 'E kaasan',
        evening: 'E kaale',
        formal: 'E ku aaro, Sir/Madam',
        casual: 'Bawo'
      },
      common_phrases: {
        thank_you: 'E se',
        please: 'Je ka',
        welcome: 'E kaabo',
        goodbye: 'O dabo',
        yes: 'Beeni',
        no: 'Rara',
        ok: 'O dara',
        cancel: 'Fagile',
        confirm: 'Jeri',
        save: 'Fi pamọ',
        delete: 'Pa rẹ',
        edit: 'Tunse',
        view: 'Wo',
        download: 'Gba sile',
        upload: 'Gbe soke',
        search: 'Wa',
        filter: 'Se ayẹwo',
        sort: 'To',
        refresh: 'Tun bere',
        loading: 'Ngbọn...',
        error: 'Aṣise',
        success: 'Aṣeyọri',
        warning: 'Ikilọ',
        info: 'Alaye'
      },
      business_messages: {
        invoice_sent: 'A ti fi iwe owo ranṣẹ ni aṣeyọri',
        payment_received: 'A ti gba sisanwo ni aṣeyọri',
        payment_pending: 'Sisanwo ti wa ni idaduro',
        payment_failed: 'Sisanwo ti kuna. E tun gbiyanju',
        invoice_overdue: 'Iwe owo ti koja akoko',
        welcome_message: 'E kaabo si TaxPoynt eInvoice',
        transaction_complete: 'Iṣowo ti pari ni aṣeyọri',
        verification_required: 'A nilo ijẹrisi'
      }
    } as LanguageConfig,
    
    'ig-NG': {
      name: 'Igbo (Nigeria)',
      currency: 'NGN',
      date_format: 'DD/MM/YYYY',
      number_format: '#,##0.00',
      business_terminology: {
        invoice: 'Akwụkwọ ego',
        receipt: 'Akwụkwọ nnata',
        payment: 'Ịkwụ ụgwọ',
        tax: 'Ụtụ',
        vat: 'VAT',
        total: 'Mkpokọta',
        subtotal: 'Mkpokọta nta',
        discount: 'Mbelata ego',
        customer: 'Onye azụmaahịa',
        business: 'Azụmaahịa',
        date: 'Ụbọchị',
        amount: 'Ego ole',
        description: 'Nkọwa',
        quantity: 'Ole',
        price: 'Ọnụahịa',
        status: 'Ọnọdụ',
        pending: 'Na-eche',
        completed: 'Emechala',
        failed: 'Adaghị',
        cancelled: 'Akagbuola',
        refunded: 'Alaghachila'
      },
      greetings: {
        morning: 'Ụtụtụ ọma',
        afternoon: 'Ehihie ọma',
        evening: 'Mgbede ọma',
        formal: 'Ndewo, Sir/Madam',
        casual: 'Ndewo'
      },
      common_phrases: {
        thank_you: 'Daalụ',
        please: 'Biko',
        welcome: 'Nnọọ',
        goodbye: 'Ka ọ dị',
        yes: 'Ee',
        no: 'Mba',
        ok: 'Ọ dị mma',
        cancel: 'Kagbuo',
        confirm: 'Kwenye',
        save: 'Chekwaa',
        delete: 'Hichapụ',
        edit: 'Mezigharịa',
        view: 'Lee',
        download: 'Budata',
        upload: 'Bulite',
        search: 'Chọọ',
        filter: 'Kewaa',
        sort: 'Hazie',
        refresh: 'Weghachi',
        loading: 'Na-ebu...',
        error: 'Njehie',
        success: 'Ihe ịga nke ọma',
        warning: 'Ịdọ aka na ntị',
        info: 'Ozi'
      },
      business_messages: {
        invoice_sent: 'E ziyela akwụkwọ ego nke ọma',
        payment_received: 'Anara ụgwọ nke ọma',
        payment_pending: 'Ịkwụ ụgwọ na-eche',
        payment_failed: 'Ịkwụ ụgwọ adaala. Biko nwaa ọzọ',
        invoice_overdue: 'Akwụkwọ ego agafela oge',
        welcome_message: 'Nnọọ na TaxPoynt eInvoice',
        transaction_complete: 'Azụmaahịa mechara nke ọma',
        verification_required: 'A chọrọ nkwenye'
      }
    } as LanguageConfig
  },
  
  currency_formatting: {
    naira_symbol: '₦',
    kobo_decimal_places: 2,
    thousands_separator: ',',
    decimal_separator: '.',
    format_template: '₦#,##0.00'
  },
  
  cultural_adaptations: {
    greeting_time_sensitive: true,  // "Good morning" vs "Good afternoon"
    respect_titles: true,  // "Alhaji", "Chief", "Dr.", "Engr."
    age_respectful_language: true,
    gender_appropriate_language: true
  }
};

// Nigerian currency formatter
export class NairaCurrencyFormatter {
  static format(amount: number, locale: string = 'en-NG'): string {
    const formatter = new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'NGN',
      currencyDisplay: 'symbol'
    });
    return formatter.format(amount);
  }
  
  static formatWithLocale(amount: number, languageCode: string): string {
    const symbol = NigerianLocalization.currency_formatting.naira_symbol;
    const formattedNumber = new Intl.NumberFormat('en-NG', {
      minimumFractionDigits: NigerianLocalization.currency_formatting.kobo_decimal_places,
      maximumFractionDigits: NigerianLocalization.currency_formatting.kobo_decimal_places,
    }).format(amount);
    
    return `${symbol}${formattedNumber}`;
  }
  
  static toKobo(naira: number): number {
    return Math.round(naira * 100);
  }
  
  static fromKobo(kobo: number): number {
    return kobo / 100;
  }
  
  static formatKobo(kobo: number, languageCode: string = 'en-NG'): string {
    return this.formatWithLocale(this.fromKobo(kobo), languageCode);
  }
}

// Date formatting utilities
export class NigerianDateFormatter {
  static format(date: Date | string, locale: string = 'en-NG'): string {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    // Get format from language config
    const langConfig = NigerianLocalization.languages[locale as keyof typeof NigerianLocalization.languages];
    const format = langConfig?.date_format || 'DD/MM/YYYY';
    
    // For now, use standard Nigerian date format (DD/MM/YYYY)
    return dateObj.toLocaleDateString('en-GB'); // en-GB uses DD/MM/YYYY format
  }
  
  static formatDateTime(date: Date | string, locale: string = 'en-NG'): string {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }
}

// Number formatting utilities
export class NigerianNumberFormatter {
  static format(value: number, locale: string = 'en-NG', decimals: number = 0): string {
    if (isNaN(value)) return '0';
    
    return new Intl.NumberFormat('en-NG', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }
}

// Localization utility functions
export class LocalizationUtils {
  static getGreeting(languageCode: string, timeOfDay?: 'morning' | 'afternoon' | 'evening'): string {
    const config = NigerianLocalization.languages[languageCode as keyof typeof NigerianLocalization.languages];
    if (!config) return 'Hello';
    
    if (timeOfDay && NigerianLocalization.cultural_adaptations.greeting_time_sensitive) {
      return config.greetings[timeOfDay];
    }
    
    return config.greetings.formal;
  }
  
  static getCurrentTimeOfDay(): 'morning' | 'afternoon' | 'evening' {
    const hour = new Date().getHours();
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    return 'evening';
  }
  
  static getLocalizedBusinessTerm(term: keyof LocalizedBusinessTerms, languageCode: string): string {
    const config = NigerianLocalization.languages[languageCode as keyof typeof NigerianLocalization.languages];
    if (!config) return term;
    
    return config.business_terminology[term] || term;
  }
  
  static getLocalizedPhrase(phrase: keyof LanguageConfig['common_phrases'], languageCode: string): string {
    const config = NigerianLocalization.languages[languageCode as keyof typeof NigerianLocalization.languages];
    if (!config) return phrase;
    
    return config.common_phrases[phrase] || phrase;
  }
  
  static getLocalizedBusinessMessage(message: keyof LanguageConfig['business_messages'], languageCode: string): string {
    const config = NigerianLocalization.languages[languageCode as keyof typeof NigerianLocalization.languages];
    if (!config) return message;
    
    return config.business_messages[message] || message;
  }
  
  static getSupportedLanguages(): Array<{code: string, name: string}> {
    return Object.entries(NigerianLocalization.languages).map(([code, config]) => ({
      code,
      name: config.name
    }));
  }
  
  static isRTL(languageCode: string): boolean {
    // None of the Nigerian languages are RTL
    return false;
  }
}

export default NigerianLocalization;
