interface Props {
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({ title, description, action }: Props) {
  return (
    <div className="text-center py-16">
      <h3 className="text-lg font-medium text-text-primary mb-2">{title}</h3>
      {description && <p className="text-sm text-text-muted mb-4">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-2.5 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
