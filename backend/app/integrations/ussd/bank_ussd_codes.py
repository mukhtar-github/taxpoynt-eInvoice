"""
Nigerian Bank USSD Codes and Payment Integration
Complete mapping of major Nigerian banks' USSD codes
"""

from typing import Dict, List, Optional
from enum import Enum

class BankCategory(str, Enum):
    """Bank category classification"""
    TIER_1 = "tier_1"  # Major commercial banks
    TIER_2 = "tier_2"  # Medium-sized banks
    MICROFINANCE = "microfinance"
    DIGITAL = "digital"  # Digital-first banks

class NetworkOperator(str, Enum):
    """Nigerian mobile network operators"""
    MTN = "mtn"
    AIRTEL = "airtel"
    GLO = "glo"
    NINE_MOBILE = "9mobile"
    ALL = "all"

NIGERIAN_BANK_USSD_CODES = {
    # Tier 1 Banks
    'GTB': {
        'name': 'Guaranty Trust Bank',
        'code': '*737#',
        'transfer_code': '*737*1*',
        'balance_code': '*737*6*1#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*737*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*737*51*',
        'airtime_code': '*737*2*',
        'data_code': '*737*3*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'data_purchase': True,
            'merchant_payment': True,
            'pos_withdrawal': True
        },
        'limits': {
            'daily_transfer': 1000000,  # 1M Naira
            'single_transaction': 200000,  # 200k Naira
            'monthly': 5000000  # 5M Naira
        }
    },
    
    'UBA': {
        'name': 'United Bank for Africa',
        'code': '*919#',
        'transfer_code': '*919*3*',
        'balance_code': '*919*00#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*919*3*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*919*11*',
        'airtime_code': '*919*4*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'leo_savings': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 3000000
        }
    },
    
    'FIRST_BANK': {
        'name': 'First Bank of Nigeria',
        'code': '*894#',
        'transfer_code': '*894*1*',
        'balance_code': '*894*00#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*894*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*894*3*',
        'airtime_code': '*894*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'data_purchase': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 1000000,
            'single_transaction': 200000,
            'monthly': 5000000
        }
    },
    
    'ZENITH': {
        'name': 'Zenith Bank',
        'code': '*966#',
        'transfer_code': '*966*1*',
        'balance_code': '*966*00#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*966*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*966*4*',
        'airtime_code': '*966*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'beta_life_insurance': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 1000000,
            'single_transaction': 200000,
            'monthly': 5000000
        }
    },
    
    'ACCESS': {
        'name': 'Access Bank',
        'code': '*901#',
        'transfer_code': '*901*1*',
        'balance_code': '*901*5#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*901*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*901*3*',
        'airtime_code': '*901*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'paywithcapture': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 1000000,
            'single_transaction': 200000,
            'monthly': 5000000
        }
    },
    
    'STANBIC': {
        'name': 'Stanbic IBTC Bank',
        'code': '*909#',
        'transfer_code': '*909*1*',
        'balance_code': '*909*00#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*909*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*909*7*',
        'airtime_code': '*909*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'instant_transfer': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 3000000
        }
    },
    
    'FCMB': {
        'name': 'First City Monument Bank',
        'code': '*329#',
        'transfer_code': '*329*1*',
        'balance_code': '*329*00#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*329*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*329*3*',
        'airtime_code': '*329*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 2000000
        }
    },
    
    'FIDELITY': {
        'name': 'Fidelity Bank',
        'code': '*770#',
        'transfer_code': '*770*1*',
        'balance_code': '*770*0#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*770*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*770*3*',
        'airtime_code': '*770*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 2000000
        }
    },
    
    'UNION': {
        'name': 'Union Bank of Nigeria',
        'code': '*826#',
        'transfer_code': '*826*1*',
        'balance_code': '*826*00#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*826*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*826*3*',
        'airtime_code': '*826*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 2000000
        }
    },
    
    'ECOBANK': {
        'name': 'Ecobank Nigeria',
        'code': '*326#',
        'transfer_code': '*326*1*',
        'balance_code': '*326*0#',
        'category': BankCategory.TIER_1,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*326*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*326*3*',
        'airtime_code': '*326*2*',
        'features': {
            'cardless_withdrawal': True,
            'bill_payment': True,
            'airtime_purchase': True,
            'xpress_account': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 2000000
        }
    },
    
    # Digital Banks
    'KUDA': {
        'name': 'Kuda Bank',
        'code': '*894*1*',
        'transfer_code': '*894*1*1*',
        'balance_code': '*894*1*00#',
        'category': BankCategory.DIGITAL,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*894*1*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*894*1*3*',
        'features': {
            'zero_fees': True,
            'bill_payment': True,
            'instant_transfer': True,
            'savings_goals': True,
            'merchant_payment': True
        },
        'limits': {
            'daily_transfer': 1000000,
            'single_transaction': 200000,
            'monthly': 5000000
        }
    },
    
    'OPAY': {
        'name': 'OPay',
        'code': '*955#',
        'transfer_code': '*955*1*',
        'balance_code': '*955*0#',
        'category': BankCategory.DIGITAL,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*955*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*955*3*',
        'features': {
            'ride_hailing_payment': True,
            'bill_payment': True,
            'merchant_payment': True,
            'pos_agent_banking': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 2000000
        }
    },
    
    'PALMPAY': {
        'name': 'PalmPay',
        'code': '*861#',
        'transfer_code': '*861*1*',
        'balance_code': '*861*0#',
        'category': BankCategory.DIGITAL,
        'supported_networks': [NetworkOperator.ALL],
        'payment_format': '*861*1*{amount}*{account_number}#{pin}',
        'bill_payment_code': '*861*3*',
        'features': {
            'cashback_rewards': True,
            'bill_payment': True,
            'merchant_payment': True,
            'loan_services': True
        },
        'limits': {
            'daily_transfer': 500000,
            'single_transaction': 100000,
            'monthly': 2000000
        }
    }
}

