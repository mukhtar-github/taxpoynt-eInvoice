import React from 'react';

const LoadingScreen: React.FC = () => (
  <div className="flex items-center justify-center min-h-[40vh] w-full">
    <svg className="animate-spin h-8 w-8 text-blue-600 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
    </svg>
    <span className="text-blue-700 font-medium text-lg">Loading...</span>
  </div>
);

export default LoadingScreen;
