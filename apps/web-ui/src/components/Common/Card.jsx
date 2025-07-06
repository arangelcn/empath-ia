import React from 'react';

const Card = ({
  children,
  variant = 'default',
  className = '',
  padding = 'default',
  hover = false,
  ...props
}) => {
  const baseClasses = 'transition-all duration-300';
  
  const variants = {
    default: 'card-therapy',
    glass: 'card-therapy-glass',
    elevated: 'card-therapy-elevated',
  };
  
  const paddings = {
    none: '',
    sm: 'p-4',
    default: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  };
  
  const hoverClasses = hover ? 'hover:shadow-therapy-large hover:-translate-y-1' : '';
  
  const classes = [
    baseClasses,
    variants[variant],
    paddings[padding],
    hoverClasses,
    className
  ].filter(Boolean).join(' ');
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export default Card; 