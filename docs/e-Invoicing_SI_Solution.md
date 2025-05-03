# Evaluation of Proposed FIRS e-Invoicing SI Solution

**Architecture & Rollout Strategy:** The 6‑month phased plan (POC → Prototype → MVP) is generally sound, since FIRS will pilot e‑invoicing with large taxpayers in H2 2025.  A focused MVP for Odoo is acceptable if it fully supports the core e‑invoice flow by pilot time.  However, the schedule is aggressive: FIRS requires completion of development, testing and certification before the pilot.  The phased approach enables iterative feedback, but **each phase must ensure full compliance** with the FIRS specs (UBL format, validation rules, etc.) so no rework is needed later.  Future multi‑ERP support is desirable; starting with Odoo is fine as long as abstraction allows later ERP connectors.  Stakeholder engagement (e.g. FIRS workshops) should guide early phases to catch changes in requirements.  The solution should adopt the BIS Billing 3.0 UBL e‑invoice standard now (as FIRS mandates) and plan to scale securely (e.g. support cloud backup, redundancy) to match FIRS uptime requirements.

* **Timeline Alignment:** FIRS has announced a phased launch beginning July 2025 with a pilot for large taxpayers.  The 6‑month MVP (by \~Nov 2025) can align with pilot timelines if development proceeds without delays.  Risk: FIRS may finalize specs late, so leave buffer for last-minute changes.
* **Phased Features:** The MVP focuses on core functions (IRN generation, signing, submission).  This aligns with an SI’s primary roles – integration, digital signing and API exchange.  Advanced features (analytics, multi‑ERP, BI dashboards) can follow.  Ensure that deferrals (e.g. advanced security hardening, offline caching) do not violate any FIRS minimum requirements.
* **Stakeholder Feedback:** Use FIRS pilot guidance.  Keep the MVP extensible to incorporate feedback (e.g. new data fields, business rules).  Regularly consult FIRS/NITDA bulletins or public workshops to adjust scope.

## Technology Stack and Compliance

FastAPI (Python) and Next.js are modern, capable frameworks for building a secure e‑invoicing SI. FIRS integration is via a RESTful API over HTTPS, so the language/framework is not restricted. However, ensure strong security and compliance:

* **Security & Data Protection:** All FIRS calls must use TLS with up‑to‑date encryption.  In practice, FIRS requires that APs encrypt e‑invoices end-to-end. The SI should enforce HTTPS on all endpoints, securely store private keys/certificates (preferably in a key vault or HSM), and comply with Nigeria’s data protection laws (NDPR).  Railway and Vercel use cloud infrastructure (mostly on AWS/GCP); this is acceptable if configured securely.  *Action:* Verify Railway/Vercel regional hosting; consider dedicated IP/SSL certificates if FIRS mandates static endpoints.
* **Digital Certificates:** System Integrators must manage digital certificates and device registration for cryptographic stamping. The plan should include a secure method to request, store and renew the X.509 certificate used to sign invoices (the “cryptographic stamp”). FastAPI has libraries (e.g. `cryptography`) to apply signatures. Ensure certificate provisioning is integrated (e.g. via a secure API with FIRS).
* **Standards Compliance:** FIRS mandates BIS Billing 3.0 (UBL) invoicing. The solution must output invoices in the UBL XML/JSON schema exactly as specified. Next.js can be used to configure and display integration settings, but invoice payloads must follow the UBL structure. As noted, SIs are explicitly required to ensure adherence to UBL/Peppol or any mandated format. (Peppol identifiers may be needed if FIRS aligns with international frameworks.)
* **ERP Connectivity:** Using FastAPI allows building a backend that connects to Odoo (via XML-RPC or REST) to retrieve invoice data. Ensure data mapping to the UBL schema. Plan to secure Odoo credentials and allow multi-company setups.
* **Regulatory Compliance:** There are *no known prohibitions* against using cloud hosting for FIRS integration. However, FIRS SIs must be **NITDA‑accredited**. This means the owning company (and its technology) must meet Nigerian IT security standards. In practice, register the SI business with CAC in Nigeria, prepare security policies, and pass NITDA’s accreditation (which includes checking that the software meets standards like NDPR). The tech stack must support these (e.g. logging, audit trails).

