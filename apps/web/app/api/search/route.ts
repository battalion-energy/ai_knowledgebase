import { NextRequest, NextResponse } from 'next/server'

const SEARCH_API_URL = process.env.SEARCH_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const { query, filters, limit = 20 } = await request.json()

    if (!query) {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      )
    }

    // Call the Python search API
    const searchResponse = await fetch(`${SEARCH_API_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        limit,
        filters,
      }),
    })

    if (!searchResponse.ok) {
      throw new Error(`Search API returned ${searchResponse.status}`)
    }

    const searchResults = await searchResponse.json()

    // Transform the results to match our frontend format
    const transformedResults = searchResults.results?.map((result: any) => ({
      id: result.id || result.metadata?.document_id || Math.random().toString(),
      title: result.metadata?.title || extractTitle(result.content),
      content: result.content || result.text,
      type: result.metadata?.type || 'DOCUMENT',
      score: result.score || result.similarity || 0,
      metadata: {
        source: result.metadata?.source || 'Unknown',
        page: result.metadata?.page,
        date: result.metadata?.date,
        tags: result.metadata?.tags || [],
        ktc: result.metadata?.ktc,
      },
    })) || []

    // Log search analytics (optional)
    // await logSearchEvent(query, transformedResults.length)

    return NextResponse.json(transformedResults)
  } catch (error) {
    console.error('Search error:', error)
    return NextResponse.json(
      { error: 'Failed to perform search' },
      { status: 500 }
    )
  }
}

// Helper function to extract title from content
function extractTitle(content: string): string {
  if (!content) return 'Untitled Document'
  
  // Try to get first line or first 60 characters
  const firstLine = content.split('\n')[0]
  if (firstLine.length <= 100) {
    return firstLine
  }
  
  return content.substring(0, 60) + '...'
}