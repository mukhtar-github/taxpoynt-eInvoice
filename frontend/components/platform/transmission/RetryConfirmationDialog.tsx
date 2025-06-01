import React, { useState } from 'react';
import { AlertCircle, RotateCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Label } from '@/components/ui/Label';
import { Input } from '@/components/ui/Input';
import { Switch } from '@/components/ui/Switch';

interface RetryConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (maxRetries: number, retryDelay: number, force: boolean) => void;
  transmissionId: string;
  isLoading: boolean;
}

/**
 * Dialog component for configuring and confirming transmission retry parameters
 * Allows users to set:
 * - Maximum number of retry attempts
 * - Base delay between retries (for exponential backoff)
 * - Force retry option for non-failed transmissions
 */
const RetryConfirmationDialog: React.FC<RetryConfirmationDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  transmissionId,
  isLoading,
}) => {
  // Default retry parameters
  const [maxRetries, setMaxRetries] = useState(3);
  const [retryDelay, setRetryDelay] = useState(30); // seconds
  const [force, setForce] = useState(false);

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm(maxRetries, retryDelay, force);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalHeader>
        <div className="flex items-center gap-2">
          <RotateCw className="h-5 w-5 text-yellow-500" />
          <h2 className="text-lg font-medium">Retry Transmission</h2>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Configure retry parameters for transmission {transmissionId.slice(0, 8)}...
        </p>
      </ModalHeader>

      <form onSubmit={handleSubmit}>
        <ModalBody>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="maxRetries">Maximum Retry Attempts</Label>
              <Input
                id="maxRetries"
                type="number"
                min={1}
                max={10}
                value={maxRetries}
                onChange={(e) => setMaxRetries(parseInt(e.target.value))}
                required
              />
              <p className="text-xs text-gray-500">
                Maximum number of times to retry this transmission (1-10)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="retryDelay">Base Retry Delay (seconds)</Label>
              <Input
                id="retryDelay"
                type="number"
                min={0}
                max={3600}
                value={retryDelay}
                onChange={(e) => setRetryDelay(parseInt(e.target.value))}
                required
              />
              <p className="text-xs text-gray-500">
                Initial delay between retries in seconds. Uses exponential backoff:
                <br />
                1st retry: {retryDelay}s, 2nd: {retryDelay * 2}s, 3rd: {retryDelay * 4}s...
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="force"
                checked={force}
                onCheckedChange={setForce}
              />
              <div className="grid gap-1.5">
                <Label htmlFor="force">Force Retry</Label>
                <p className="text-xs text-gray-500">
                  Retry even if transmission is not in a failed state
                </p>
              </div>
            </div>

            {force && (
              <div className="rounded-md bg-amber-50 p-3">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <AlertCircle className="h-5 w-5 text-amber-400" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-amber-700">
                      Forcing a retry on a non-failed transmission may cause duplicate 
                      transmissions or unexpected behavior. Use with caution.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ModalBody>
        
        <ModalFooter>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <RotateCw className="mr-2 h-4 w-4 animate-spin" />
                  Retrying...
                </>
              ) : (
                'Retry Transmission'
              )}
            </Button>
          </div>
        </ModalFooter>
      </form>
    </Modal>
  );
};

export default RetryConfirmationDialog;
