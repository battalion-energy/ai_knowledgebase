'use client'

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import AccountStatusButton from './auth/AccountStatusButton';

const drawerWidth = 280;

interface NavigationItem {
  text: string;
  icon: React.ReactElement;
  href?: string;
  children?: NavigationItem[];
}

// Icon components using SVG
const MenuIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const ChevronLeftIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
  </svg>
);

const ChevronDownIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

const ChevronUpIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
  </svg>
);

const SearchIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const CloseIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

// Navigation icons
const DashboardIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);

const SearchDocIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 21h7a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v11m0 5l4.879-4.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242z" />
  </svg>
);

const DocumentIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const ChatIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const ChartIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const BookOpenIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const TagIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
  </svg>
);

const FolderIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
  </svg>
);

const ClockIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const BookmarkIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
  </svg>
);

const SettingsIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const DatabaseIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
  </svg>
);

const LightningIcon = ({ color = 'currentColor' }: { color?: string }) => (
  <svg className="w-5 h-5" fill="none" stroke={color} viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const SparklesIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const navigationSections = [
  {
    title: 'Main',
    items: [
      { text: 'Dashboard', icon: <DashboardIcon color="#3b82f6" />, color: '#3b82f6', href: '/dashboard' },
      { text: 'Search Documents', icon: <SearchDocIcon color="#10b981" />, color: '#10b981', href: '/search' },
      { text: 'AI Assistant', icon: <ChatIcon color="#a855f7" />, color: '#a855f7', href: '/chat' },
    ],
  },
  {
    title: 'Documents',
    items: [
      { text: 'All Documents', icon: <DocumentIcon color="#6366f1" />, color: '#6366f1', href: '/documents' },
      { text: 'NPRR', icon: <FolderIcon color="#ec4899" />, color: '#ec4899', href: '/documents/nprr' },
      { text: 'Protocols', icon: <BookOpenIcon color="#f59e0b" />, color: '#f59e0b', href: '/documents/protocols' },
      { text: 'Operating Guides', icon: <BookOpenIcon color="#14b8a6" />, color: '#14b8a6', href: '/documents/guides' },
      { text: 'Reports', icon: <ChartIcon color="#0ea5e9" />, color: '#0ea5e9', href: '/documents/reports' },
      { text: 'Categories', icon: <TagIcon color="#84cc16" />, color: '#84cc16', href: '/documents/categories' },
    ],
  },
  {
    title: 'Analytics',
    items: [
      { text: 'Search Analytics', icon: <ChartIcon color="#6366f1" />, color: '#6366f1', href: '/analytics/search' },
      { text: 'Usage Metrics', icon: <LightningIcon color="#f59e0b" />, color: '#f59e0b', href: '/analytics/usage' },
      { text: 'Document Insights', icon: <DatabaseIcon color="#10b981" />, color: '#10b981', href: '/analytics/documents' },
    ],
  },
  {
    title: 'Personal',
    items: [
      { text: 'Recent Activity', icon: <ClockIcon color="#64748b" />, color: '#64748b', href: '/activity' },
      { text: 'Saved Searches', icon: <BookmarkIcon color="#06b6d4" />, color: '#06b6d4', href: '/saved' },
      { text: 'Annotations', icon: <TagIcon color="#a855f7" />, color: '#a855f7', href: '/annotations' },
      { text: 'Settings', icon: <SettingsIcon color="#6b7280" />, color: '#6b7280', href: '/settings' },
    ],
  },
];

interface NavigationProps {
  open?: boolean;
  onToggle?: () => void;
}

export default function Navigation({ open: controlledOpen, onToggle }: NavigationProps = {}) {
  const [localOpen, setLocalOpen] = useState(true);
  const [sectionsOpen, setSectionsOpen] = useState<{ [key: string]: boolean }>(
    Object.fromEntries(navigationSections.map(section => [section.title, true]))
  );
  const pathname = usePathname();
  const { data: session } = useSession();

  const open = controlledOpen !== undefined ? controlledOpen : localOpen;
  
  const handleDrawerToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setLocalOpen(!localOpen);
    }
  };

  const handleSectionToggle = (sectionTitle: string) => {
    setSectionsOpen(prev => ({
      ...prev,
      [sectionTitle]: !prev[sectionTitle],
    }));
  };

  return (
    <>
      {/* App Bar */}
      <header className="fixed top-0 left-0 right-0 z-30 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center h-16 px-4">
          <button
            onClick={handleDrawerToggle}
            className="p-2 mr-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="toggle drawer"
          >
            {open ? <ChevronLeftIcon /> : <MenuIcon />}
          </button>
          
          <button
            className="p-2 mr-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="search"
          >
            <SearchIcon />
          </button>

          <img
            src="/Battalogo_2025.png"
            alt="Battalion Energy Logo"
            className="w-8 h-8 object-contain mr-2"
          />
          
          <div className="flex flex-col">
            <h1 className="text-lg font-semibold">
              Energence.ai
            </h1>
            <span className="text-xs text-gray-500">AI-Enabled Energy Intelligence Platform</span>
          </div>
          
          <div className="ml-2 text-xs text-gray-400 border-l pl-2">
            by Battalion Energy
          </div>

          <div className="flex-grow flex items-center justify-center px-4">
            <div className="max-w-2xl w-full">
              <input
                type="text"
                placeholder="Quick search documents..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            {session?.user && (
              <>
                <Link 
                  href="/admin"
                  title="Admin Panel"
                  className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </Link>
              </>
            )}
            <AccountStatusButton 
              session={session}
            />
          </div>
        </div>
      </header>

      {/* Drawer */}
      <aside
        className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-gray-50 border-r border-gray-200 transition-all duration-300 ease-in-out overflow-hidden ${
          open ? 'w-[280px]' : 'w-0'
        }`}
      >
        <div className="h-full overflow-y-auto flex flex-col">
          <div className="flex-1">
            {navigationSections.map((section) => (
              <div key={section.title}>
                <button
                  onClick={() => handleSectionToggle(section.title)}
                  className="w-full px-6 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
                >
                  <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {section.title}
                  </span>
                  {sectionsOpen[section.title] ? <ChevronUpIcon /> : <ChevronDownIcon />}
                </button>
                
                {sectionsOpen[section.title] && (
                  <div className="pb-2">
                    {section.items.map((item) => {
                      const isActive = pathname === item.href || 
                        (item.href && pathname.startsWith(item.href));
                      
                      return (
                        <Link
                          key={item.text}
                          href={item.href || '#'}
                          className={`flex items-center px-4 py-2 mx-2 rounded-lg transition-colors ${
                            isActive
                              ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600'
                              : 'text-gray-700 hover:bg-gray-100 border-l-4 border-transparent'
                          }`}
                        >
                          <span className="mr-3" style={{ color: isActive ? '#3b82f6' : item.color }}>
                            {item.icon}
                          </span>
                          <span className={`text-sm ${isActive ? 'font-medium' : ''}`}>
                            {item.text}
                          </span>
                        </Link>
                      );
                    })}
                  </div>
                )}
                
                {section.title !== 'Personal' && <div className="border-b border-gray-200 my-2 mx-4" />}
              </div>
            ))}
          </div>
          
          {/* Info Box */}
          <div className="mt-auto border-t border-gray-200">
            <div className="bg-white rounded-lg p-4 m-4 border border-gray-200 relative">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <SparklesIcon />
                  <h3 className="text-sm font-semibold">Energence.ai</h3>
                </div>
                <button className="p-1 hover:bg-gray-100 rounded">
                  <CloseIcon />
                </button>
              </div>
              
              <p className="text-sm text-gray-600 mb-3">
                ERCOT Knowledge Base • ChromaDB Index • Updated {new Date().toLocaleDateString()}
              </p>
              
              <Link
                href="/admin/index"
                className="block text-center py-2 px-4 border border-blue-500 text-blue-500 rounded font-medium text-sm hover:bg-blue-500 hover:text-white transition-colors"
              >
                Update Index
              </Link>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}