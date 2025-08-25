import React from 'react';
import clsx from 'clsx';

export interface CompactAIBadgeProps {
  method: 'DET' | 'AI' | 'HYBRID';
  confidence: number; // 0-100
  className?: string;
}

export const CompactAIBadge: React.FC<CompactAIBadgeProps> = ({ method, confidence, className }) => {
  const color = method === 'DET' ? 'bg-green-500' : method === 'AI' ? 'bg-blue-500' : 'bg-purple-500';
  return (
    <div className={clsx('compact-ai-badge', className)} title={`${method} • ${confidence}%`}>
      <div className={clsx('w-1.5 h-1.5 rounded-full', color)} />
      <span className="uppercase tracking-wide text-gray-700">{method}</span>
      <div className="confidence-bar">
        <div className="confidence-fill" style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }} />
      </div>
    </div>
  );
};
