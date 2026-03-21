'use client';

import { Cloud } from 'lucide-react';

export function FloatingClouds() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <Cloud
        className="absolute top-20 left-10 w-32 h-32 cloud-animation"
        style={{ animationDelay: '0s', color: 'rgba(255, 255, 255, 0.4)' }}
        fill="currentColor"
      />
      <Cloud
        className="absolute top-40 right-20 w-24 h-24 cloud-animation"
        style={{ animationDelay: '5s', color: 'rgba(255, 255, 255, 0.3)' }}
        fill="currentColor"
      />
      <Cloud
        className="absolute bottom-32 left-1/4 w-28 h-28 cloud-animation"
        style={{ animationDelay: '10s', color: 'rgba(255, 255, 255, 0.35)' }}
        fill="currentColor"
      />
      <Cloud
        className="absolute top-1/3 right-1/3 w-36 h-36 cloud-animation"
        style={{ animationDelay: '15s', color: 'rgba(255, 255, 255, 0.25)' }}
        fill="currentColor"
      />
    </div>
  );
}
