import React, { useEffect, useRef } from 'react';

interface CommentaryItem {
  commentary: string;
  excitement: number;
  timestamp: string;
  playId: string;
}

interface AICommentaryProps {
  commentary: CommentaryItem[];
}

export const AICommentary: React.FC<AICommentaryProps> = ({ commentary }) => {
  const feedRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest commentary
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [commentary]);

  const getExcitementClass = (excitement: number) => {
    if (excitement > 0.8) {
      return 'text-xl font-bold text-yellow-400 animate-pulse';
    } else if (excitement > 0.5) {
      return 'text-lg font-semibold text-blue-300';
    } else {
      return 'text-base text-gray-300';
    }
  };

  const getExcitementBg = (excitement: number) => {
    if (excitement > 0.8) {
      return 'bg-gradient-to-r from-yellow-900/30 to-orange-900/30 border-yellow-500/50';
    } else if (excitement > 0.5) {
      return 'bg-gradient-to-r from-blue-900/30 to-purple-900/30 border-blue-500/50';
    } else {
      return 'bg-gray-800/30 border-gray-600/50';
    }
  };

  if (commentary.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 h-96 flex items-center justify-center">
        <p className="text-gray-400 text-center">
          🎙️ AI Commentary will appear here during the game...
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 h-96 flex flex-col">
      <h3 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
        🎙️ AI Commentary
      </h3>
      
      <div 
        ref={feedRef}
        className="flex-1 overflow-y-auto space-y-3 scroll-smooth"
      >
        {commentary.map((item, index) => (
          <div
            key={`${item.playId}-${item.timestamp}`}
            className={`
              p-4 rounded-lg border-l-4 
              ${getExcitementBg(item.excitement)}
              transform transition-all duration-300 ease-in-out
              hover:scale-[1.02] hover:shadow-lg
              animate-slideIn
            `}
          >
            <p className={`${getExcitementClass(item.excitement)} mb-1`}>
              {item.commentary}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              {new Date(item.timestamp).toLocaleTimeString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};