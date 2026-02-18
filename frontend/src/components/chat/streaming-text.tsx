'use client';

interface Props {
  content: string;
  isStreaming?: boolean;
}

export default function StreamingText({ content, isStreaming = false }: Props) {
  return (
    <span>
      {content}
      {isStreaming && (
        <span className="inline-block w-0.5 h-4 bg-brand-primary animate-pulse ml-0.5" />
      )}
    </span>
  );
}
