'use client';

const suggestions = [
  'What were our top 10 products by revenue last quarter?',
  'Show me monthly revenue trends for the past year',
  'Which customers have the highest order values?',
  'Compare sales performance across regions',
  'What is our current inventory status?',
  'Show me supplier costs breakdown',
];

interface Props {
  onSelect?: (question: string) => void;
}

export default function SuggestedQuestions({ onSelect }: Props) {
  return (
    <div className="grid grid-cols-2 gap-2 max-w-2xl">
      {suggestions.map((q) => (
        <button
          key={q}
          onClick={() => onSelect?.(q)}
          className="px-4 py-3 text-left text-sm text-text-secondary bg-bg-elevated border border-border-default rounded-xl hover:border-brand-primary hover:text-brand-primary transition-colors"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
