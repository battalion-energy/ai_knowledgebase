'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

interface SearchResult {
  id: string
  title: string
  content: string
  type: string
  score: number
  metadata: {
    source: string
    page?: number
    date?: string
    tags?: string[]
  }
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  const { data: results, isLoading, error } = useQuery({
    queryKey: ['search', searchTerm],
    queryFn: async () => {
      if (!searchTerm) return []
      const response = await fetch(`/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchTerm })
      })
      if (!response.ok) throw new Error('Search failed')
      return response.json()
    },
    enabled: searchTerm.length > 2,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchTerm(query)
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Search Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Document Search</h1>
        <p className="text-gray-600">Search through ERCOT protocols, NPRRs, and market documents</p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for energy market documents, protocols, or regulations..."
            className="w-full px-6 py-4 pr-12 text-lg border border-gray-200 rounded-xl 
                     bg-white/80 backdrop-blur-sm shadow-lg
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     transition-all duration-200"
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 p-3 
                     bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     transition-colors duration-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </div>
      </form>

      {/* Filters */}
      <div className="mb-6 flex gap-3 flex-wrap">
        <FilterChip label="All Types" active />
        <FilterChip label="NPRR" />
        <FilterChip label="Protocols" />
        <FilterChip label="Guides" />
        <FilterChip label="Reports" />
        <FilterChip label="Tariffs" />
      </div>

      {/* Results */}
      <div className="space-y-4">
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center gap-2 text-gray-600">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Searching...
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50/80 backdrop-blur-sm border border-red-200 rounded-lg p-4 text-red-700">
            Error: {(error as Error).message}
          </div>
        )}

        {results?.map((result: SearchResult) => (
          <SearchResultCard key={result.id} result={result} />
        ))}

        {searchTerm && !isLoading && !error && results?.length === 0 && (
          <div className="text-center py-12 text-gray-600">
            No results found for "{searchTerm}"
          </div>
        )}

        {!searchTerm && !isLoading && (
          <div className="text-center py-12">
            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-8 shadow-lg border border-gray-100">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Start Searching</h3>
              <p className="text-gray-600">Enter a search term to find relevant ERCOT documents</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function FilterChip({ label, active = false }: { label: string; active?: boolean }) {
  return (
    <button
      className={`px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 
                  ${active 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'bg-white/70 backdrop-blur-sm text-gray-700 hover:bg-white/90 border border-gray-200'}`}
    >
      {label}
    </button>
  )
}

function SearchResultCard({ result }: { result: SearchResult }) {
  return (
    <div className="bg-white/70 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-gray-100 
                    hover:bg-white/80 hover:shadow-xl transition-all duration-200 cursor-pointer">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors">
          {result.title}
        </h3>
        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded">
          {result.type}
        </span>
      </div>
      
      <p className="text-gray-600 text-sm mb-3 line-clamp-2">
        {result.content}
      </p>
      
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {result.metadata.source}
        </span>
        {result.metadata.page && (
          <span>Page {result.metadata.page}</span>
        )}
        {result.metadata.date && (
          <span>{new Date(result.metadata.date).toLocaleDateString()}</span>
        )}
        <span className="ml-auto text-green-600 font-medium">
          {Math.round(result.score * 100)}% match
        </span>
      </div>
      
      {result.metadata.tags && result.metadata.tags.length > 0 && (
        <div className="mt-3 flex gap-2 flex-wrap">
          {result.metadata.tags.map(tag => (
            <span key={tag} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}