import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { MailIcon, PhoneIcon, MapPinIcon, ClockIcon } from '@heroicons/react/24/outline';
import MainLayout from '../components/layouts/MainLayout';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { FormField } from '../components/ui/FormField';

interface ContactForm {
  name: string;
  email: string;
  company: string;
  phone: string;
  plan: string;
  message: string;
}

const Contact: React.FC = () => {
  const router = useRouter();
  const [form, setForm] = useState<ContactForm>({
    name: '',
    email: '',
    company: '',
    phone: '',
    plan: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Get plan from URL params (coming from pricing page)
  useEffect(() => {
    const { plan } = router.query;
    if (plan && typeof plan === 'string') {
      setForm(prev => ({ ...prev, plan: plan.charAt(0).toUpperCase() + plan.slice(1) }));
    }
  }, [router.query]);

  const handleInputChange = (field: keyof ContactForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Here you would integrate with your backend API
      // For now, we'll simulate a successful submission
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSubmitted(true);
      
      // Reset form
      setForm({
        name: '',
        email: '',
        company: '',
        phone: '',
        plan: form.plan, // Keep the plan if it came from URL
        message: ''
      });
    } catch (error) {
      console.error('Error submitting contact form:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const contactInfo = [
    {
      icon: MailIcon,
      title: 'Email',
      details: 'sales@taxpoynt.com',
      description: 'Send us an email anytime!'
    },
    {
      icon: PhoneIcon,
      title: 'Phone',
      details: '+234 (0) 809-123-4567',
      description: 'Mon-Fri from 8am to 5pm WAT'
    },
    {
      icon: MapPinIcon,
      title: 'Office',
      details: 'Lagos, Nigeria',
      description: 'Visit our headquarters'
    },
    {
      icon: ClockIcon,
      title: 'Response Time',
      details: '< 2 hours',
      description: 'We respond quickly to all inquiries'
    }
  ];

  if (submitted) {
    return (
      <MainLayout>
        <Head>
          <title>Thank You - TaxPoynt eInvoice</title>
          <meta name="description" content="Thank you for contacting TaxPoynt eInvoice. We'll be in touch soon!" />
        </Head>
        
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center px-4">
          <Card className="max-w-md w-full p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h1>
            <p className="text-gray-600 mb-6">
              We've received your message and will get back to you within 2 hours during business hours.
            </p>
            <div className="space-y-3">
              <Button 
                variant="primary" 
                className="w-full"
                onClick={() => router.push('/pricing')}
              >
                View Pricing
              </Button>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => router.push('/')}
              >
                Back to Home
              </Button>
            </div>
          </Card>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <Head>
        <title>Contact Sales - TaxPoynt eInvoice | Get FIRS Compliant Today</title>
        <meta 
          name="description" 
          content="Contact TaxPoynt eInvoice sales team for enterprise solutions, custom integrations, and FIRS compliance consulting. Get in touch today!" 
        />
        <meta name="keywords" content="TaxPoynt contact, FIRS invoice sales, Nigerian e-invoice support" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
        {/* Hero Section */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <div className="text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Get in Touch with Our Team
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                Ready to get FIRS compliant? Have questions about our platform? 
                Our Nigerian e-invoicing experts are here to help.
              </p>
              {form.plan && (
                <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  Interested in: {form.plan} Plan
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid lg:grid-cols-3 gap-12">
            {/* Contact Information */}
            <div className="lg:col-span-1">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Contact Information</h2>
              <p className="text-gray-600 mb-8">
                We're here to help you achieve FIRS compliance and streamline your invoicing process.
              </p>

              <div className="space-y-6">
                {contactInfo.map((item, index) => (
                  <div key={index} className="flex items-start">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <item.icon className="w-5 h-5 text-blue-600" />
                      </div>
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-medium text-gray-900">{item.title}</h3>
                      <p className="text-gray-900 font-medium">{item.details}</p>
                      <p className="text-sm text-gray-600">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* WhatsApp Contact */}
              <Card className="p-6 mt-8 bg-green-50 border-green-200">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.148"/>
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="font-medium text-gray-900">WhatsApp Business</h3>
                    <p className="text-sm text-gray-600">For quick questions and support</p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  className="w-full border-green-600 text-green-600 hover:bg-green-600 hover:text-white"
                  onClick={() => window.open('https://wa.me/2348091234567?text=Hello%20TaxPoynt!%20I%27m%20interested%20in%20FIRS%20e-invoicing%20compliance.', '_blank')}
                >
                  Chat on WhatsApp
                </Button>
              </Card>
            </div>

            {/* Contact Form */}
            <div className="lg:col-span-2">
              <Card className="p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Send us a Message</h2>
                
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <FormField label="Full Name" required>
                      <Input
                        type="text"
                        value={form.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        placeholder="John Doe"
                        required
                      />
                    </FormField>

                    <FormField label="Email Address" required>
                      <Input
                        type="email"
                        value={form.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="john@company.com"
                        required
                      />
                    </FormField>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <FormField label="Company Name" required>
                      <Input
                        type="text"
                        value={form.company}
                        onChange={(e) => handleInputChange('company', e.target.value)}
                        placeholder="Your Company Ltd"
                        required
                      />
                    </FormField>

                    <FormField label="Phone Number">
                      <Input
                        type="tel"
                        value={form.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        placeholder="+234 809 123 4567"
                      />
                    </FormField>
                  </div>

                  <FormField label="Interested Plan">
                    <select
                      value={form.plan}
                      onChange={(e) => handleInputChange('plan', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select a plan</option>
                      <option value="Starter">Starter - ₦25,000/month</option>
                      <option value="Business">Business - ₦75,000/month</option>
                      <option value="Enterprise">Enterprise - ₦150,000/month</option>
                      <option value="Enterprise+">Enterprise+ - Custom pricing</option>
                      <option value="Custom">Custom Solution</option>
                    </select>
                  </FormField>

                  <FormField label="Message" required>
                    <Textarea
                      value={form.message}
                      onChange={(e) => handleInputChange('message', e.target.value)}
                      placeholder="Tell us about your business requirements, current invoicing challenges, or any questions about FIRS compliance..."
                      rows={5}
                      required
                    />
                  </FormField>

                  <div className="flex flex-col sm:flex-row gap-4">
                    <Button
                      type="submit"
                      variant="primary"
                      className="flex-1"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? 'Sending...' : 'Send Message'}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => router.push('/pricing')}
                    >
                      View Pricing
                    </Button>
                  </div>

                  <p className="text-sm text-gray-600">
                    By submitting this form, you agree to our privacy policy. 
                    We'll only use your information to respond to your inquiry and provide relevant updates about our services.
                  </p>
                </form>
              </Card>
            </div>
          </div>

          {/* Why Choose TaxPoynt Section */}
          <Card className="p-8 mt-16 bg-blue-50 border-blue-200">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Why Choose TaxPoynt eInvoice?
              </h2>
              <p className="text-gray-600">
                Join thousands of Nigerian businesses already using our platform
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="font-bold text-gray-900 mb-2">FIRS Certified</h3>
                <p className="text-sm text-gray-600">
                  Official FIRS certification with guaranteed compliance and penalty protection
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="font-bold text-gray-900 mb-2">Fast Implementation</h3>
                <p className="text-sm text-gray-600">
                  Get FIRS compliant in 24 hours with our quick setup and onboarding process
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25a9.75 9.75 0 109.75 9.75A9.75 9.75 0 0012 2.25z" />
                  </svg>
                </div>
                <h3 className="font-bold text-gray-900 mb-2">Expert Support</h3>
                <p className="text-sm text-gray-600">
                  Nigerian regulatory experts available to help with compliance and integration
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
};

export default Contact;