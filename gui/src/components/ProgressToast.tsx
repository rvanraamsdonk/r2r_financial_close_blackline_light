import React from 'react';
import { Loader, CheckCircle, XCircle, X } from 'lucide-react';

interface ProgressToastProps {
  isVisible: boolean;
  run?: {
    timestamp: string;
    label: string;
    status: 'running' | 'completed' | 'failed';
    entity: string;
    period: string;
    progress?: {
      current_step: string;
      completed_steps: number;
      total_steps: number;
      percentage: number;
    };
    duration_seconds?: number;
    artifacts_count?: number;
  } | null;
  onClose: () => void;
}

export const ProgressToast: React.FC<ProgressToastProps> = ({ isVisible, run, onClose }) => {
  if (!isVisible || !run) return null;

  const getStatusIcon = () => {
    switch (run.status) {
      case 'running':
        return <Loader className="w-5 h-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Loader className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (run.status) {
      case 'running':
        return 'border-blue-200 bg-blue-50';
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'failed':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className={`fixed top-4 right-4 z-50 max-w-sm w-full transition-all duration-300 ${
      isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
    }`}>
      <div className={`border rounded-lg p-4 shadow-lg ${getStatusColor()}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3 flex-1">
            {getStatusIcon()}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {run.status === 'running' ? 'Processing Close...' : 
                 run.status === 'completed' ? 'Close Completed' : 'Close Failed'}
              </p>
              <p className="text-xs text-gray-600 truncate">
                {run.label}
              </p>
            </div>
          </div>
          
          {run.status !== 'running' && (
            <button
              onClick={onClose}
              className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Progress Bar for Running Status */}
        {run.status === 'running' && run.progress && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>{run.progress.current_step}</span>
              <span>{run.progress.percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                style={{ width: `${run.progress.percentage}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Step {run.progress.completed_steps + 1} of {run.progress.total_steps}
            </div>
          </div>
        )}

        {/* Completion Summary */}
        {run.status === 'completed' && (
          <div className="mt-2 text-xs text-green-700">
            ✅ {run.artifacts_count} artifacts • {run.duration_seconds}s
          </div>
        )}
      </div>
    </div>
  );
};
