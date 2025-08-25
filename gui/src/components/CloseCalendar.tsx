/**
 * Close Calendar Component
 * Timeline-driven process orchestration for financial close
 * Implements Big 4 best practices for close management
 */

import React, { useState } from 'react';
import type { ClosePhase, CloseTask } from '../types.js';
import { Calendar, Clock, CheckCircle, AlertCircle, Play, Pause } from 'lucide-react';

interface CloseCalendarProps {
  phases: ClosePhase[];
  onTaskClick: (task: CloseTask) => void;
  onPhaseClick: (phase: ClosePhase) => void;
  className?: string;
}

export const CloseCalendar: React.FC<CloseCalendarProps> = ({
  phases,
  onTaskClick,
  onPhaseClick,
  className = ""
}) => {
  const [selectedPhase, setSelectedPhase] = useState<string | null>(null);

  // Calculate overall progress
  const overallProgress = phases.reduce((total, phase) => {
    const phaseProgress = phase.tasks.filter(task => task.status === 'complete').length / phase.tasks.length;
    return total + (phaseProgress / phases.length);
  }, 0) * 100;

  // Get status counts
  const getStatusCounts = () => {
    const counts = { pending: 0, inProgress: 0, complete: 0, overdue: 0, blocked: 0 };
    phases.forEach(phase => {
      phase.tasks.forEach(task => {
        counts[task.status as keyof typeof counts]++;
      });
    });
    return counts;
  };

  const statusCounts = getStatusCounts();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'in-progress':
        return <Play className="w-4 h-4 text-blue-500" />;
      case 'overdue':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'blocked':
        return <Pause className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'in-progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'overdue':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'blocked':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPhaseStatusColor = (phase: ClosePhase) => {
    const completedTasks = phase.tasks.filter(task => task.status === 'complete').length;
    const totalTasks = phase.tasks.length;
    const progress = totalTasks > 0 ? completedTasks / totalTasks : 0;

    if (progress === 1) return 'bg-green-500';
    if (progress > 0) return 'bg-blue-500';
    return 'bg-gray-300';
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* Calendar Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Close Calendar</h2>
          </div>
          
          {/* Overall Progress */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{overallProgress.toFixed(1)}% Complete</p>
              <p className="text-xs text-gray-500">Overall Progress</p>
            </div>
            <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${overallProgress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Status Summary */}
        <div className="flex items-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">{statusCounts.pending} Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <Play className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-gray-600">{statusCounts.inProgress} In Progress</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-sm text-gray-600">{statusCounts.complete} Complete</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <span className="text-sm text-gray-600">{statusCounts.overdue} Overdue</span>
          </div>
          <div className="flex items-center gap-2">
            <Pause className="w-4 h-4 text-yellow-500" />
            <span className="text-sm text-gray-600">{statusCounts.blocked} Blocked</span>
          </div>
        </div>
      </div>

      {/* Timeline View */}
      <div className="overflow-x-auto">
        <div className="flex min-w-max p-4">
          {phases.map(phase => (
            <div key={phase.id} className="flex-shrink-0 w-80 mr-6">
              {/* Phase Header */}
              <div 
                className="flex items-center justify-between p-3 bg-gray-50 rounded-t-lg border cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={() => {
                  setSelectedPhase(selectedPhase === phase.id ? null : phase.id);
                  onPhaseClick(phase);
                }}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${getPhaseStatusColor(phase)}`} />
                  <div>
                    <h3 className="font-medium text-gray-900">{phase.name}</h3>
                    <p className="text-xs text-gray-500">
                      {phase.tasks.filter(t => t.status === 'complete').length} / {phase.tasks.length} tasks
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">{phase.startDate}</p>
                  <p className="text-xs text-gray-500">{phase.endDate}</p>
                </div>
              </div>

              {/* Phase Tasks */}
              <div className="border border-gray-200 rounded-b-lg bg-white">
                {phase.tasks.map(task => (
                  <div
                    key={task.id}
                    className={`p-3 border-b border-gray-100 last:border-b-0 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedPhase === phase.id ? '' : 'hidden'
                    }`}
                    onClick={() => onTaskClick(task)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {getStatusIcon(task.status)}
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {task.name}
                          </h4>
                        </div>
                        
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs text-gray-500">{task.assignee}</span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">{task.dueDate}</span>
                        </div>

                        {/* Priority and Dependencies */}
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                            {task.status}
                          </span>
                          {task.priority === 'high' && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              High Priority
                            </span>
                          )}
                          {task.dependencies.length > 0 && (
                            <span className="text-xs text-gray-500">
                              {task.dependencies.length} deps
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Evidence indicator */}
                      {task.evidence.length > 0 && (
                        <div className="ml-2 text-xs text-blue-600">
                          {task.evidence.length} evidence
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
              View All Tasks
            </button>
            <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
              Export Timeline
            </button>
            <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
              Print Calendar
            </button>
          </div>
          
          <div className="text-xs text-gray-500">
            Last updated: {new Date().toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
};

// Task Detail Modal Component
interface TaskDetailModalProps {
  task: CloseTask | null;
  onClose: () => void;
  onUpdateStatus: (taskId: string, status: string) => void;
}

export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  task,
  onClose,
  onUpdateStatus
}) => {
  if (!task) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">{task.name}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ×
          </button>
        </div>

        <div className="space-y-4">
          {/* Task Details */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Assignee</label>
              <p className="text-sm text-gray-900">{task.assignee}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
              <p className="text-sm text-gray-900">{task.dueDate}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                task.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {task.priority}
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={task.status}
                onChange={(e) => onUpdateStatus(task.id, e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="pending">Pending</option>
                <option value="in-progress">In Progress</option>
                <option value="complete">Complete</option>
                <option value="blocked">Blocked</option>
                <option value="overdue">Overdue</option>
              </select>
            </div>
          </div>

          {/* Dependencies */}
          {task.dependencies.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dependencies</label>
              <div className="text-sm text-gray-600">
                {task.dependencies.length} dependent tasks
              </div>
            </div>
          )}

          {/* Evidence */}
          {task.evidence.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Evidence</label>
              <div className="space-y-2">
                {task.evidence.map(evidence => (
                  <div key={evidence.id} className="flex items-center justify-between p-2 bg-gray-50 rounded border">
                    <div>
                      <p className="text-sm font-medium">{evidence.type}</p>
                      <p className="text-xs text-gray-600">{evidence.timestamp}</p>
                    </div>
                    <button className="text-xs text-blue-600 hover:text-blue-800">
                      View
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Contribution */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">AI Contribution</label>
            <div className="p-3 bg-blue-50 rounded border">
              <p className="text-sm text-gray-900">{task.aiContribution.contribution}</p>
              <p className="text-xs text-gray-600 mt-1">Confidence: {task.aiContribution.confidence}%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

