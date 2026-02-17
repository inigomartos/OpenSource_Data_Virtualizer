'use client';

interface LoadingSkeletonProps {
  width?: string;
  height?: string;
  className?: string;
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

export function LoadingSkeleton({
  width,
  height,
  className = '',
  rounded = 'lg',
}: LoadingSkeletonProps) {
  const roundedClass = {
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    full: 'rounded-full',
  }[rounded];

  return (
    <div
      className={`bg-bg-elevated animate-pulse ${roundedClass} ${className}`}
      style={{ width, height }}
    />
  );
}

export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`p-4 bg-bg-surface border border-border-default rounded-xl space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <LoadingSkeleton width="40%" height="20px" />
        <LoadingSkeleton width="80px" height="24px" rounded="full" />
      </div>
      <LoadingSkeleton width="70%" height="14px" />
      <div className="flex items-center gap-4 pt-1">
        <LoadingSkeleton width="100px" height="12px" />
        <LoadingSkeleton width="80px" height="12px" />
      </div>
    </div>
  );
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
