# IRN Signing
**This document guides you on how to:**
1. Download the crypto keys as a .txt file.
2. Extract the keys from the .txt file.
3. Encrypt a message using the public key.
4. Package the encrypted message with the certificate.
5. Generate a QR code containing the encrypted data and metadata.

## Step 1: Download the Crypto Keys
**On your dashboard:**
1. On your dashboard:
2. Click on the button to download a file named crypto_keys.txt.

**The downloaded crypto_keys.txt contains:**
- The public key.
- Certificate .

## Step 2: Extract Keys from the Text File
**View the File Contents**
To view the contents of the crypto_keys.txt file, use the following command:
{
"cat crypto_keys.txt":
}
The file will have the following structure:
{
"-----BEGIN PUBLIC KEY-----
(base64-encoded public key data)
-----END PUBLIC KEY-----
(base64-encoded certificate data)
}
Extract the Public Key
Save the public key portion to a separate file:
{
awk '/-----BEGIN PUBLIC KEY-----/,/-----END PUBLIC KEY-----/' crypto_keys.txt > public_key.p
}
Extract the Certificate
Save the certificate portion to a separate file:
{VVhrallFNVZUdDV0eUJmYWV1RmYwUXJRNEhTdXlhcU1pOGZsWF35sfhWRT0=}

## Step 3: Encrypt a IRN and Certificate Using the Public Key
**Prepare the IRN**
Create a json IRN plus timestamp, for example "INV001-345SFG-
20241011.1731618237",
And certificate
{
Create a json IRN plus timestamp, for example "INV001-345SFG-20241011.1731618237",
}
 And
{
"irn": "INV001-345SFG-20241011.1731618237",
"certificate": "VVhrallFNVZUdDV0eUJmYWV1RmYwUXJRNEhTdXlhcU1pOGZsWF35sfhWRT0
}

**Encrypt the Message and Certificate**
Encrypt the message using the extracted public_key.pem:
{
openssl pkeyutl -encrypt -inkey public_key.pem -pubin -in data.json -out encrypted_data.b
}
The encrypted data is saved in encrypted_message.bin.
Convert the encrypted data to Base64 for sharing: base64 -i encrypted_data.bin -o encrypted_data.txt

## Step 4: Generate a QR Code
- **Ensure you have the Encrypted Data in Base64:**
After encrypting your data (IRN and certificate) using the recipient's public key, you will have the encrypted data in Base64 format.
For example:
Combine the encrypted message and certificate into a JSON structure for sharing:
aLI+LP+gVeA4dTMTYAdemTMOnIY67d0AB1pmH2QXXN2kzoXxLo+QPTNaOlxHsKyKA/8KvqV
8mC92+hzUIQz+UMc9gI4/sFCmYHgAlvX9NGcTM+fO6WwxJt2tCvIehpELbswo0xR68MUAm
JMRnT18DGoa9RHIn3E2+27JCfe4h9QeV03b02XzfAIoxebrJyIG4GKS25kWnYfESqkk+SDWe

- **Create the QR Code from the Encrypted Base64 String:**
You can directly generate the QR code from the Base64-encoded encrypted data.
Here's the command to create the QR code:
qrencode -o qr_code.png -t PNG "kjiJ34xI+od12zBmUx1eYZHgBtx9KnJiQ43tRHk67WiWv2xo
Replace the string "kjiJ34xI+od12zBmUx1eYZHgBtx9KnJiQ43tRHk67WiWv2xopjQlJnfsxPI7BnRk..." with your actual Base64-encoded encrypted data.
View the QR Code:
After running the above command, you will have the qr_code.png file containing the
QR code. You can view the QR code using an image viewer:

## Summary of Commands
**Action**                  **Command**
View the keys file          cat crypto_keys.txt

Extract Public Key          awk '/-----BEGIN PUBLIC KEY-----/,/-----END PUBLIC KEY-----/' crypto_keys.txt > public_key.pem

Extract Certificate         awk '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/' crypto_keys.txt > certificate.pem

Encrypt a Message and Certificate     openssl pkeyutl -encrypt -inkey public_key.pem -pubin -in data.json -out encrypted_data.txt

Generate QR Code           qrencode -o qr_code.png -t PNG "kjiJ34xI+od12zBmUx1eYZHgBtx9KnJiQ43tRHk67WiWv2xopjQlJnfsxPI7BnRk..


This workflow enables secure encryption using the public key from the downloaded .txt file, adds metadata via the certificate, and facilitates sharing through a QR code.