# Common USSD patterns for different operations
USSD_PATTERNS = {
    'balance_inquiry': {
        'pattern': '{base_code}*00#',
        'description': 'Check account balance'
    },
    'transfer': {
        'pattern': '{transfer_code}{amount}*{account_number}#{pin}',
        'description': 'Transfer money to another account'
    },
    'bill_payment': {
        'pattern': '{bill_code}{biller_code}*{customer_id}*{amount}#{pin}',
        'description': 'Pay bills (electricity, cable, etc.)'
    },
    'airtime_purchase': {
        'pattern': '{airtime_code}{amount}*{phone_number}#{pin}',
        'description': 'Buy airtime for self or others'
    },
    'merchant_payment': {
        'pattern': '{base_code}*{merchant_code}*{amount}#{pin}',
        'description': 'Pay at merchant locations'
    }
}

# Network-specific considerations
NETWORK_CONSIDERATIONS = {
    NetworkOperator.MTN: {
        'ussd_support': 'excellent',
        'session_timeout': 180,  # seconds
        'max_menu_depth': 7,
        'special_features': ['ussd_push', 'callback_support']
    },
    NetworkOperator.AIRTEL: {
        'ussd_support': 'excellent', 
        'session_timeout': 120,
        'max_menu_depth': 6,
        'special_features': ['ussd_push', 'sms_fallback']
    },
    NetworkOperator.GLO: {
        'ussd_support': 'good',
        'session_timeout': 120,
        'max_menu_depth': 6,
        'special_features': ['sms_fallback']
    },
    NetworkOperator.NINE_MOBILE: {
        'ussd_support': 'good',
        'session_timeout': 90,
        'max_menu_depth': 5,
        'special_features': ['sms_fallback']
    }
}

def get_bank_by_code(bank_code: str) -> Optional[Dict]:
    """Get bank information by bank code"""
    return NIGERIAN_BANK_USSD_CODES.get(bank_code.upper())

def get_banks_by_category(category: BankCategory) -> Dict[str, Dict]:
    """Get banks filtered by category"""
    return {
        code: bank for code, bank in NIGERIAN_BANK_USSD_CODES.items()
        if bank['category'] == category
    }

def get_supported_banks_for_network(network: NetworkOperator) -> Dict[str, Dict]:
    """Get banks that support a specific network operator"""
    return {
        code: bank for code, bank in NIGERIAN_BANK_USSD_CODES.items()
        if network in bank['supported_networks'] or NetworkOperator.ALL in bank['supported_networks']
    }

def generate_ussd_code(bank_code: str, operation: str, **kwargs) -> Optional[str]:
    """Generate USSD code for specific bank operation"""
    bank = get_bank_by_code(bank_code)
    if not bank:
        return None
    
    pattern = USSD_PATTERNS.get(operation)
    if not pattern:
        return None
    
    try:
        if operation == 'balance_inquiry':
            return pattern['pattern'].format(base_code=bank['code'].replace('#', ''))
        elif operation == 'transfer':
            return pattern['pattern'].format(
                transfer_code=bank['transfer_code'],
                amount=kwargs.get('amount', ''),
                account_number=kwargs.get('account_number', ''),
                pin=kwargs.get('pin', '')
            )
        # Add more operations as needed
    except KeyError:
        return None
    
    return None

def validate_transaction_limits(bank_code: str, amount: int, transaction_type: str = 'transfer') -> Dict[str, bool]:
    """Validate transaction against bank limits"""
    bank = get_bank_by_code(bank_code)
    if not bank:
        return {'valid': False, 'reason': 'Bank not found'}
    
    limits = bank.get('limits', {})
    amount_naira = amount / 100  # Convert from kobo to naira
    
    validations = {
        'within_single_limit': amount_naira <= limits.get('single_transaction', 0),
        'within_daily_limit': True,  # Would need to check daily total
        'within_monthly_limit': True,  # Would need to check monthly total
        'bank_supports_feature': True
    }
    
    return {
        'valid': all(validations.values()),
        'checks': validations,
        'limits': limits
    }