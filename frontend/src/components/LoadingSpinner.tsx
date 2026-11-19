import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  fullPage?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'md',
  fullPage = false,
}) => {
  const sizeMap = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const content = (
    <div className="flex flex-col items-center justify-center gap-3 p-6">
      <div className="relative flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-indigo-500 to-cyan-500 blur-lg opacity-40 animate-pulse" />
        <Loader2 className={`${sizeMap[size]} text-indigo-400 animate-spin relative z-10`} />
      </div>
      {message && (
        <p className="text-sm text-slate-400 font-medium tracking-wide animate-pulse">
          {message}
        </p>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 bg-[#0a0a0f]/80 backdrop-blur-md flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return content;
};

export default LoadingSpinner;
