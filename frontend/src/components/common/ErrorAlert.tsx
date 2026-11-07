import React from 'react';
import { AlertCircle, XCircle } from 'lucide-react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'An error occurred',
  message,
  onRetry,
  onDismiss,
}) => {
  return (
    <div className="p-4 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/80 dark:bg-red-950/30 text-red-900 dark:text-red-200 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-red-800 dark:text-red-300">{title}</h4>
            <p className="mt-1 text-xs text-red-700 dark:text-red-400">{message}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-2 text-xs font-semibold text-red-700 dark:text-red-300 underline hover:text-red-900"
              >
                Try again
              </button>
            )}
          </div>
        </div>
        {onDismiss && (
          <button onClick={onDismiss} className="text-red-500 hover:text-red-700">
            <XCircle className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
