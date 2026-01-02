'use client';

import { useState } from 'react';
import LandingSimple from '@/components/landing/LandingSimple';
import LandingGradient from '@/components/landing/LandingGradient';

export default function HomePage() {
  const [theme, setTheme] = useState<'simple' | 'gradient'>('simple');

  const toggleTheme = () => {
    setTheme(theme === 'simple' ? 'gradient' : 'simple');
  };

  return (
    <>
      {/* Theme Switcher Button */}
      <button
        onClick={toggleTheme}
        className="fixed bottom-6 right-6 z-[100] group"
        aria-label="Switch theme"
      >
        <div className="relative">
          {/* Glow effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full blur-lg opacity-60 group-hover:opacity-100 transition-opacity"></div>

          {/* Button */}
          <div className="relative bg-gray-900 text-white px-6 py-3 rounded-full shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105 flex items-center gap-2">
            <span className="text-2xl">{theme === 'simple' ? '✨' : '🎨'}</span>
            <span className="font-semibold hidden sm:inline">
              {theme === 'simple' ? 'Gradient Theme' : 'Simple Theme'}
            </span>
          </div>
        </div>
      </button>

      {/* Render Selected Theme */}
      {theme === 'simple' ? <LandingSimple /> : <LandingGradient />}
    </>
  );
}
