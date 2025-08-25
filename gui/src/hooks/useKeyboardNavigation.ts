import { useEffect, useCallback, useState } from 'react';

interface KeyboardNavigationOptions {
  onArrowUp?: () => void;
  onArrowDown?: () => void;
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
  onEnter?: () => void;
  onEscape?: () => void;
  onTab?: () => void;
  onShiftTab?: () => void;
  onCtrlC?: () => void;
  onCtrlV?: () => void;
  onCtrlA?: () => void;
  onDelete?: () => void;
  onF2?: () => void;
  enabled?: boolean;
}

export const useKeyboardNavigation = (options: KeyboardNavigationOptions) => {
  const [isEnabled, setIsEnabled] = useState(options.enabled ?? true);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!isEnabled) return;

    const { key, ctrlKey, metaKey, shiftKey } = event;
    const isModifierPressed = ctrlKey || metaKey;

    // Prevent default for navigation keys to avoid page scrolling
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(key)) {
      event.preventDefault();
    }

    switch (key) {
      case 'ArrowUp':
        options.onArrowUp?.();
        break;
      case 'ArrowDown':
        options.onArrowDown?.();
        break;
      case 'ArrowLeft':
        options.onArrowLeft?.();
        break;
      case 'ArrowRight':
        options.onArrowRight?.();
        break;
      case 'Enter':
        options.onEnter?.();
        break;
      case 'Escape':
        options.onEscape?.();
        break;
      case 'Tab':
        if (shiftKey) {
          options.onShiftTab?.();
        } else {
          options.onTab?.();
        }
        break;
      case 'Delete':
      case 'Backspace':
        options.onDelete?.();
        break;
      case 'F2':
        options.onF2?.();
        break;
      case 'c':
      case 'C':
        if (isModifierPressed) {
          event.preventDefault();
          options.onCtrlC?.();
        }
        break;
      case 'v':
      case 'V':
        if (isModifierPressed) {
          event.preventDefault();
          options.onCtrlV?.();
        }
        break;
      case 'a':
      case 'A':
        if (isModifierPressed) {
          event.preventDefault();
          options.onCtrlA?.();
        }
        break;
    }
  }, [options, isEnabled]);

  useEffect(() => {
    if (isEnabled) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [handleKeyDown, isEnabled]);

  return {
    setEnabled: setIsEnabled,
    isEnabled
  };
};

// Hook for managing cell selection in tables
export const useTableNavigation = (
  rowCount: number,
  columnCount: number,
  onCellSelect?: (row: number, col: number) => void,
  onCellEdit?: (row: number, col: number) => void
) => {
  const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>(null);
  const [editingCell, setEditingCell] = useState<{ row: number; col: number } | null>(null);

  const moveSelection = useCallback((deltaRow: number, deltaCol: number) => {
    if (!selectedCell) return;

    const newRow = Math.max(0, Math.min(rowCount - 1, selectedCell.row + deltaRow));
    const newCol = Math.max(0, Math.min(columnCount - 1, selectedCell.col + deltaCol));
    
    const newSelection = { row: newRow, col: newCol };
    setSelectedCell(newSelection);
    onCellSelect?.(newRow, newCol);
  }, [selectedCell, rowCount, columnCount, onCellSelect]);

  const startEditing = useCallback(() => {
    if (selectedCell) {
      setEditingCell(selectedCell);
      onCellEdit?.(selectedCell.row, selectedCell.col);
    }
  }, [selectedCell, onCellEdit]);

  const stopEditing = useCallback(() => {
    setEditingCell(null);
  }, []);

  const keyboardOptions: KeyboardNavigationOptions = {
    onArrowUp: () => moveSelection(-1, 0),
    onArrowDown: () => moveSelection(1, 0),
    onArrowLeft: () => moveSelection(0, -1),
    onArrowRight: () => moveSelection(0, 1),
    onEnter: () => {
      if (editingCell) {
        stopEditing();
        moveSelection(1, 0); // Move to next row after editing
      } else {
        startEditing();
      }
    },
    onEscape: stopEditing,
    onF2: startEditing,
    enabled: !editingCell // Disable navigation when editing
  };

  const navigation = useKeyboardNavigation(keyboardOptions);

  return {
    selectedCell,
    editingCell,
    setSelectedCell,
    startEditing,
    stopEditing,
    moveSelection,
    ...navigation
  };
};

// Hook for clipboard operations
export const useClipboard = () => {
  const [clipboardData, setClipboardData] = useState<string>('');

  const copyToClipboard = useCallback(async (data: string) => {
    try {
      await navigator.clipboard.writeText(data);
      setClipboardData(data);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = data;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setClipboardData(data);
    }
  }, []);

  const pasteFromClipboard = useCallback(async (): Promise<string> => {
    try {
      const data = await navigator.clipboard.readText();
      return data;
    } catch (error) {
      console.error('Failed to read from clipboard:', error);
      return clipboardData; // Fallback to internal clipboard
    }
  }, [clipboardData]);

  return {
    copyToClipboard,
    pasteFromClipboard,
    clipboardData
  };
};
