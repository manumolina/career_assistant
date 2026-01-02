'use client'

import { Check, Circle } from 'lucide-react'

interface ProgressTrackerProps {
  status: {
    tasks: {
      understand_cv: boolean
      understand_offer: boolean
      compare: boolean
      generate_pdf: boolean
    }
    status: string
  }
}

export default function ProgressTracker({ status }: ProgressTrackerProps) {
  const tasks = [
    { id: 'understand_cv', label: 'Understanding CV', completed: status.tasks.understand_cv },
    { id: 'understand_offer', label: 'Understanding job offer', completed: status.tasks.understand_offer },
    { id: 'compare', label: 'Comparing and analyzing', completed: status.tasks.compare },
    { id: 'generate_pdf', label: 'Generating PDF', completed: status.tasks.generate_pdf },
  ]

  // Find the first incomplete task to show as "in progress"
  const currentTaskIndex = tasks.findIndex(task => !task.completed)
  const isProcessing = currentTaskIndex !== -1

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6 animate-fade-in">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
        <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Analysis Progress
      </h2>
      <div className="space-y-4">
        {tasks.map((task, index) => {
          const isCurrentTask = index === currentTaskIndex && isProcessing
          return (
            <div key={task.id} className="flex items-center space-x-3 transition-all duration-300">
              {task.completed ? (
                <Check className="h-6 w-6 text-green-500 animate-scale-in" />
              ) : isCurrentTask ? (
                <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <Circle className="h-6 w-6 text-gray-300" />
              )}
              <span
                className={`text-lg transition-colors duration-300 ${
                  task.completed 
                    ? 'text-gray-900 font-medium' 
                    : isCurrentTask 
                    ? 'text-blue-600 font-medium animate-pulse' 
                    : 'text-gray-400'
                }`}
              >
                {task.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

