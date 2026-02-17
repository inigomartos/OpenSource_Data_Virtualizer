export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-primary">
      <div className="w-full max-w-md p-8 bg-bg-surface rounded-2xl border border-border-default shadow-xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-heading font-bold text-text-primary">
            Data<span className="text-brand-primary">Mind</span>
          </h1>
        </div>
        {children}
      </div>
    </div>
  );
}
