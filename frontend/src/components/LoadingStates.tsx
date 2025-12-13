import { Activity, AlertCircle, RefreshCw } from 'lucide-react';

export function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="relative">
        <div className="w-16 h-16 border-4 border-zinc-700 rounded-full" />
        <div className="absolute inset-0 w-16 h-16 border-4 border-iowa-gold border-t-transparent rounded-full animate-spin" />
        <Activity className="absolute inset-0 m-auto w-6 h-6 text-iowa-gold" />
      </div>
      <p className="mt-4 text-zinc-400 text-sm animate-pulse">{message}</p>
    </div>
  );
}

export function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
            <div className="h-2 w-1/3 bg-zinc-800 rounded mb-3" />
            <div className="h-6 w-3/4 bg-zinc-800 rounded mb-4" />
            <div className="flex justify-between">
              <div className="h-8 w-16 bg-zinc-800 rounded" />
              <div className="h-8 w-12 bg-zinc-800 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface ErrorDisplayProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorDisplay({ title = 'Error', message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8 text-red-400" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-zinc-400 text-sm max-w-md mb-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn-iowa-outline flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ 
  icon: Icon = Activity,
  title = 'No data found',
  message = 'There are no items to display.',
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title?: string;
  message?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-zinc-600" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-zinc-500 text-sm max-w-md">{message}</p>
    </div>
  );
}
