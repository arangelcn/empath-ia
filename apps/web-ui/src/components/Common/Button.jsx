import React from 'react';

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  className = '',
  onClick,
  type = 'button',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'btn-therapy-primary',
    secondary: 'btn-therapy-secondary',
    accent: 'btn-therapy-accent',
    outline: 'btn-therapy-outline',
    ghost: 'btn-therapy-ghost',
  };
  
  const sizes = {
    sm: 'px-3 py-2 text-sm min-h-[36px]',
    md: 'px-4 py-3 text-sm min-h-[44px]',
    lg: 'px-6 py-4 text-base min-h-[52px]',
    xl: 'px-8 py-5 text-lg min-h-[60px]',
    // Novos tamanhos específicos para mobile
    'mobile-sm': 'px-4 py-3 text-sm min-h-[48px] sm:px-3 sm:py-2 sm:min-h-[36px]',
    'mobile-md': 'px-6 py-4 text-base min-h-[52px] sm:px-4 sm:py-3 sm:text-sm sm:min-h-[44px]',
    'mobile-lg': 'px-8 py-5 text-lg min-h-[60px] sm:px-6 sm:py-4 sm:text-base sm:min-h-[52px]',
    // Tamanho específico para botões de ação importantes em mobile
    'touch-friendly': 'px-6 py-4 text-base min-h-[52px] md:px-4 md:py-3 md:text-sm md:min-h-[44px]',
    // Para botões de ícone em mobile
    icon: 'w-10 h-10 md:w-8 md:h-8 flex items-center justify-center',
    'icon-lg': 'w-12 h-12 md:w-10 md:h-10 flex items-center justify-center',
  };
  
  const classes = [
    baseClasses,
    variants[variant],
    sizes[size],
    className
  ].filter(Boolean).join(' ');
  
  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <div className="mr-2 animate-spin">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24">
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
      )}
      {children}
    </button>
  );
};

export default Button; 