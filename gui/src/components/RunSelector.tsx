import React, { useState, useEffect, useRef } from 'react';
import { Play, ChevronDown, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { artifactService } from '../services/artifactService.js';
import { ProgressToast } from './ProgressToast.js';

interface Run {
  timestamp: string;
  label: string;
  status: 'running' | 'completed' | 'failed';
  entity: string;
  period: string;
  created_at: string;
  duration_seconds?: number;
  artifacts_count?: number;
  progress?: {
    current_step: string;
    completed_steps: number;
    total_steps: number;
    percentage: number;
  };
}


interface RunSelectorProps {
  onRunChange?: (timestamp: string) => void;
}

export const RunSelector: React.FC<RunSelectorProps> = ({ onRunChange }) => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<string>('latest');
  const [loading, setLoading] = useState(true);
  const [showProgressToast, setShowProgressToast] = useState(false);
  const [currentRunningProcess, setCurrentRunningProcess] = useState<Run | null>(null);
  const pollIntervalRef = useRef<number | null>(null);
  const runsRef = useRef<Run[]>([]);
  const currentRunningRef = useRef<Run | null>(null);

  useEffect(() => {
    loadRuns();
    startPolling();
    return () => stopPolling();
  }, []);

  // Add dependency to re-run effect when currentRunningProcess changes
  useEffect(() => {
    console.log('Current running process updated:', currentRunningProcess);
    currentRunningRef.current = currentRunningProcess;
  }, [currentRunningProcess]);

  const loadRuns = async () => {
    try {
      const manifest = await artifactService.getAvailableRuns();
      const newRuns = manifest.runs || [];
      runsRef.current = newRuns;
      
      // Check for running processes and show progress modal
      const runningRuns = newRuns.filter((run: Run) => run.status === 'running');
      if (runningRuns.length > 0) {
        const runningRun = runningRuns[0];
        console.log('Running process found:', runningRun.timestamp, runningRun.progress);
        setCurrentRunningProcess(runningRun);
        setShowProgressToast(true);
      } else {
        // Check if a previously running process just completed
        if (currentRunningProcess) {
          const completedRun = newRuns.find((run: Run) => 
            run.timestamp === currentRunningProcess.timestamp && 
            run.status !== 'running'
          );
          if (completedRun) {
            setCurrentRunningProcess(completedRun);
            // Keep modal open to show completion status
          }
        }
      }
      
      setRuns(newRuns);
      // Choose selected run: prefer manifest.latest, else newest run if available
      if (manifest.latest) {
        setSelectedRun(manifest.latest);
      } else if (newRuns.length > 0) {
        setSelectedRun(newRuns[0].timestamp);
      } else {
        setSelectedRun('latest');
      }
    } catch (error) {
      console.error('Failed to load runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const startPolling = () => {
    stopPolling();
    pollIntervalRef.current = window.setInterval(async () => {
      // Always refresh runs list
      await loadRuns();

      // If a run is currently active, fetch its live status (progress)
      const running = runsRef.current.find(r => r.status === 'running');
      const target = running || currentRunningRef.current;
      if (target && target.status === 'running') {
        try {
          const res = await fetch(`http://localhost:5001/api/runs/${target.timestamp}/status`);
          if (res.ok) {
            const live = await res.json();
            setCurrentRunningProcess(live);
            setShowProgressToast(true);
          }
        } catch (e) {
          // ignore transient errors
        }
      }
    }, 1000); // Poll every 1 second for better responsiveness
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const handleRunChange = (timestamp: string) => {
    setSelectedRun(timestamp);
    artifactService.setSelectedRun(timestamp);
    onRunChange?.(timestamp);
  };

  const startNewRun = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5001/api/runs/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity: 'ALL',
          period: '2025-08'
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to start run');
      }
      
      const result = await response.json();
      console.log('New run started:', result.timestamp);
      
      // Reload runs list to show the new running process
      await loadRuns();
      
      // Select the new run
      handleRunChange(result.timestamp);
      
    } catch (error) {
      console.error('Failed to start new run:', error);
      alert('Failed to start new run. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader className="w-4 h-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const currentRun = runs.find(run => run.timestamp === selectedRun);
  const hasRunningProcesses = runs.some(run => run.status === 'running');

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        <span className="text-sm text-gray-600">Loading runs...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-3">
      {/* Run Selector Dropdown */}
      <div className="relative">
        <select
          value={selectedRun}
          onChange={(e) => handleRunChange(e.target.value)}
          className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-48"
        >
          {runs.map((run) => (
            <option key={run.timestamp} value={run.timestamp}>
              {run.label} • {run.status}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>

      {/* Status and Progress Indicator */}
      {currentRun && (
        <div className="flex items-center space-x-2">
          {getStatusIcon(currentRun.status)}
          {currentRun.status === 'running' && currentRun.progress && (
            <div className="flex items-center space-x-2">
              <div className="w-24 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${currentRun.progress.percentage}%` }}
                ></div>
              </div>
              <span className="text-xs text-gray-600">
                {currentRun.progress.completed_steps}/{currentRun.progress.total_steps}
              </span>
            </div>
          )}
          {currentRun.status === 'running' && !currentRun.progress && (
            <span className="text-xs text-blue-600">Processing...</span>
          )}
          {currentRun.status === 'completed' && (
            <span className="text-xs text-green-600">
              {currentRun.artifacts_count} artifacts • {currentRun.duration_seconds}s
            </span>
          )}
          {currentRun.status === 'failed' && (
            <span className="text-xs text-red-600">Failed</span>
          )}
        </div>
      )}

      {/* Start New Run Button */}
      <button
        onClick={startNewRun}
        disabled={hasRunningProcesses}
        className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          hasRunningProcesses 
            ? 'bg-gray-400 cursor-not-allowed text-white' 
            : 'bg-green-600 hover:bg-green-700 text-white'
        }`}
      >
        <Play className="w-4 h-4" />
        <span>{hasRunningProcesses ? 'Run in Progress' : 'Start New Run'}</span>
      </button>
      
      {/* Progress Toast */}
      <ProgressToast
        isVisible={showProgressToast}
        run={currentRunningProcess}
        onClose={() => {
          setShowProgressToast(false);
          setCurrentRunningProcess(null);
        }}
      />
    </div>
  );
};
