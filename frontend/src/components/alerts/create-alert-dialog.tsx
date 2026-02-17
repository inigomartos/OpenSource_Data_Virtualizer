'use client';

import { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, AlertTriangle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface Connection {
  id: string;
  name: string;
  type: string;
}

interface CreateAlertDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

type ConditionType = 'above' | 'below' | 'change_pct' | 'anomaly';

interface FormState {
  name: string;
  description: string;
  connection_id: string;
  sql_query: string;
  condition_type: ConditionType;
  threshold: string;
  check_interval_minutes: string;
}

const initialForm: FormState = {
  name: '',
  description: '',
  connection_id: '',
  sql_query: '',
  condition_type: 'above',
  threshold: '',
  check_interval_minutes: '60',
};

const conditionOptions: { value: ConditionType; label: string; description: string }[] = [
  { value: 'above', label: 'Above threshold', description: 'Triggers when the value exceeds the threshold' },
  { value: 'below', label: 'Below threshold', description: 'Triggers when the value falls below the threshold' },
  { value: 'change_pct', label: 'Percentage change', description: 'Triggers when value changes by more than the threshold %' },
  { value: 'anomaly', label: 'Anomaly detection', description: 'Triggers when an anomaly is detected (AI-powered)' },
];

export function CreateAlertDialog({ open, onOpenChange, onCreated }: CreateAlertDialogProps) {
  const [form, setForm] = useState<FormState>(initialForm);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loadingConnections, setLoadingConnections] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setLoadingConnections(true);
      apiClient('/connections')
        .then((data) => setConnections(data?.data || []))
        .catch(() => setConnections([]))
        .finally(() => setLoadingConnections(false));
      setForm(initialForm);
      setErrors({});
      setSubmitError(null);
    }
  }, [open]);

  const updateField = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FormState, string>> = {};

    if (!form.name.trim()) {
      newErrors.name = 'Alert name is required';
    }
    if (!form.connection_id) {
      newErrors.connection_id = 'Please select a connection';
    }
    if (!form.sql_query.trim()) {
      newErrors.sql_query = 'SQL query is required';
    }
    if (form.condition_type !== 'anomaly') {
      const threshold = parseFloat(form.threshold);
      if (isNaN(threshold)) {
        newErrors.threshold = 'Please enter a valid number';
      }
    }
    const interval = parseInt(form.check_interval_minutes, 10);
    if (isNaN(interval) || interval < 1) {
      newErrors.check_interval_minutes = 'Interval must be at least 1 minute';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    setSubmitting(true);
    setSubmitError(null);

    try {
      await apiClient('/alerts', {
        method: 'POST',
        body: JSON.stringify({
          name: form.name.trim(),
          description: form.description.trim() || undefined,
          connection_id: form.connection_id,
          query_sql: form.sql_query.trim(),
          condition_type: form.condition_type,
          threshold_value: form.condition_type !== 'anomaly' ? parseFloat(form.threshold) : 0,
          check_interval_minutes: parseInt(form.check_interval_minutes, 10),
        }),
      });
      onCreated();
      onOpenChange(false);
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to create alert');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg max-h-[85vh] overflow-y-auto bg-bg-surface border border-border-default rounded-2xl shadow-2xl z-50 p-6">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-lg font-heading font-semibold text-text-primary">
              Create New Alert
            </Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-colors">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {submitError && (
            <div className="mb-4 p-3 rounded-lg bg-brand-danger/10 border border-brand-danger/20 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-brand-danger mt-0.5 shrink-0" />
              <p className="text-sm text-brand-danger">{submitError}</p>
            </div>
          )}

          <div className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Alert Name <span className="text-brand-danger">*</span>
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => updateField('name', e.target.value)}
                placeholder="e.g., Revenue drop alert"
                className={`w-full px-3 py-2 bg-bg-elevated border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary ${
                  errors.name ? 'border-brand-danger' : 'border-border-default'
                }`}
              />
              {errors.name && (
                <p className="mt-1 text-xs text-brand-danger">{errors.name}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => updateField('description', e.target.value)}
                placeholder="Optional description for this alert..."
                rows={2}
                className="w-full px-3 py-2 bg-bg-elevated border border-border-default rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary resize-none"
              />
            </div>

            {/* Connection */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Connection <span className="text-brand-danger">*</span>
              </label>
              <select
                value={form.connection_id}
                onChange={(e) => updateField('connection_id', e.target.value)}
                disabled={loadingConnections}
                className={`w-full px-3 py-2 bg-bg-elevated border rounded-lg text-sm text-text-primary focus:outline-none focus:border-brand-primary ${
                  errors.connection_id ? 'border-brand-danger' : 'border-border-default'
                }`}
              >
                <option value="">
                  {loadingConnections ? 'Loading connections...' : 'Select a connection...'}
                </option>
                {connections.map((conn) => (
                  <option key={conn.id} value={conn.id}>
                    {conn.name} ({conn.type})
                  </option>
                ))}
              </select>
              {errors.connection_id && (
                <p className="mt-1 text-xs text-brand-danger">{errors.connection_id}</p>
              )}
            </div>

            {/* SQL Query */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                SQL Query <span className="text-brand-danger">*</span>
              </label>
              <textarea
                value={form.sql_query}
                onChange={(e) => updateField('sql_query', e.target.value)}
                placeholder="SELECT COUNT(*) FROM orders WHERE status = 'failed'"
                rows={4}
                className={`w-full px-3 py-2 bg-bg-elevated border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary resize-none font-mono ${
                  errors.sql_query ? 'border-brand-danger' : 'border-border-default'
                }`}
              />
              {errors.sql_query && (
                <p className="mt-1 text-xs text-brand-danger">{errors.sql_query}</p>
              )}
              <p className="mt-1 text-xs text-text-muted">
                Query must return a single numeric value
              </p>
            </div>

            {/* Condition Type */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Condition Type <span className="text-brand-danger">*</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                {conditionOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateField('condition_type', option.value)}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      form.condition_type === option.value
                        ? 'border-brand-primary bg-brand-primary/10 text-text-primary'
                        : 'border-border-default bg-bg-elevated text-text-secondary hover:border-border-hover'
                    }`}
                  >
                    <span className="text-sm font-medium block">{option.label}</span>
                    <span className="text-xs text-text-muted mt-0.5 block">{option.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Threshold */}
            {form.condition_type !== 'anomaly' && (
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">
                  Threshold Value <span className="text-brand-danger">*</span>
                </label>
                <input
                  type="number"
                  value={form.threshold}
                  onChange={(e) => updateField('threshold', e.target.value)}
                  placeholder={form.condition_type === 'change_pct' ? 'e.g., 10 (percent)' : 'e.g., 100'}
                  className={`w-full px-3 py-2 bg-bg-elevated border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary ${
                    errors.threshold ? 'border-brand-danger' : 'border-border-default'
                  }`}
                />
                {errors.threshold && (
                  <p className="mt-1 text-xs text-brand-danger">{errors.threshold}</p>
                )}
              </div>
            )}

            {/* Check Interval */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Check Interval (minutes) <span className="text-brand-danger">*</span>
              </label>
              <input
                type="number"
                min={1}
                value={form.check_interval_minutes}
                onChange={(e) => updateField('check_interval_minutes', e.target.value)}
                className={`w-full px-3 py-2 bg-bg-elevated border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary ${
                  errors.check_interval_minutes ? 'border-brand-danger' : 'border-border-default'
                }`}
              />
              {errors.check_interval_minutes && (
                <p className="mt-1 text-xs text-brand-danger">{errors.check_interval_minutes}</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-border-default">
            <Dialog.Close asChild>
              <button className="px-4 py-2 text-sm font-medium text-text-secondary bg-bg-elevated border border-border-default rounded-lg hover:border-border-hover transition-colors">
                Cancel
              </button>
            </Dialog.Close>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 shadow-[0_0_20px_rgba(99,102,241,0.3)]"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {submitting ? 'Creating...' : 'Create Alert'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
