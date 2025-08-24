'use client'

import { useState } from 'react';
import Navigation from './Navigation';

export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(true);

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <>
      <Navigation open={drawerOpen} onToggle={handleDrawerToggle} />
      <main
        className={`flex-grow p-6 mt-16 bg-gray-50 min-h-[calc(100vh-4rem)] transition-all duration-300 ease-in-out ${
          drawerOpen ? 'ml-[280px]' : 'ml-0'
        }`}
      >
        {children}
      </main>
    </>
  );
}