import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { cn } from '../../utils/cn';
import apiService from '../../utils/apiService';
import { CertificateType } from '../../types/app';

interface CertificateRequestWizardProps {
  isOpen: boolean;
  onClose: () => void;
  organizationId: string;
  onRequestComplete: () => void;
}

// Wizard step definitions
type WizardStep = 'type' | 'subject' | 'key' | 'review' | 'submit';

const CertificateRequestWizard: React.FC<CertificateRequestWizardProps> = ({
  isOpen,
  onClose,
  organizationId,
  onRequestComplete
}) => {
  // State for tracking current step
  const [currentStep, setCurrentStep] = useState<WizardStep>('type');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  
  // State for collecting form data across steps
  const [requestData, setRequestData] = useState({
    certificateType: '' as CertificateType,
    subjectInfo: {
      commonName: '',
      organization: '',
      organizationalUnit: '',
      country: '',
      state: '',
      locality: '',
      email: ''
    },
    keyInfo: {
      keySize: 2048,
      keyAlgorithm: 'RSA'
    },
    comment: ''
  });
  
  // Navigation functions
  const goToNextStep = () => {
    switch (currentStep) {
      case 'type':
        setCurrentStep('subject');
        break;
      case 'subject':
        setCurrentStep('key');
        break;
      case 'key':
        setCurrentStep('review');
        break;
      case 'review':
        setCurrentStep('submit');
        handleSubmit();
        break;
    }
  };
  
  const goToPreviousStep = () => {
    switch (currentStep) {
      case 'subject':
        setCurrentStep('type');
        break;
      case 'key':
        setCurrentStep('subject');
        break;
      case 'review':
        setCurrentStep('key');
        break;
    }
  };
  
  // Update form data based on step
  const updateTypeData = (type: CertificateType) => {
    setRequestData(prev => ({
      ...prev,
      certificateType: type
    }));
  };
  
  const updateSubjectData = (subjectData: typeof requestData.subjectInfo) => {
    setRequestData(prev => ({
      ...prev,
      subjectInfo: {
        ...prev.subjectInfo,
        ...subjectData
      }
    }));
  };
  
  const updateKeyData = (keyData: typeof requestData.keyInfo, comment: string) => {
    setRequestData(prev => ({
      ...prev,
      keyInfo: {
        ...prev.keyInfo,
        ...keyData
      },
      comment: comment
    }));
  };
  
  // Final submission
  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    
    try {
      const response = await apiService.post('/api/v1/certificate-requests', {
        organization_id: organizationId,
        request_type: 'new',
        subject_info: {
          common_name: requestData.subjectInfo.commonName,
          organization: requestData.subjectInfo.organization,
          organizational_unit: requestData.subjectInfo.organizationalUnit || undefined,
          country: requestData.subjectInfo.country,
          state: requestData.subjectInfo.state || undefined,
          locality: requestData.subjectInfo.locality || undefined,
          email: requestData.subjectInfo.email || undefined
        },
        certificate_type: requestData.certificateType,
        key_size: requestData.keyInfo.keySize,
        key_algorithm: requestData.keyInfo.keyAlgorithm,
        comment: requestData.comment || undefined
      });
      
      setSuccess(true);
      setTimeout(() => {
        onRequestComplete();
        onClose();
      }, 2000);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit certificate request');
      setCurrentStep('review');
    } finally {
      setSubmitting(false);
    }
  };
  
  // Close handling
  const handleClose = () => {
    if (!submitting) {
      onClose();
    }
  };
  
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl mx-4">
        {/* Header */}
        <div className="border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold">Request New Certificate</h2>
          <button 
            onClick={handleClose}
            disabled={submitting}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
        
        {/* Progress Indicator */}
        <div className="px-6 pt-4">
          <div className="flex justify-between mb-2">
            {['Certificate Type', 'Subject Information', 'Key Options', 'Review'].map((step, index) => (
              <div 
                key={step} 
                className={cn(
                  'text-xs font-medium',
                  index === 0 && currentStep === 'type' ? 'text-blue-600' : '',
                  index === 1 && currentStep === 'subject' ? 'text-blue-600' : '',
                  index === 2 && currentStep === 'key' ? 'text-blue-600' : '',
                  index === 3 && currentStep === 'review' ? 'text-blue-600' : '',
                  (currentStep === 'submit' || success) ? 'text-gray-400' : '',
                  // If step is passed
                  (
                    (index === 0 && ['subject', 'key', 'review'].includes(currentStep)) ||
                    (index === 1 && ['key', 'review'].includes(currentStep)) ||
                    (index === 2 && ['review'].includes(currentStep))
                  ) ? 'text-gray-500' : 'text-gray-400'
                )}
              >
                {step}
              </div>
            ))}
          </div>
          <div className="h-2 bg-gray-200 rounded-full">
            <div
              className={cn(
                'h-full bg-blue-600 rounded-full transition-all',
                currentStep === 'type' ? 'w-1/4' : '',
                currentStep === 'subject' ? 'w-1/2' : '',
                currentStep === 'key' ? 'w-3/4' : '',
                (currentStep === 'review' || currentStep === 'submit') ? 'w-full' : ''
              )}
            />
          </div>
        </div>
        
        {/* Step Content */}
        <div className="px-6 py-4">
          {/* Type Selection Step */}
          {currentStep === 'type' && (
            <TypeSelectionStep 
              selectedType={requestData.certificateType}
              onTypeSelect={updateTypeData}
            />
          )}
          
          {/* Subject Information Step */}
          {currentStep === 'subject' && (
            <SubjectInfoStep
              subjectData={requestData.subjectInfo}
              onSubjectDataUpdate={updateSubjectData}
            />
          )}
          
          {/* Key Options Step */}
          {currentStep === 'key' && (
            <KeyOptionsStep
              keyData={requestData.keyInfo}
              comment={requestData.comment}
              onKeyDataUpdate={updateKeyData}
            />
          )}
          
          {/* Review Step */}
          {currentStep === 'review' && (
            <ReviewStep
              requestData={requestData}
              organizationId={organizationId}
            />
          )}
          
          {/* Submit Step */}
          {currentStep === 'submit' && (
            <div className="text-center py-10">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
              <p>Submitting your certificate request...</p>
            </div>
          )}
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="px-6 mb-4">
            <div className="bg-red-50 text-red-800 p-3 rounded border border-red-200">
              <p>{error}</p>
            </div>
          </div>
        )}
        
        {/* Success Message */}
        {success && (
          <div className="px-6 mb-4">
            <div className="bg-green-50 text-green-800 p-3 rounded border border-green-200">
              <p>Certificate request submitted successfully!</p>
            </div>
          </div>
        )}
        
        {/* Footer with Navigation Buttons */}
        <div className="px-6 py-4 border-t flex justify-between">
          <button
            onClick={currentStep === 'type' ? handleClose : goToPreviousStep}
            disabled={submitting}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            {currentStep === 'type' ? 'Cancel' : 'Back'}
          </button>
          
          <button
            onClick={goToNextStep}
            disabled={
              submitting ||
              (currentStep === 'type' && !requestData.certificateType) ||
              // Add other validation conditions for subsequent steps
              currentStep === 'submit'
            }
            className={cn(
              'px-4 py-2 text-sm text-white rounded',
              submitting ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700',
              (
                (currentStep === 'type' && !requestData.certificateType) ||
                currentStep === 'submit'
              ) ? 'opacity-50 cursor-not-allowed' : ''
            )}
          >
            {submitting ? 'Submitting...' :
             currentStep === 'review' ? 'Submit Request' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Certificate Type Selection Step Component
interface TypeSelectionStepProps {
  selectedType: CertificateType;
  onTypeSelect: (type: CertificateType) => void;
}

const TypeSelectionStep: React.FC<TypeSelectionStepProps> = ({ 
  selectedType, 
  onTypeSelect 
}) => {
  const certificateTypes = [
    {
      id: 'access_point',
      title: 'Access Point Certificate',
      description: 'Used for secure communications with FIRS API as an Access Point Provider (APP).',
      icon: '🔐'
    },
    {
      id: 'authentication',
      title: 'Authentication Certificate',
      description: 'Used for authenticating to FIRS services and APIs.',
      icon: '🔒'
    },
    {
      id: 'signing',
      title: 'Signing Certificate',
      description: 'Used for digitally signing invoices and documents.',
      icon: '✍️'
    }
  ];

  return (
    <div>
      <h3 className="text-lg font-medium mb-2">Select Certificate Type</h3>
      <p className="text-sm text-gray-600 mb-4">
        Choose the type of certificate you need based on your integration requirements.
      </p>
      
      <div className="space-y-3">
        {certificateTypes.map(type => (
          <div
            key={type.id}
            onClick={() => onTypeSelect(type.id as CertificateType)}
            className={cn(
              'border rounded-lg p-4 cursor-pointer transition-colors',
              selectedType === type.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:bg-gray-50'
            )}
          >
            <div className="flex">
              <div className="text-2xl mr-3">{type.icon}</div>
              <div>
                <h4 className="font-medium">{type.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{type.description}</p>
              </div>
              {selectedType === type.id && (
                <div className="ml-auto text-blue-600">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Subject Information Step Component
interface SubjectInfoStepProps {
  subjectData: {
    commonName: string;
    organization: string;
    organizationalUnit: string;
    country: string;
    state: string;
    locality: string;
    email: string;
  };
  onSubjectDataUpdate: (data: SubjectInfoStepProps['subjectData']) => void;
}

const SubjectInfoStep: React.FC<SubjectInfoStepProps> = ({ 
  subjectData, 
  onSubjectDataUpdate 
}) => {
  const { register, formState: { errors }, handleSubmit } = useForm({
    defaultValues: subjectData,
    mode: 'onChange'
  });

  const onSubmit = (data: SubjectInfoStepProps['subjectData']) => {
    onSubjectDataUpdate(data);
  };

  // Auto-save as fields change
  const handleFieldChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    // Build a new object with just the changed field
    const updatedData = { ...subjectData, [name]: value };
    onSubjectDataUpdate(updatedData);
  };

  // Country codes for dropdown
  const countryCodes = [
    { code: 'NG', name: 'Nigeria' },
    { code: 'US', name: 'United States' },
    { code: 'GB', name: 'United Kingdom' },
    { code: 'CA', name: 'Canada' },
    { code: 'AU', name: 'Australia' },
    { code: 'FR', name: 'France' },
    { code: 'DE', name: 'Germany' },
    // Add more countries as needed
  ];

  return (
    <div>
      <h3 className="text-lg font-medium mb-2">Subject Information</h3>
      <p className="text-sm text-gray-600 mb-4">
        Enter the information to be included in your certificate.
      </p>
      
      <form onChange={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-1 gap-4">
          {/* Common Name */}
          <div>
            <label htmlFor="commonName" className="block text-sm font-medium text-gray-700 mb-1">
              Common Name (CN) <span className="text-red-600">*</span>
            </label>
            <input
              id="commonName"
              type="text"
              {...register('commonName', { required: true })}
              onChange={handleFieldChange}
              className={cn(
                'w-full px-3 py-2 border rounded-md',
                errors.commonName ? 'border-red-500' : 'border-gray-300'
              )}
              placeholder="e.g. taxpoynt.app.example.com"
            />
            {errors.commonName && (
              <p className="mt-1 text-sm text-red-600">Common Name is required</p>
            )}
          </div>
          
          {/* Organization */}
          <div>
            <label htmlFor="organization" className="block text-sm font-medium text-gray-700 mb-1">
              Organization (O) <span className="text-red-600">*</span>
            </label>
            <input
              id="organization"
              type="text"
              {...register('organization', { required: true })}
              onChange={handleFieldChange}
              className={cn(
                'w-full px-3 py-2 border rounded-md',
                errors.organization ? 'border-red-500' : 'border-gray-300'
              )}
              placeholder="e.g. Your Company Ltd"
            />
            {errors.organization && (
              <p className="mt-1 text-sm text-red-600">Organization is required</p>
            )}
          </div>
          
          {/* Organizational Unit */}
          <div>
            <label htmlFor="organizationalUnit" className="block text-sm font-medium text-gray-700 mb-1">
              Organizational Unit (OU)
            </label>
            <input
              id="organizationalUnit"
              type="text"
              {...register('organizationalUnit')}
              onChange={handleFieldChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g. IT Department"
            />
          </div>

          {/* Country */}
          <div>
            <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
              Country (C) <span className="text-red-600">*</span>
            </label>
            <select
              id="country"
              {...register('country', { required: true })}
              onChange={(e) => handleFieldChange(e as unknown as React.ChangeEvent<HTMLInputElement>)}
              className={cn(
                'w-full px-3 py-2 border rounded-md',
                errors.country ? 'border-red-500' : 'border-gray-300'
              )}
            >
              <option value="">Select a country</option>
              {countryCodes.map(country => (
                <option key={country.code} value={country.code}>
                  {country.name} ({country.code})
                </option>
              ))}
            </select>
            {errors.country && (
              <p className="mt-1 text-sm text-red-600">Country is required</p>
            )}
          </div>

          {/* State/Province */}
          <div>
            <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
              State/Province (ST)
            </label>
            <input
              id="state"
              type="text"
              {...register('state')}
              onChange={handleFieldChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g. Lagos"
            />
          </div>

          {/* Locality */}
          <div>
            <label htmlFor="locality" className="block text-sm font-medium text-gray-700 mb-1">
              Locality (L)
            </label>
            <input
              id="locality"
              type="text"
              {...register('locality')}
              onChange={handleFieldChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g. Victoria Island"
            />
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              {...register('email', { 
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: "Invalid email address"
                }
              })}
              onChange={handleFieldChange}
              className={cn(
                'w-full px-3 py-2 border rounded-md',
                errors.email ? 'border-red-500' : 'border-gray-300'
              )}
              placeholder="e.g. admin@example.com"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>
        </div>
      </form>
      
      <div className="mt-6 bg-gray-50 p-4 rounded-md border border-gray-200">
        <h4 className="text-sm font-medium text-gray-700">Certificate Subject Preview</h4>
        <p className="mt-2 text-xs font-mono break-all">
          CN={subjectData.commonName}, 
          O={subjectData.organization}
          {subjectData.organizationalUnit && `, OU=${subjectData.organizationalUnit}`}
          {subjectData.country && `, C=${subjectData.country}`}
          {subjectData.state && `, ST=${subjectData.state}`}
          {subjectData.locality && `, L=${subjectData.locality}`}
          {subjectData.email && `, E=${subjectData.email}`}
        </p>
      </div>
    </div>
  );
};

// Key Options Step Component
interface KeyOptionsStepProps {
  keyData: {
    keySize: number;
    keyAlgorithm: string;
  };
  comment: string;
  onKeyDataUpdate: (keyData: KeyOptionsStepProps['keyData'], comment: string) => void;
}

const KeyOptionsStep: React.FC<KeyOptionsStepProps> = ({ 
  keyData, 
  comment,
  onKeyDataUpdate 
}) => {
  // State to track current values
  const [localKeyData, setLocalKeyData] = useState(keyData);
  const [localComment, setLocalComment] = useState(comment);
  
  // Update parent component when values change
  useEffect(() => {
    onKeyDataUpdate(localKeyData, localComment);
  }, [localKeyData, localComment]);
  
  // Key size options
  const keySizeOptions = [2048, 3072, 4096];
  
  // Key algorithm options
  const keyAlgorithmOptions = ['RSA', 'ECDSA'];
  
  // Handle key size change
  const handleKeySizeChange = (size: number) => {
    setLocalKeyData(prev => ({ ...prev, keySize: size }));
  };
  
  // Handle key algorithm change
  const handleKeyAlgorithmChange = (algorithm: string) => {
    setLocalKeyData(prev => ({ ...prev, keyAlgorithm: algorithm }));
  };
  
  return (
    <div>
      <h3 className="text-lg font-medium mb-2">Key Options</h3>
      <p className="text-sm text-gray-600 mb-4">
        Configure the cryptographic options for your certificate.
      </p>
      
      <div className="space-y-6">
        {/* Key Size Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Key Size
          </label>
          <div className="flex space-x-4">
            {keySizeOptions.map(size => (
              <div key={size} className="flex items-center">
                <input
                  type="radio"
                  id={`size-${size}`}
                  name="keySize"
                  value={size}
                  checked={localKeyData.keySize === size}
                  onChange={() => handleKeySizeChange(size)}
                  className="mr-2"
                />
                <label htmlFor={`size-${size}`} className="text-sm">
                  {size} bits
                </label>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Larger key sizes provide stronger security but may impact performance.
          </p>
        </div>
        
        {/* Key Algorithm Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Key Algorithm
          </label>
          <div className="flex space-x-4">
            {keyAlgorithmOptions.map(algorithm => (
              <div key={algorithm} className="flex items-center">
                <input
                  type="radio"
                  id={`algo-${algorithm}`}
                  name="keyAlgorithm"
                  value={algorithm}
                  checked={localKeyData.keyAlgorithm === algorithm}
                  onChange={() => handleKeyAlgorithmChange(algorithm)}
                  className="mr-2"
                />
                <label htmlFor={`algo-${algorithm}`} className="text-sm">
                  {algorithm}
                </label>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-500">
            RSA is widely supported. ECDSA provides similar security with smaller key sizes.
          </p>
        </div>
        
        {/* Additional Comments */}
        <div>
          <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
            Additional Comments (optional)
          </label>
          <textarea
            id="comment"
            rows={3}
            value={localComment}
            onChange={(e) => setLocalComment(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="Add any additional information about this certificate request"
          />
        </div>
      </div>
      
      <div className="mt-6 bg-gray-50 p-4 rounded-md border border-gray-200">
        <h4 className="text-sm font-medium text-gray-700">Security Information</h4>
        <p className="mt-2 text-xs text-gray-600">
          Your private key will be generated securely within your TaxPoynt environment. 
          The private key will never leave your system, while only the Certificate Signing Request (CSR) 
          will be submitted to the certificate authority.
        </p>
      </div>
    </div>
  );
};

// Review Step Component
interface ReviewStepProps {
  requestData: {
    certificateType: CertificateType;
    subjectInfo: {
      commonName: string;
      organization: string;
      organizationalUnit: string;
      country: string;
      state: string;
      locality: string;
      email: string;
    };
    keyInfo: {
      keySize: number;
      keyAlgorithm: string;
    };
    comment: string;
  };
  organizationId: string;
}

const ReviewStep: React.FC<ReviewStepProps> = ({ requestData, organizationId }) => {
  // Function to get readable certificate type
  const getCertificateTypeDisplay = (type: CertificateType) => {
    switch (type) {
      case 'access_point':
        return 'Access Point Certificate';
      case 'authentication':
        return 'Authentication Certificate';
      case 'signing':
        return 'Signing Certificate';
      default:
        return type;
    }
  };

  return (
    <div>
      <h3 className="text-lg font-medium mb-2">Review Certificate Request</h3>
      <p className="text-sm text-gray-600 mb-4">
        Please review your certificate request details before submission.
      </p>
      
      <div className="space-y-6">
        {/* Certificate Type */}
        <div className="border-t border-b border-gray-200 py-4">
          <h4 className="text-sm font-semibold text-gray-700">Certificate Type</h4>
          <p className="mt-1">
            {getCertificateTypeDisplay(requestData.certificateType)}
          </p>
        </div>
        
        {/* Subject Information */}
        <div className="border-b border-gray-200 py-4">
          <h4 className="text-sm font-semibold text-gray-700">Subject Information</h4>
          <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
            <div>
              <p className="text-xs text-gray-500">Common Name (CN)</p>
              <p className="text-sm">{requestData.subjectInfo.commonName}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Organization (O)</p>
              <p className="text-sm">{requestData.subjectInfo.organization}</p>
            </div>
            {requestData.subjectInfo.organizationalUnit && (
              <div>
                <p className="text-xs text-gray-500">Organizational Unit (OU)</p>
                <p className="text-sm">{requestData.subjectInfo.organizationalUnit}</p>
              </div>
            )}
            <div>
              <p className="text-xs text-gray-500">Country (C)</p>
              <p className="text-sm">{requestData.subjectInfo.country}</p>
            </div>
            {requestData.subjectInfo.state && (
              <div>
                <p className="text-xs text-gray-500">State/Province (ST)</p>
                <p className="text-sm">{requestData.subjectInfo.state}</p>
              </div>
            )}
            {requestData.subjectInfo.locality && (
              <div>
                <p className="text-xs text-gray-500">Locality (L)</p>
                <p className="text-sm">{requestData.subjectInfo.locality}</p>
              </div>
            )}
            {requestData.subjectInfo.email && (
              <div>
                <p className="text-xs text-gray-500">Email</p>
                <p className="text-sm">{requestData.subjectInfo.email}</p>
              </div>
            )}
          </div>
        </div>
        
        {/* Key Options */}
        <div className="border-b border-gray-200 py-4">
          <h4 className="text-sm font-semibold text-gray-700">Key Options</h4>
          <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
            <div>
              <p className="text-xs text-gray-500">Key Size</p>
              <p className="text-sm">{requestData.keyInfo.keySize} bits</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Key Algorithm</p>
              <p className="text-sm">{requestData.keyInfo.keyAlgorithm}</p>
            </div>
          </div>
        </div>
        
        {/* Comments */}
        {requestData.comment && (
          <div className="border-b border-gray-200 py-4">
            <h4 className="text-sm font-semibold text-gray-700">Additional Comments</h4>
            <p className="mt-2 text-sm whitespace-pre-wrap">{requestData.comment}</p>
          </div>
        )}
        
        {/* Organization Info */}
        <div className="py-4">
          <h4 className="text-sm font-semibold text-gray-700">Organization ID</h4>
          <p className="mt-1 text-sm font-mono">{organizationId}</p>
        </div>
      </div>
      
      <div className="mt-6 bg-yellow-50 p-4 rounded-md border border-yellow-200">
        <h4 className="text-sm font-medium text-yellow-800">Important Information</h4>
        <ul className="mt-2 text-xs text-yellow-700 list-disc pl-5 space-y-1">
          <li>Certificate requests may take up to 24-48 hours to be processed.</li>
          <li>You will receive an email notification when your certificate is ready.</li>
          <li>After approval, you'll be able to download your certificate from the dashboard.</li>
          <li>Keep your private key secure - it will only be available during the initial download.</li>
        </ul>
      </div>
    </div>
  );
};

export default CertificateRequestWizard;
