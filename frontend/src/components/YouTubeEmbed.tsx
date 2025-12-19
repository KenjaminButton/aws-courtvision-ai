import { Play, Tv } from 'lucide-react';

interface YouTubeEmbedProps {
  url: string;
  title?: string;
}

// Extract video ID from YouTube URL
function getYouTubeId(url: string): string | null {
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/);
  return match ? match[1] : null;
}

export function YouTubeEmbed({ url, title = "Video" }: YouTubeEmbedProps) {
  const videoId = getYouTubeId(url);
  
  if (!videoId) {
    return null;
  }

  return (
    <div className="aspect-video w-full rounded-lg overflow-hidden bg-zinc-900">
      <iframe
        src={`https://www.youtube.com/embed/${videoId}`}
        title={title}
        className="w-full h-full"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
}

interface GameMediaProps {
  highlightsUrl?: string | null;
  postgameUrl?: string | null;
  redditUrl?: string | null;
}

export function GameMedia({ highlightsUrl, postgameUrl, redditUrl }: GameMediaProps) {
  const hasMedia = highlightsUrl || postgameUrl || redditUrl;
  
  if (!hasMedia) {
    return null;
  }

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
        <Tv className="w-5 h-5" />
        Game Media
      </h3>
      
      <div className="space-y-4">
        {/* Highlights - Primary embed */}
        {highlightsUrl && (
          <div>
            <p className="text-sm text-zinc-400 mb-2">🎬 Game Highlights</p>
            <YouTubeEmbed url={highlightsUrl} title="Game Highlights" />
          </div>
        )}
        
        {/* Post-game - Also embedded */}
        {postgameUrl && (
          <div>
            <p className="text-sm text-zinc-400 mb-2">🎙️ Post-Game Show</p>
            <YouTubeEmbed url={postgameUrl} title="Post-Game Show" />
          </div>
        )}
        
        {/* Reddit thread link */}
        {redditUrl && (
          <div className="pt-2 border-t border-zinc-800">
            <a
              href={redditUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-orange-500 hover:text-orange-400 transition-colors"
            >
              📱 View Game Thread on Reddit →
            </a>
          </div>
        )}
      </div>
    </div>
  );
}