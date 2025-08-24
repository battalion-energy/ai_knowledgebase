import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col items-center justify-center">
      <div className="max-w-4xl mx-auto text-center px-4">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Welcome to Energence.ai
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-Enabled Energy Intelligence Platform for ERCOT Market Analysis
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <Link href="/search" className="group">
            <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-green-200 transition-colors">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">Document Search</h3>
              <p className="text-gray-600">
                Search through ERCOT protocols, NPRRs, and market documents with advanced semantic search
              </p>
            </div>
          </Link>

          <Link href="/chat" className="group">
            <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-200 transition-colors">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">AI Assistant</h3>
              <p className="text-gray-600">
                Get intelligent answers about energy markets with context from relevant documents
              </p>
            </div>
          </Link>

          <Link href="/analytics" className="group">
            <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">Analytics</h3>
              <p className="text-gray-600">
                Track search patterns, document usage, and gain insights into market trends
              </p>
            </div>
          </Link>
        </div>

        <div className="mt-12">
          <p className="text-sm text-gray-500">
            Powered by ChromaDB • {new Date().toLocaleDateString()} Index
          </p>
        </div>
      </div>
    </div>
  )
}