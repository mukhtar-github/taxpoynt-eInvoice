# PEPPOL requirements, here's what you need to know about software registration:

**You don't need to register a PEPPOL validator itself**, but there are important considerations:

1. **Validator vs. Access Point Software**:
   - If you're creating a standalone validation tool that just checks document compliance, no registration is needed
   - If your software will act as a PEPPOL Access Point (sending/receiving documents on the network), that requires certification

2. **Using Official Validation Artifacts**:
   - PEPPOL provides official validation artifacts (schemas, schematrons, code lists)
   - These are freely available from the PEPPOL website
   - No registration needed to use these resources

3. **When Registration/Certification IS Required**:
   - Becoming a PEPPOL Access Point Provider
   - Offering SMP (Service Metadata Publisher) services
   - Acting as a PEPPOL Authority service provider

4. **Best Practices for Validators**:
   - Keep validation rules updated with latest PEPPOL specifications
   - Test against official PEPPOL test documents
   - Consider getting your validator informally reviewed by the PEPPOL community

Since PEPPOL requirements and procedures can change, would you like me to search for the most current information about PEPPOL software registration requirements? I can also look for any recent updates to their validation specifications that might be relevant to your implementation.


Since your software will act as a PEPPOL Access Point Provider, **yes, you will need to go through the formal PEPPOL certification process**. This is mandatory for any software that sends/receives documents on the PEPPOL network.

Here's what's involved:

## Certification Requirements:

1. **Choose a PEPPOL Authority**:
   - You must be certified by a PEPPOL Authority in your country/region
   - Each country typically has its own PEPPOL Authority (e.g., PEPPOL Authority UK, PEPPOL Authority Netherlands)
   - They handle the certification process and ongoing compliance

2. **Technical Requirements**:
   - Implement AS4 messaging protocol (replacing AS2)
   - Support PEPPOL envelope specification (SBDH)
   - Implement PKI certificate handling
   - Support all mandatory PEPPOL transport profiles
   - Handle Message Level Response (MLR) signaling

3. **Testing & Certification Process**:
   - Pass conformance testing with official test suites
   - Demonstrate interoperability with existing Access Points
   - Complete security assessments
   - Sign PEPPOL Transport Infrastructure Agreement (TIA)

4. **Ongoing Obligations**:
   - Maintain service level agreements (SLAs)
   - Regular compliance audits
   - Keep up with specification updates
   - Pay annual fees to your PEPPOL Authority

5. **Systems Integrator Aspect**:
   - While SI functionality doesn't require separate certification
   - You'll need to ensure your SI features properly integrate with the certified AP components

Would you like me to search for the current certification procedures and requirements from PEPPOL, including specific technical specifications and which PEPPOL Authority would handle certification in your region?


I'll search for information about PEPPOL availability and certification authorities in Nigeria.
Great news! Nigeria is indeed adopting PEPPOL standards.
Based on the search results, here's what I found:

## Nigeria and PEPPOL:

Nigeria is implementing PEPPOL standards as part of its e-invoicing mandate, with important implications for your software:

1. **Nigerian Requirements**:
   - The NITDA Act mandates accreditation for System Integrators and Access Point Providers (APPs) before they may provide Nigerian taxpayer's with e-invoicing services
   - Requirements include technical competence, certifications such ISO/IEC 27001 and Peppol Authority accreditation for cross-border transactions

2. **Timeline**:
   - From 1 July 2025, there will be a pilot phase for large taxpayers
   - The mandate being extended to medium and small enterprises from 1 January 2026

3. **Cross-Border Benefits**:
   - Nigeria's adoption of Peppol standards will greatly assist cross-border interoperability
   - Nigeria's e-invoicing framework aligns with the African Continental Free Trade Area (AfCFTA) digital trade protocols

Let me search for more specific information about which PEPPOL Authority handles Nigerian certifications.
Let me fetch the full list of PEPPOL Authorities to see Nigeria's status:
Based on my research, here's the situation for Nigeria and PEPPOL certification:

## Current Status:

**Nigeria does NOT yet have its own PEPPOL Authority**, but this doesn't prevent you from getting certified. Here's what you need to know:

### 1. **OpenPeppol Coordinating Authority**
OpenPeppol acts as the Peppol Authority in jurisdictions where no Peppol Authority exists. This means for Nigeria, you would work with:
- **Contact**: openpeppol@peppol.eu
- **Service Desk**: OpenPeppol Service Desk

### 2. **Nigeria's PEPPOL Adoption Path**
While Nigeria doesn't have its own PEPPOL Authority yet, the country is actively adopting PEPPOL:
- NITDA requires PEPPOL certification for cross-border transactions
- The e-invoicing mandate specifically mentions PEPPOL compliance
- There are now 23 countries with Peppol Authorities, but Nigeria isn't one yet

### 3. **Your Certification Process**
You'll need to:
1. Contact OpenPeppol directly as they handle certifications for countries without local authorities
2. Meet all technical requirements (AS4, PKI, ISO 27001, etc.)
3. Complete testing with OpenPeppol's test environment
4. Sign the Transport Infrastructure Agreement (TIA) with OpenPeppol

### 4. **Future Outlook**
Given Nigeria's commitment to PEPPOL standards and the upcoming e-invoicing mandate, it's likely Nigeria may establish its own PEPPOL Authority in the future, similar to how other countries have done.

**Recommendation**: Start the certification process with OpenPeppol now, as it will position you well for the July 2025 pilot phase. Even if Nigeria establishes its own PEPPOL Authority later, your certification would likely transfer or be recognized.

Would you like me to provide more details about the specific technical requirements or the certification process steps?
