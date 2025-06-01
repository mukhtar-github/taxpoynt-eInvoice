import React, { useState, useRef } from 'react';
import { Download, Upload, Shield, Lock, Unlock, CheckCircle, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Alert, AlertDescription } from '../ui/Alert';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { Progress } from '../ui/Progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import apiService from '../../utils/apiService';
import { cn } from '../../utils/cn';
import { Certificate } from '../../types/app';

interface CertificateBackupRestoreProps {
  organizationId: string;
  certificates: Certificate[];
  onBackupComplete?: (backupId: string) => void;
  onRestoreComplete?: (restoredCertificates: Certificate[]) => void;
  className?: string;
}

/**
 * Certificate Backup and Restore Component
 * 
 * Provides functionality for backing up certificates to encrypted archives
 * and restoring certificates from previous backups with password protection.
 */
const CertificateBackupRestore: React.FC<CertificateBackupRestoreProps> = ({
  organizationId,
  certificates,
  onBackupComplete,
  onRestoreComplete,
  className = ''
}) => {
  // References
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Backup state
  const [backupState, setBackupState] = useState<'idle' | 'preparing' | 'encrypting' | 'downloading' | 'complete' | 'error'>('idle');
  const [backupProgress, setBackupProgress] = useState<number>(0);
  const [backupError, setBackupError] = useState<string | null>(null);
  const [backupPassword, setBackupPassword] = useState<string>('');
  const [confirmBackupPassword, setConfirmBackupPassword] = useState<string>('');
  const [selectedCertificates, setSelectedCertificates] = useState<string[]>([]);
  const [backupIncludePrivateKeys, setBackupIncludePrivateKeys] = useState<boolean>(true);
  const [backupResult, setBackupResult] = useState<{id: string, filename: string} | null>(null);
  
  // Restore state
  const [restoreState, setRestoreState] = useState<'idle' | 'uploading' | 'decrypting' | 'validating' | 'complete' | 'error'>('idle');
  const [restoreProgress, setRestoreProgress] = useState<number>(0);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const [restorePassword, setRestorePassword] = useState<string>('');
  const [restoreFile, setRestoreFile] = useState<File | null>(null);
  const [restoreResult, setRestoreResult] = useState<{
    certificatesRestored: number,
    certificateIds: string[]
  } | null>(null);
  
  // Password validation
  const isPasswordValid = (password: string) => {
    // At least 8 characters with a mix of letters, numbers, and special characters
    return password.length >= 8 && 
           /[A-Za-z]/.test(password) && 
           /[0-9]/.test(password) && 
           /[^A-Za-z0-9]/.test(password);
  };
  
  // Password confirmation validation
  const doPasswordsMatch = () => {
    return backupPassword === confirmBackupPassword;
  };
  
  // Toggle certificate selection for backup
  const toggleCertificateSelection = (certId: string) => {
    if (selectedCertificates.includes(certId)) {
      setSelectedCertificates(selectedCertificates.filter(id => id !== certId));
    } else {
      setSelectedCertificates([...selectedCertificates, certId]);
    }
  };
  
  // Select all certificates
  const selectAllCertificates = () => {
    setSelectedCertificates(certificates.map(cert => cert.id));
  };
  
  // Deselect all certificates
  const deselectAllCertificates = () => {
    setSelectedCertificates([]);
  };
  
  // Trigger file input click for restore
  const handleBrowseFiles = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  // Handle file selection for restore
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setRestoreFile(files[0]);
      setRestoreError(null);
    }
  };
  
  // Start backup process
  const handleStartBackup = async () => {
    if (selectedCertificates.length === 0) {
      setBackupError('Please select at least one certificate to backup');
      return;
    }
    
    if (!isPasswordValid(backupPassword)) {
      setBackupError('Password must be at least 8 characters with letters, numbers, and special characters');
      return;
    }
    
    if (!doPasswordsMatch()) {
      setBackupError('Passwords do not match');
      return;
    }
    
    setBackupState('preparing');
    setBackupProgress(10);
    setBackupError(null);
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setBackupProgress(prev => {
          const next = prev + 5;
          if (next >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return next;
        });
      }, 300);
      
      // Start backup process with API
      const response = await apiService.post('/api/v1/certificates/backup', {
        organization_id: organizationId,
        certificate_ids: selectedCertificates,
        include_private_keys: backupIncludePrivateKeys,
        password: backupPassword
      }, {
        responseType: 'blob'
      });
      
      clearInterval(progressInterval);
      setBackupProgress(100);
      
      // Extract backup ID from headers
      const backupId = response.headers['x-backup-id'];
      
      // Get filename from content-disposition header or generate one
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'certificate-backup.zip';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create a download link and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      // Update state
      setBackupState('complete');
      setBackupResult({ id: backupId, filename });
      
      // Reset form after backup
      setBackupPassword('');
      setConfirmBackupPassword('');
      
      // Callback
      if (onBackupComplete) {
        onBackupComplete(backupId);
      }
    } catch (err: any) {
      setBackupState('error');
      setBackupError(err.response?.data?.detail || 'Failed to create backup. Please try again.');
    }
  };
  
  // Start restore process
  const handleStartRestore = async () => {
    if (!restoreFile) {
      setRestoreError('Please select a backup file to restore');
      return;
    }
    
    if (!restorePassword) {
      setRestoreError('Please enter the backup password');
      return;
    }
    
    setRestoreState('uploading');
    setRestoreProgress(10);
    setRestoreError(null);
    
    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', restoreFile);
      formData.append('password', restorePassword);
      formData.append('organization_id', organizationId);
      
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setRestoreProgress(prev => {
          const next = prev + 5;
          if (next >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return next;
        });
      }, 300);
      
      // Start restore process with API
      const response = await apiService.post('/api/v1/certificates/restore', formData);
      
      clearInterval(progressInterval);
      setRestoreProgress(100);
      
      // Update state
      setRestoreState('complete');
      setRestoreResult({
        certificatesRestored: response.data.certificates_restored,
        certificateIds: response.data.certificate_ids
      });
      
      // Reset form after restore
      setRestoreFile(null);
      setRestorePassword('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Callback
      if (onRestoreComplete && response.data.certificate_ids) {
        const restoredCertificates = certificates.filter(
          cert => response.data.certificate_ids.includes(cert.id)
        );
        onRestoreComplete(restoredCertificates);
      }
    } catch (err: any) {
      setRestoreState('error');
      setRestoreError(
        err.response?.data?.detail || 
        'Failed to restore certificates. Please check your file and password.'
      );
    }
  };
  
  // Reset states
  const resetBackup = () => {
    setBackupState('idle');
    setBackupProgress(0);
    setBackupError(null);
    setBackupResult(null);
  };
  
  const resetRestore = () => {
    setRestoreState('idle');
    setRestoreProgress(0);
    setRestoreError(null);
    setRestoreResult(null);
    setRestoreFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  return (
    <Card className={cn('border-l-4 border-cyan-500', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center">
          <Shield className="h-5 w-5 mr-2 text-cyan-500" />
          Certificate Backup & Restore
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="backup" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="backup" className="flex items-center">
              <Download className="h-4 w-4 mr-2" />
              Backup
            </TabsTrigger>
            <TabsTrigger value="restore" className="flex items-center">
              <Upload className="h-4 w-4 mr-2" />
              Restore
            </TabsTrigger>
          </TabsList>
          
          {/* Backup Tab */}
          <TabsContent value="backup" className="mt-4">
            {backupState === 'complete' ? (
              <div className="text-center py-4">
                <div className="flex justify-center mb-4">
                  <div className="bg-green-100 p-3 rounded-full">
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  </div>
                </div>
                
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  Backup Complete
                </h3>
                
                <p className="text-gray-600 mb-4">
                  Your certificates have been backed up successfully. 
                  The backup file has been downloaded to your device.
                </p>
                
                <div className="bg-gray-50 p-3 rounded-md text-sm text-left mb-4">
                  <p><span className="font-medium">Backup ID:</span> {backupResult?.id}</p>
                  <p><span className="font-medium">Filename:</span> {backupResult?.filename}</p>
                  <p><span className="font-medium">Certificates:</span> {selectedCertificates.length}</p>
                </div>
                
                <Button 
                  onClick={resetBackup}
                  className="bg-cyan-600 hover:bg-cyan-700"
                >
                  Create Another Backup
                </Button>
              </div>
            ) : (
              <>
                {backupError && (
                  <Alert variant="error" className="mb-4">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{backupError}</AlertDescription>
                  </Alert>
                )}
                
                {['preparing', 'encrypting', 'downloading'].includes(backupState) && (
                  <div className="mb-6">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium">
                        {backupState === 'preparing' && 'Preparing backup...'}
                        {backupState === 'encrypting' && 'Encrypting certificates...'}
                        {backupState === 'downloading' && 'Generating download...'}
                      </span>
                      <span className="text-sm">{backupProgress}%</span>
                    </div>
                    <Progress value={backupProgress} className="h-2" />
                  </div>
                )}
                
                <div className="space-y-4">
                  {/* Certificate Selection */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-sm font-medium">
                        Select Certificates to Backup
                      </label>
                      <div className="flex space-x-2">
                        <Button 
                          onClick={selectAllCertificates}
                          variant="outline" 
                          size="sm"
                          disabled={backupState !== 'idle'}
                        >
                          Select All
                        </Button>
                        <Button 
                          onClick={deselectAllCertificates}
                          variant="outline" 
                          size="sm"
                          disabled={backupState !== 'idle'}
                        >
                          Clear
                        </Button>
                      </div>
                    </div>
                    
                    <div className="max-h-48 overflow-y-auto border rounded-md p-1">
                      {certificates.length === 0 ? (
                        <div className="p-4 text-center text-gray-500">
                          No certificates available
                        </div>
                      ) : (
                        <div className="space-y-1">
                          {certificates.map(cert => (
                            <div 
                              key={cert.id}
                              className={cn(
                                "flex items-center p-2 rounded cursor-pointer",
                                selectedCertificates.includes(cert.id) 
                                  ? "bg-cyan-50 border border-cyan-200" 
                                  : "hover:bg-gray-50"
                              )}
                              onClick={() => toggleCertificateSelection(cert.id)}
                            >
                              <input 
                                type="checkbox" 
                                checked={selectedCertificates.includes(cert.id)}
                                onChange={() => {}} // Handled by div click
                                className="mr-2"
                                disabled={backupState !== 'idle'}
                              />
                              <div className="flex-1 truncate">
                                <div className="font-medium text-sm truncate">
                                  {cert.subject}
                                </div>
                                <div className="text-xs text-gray-500 flex items-center">
                                  <span className="truncate">
                                    {cert.serial_number}
                                  </span>
                                  <Badge 
                                    className={cn(
                                      "ml-2 text-xs",
                                      cert.status === 'active' 
                                        ? "bg-green-100 text-green-800" 
                                        : "bg-gray-100 text-gray-800"
                                    )}
                                  >
                                    {cert.status}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Options */}
                  <div>
                    <label className="flex items-center space-x-2 mb-4">
                      <input 
                        type="checkbox" 
                        checked={backupIncludePrivateKeys}
                        onChange={() => setBackupIncludePrivateKeys(!backupIncludePrivateKeys)}
                        disabled={backupState !== 'idle'}
                      />
                      <span className="text-sm">Include private keys (requires password protection)</span>
                    </label>
                  </div>
                  
                  {/* Password Protection */}
                  <div className="space-y-3">
                    <div>
                      <label htmlFor="backup-password" className="block text-sm font-medium mb-1">
                        Backup Password
                      </label>
                      <div className="relative">
                        <Input
                          id="backup-password"
                          type="password"
                          value={backupPassword}
                          onChange={(e) => setBackupPassword(e.target.value)}
                          placeholder="Enter a strong password"
                          className="pr-10"
                          disabled={backupState !== 'idle'}
                        />
                        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                          {backupPassword ? (
                            isPasswordValid(backupPassword) ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-amber-500" />
                            )
                          ) : null}
                        </div>
                      </div>
                      {backupPassword && !isPasswordValid(backupPassword) && (
                        <p className="mt-1 text-xs text-amber-600">
                          Password must be at least 8 characters with letters, numbers, and special characters
                        </p>
                      )}
                    </div>
                    
                    <div>
                      <label htmlFor="confirm-backup-password" className="block text-sm font-medium mb-1">
                        Confirm Password
                      </label>
                      <div className="relative">
                        <Input
                          id="confirm-backup-password"
                          type="password"
                          value={confirmBackupPassword}
                          onChange={(e) => setConfirmBackupPassword(e.target.value)}
                          placeholder="Confirm your password"
                          className="pr-10"
                          disabled={backupState !== 'idle'}
                        />
                        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                          {confirmBackupPassword && (
                            doPasswordsMatch() ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-amber-500" />
                            )
                          )}
                        </div>
                      </div>
                      {confirmBackupPassword && !doPasswordsMatch() && (
                        <p className="mt-1 text-xs text-amber-600">
                          Passwords do not match
                        </p>
                      )}
                    </div>
                  </div>
                  
                  {/* Action Button */}
                  <div className="pt-2">
                    <Button 
                      onClick={handleStartBackup}
                      disabled={
                        backupState !== 'idle' ||
                        selectedCertificates.length === 0 ||
                        !isPasswordValid(backupPassword) ||
                        !doPasswordsMatch()
                      }
                      className="w-full bg-cyan-600 hover:bg-cyan-700"
                    >
                      {backupState === 'idle' ? (
                        <>
                          <Download className="h-4 w-4 mr-2" />
                          Create Encrypted Backup
                        </>
                      ) : (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Processing...
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </TabsContent>
          
          {/* Restore Tab */}
          <TabsContent value="restore" className="mt-4">
            {restoreState === 'complete' ? (
              <div className="text-center py-4">
                <div className="flex justify-center mb-4">
                  <div className="bg-green-100 p-3 rounded-full">
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  </div>
                </div>
                
                <h3 className="text-lg font-medium text-green-800 mb-2">
                  Restoration Complete
                </h3>
                
                <p className="text-gray-600 mb-4">
                  {restoreResult?.certificatesRestored} certificates have been successfully restored.
                </p>
                
                <Button 
                  onClick={resetRestore}
                  className="bg-cyan-600 hover:bg-cyan-700"
                >
                  Restore Another Backup
                </Button>
              </div>
            ) : (
              <>
                {restoreError && (
                  <Alert variant="error" className="mb-4">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{restoreError}</AlertDescription>
                  </Alert>
                )}
                
                {['uploading', 'decrypting', 'validating'].includes(restoreState) && (
                  <div className="mb-6">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium">
                        {restoreState === 'uploading' && 'Uploading backup...'}
                        {restoreState === 'decrypting' && 'Decrypting certificates...'}
                        {restoreState === 'validating' && 'Validating certificates...'}
                      </span>
                      <span className="text-sm">{restoreProgress}%</span>
                    </div>
                    <Progress value={restoreProgress} className="h-2" />
                  </div>
                )}
                
                <div className="space-y-4">
                  {/* File Selection */}
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Select Backup File
                    </label>
                    
                    <div className="flex items-center">
                      <Input
                        ref={fileInputRef}
                        type="file"
                        accept=".zip,.enc"
                        onChange={handleFileChange}
                        className="hidden"
                        disabled={restoreState !== 'idle'}
                      />
                      
                      <Button 
                        type="button" 
                        onClick={handleBrowseFiles}
                        variant="outline"
                        className="mr-2"
                        disabled={restoreState !== 'idle'}
                      >
                        Browse...
                      </Button>
                      
                      <div className="flex-1 truncate">
                        {restoreFile ? (
                          <span className="text-sm">{restoreFile.name}</span>
                        ) : (
                          <span className="text-sm text-gray-500">No file selected</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Password */}
                  <div>
                    <label htmlFor="restore-password" className="block text-sm font-medium mb-2">
                      Backup Password
                    </label>
                    <div className="relative">
                      <Input
                        id="restore-password"
                        type="password"
                        value={restorePassword}
                        onChange={(e) => setRestorePassword(e.target.value)}
                        placeholder="Enter the backup password"
                        className="pr-10"
                        disabled={restoreState !== 'idle'}
                      />
                      <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                        {restorePassword ? <Lock className="h-4 w-4 text-gray-500" /> : null}
                      </div>
                    </div>
                  </div>
                  
                  {/* Info */}
                  <Alert className="bg-blue-50 border-blue-200">
                    <AlertTriangle className="h-4 w-4 text-blue-500" />
                    <AlertDescription className="text-blue-800">
                      Restoring certificates will add them to your existing certificates. 
                      Duplicate certificates (with same fingerprint) will be skipped.
                    </AlertDescription>
                  </Alert>
                  
                  {/* Action Button */}
                  <div className="pt-2">
                    <Button 
                      onClick={handleStartRestore}
                      disabled={
                        restoreState !== 'idle' ||
                        !restoreFile ||
                        !restorePassword
                      }
                      className="w-full bg-cyan-600 hover:bg-cyan-700"
                    >
                      {restoreState === 'idle' ? (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          Restore Certificates
                        </>
                      ) : (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Processing...
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default CertificateBackupRestore;
