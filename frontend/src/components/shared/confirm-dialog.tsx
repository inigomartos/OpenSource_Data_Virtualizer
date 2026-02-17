'use client';

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Confirm', onConfirm, onCancel }: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onCancel} />
      <div className="relative bg-bg-surface border border-border-default rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
        <h3 className="text-lg font-medium text-text-primary mb-2">{title}</h3>
        <p className="text-sm text-text-secondary mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="px-4 py-2 bg-bg-elevated border border-border-default rounded-lg text-sm text-text-primary">
            Cancel
          </button>
          <button onClick={onConfirm} className="px-4 py-2 bg-brand-danger text-white rounded-lg text-sm font-medium">
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
