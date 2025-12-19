import { useState, useEffect } from 'react';
import { MessageCircle } from 'lucide-react';

interface RedditSentimentProps {
  gameId: string;
  redditUrl?: string;
}

interface NotableQuote {
  text: string;
  context: string;
}

interface SentimentResponse {
  score: number;
  label: string;
  summary: string;
  themes: string[];
  notable_quotes: NotableQuote[];
  comment_count: number;
  analyzed_at: string;
  cached: boolean;
}

const API_BASE = 'https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod';

// Color mapping for sentiment labels
const sentimentColors: Record<string, { bg: string; text: string; bar: string }> = {
  'Ecstatic': { bg: 'bg-green-500/20', text: 'text-green-400', bar: 'bg-green-500' },
  'Happy': { bg: 'bg-green-500/20', text: 'text-green-400', bar: 'bg-green-500' },
  'Satisfied': { bg: 'bg-blue-500/20', text: 'text-blue-400', bar: 'bg-blue-500' },
  'Mixed': { bg: 'bg-yellow-500/20', text: 'text-yellow-400', bar: 'bg-yellow-500' },
  'Disappointed': { bg: 'bg-orange-500/20', text: 'text-orange-400', bar: 'bg-orange-500' },
  'Frustrated': { bg: 'bg-red-500/20', text: 'text-red-400', bar: 'bg-red-500' },
  'Upset': { bg: 'bg-red-500/20', text: 'text-red-400', bar: 'bg-red-500' },
};

export function RedditSentiment({ gameId, redditUrl }: RedditSentimentProps) {
  const [sentiment, setSentiment] = useState<SentimentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSentiment() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE}/games/${gameId}/sentiment`);
        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to load sentiment');
        }
        const data = await response.json();
        setSentiment(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchSentiment();
  }, [gameId]);

  // Loading state
  if (loading) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
        <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-orange-500" />
          Fan Sentiment
        </h3>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-zinc-800 rounded w-1/3"></div>
          <div className="h-2 bg-zinc-800 rounded w-full"></div>
          <div className="h-4 bg-zinc-800 rounded w-full"></div>
          <div className="h-4 bg-zinc-800 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  // Error or no data state
  if (error || !sentiment) {
    // If no Reddit URL, don't show anything
    if (!redditUrl) return null;
    
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
        <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-orange-500" />
          Fan Sentiment
        </h3>
        <p className="text-zinc-500 text-sm">Sentiment analysis not available for this game.</p>
        {redditUrl && (
          
            <a href={redditUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-orange-500 hover:text-orange-400 transition-colors text-sm mt-2"
          >
            View Game Thread on Reddit →
          </a>
        )}
      </div>
    );
  }

  const colors = sentimentColors[sentiment.label] || sentimentColors['Mixed'];

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
        <MessageCircle className="w-5 h-5 text-orange-500" />
        Fan Sentiment
        <span className="text-zinc-500 text-sm font-normal ml-auto">
          {sentiment.comment_count} comments analyzed
        </span>
      </h3>

      {/* Score and Label */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="text-3xl font-bold text-white">{sentiment.score}</div>
          <div className="text-zinc-500 text-sm">/10</div>
          <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className={`h-full ${colors.bar} transition-all duration-500`}
              style={{ width: `${sentiment.score * 10}%` }}
            />
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors.bg} ${colors.text}`}>
          {sentiment.label}
        </span>
      </div>

      {/* Summary */}
      <p className="text-zinc-300 text-sm leading-relaxed mb-4">
        {sentiment.summary}
      </p>

      {/* Themes */}
      <div className="mb-4">
        <p className="text-zinc-500 text-xs uppercase tracking-wider mb-2">Key Themes</p>
        <div className="flex flex-wrap gap-2">
          {sentiment.themes.map((theme, index) => (
            <span 
              key={index}
              className="px-2 py-1 bg-zinc-800 text-zinc-300 text-xs rounded-full"
            >
              {theme}
            </span>
          ))}
        </div>
      </div>

      {/* Notable Quotes */}
      {sentiment.notable_quotes.length > 0 && (
        <div className="border-t border-zinc-800 pt-4">
          <p className="text-zinc-500 text-xs uppercase tracking-wider mb-2">Fan Reactions</p>
          <div className="space-y-3">
            {sentiment.notable_quotes.map((quote, index) => (
              <div key={index} className="text-sm">
                <p className="text-zinc-300 italic">"{quote.text}"</p>
                <p className="text-zinc-600 text-xs mt-1">— {quote.context}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reddit Link */}
      {redditUrl && (
        <div className="border-t border-zinc-800 pt-4 mt-4">
          
            <a href={redditUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-orange-500 hover:text-orange-400 transition-colors text-sm"
          >
            📱 View Full Thread on Reddit →
          </a>
        </div>
      )}
    </div>
  );
}