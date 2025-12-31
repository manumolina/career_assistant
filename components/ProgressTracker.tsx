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
    { id: 'understand_cv', label: 'Entendiendo el CV', completed: status.tasks.understand_cv },
    { id: 'understand_offer', label: 'Entendiendo la oferta de trabajo', completed: status.tasks.understand_offer },
    { id: 'compare', label: 'Comparando y analizando', completed: status.tasks.compare },
    { id: 'generate_pdf', label: 'Generando PDF', completed: status.tasks.generate_pdf },
  ]

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">
        Progreso del Análisis
      </h2>
      <div className="space-y-4">
        {tasks.map((task, index) => (
          <div key={task.id} className="flex items-center space-x-3">
            {task.completed ? (
              <Check className="h-6 w-6 text-green-500" />
            ) : (
              <Circle className="h-6 w-6 text-gray-300" />
            )}
            <span
              className={`text-lg ${
                task.completed ? 'text-gray-900' : 'text-gray-400'
              }`}
            >
              {task.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

