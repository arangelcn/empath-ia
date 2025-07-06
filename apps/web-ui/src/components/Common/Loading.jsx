import React from 'react';

const Loading = ({
  size = 'md',
  variant = 'primary',
  text,
  className = '',
}) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };
  
  const variants = {
    primary: 'text-primary-500',
    secondary: 'text-secondary-500',
    accent: 'text-accent-500',
    white: 'text-white',
  };
  
  const spinnerClasses = [
    'animate-spin',
    sizes[size],
    variants[variant],
    className
  ].filter(Boolean).join(' ');
  
  return (
    <div className="flex flex-col items-center justify-center space-y-3">
      <div className={spinnerClasses}>
        <svg fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>
      
      {text && (
        <p className="text-sm text-text-secondary dark:text-text-secondary-dark text-center">
          {text}
        </p>
      )}
    </div>
  );
};

export default Loading; 