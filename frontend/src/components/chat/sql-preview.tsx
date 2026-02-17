'use client';

import { useState } from 'react';

interface Props {
  sql: string;
}

export default function SQLPreview({ sql }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs text-text-muted hover:text-text-secondary"
      >
        <span>{expanded ? '▼' : '▶'}</span>
        <span>View SQL</span>
      </button>

      {expanded && (
        <div className="mt-2 relative group">
          <pre className="bg-[#0d1117] border border-border-default rounded-lg p-3 text-xs text-green-400 font-mono overflow-x-auto">
            <code>{sql}</code>
          </pre>
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 px-2 py-1 text-xs bg-bg-elevated border border-border-default rounded text-text-muted hover:text-text-primary opacity-0 group-hover:opacity-100 transition-opacity"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      )}
    </div>
  );
}
