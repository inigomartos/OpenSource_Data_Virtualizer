'use client';

export default function ChatPage() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center">
      <h2 className="text-2xl font-heading font-bold text-text-primary mb-2">
        Ask anything about your data
      </h2>
      <p className="text-text-secondary mb-6">
        Select a connection and start asking questions in natural language.
      </p>
      <div className="w-full max-w-2xl">
        <input
          type="text"
          placeholder="What were our top 10 products by revenue last quarter?"
          className="w-full px-6 py-4 bg-bg-elevated border border-border-default rounded-xl text-text-primary focus:outline-none focus:border-brand-primary text-lg"
        />
      </div>
    </div>
  );
}
