"""
Financial Systems - Payment Processors
=====================================

Payment processor integrations for transaction data collection and FIRS compliance.

Note: TaxPoynt is a data collector and invoice generator, NOT a payment processor.
These integrations collect transaction data from payment processors for FIRS compliance.

Nigerian Payment Processors:
- Paystack: Market leader
- Moniepoint: POS/agent banking leader  
- OPay: Mobile payments
- PalmPay: Mobile platform
- Interswitch: Interbank switching

African Regional Processors:
- Flutterwave: Pan-African

Global Processors:
- Stripe: Global leader
- Square: Payment processing
"""

from .nigerian_processors import *
from .african_processors import *
from .global_processors import *