'use client';

interface Props {
  columns: string[];
  rows: any[][];
  title?: string;
}

export default function DataTable({ columns, rows, title }: Props) {
  return (
    <div className="bg-bg-surface border border-border-default rounded-xl overflow-hidden">
      {title && (
        <div className="px-4 py-3 border-b border-border-default">
          <h3 className="text-sm font-medium text-text-primary">{title}</h3>
        </div>
      )}
      <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-bg-elevated sticky top-0">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2.5 text-left text-xs font-medium text-text-muted uppercase tracking-wider border-b border-border-default"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-default">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-bg-elevated/50 transition-colors">
                {row.map((cell, j) => (
                  <td key={j} className="px-4 py-2.5 text-text-primary whitespace-nowrap">
                    {cell === null ? (
                      <span className="text-text-muted italic">null</span>
                    ) : (
                      String(cell)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 0 && (
        <div className="px-4 py-2 bg-bg-elevated border-t border-border-default text-xs text-text-muted">
          Showing {rows.length} rows
        </div>
      )}
    </div>
  );
}
