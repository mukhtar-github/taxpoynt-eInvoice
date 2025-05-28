import React from 'react';

const QuickBooksConnectionForm = ({ config, onChange, isSubmitting }: any) => (
  <div className="space-y-4">
    <div>
      <label className="block text-sm font-medium mb-1">Company ID</label>
      <input
        className="input input-bordered w-full"
        type="text"
        value={config.companyId || ''}
        onChange={e => onChange('companyId', e.target.value)}
        disabled={isSubmitting}
      />
    </div>
    <div>
      <label className="block text-sm font-medium mb-1">Client Secret</label>
      <input
        className="input input-bordered w-full"
        type="password"
        value={config.clientSecret || ''}
        onChange={e => onChange('clientSecret', e.target.value)}
        disabled={isSubmitting}
      />
    </div>
  </div>
);

export default QuickBooksConnectionForm;
