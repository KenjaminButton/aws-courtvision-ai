import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

interface AISummaryProps {
  gameId: string;
}

interface AISummaryResponse {
  summary: string;
  generated_at: string;
  cached: boolean;
}

const API_BASE = 'https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod';

export function AISummary({ gameId }: AISummaryProps) {
  const [summary, setSummary] = useState<AISummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSummary() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE}/games/${gameId}/summary`);
        if (!response.ok) {
          throw new Error('Failed to load summary');
        }
        const data = await response.json();
        setSummary(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchSummary();
  }, [gameId]);

  // Loading state
  if (loading) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
        <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-iowa-gold" />
          Game Summary
        </h3>
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-zinc-800 rounded w-full"></div>
          <div className="h-4 bg-zinc-800 rounded w-full"></div>
          <div className="h-4 bg-zinc-800 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !summary) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
        <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-iowa-gold" />
          Game Summary
        </h3>
        <p className="text-zinc-500 text-sm">Summary not available for this game.</p>
      </div>
    );
  }

  // Format the timestamp
  const generatedDate = new Date(summary.generated_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-iowa-gold" />
        Game Summary
      </h3>
      
      <p className="text-zinc-300 text-sm leading-relaxed whitespace-pre-line">
        {summary.summary}
      </p>
      
      <p className="text-zinc-600 text-xs mt-4">
        Date: {generatedDate}
      </p>
    </div>
  );
}