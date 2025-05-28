import React from 'react';

const DynamicsConnectionForm = ({ config, onChange, isSubmitting }: any) => (
  <div className="space-y-4">
    <div>
      <label className="block text-sm font-medium mb-1">Dynamics Tenant ID</label>
      <input
        className="input input-bordered w-full"
        type="text"
        value={config.tenantId || ''}
        onChange={e => onChange('tenantId', e.target.value)}
        disabled={isSubmitting}
      />
    </div>
    <div>
      <label className="block text-sm font-medium mb-1">Dynamics Secret</label>
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

export default DynamicsConnectionForm;
