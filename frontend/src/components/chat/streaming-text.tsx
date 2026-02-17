'use client';

import { useState, useEffect } from 'react';

interface Props {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

export default function StreamingText({ text, speed = 20, onComplete }: Props) {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText((prev) => prev + text[currentIndex]);
        setCurrentIndex((prev) => prev + 1);
      }, speed);
      return () => clearTimeout(timer);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentIndex, text, speed, onComplete]);

  return (
    <span>
      {displayedText}
      {currentIndex < text.length && (
        <span className="inline-block w-0.5 h-4 bg-brand-primary animate-pulse ml-0.5" />
      )}
    </span>
  );
}