## Planned Features vs. FIRS Requirements

The MVP’s planned features largely map to FIRS’s SI role:

* **IRN Generation:** *Required.* The SI must call the FIRS “Validate/Sign” API to generate an Invoice Reference Number (IRN). By definition, “SIs generate Invoice Reference Numbers (IRNs) and retrieve invoice details”. The plan includes an IRN generation tool, which is correct. Ensure the payload is complete (all required fields) so FIRS returns the IRN.
* **Cryptographic Signing (CSID):** *Required.* Each invoice must carry a FIRS-issued cryptographic stamp (CSID) – essentially a digital signature – to prevent fraud. The solution must apply the taxpayer’s private key to sign the invoice content before sending. FastAPI can handle the signing process if given the key. The “Sign” endpoint should produce the CSID. The plan notes cryptographic signing, which aligns with “assign a digital signature (CSID)”.
* **Invoice Validation:** *Required.* Before requesting an IRN, the SI should validate the invoice against the FIRS schema. FIRS provides a `/validate` endpoint (or enforces checks on `/sign`). The feature list should explicitly include schema validation (missing or incorrect fields must be caught). The DigiTax guide emphasizes that SIs “validate invoice data to ensure it meets regulatory requirements before submission”. The plan’s “invoice validation” feature is appropriate.
* **Data Encryption:** *Required for transport.* While FIRS expects network (TLS) encryption, if FIRS also requires payload encryption (e.g. encrypt certain fields like IRN), the SI should support that. The security matrix indicates APs encrypt invoices; the SI should at least use HTTPS/TLS. The plan should clarify use of SSL for all API calls and may consider payload-level encryption if specified in docs.
* **Webhook/Notification Handling:** *Recommended.* The FIRS API includes asynchronous notifications. For example, the “/exchange” (transmit) endpoint will send a webhook notification containing the IRN and validation details to involved parties (not public but indicated in FIRS docs). The plan mentions webhooks; ensure endpoints to receive status updates (invoice accepted, rejected, etc.) are implemented so the ERP or user can see real-time status.
* **Monitoring Dashboard:** This is a helpful SI/admin feature. Although not mandated by FIRS, a dashboard to track submitted invoices, IRNs issued, and errors greatly aids operations. Ensure it logs all API interactions (for audit) and flags failures. This meets “compliance assurance” goals even if not strictly required.
* **UI/UX:** While FIRS compliance is achieved via APIs, a modern UI to configure integrations is an advantage (but not a certification requirement). The plan’s emphasis on responsive UI is beneficial for user adoption, though certification focuses on backend functionality.
* **Deferred Features:** Analytics, advanced security (e.g. intrusion detection), and multi‑ERP connectors are planned post-MVP. This is acceptable as long as the **core e‑invoice flow is solid first**. From a certification standpoint, they won’t be required until after initial compliance is proven.

In summary, the MVP covers the essential SI functions (IRN and CSID issuance, data validation, secure submission). The features map well to FIRS’s expectations for SIs. The team should double-check edge cases (e.g. invoice updates or cancellations) in FIRS docs (“/update” endpoint) and ensure the solution can handle those if required by the initial spec.

## Certification Process & Required Support

To achieve **FIRS SI certification**, the integrator must follow FIRS/NITDA procedures beyond just building the software. Key steps include:

* **NITDA Accreditation:** First, the SI company must be accredited by NITDA to provide e‑invoicing services. This involves submitting corporate documents (CAC registration), a security framework, business plan, and achieving the minimum capital requirement (NGN 10 million). The solution must adhere to NITDA’s forthcoming e‑invoice guidelines (standardized formats, security, NDPR compliance).
* **FIRS Registration:** The SI should register on the FIRS e‑Invoicing Portal (once open) to obtain API access credentials. The official site (einvoice.firs.gov.ng) likely has a developer registration process. Contact FIRS or your customer’s FIRS account manager to get sandbox credentials and request digital certificates for signing. (APs have a process to obtain certificates; SIs likely do too.)
* **Documentation Review:** Use the official FIRS API documentation and developer guides. Though not publicly accessible here, FIRS provides spec sheets (invoice schema, endpoint descriptions, sample requests) and testing sandboxes. Ensure you have the latest docs from FIRS Merchant Buyer Solution (MBS) portal. Key resources needed:

  * FIRS MBS **API developer guide** (endpoints: `/taxpayer-auth`, `/validate`, `/sign`, `/confirm`, `/download`, `/update`, `/exchange`, `/report`, etc.).
  * **Invoice Schema** (the required UBL fields and structure).
  * **Testing toolkit** (sample JSON/XML invoices, test certificates, sandbox URLs).
  * **Onboarding instructions** for SIs.
