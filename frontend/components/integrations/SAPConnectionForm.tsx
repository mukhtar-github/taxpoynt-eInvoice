import React from 'react';

const SAPConnectionForm = ({ config, onChange, isSubmitting }: any) => (
  <div className="space-y-4">
    <div>
      <label className="block text-sm font-medium mb-1">SAP Client ID</label>
      <input
        className="input input-bordered w-full"
        type="text"
        value={config.clientId || ''}
        onChange={e => onChange('clientId', e.target.value)}
        disabled={isSubmitting}
      />
    </div>
    <div>
      <label className="block text-sm font-medium mb-1">SAP Secret</label>
      <input
        className="input input-bordered w-full"
        type="password"
        value={config.secret || ''}
        onChange={e => onChange('secret', e.target.value)}
        disabled={isSubmitting}
      />
    </div>
  </div>
);

export default SAPConnectionForm;
