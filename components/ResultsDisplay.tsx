'use client'

import { Download, CheckCircle, XCircle, TrendingUp } from 'lucide-react'

interface ResultsDisplayProps {
  results: {
    strengths: string[]
    weaknesses: string[]
    recommendation: string
    matchPercentage: number
    fourWeekPlan: string
    pdf_available?: boolean
  }
  onDownload: () => void
  onNewProcess: () => void
}

export default function ResultsDisplay({ results, onDownload, onNewProcess }: ResultsDisplayProps) {
  const getMatchColor = (percentage: number) => {
    if (percentage >= 70) return 'text-green-600 bg-green-50'
    if (percentage >= 50) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="space-y-6">
      {/* Match Percentage */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold text-gray-900">
            Analysis Results
          </h2>
          <div
            className={`px-4 py-2 rounded-full font-bold text-2xl ${getMatchColor(
              results.matchPercentage
            )}`}
          >
            {results.matchPercentage}%
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
          <div
            className={`h-4 rounded-full transition-all ${
              results.matchPercentage >= 70
                ? 'bg-green-500'
                : results.matchPercentage >= 50
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${results.matchPercentage}%` }}
          />
        </div>
      </div>

      {/* Recommendation */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
          Recommendation
        </h3>
        <p className="text-gray-700 leading-relaxed">{results.recommendation}</p>
      </div>

      {/* Strengths */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
          Strengths
        </h3>
        <ul className="space-y-2">
          {results.strengths.map((strength, index) => (
            <li key={index} className="flex items-start">
              <span className="text-green-500 mr-2">•</span>
              <span className="text-gray-700">{strength}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Weaknesses */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <XCircle className="h-5 w-5 mr-2 text-red-600" />
          Weaknesses
        </h3>
        <ul className="space-y-2">
          {results.weaknesses.map((weakness, index) => (
            <li key={index} className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span className="text-gray-700">{weakness}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Four Week Plan */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
          4-Week Plan
        </h3>
        <div className="text-gray-700 leading-relaxed space-y-3">
          {(() => {
            // Split by weeks first (handle both newlines and inline weeks)
            const fullText = results.fourWeekPlan
            const weekPattern = /(Semana\s*\d+|Week\s*\d+)\s*:\s*([^]*?)(?=(?:Semana\s*\d+|Week\s*\d+)\s*:|$)/gi
            const weeks: Array<{number: string, content: string}> = []
            let match
            
            // Reset regex lastIndex
            weekPattern.lastIndex = 0
            
            while ((match = weekPattern.exec(fullText)) !== null) {
              weeks.push({
                number: match[1],
                content: match[2].trim()
              })
            }
            
            // If we found weeks using regex, render them
            if (weeks.length > 0) {
              return weeks.map((week, weekIndex) => {
                // Extract title (everything until first period or "Objetivos:")
                const titleMatch = week.content.match(/^([^\.]+?)(?:\.|Objetivos:)/)
                const title = titleMatch ? titleMatch[1].trim() : week.content.split('.')[0].trim()
                const content = titleMatch 
                  ? week.content.substring(titleMatch[0].length).trim()
                  : week.content.substring(week.content.indexOf('.') + 1).trim()
                
                return (
                  <div key={weekIndex} className="mt-6 mb-3 first:mt-0">
                    <h4 className="text-gray-900 text-lg border-b border-gray-200 pb-2 mb-3 font-semibold">
                      {week.number}: {title}
                    </h4>
                    {content && (
                      <div className="text-gray-700 pl-4 space-y-2">
                        {content.split('\n').map((line, lineIndex) => {
                          const trimmedLine = line.trim()
                          if (!trimmedLine) return null
                          
                          // Check if it's a bullet point
                          if (trimmedLine.startsWith('-') || trimmedLine.startsWith('•') || trimmedLine.startsWith('*')) {
                            return (
                              <div key={lineIndex} className="flex items-start">
                                <span className="text-blue-500 mr-2">•</span>
                                <span className="flex-1">{trimmedLine.substring(1).trim()}</span>
                              </div>
                            )
                          }
                          
                          // Check if it starts with "Objetivos:" or "Acciones:"
                          if (/^(Objetivos|Acciones|Actions|Goals):/i.test(trimmedLine)) {
                            return (
                              <p key={lineIndex} className="font-medium text-gray-900 mt-2">
                                {trimmedLine}
                              </p>
                            )
                          }
                          
                          return (
                            <p key={lineIndex}>{trimmedLine}</p>
                          )
                        }).filter(Boolean)}
                      </div>
                    )}
                  </div>
                )
              })
            }
            
            // Fallback: original line-by-line processing
            return results.fourWeekPlan.split('\n').map((line, index) => {
              const trimmedLine = line.trim()
              
              if (trimmedLine === '') {
                return null
              }
              
              const weekHeaderMatch = trimmedLine.match(/^(semana\s*\d+|week\s*\d+)\s*:\s*(.+)/i)
              
              if (weekHeaderMatch) {
                const weekNumber = weekHeaderMatch[1]
                const weekContent = weekHeaderMatch[2]
                const firstPeriodIndex = weekContent.indexOf('.')
                const title = firstPeriodIndex !== -1 
                  ? weekContent.substring(0, firstPeriodIndex).trim()
                  : weekContent.trim()
                const content = firstPeriodIndex !== -1 
                  ? weekContent.substring(firstPeriodIndex + 1).trim()
                  : ''
                
                return (
                  <div key={index} className="mt-6 mb-3 first:mt-0">
                    <h4 className="text-gray-900 text-lg border-b border-gray-200 pb-2 mb-3 font-semibold">
                      {weekNumber}: {title}
                    </h4>
                    {content && (
                      <p className="text-gray-700 pl-4">{content}</p>
                    )}
                  </div>
                )
              }
              
              if (trimmedLine.startsWith('-') || trimmedLine.startsWith('•') || trimmedLine.startsWith('*')) {
                return (
                  <div key={index} className="flex items-start pl-4">
                    <span className="text-blue-500 mr-2">•</span>
                    <span className="flex-1 text-gray-700">{trimmedLine.substring(1).trim()}</span>
                  </div>
                )
              }
              
              return (
                <p key={index} className="pl-4 text-gray-700">
                  {trimmedLine}
                </p>
              )
            }).filter(Boolean)
          })()}
        </div>
      </div>

      {/* Download Button */}
      {results.pdf_available !== false && (
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-3">
          <button
            onClick={onDownload}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-md font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center"
          >
            <Download className="h-5 w-5 mr-2" />
            Download Full PDF
          </button>
          <button
            onClick={onNewProcess}
            className="w-full bg-gray-200 text-gray-700 py-3 px-6 rounded-md font-semibold hover:bg-gray-300 transition-colors"
          >
            Start New Process
          </button>
        </div>
      )}
      {results.pdf_available === false && (
        <div className="bg-white rounded-lg shadow-lg p-6 space-y-3">
          <p className="text-center text-gray-500">
            PDF not available. PDF is automatically generated when analysis is available.
          </p>
          <button
            onClick={onNewProcess}
            className="w-full bg-gray-200 text-gray-700 py-3 px-6 rounded-md font-semibold hover:bg-gray-300 transition-colors"
          >
            Start New Process
          </button>
        </div>
      )}
    </div>
  )
}