* **Integration Testing:** Perform end-to-end tests in the FIRS sandbox. This typically involves:

  1. Authenticating the taxpayer and SI.
  2. Sending a valid invoice to `/validate`/`/sign` to receive an IRN and CSID.
  3. Transmitting the IRN to the buyer via `/exchange`.
  4. Handling buyer acknowledgements, downloading invoice data, and reporting if B2C.
     Pass all FIRS-provided test cases. Retain logs and screen grabs as proof. FIRS or its appointed testing authority will review these.
* **Final Certification:** After successful sandbox tests, the SI will need official sign-off. This may involve a demo or submission of documentation to FIRS (possibly through a Formal Submission Portal or FIRS helpdesk). Inquiries on specific certification steps should go to the FIRS e-Invoice team or the helpdesk email (not publicly listed yet). It’s recommended to stay engaged with FIRS: ask for technical liaison contacts and attend any training sessions or stakeholder briefings.

By completing NITDA accreditation and FIRS sandbox testing, the solution can be formally certified. Throughout, keep all official documents (test plans, certificate requests, code snippets) organized for audit.

## Recommendations

* **Engage Early with FIRS/NITDA:** Since both agencies are involved, coordinate with them. Begin the NITDA accreditation process immediately. Also seek early access to FIRS’s developer portal for specs. Use the pilot stakeholder meetings (as noted by Sovos) to raise any concerns or questions.
* **Use Official Standards:** Build invoice payloads strictly to the BIS 3.0 UBL schema. Test the JSON/XML against the provided schema validators. Ensure any coding libraries (Python UBL tools, JWT libraries) meet NITDA security standards.
* **Harden Security:** Although advanced security features were deferred, at minimum implement industry best practices now: TLS 1.2+, OWASP protections on the UI, secure storage for keys, routine code reviews. The SI will be subject to audits per NITDA; documentation of the security framework is required.
* **Prepare Test Automation:** Automate the critical workflows (invoice creation, API calls, signature, webhook handling) and run them repeatedly against the sandbox. Automate certificate renewals if possible. This reduces risk of human error during certification tests.
* **Plan for Scalability:** The MVP may serve only one ERP and limited volume, but the target platform (Railway/Vercel) should be vetted for scale. Verify plan to scale up (paid tiers) and use multiple regions or failover if needed. FIRS will process large transaction volumes during pilot, so ensure the SI’s middleware won’t be a bottleneck.
* **Documentation and Training:** Prepare internal technical docs (and user manuals) for the solution referencing FIRS terms and processes. Train support staff so they can address FIRS-related queries. Having clear docs will also help in the NITDA accreditation and any FIRS compliance review.
* **Monitor Regulatory Updates:** The e-invoicing landscape is evolving. Regularly check FIRS and NITDA announcements (e.g. via press releases or the einvoice portal) for changes to the rollout schedule or technical standards. Join industry forums or LinkedIn groups (e.g. FIRS e-invoice developer communities) to stay informed.

By following the official FIRS technical requirements and securing NITDA accreditation, the proposed FastAPI/Next.js SI solution can meet the certification criteria. The architecture and feature scope broadly cover the SI obligations (IRN issuance, signing, validation, secure transmission) as outlined by FIRS. Ensuring close alignment with FIRS documentation and thoroughly testing in their sandbox will be critical for final approval.

**Sources:** Official FIRS e‑Invoicing documentation (developer guides and stakeholder communications) and authoritative analyses. (In absence of public FIRS docs, insights are drawn from FIRS/NITDA policy announcements and industry whitepapers.)
