import React from 'react';

interface CircularProgressProps {
  value: number;
  size: string;
  thickness: string;
  color: string;
  trackColor: string;
  children?: React.ReactNode;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  size,
  thickness,
  color,
  trackColor,
  children
}) => {
  // Convert size to pixels
  const sizeInPx = parseInt(size.replace('px', ''));
  const thicknessInPx = parseInt(thickness.replace('px', ''));
  
  // Calculate the radius
  const radius = (sizeInPx / 2) - (thicknessInPx / 2);
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (value / 100) * circumference;
  
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      {/* Background circle */}
      <svg width={size} height={size}>
        <circle
          cx={sizeInPx / 2}
          cy={sizeInPx / 2}
          r={radius}
          fill="transparent"
          stroke={trackColor}
          strokeWidth={thickness}
        />
      </svg>
      
      {/* Progress circle */}
      <svg 
        width={size} 
        height={size} 
        style={{ 
          position: 'absolute', 
          top: 0, 
          left: 0,
          transform: 'rotate(-90deg)',
          transformOrigin: 'center'
        }}
      >
        <circle
          cx={sizeInPx / 2}
          cy={sizeInPx / 2}
          r={radius}
          fill="transparent"
          stroke={color}
          strokeWidth={thickness}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
        />
      </svg>
      
      {children}
    </div>
  );
};

interface CircularProgressLabelProps {
  children: React.ReactNode;
  fontWeight?: string;
}

export const CircularProgressLabel: React.FC<CircularProgressLabelProps> = ({
  children,
  fontWeight
}) => {
  return (
    <div 
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center',
        fontWeight: fontWeight || 'normal'
      }}
    >
      {children}
    </div>
  );
}; 