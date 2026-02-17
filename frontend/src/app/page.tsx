import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg-primary">
      <div className="text-center space-y-6">
        <h1 className="text-5xl font-heading font-bold text-text-primary">
          Data<span className="text-brand-primary">Mind</span>
        </h1>
        <p className="text-xl text-text-secondary max-w-lg">
          AI-powered business intelligence. Ask questions about your data in
          natural language.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)]"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="px-6 py-3 bg-bg-elevated text-text-primary rounded-lg font-medium border border-border-default hover:border-border-hover"
          >
            Get Started
          </Link>
        </div>
      </div>
    </div>
  );
}
