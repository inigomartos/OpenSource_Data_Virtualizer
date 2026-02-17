'use client';

interface Props {
  onExportPDF?: () => void;
  onExportExcel?: () => void;
  onPinToDashboard?: () => void;
  onToggleTable?: () => void;
}

export default function ChartToolbar({ onExportPDF, onExportExcel, onPinToDashboard, onToggleTable }: Props) {
  return (
    <div className="flex items-center gap-2 mt-2">
      {onToggleTable && (
        <button
          onClick={onToggleTable}
          className="px-2 py-1 text-xs text-text-muted bg-bg-elevated border border-border-default rounded hover:text-text-primary"
        >
          Table
        </button>
      )}
      {onExportPDF && (
        <button
          onClick={onExportPDF}
          className="px-2 py-1 text-xs text-text-muted bg-bg-elevated border border-border-default rounded hover:text-text-primary"
        >
          PDF
        </button>
      )}
      {onExportExcel && (
        <button
          onClick={onExportExcel}
          className="px-2 py-1 text-xs text-text-muted bg-bg-elevated border border-border-default rounded hover:text-text-primary"
        >
          Excel
        </button>
      )}
      {onPinToDashboard && (
        <button
          onClick={onPinToDashboard}
          className="px-2 py-1 text-xs text-text-muted bg-bg-elevated border border-border-default rounded hover:text-text-primary"
        >
          Pin
        </button>
      )}
    </div>
  );
}
