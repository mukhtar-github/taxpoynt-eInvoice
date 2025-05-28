import React from 'react';

const OracleConnectionForm = ({ config, onChange, isSubmitting }: any) => (
  <div className="space-y-4">
    <div>
      <label className="block text-sm font-medium mb-1">Oracle Username</label>
      <input
        className="input input-bordered w-full"
        type="text"
        value={config.username || ''}
        onChange={e => onChange('username', e.target.value)}
        disabled={isSubmitting}
      />
    </div>
    <div>
      <label className="block text-sm font-medium mb-1">Oracle Password</label>
      <input
        className="input input-bordered w-full"
        type="password"
        value={config.password || ''}
        onChange={e => onChange('password', e.target.value)}
        disabled={isSubmitting}
      />
    </div>
  </div>
);

export default OracleConnectionForm;
