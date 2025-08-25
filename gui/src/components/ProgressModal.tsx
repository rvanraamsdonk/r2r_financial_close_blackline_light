import React from 'react';
import { Loader, CheckCircle, XCircle } from 'lucide-react';

interface ProgressModalProps {
  isOpen: boolean;
  run?: {
    timestamp: string;
    label: string;
    status: 'running' | 'completed' | 'failed';
    entity: string;
    period: string;
    created_at: string;
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

export const ProgressModal: React.FC<ProgressModalProps> = ({ isOpen, run, onClose }) => {
  if (!isOpen || !run) return null;

  const getStatusIcon = () => {
    switch (run.status) {
      case 'running':
        return <Loader className="w-8 h-8 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-8 h-8 text-green-500" />;
      case 'failed':
        return <XCircle className="w-8 h-8 text-red-500" />;
      default:
        return <Loader className="w-8 h-8 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (run.status) {
      case 'running':
        return 'Processing Financial Close...';
      case 'completed':
        return 'Financial Close Completed!';
      case 'failed':
        return 'Financial Close Failed';
      default:
        return 'Processing...';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-40 pointer-events-none">
      <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl pointer-events-auto">
        <div className="text-center">
          {/* Status Icon */}
          <div className="flex justify-center mb-4">
            {getStatusIcon()}
          </div>

          {/* Status Text */}
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {getStatusText()}
          </h2>

          {/* Run Info */}
          <p className="text-sm text-gray-600 mb-6">
            {run.label}
          </p>

          {/* Progress Bar and Details */}
          {run.status === 'running' && run.progress && (
            <div className="mb-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Step {run.progress.completed_steps + 1} of {run.progress.total_steps}</span>
                <span>{run.progress.percentage}%</span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                <div 
                  className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out" 
                  style={{ width: `${run.progress.percentage}%` }}
                ></div>
              </div>

              <p className="text-sm font-medium text-gray-800">
                {run.progress.current_step}
              </p>
            </div>
          )}

          {/* Completion Details */}
          {run.status === 'completed' && (
            <div className="mb-6 p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-green-800">
                <p className="font-medium">✅ {run.artifacts_count} artifacts generated</p>
                <p>⏱️ Completed in {run.duration_seconds} seconds</p>
              </div>
            </div>
          )}

          {/* Failure Details */}
          {run.status === 'failed' && (
            <div className="mb-6 p-4 bg-red-50 rounded-lg">
              <p className="text-sm text-red-800">
                The financial close process encountered an error and could not complete.
              </p>
            </div>
          )}

          {/* Close Button */}
          {run.status !== 'running' && (
            <button
              onClick={onClose}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Close
            </button>
          )}

          {/* Running State Info */}
          {run.status === 'running' && (
            <p className="text-xs text-gray-500">
              This window will automatically update as the process continues...
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
