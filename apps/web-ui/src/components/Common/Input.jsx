import React from 'react';

const Input = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  className = '',
  ...props
}) => {
  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-text-primary dark:text-text-primary-dark">
          {label}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <div className="h-5 w-5 text-text-secondary dark:text-text-secondary-dark">
              {leftIcon}
            </div>
          </div>
        )}
        
        <input
          className={`
            w-full bg-white dark:bg-dark-surface 
            text-text-primary dark:text-text-primary-dark 
            border border-gray-200 dark:border-gray-700 
            rounded-xl px-4 py-3 
            focus:ring-2 focus:ring-primary-500 focus:border-primary-500 
            transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            ${leftIcon ? 'pl-10' : ''}
            ${rightIcon ? 'pr-10' : ''}
            ${error ? 'border-error-500 focus:ring-error-500 focus:border-error-500' : ''}
            ${className}
          `}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <div className="h-5 w-5 text-text-secondary dark:text-text-secondary-dark">
              {rightIcon}
            </div>
          </div>
        )}
      </div>
      
      {(error || helperText) && (
        <div className="text-sm">
          {error && (
            <p className="text-error-600 dark:text-error-400">{error}</p>
          )}
          {helperText && !error && (
            <p className="text-text-secondary dark:text-text-secondary-dark">{helperText}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Input; 