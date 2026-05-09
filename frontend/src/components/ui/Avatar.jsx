import React from 'react';

export function Avatar({ name, size = 'md', className = '' }) {
  const sizes = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-14 w-14 text-lg',
  };
  const initials = name
    ? name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '?';

  return (
    <div
      className={`flex items-center justify-center rounded-full bg-indigo-600 font-medium text-white ${sizes[size]} ${className}`}
    >
      {initials}
    </div>
  );
}
