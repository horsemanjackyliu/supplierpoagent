'use client'

import { ArrowRight } from 'lucide-react'

interface Props {
  questions: string[]
  onSelect: (q: string) => void
}

export default function SuggestedQuestions({ questions, onSelect }: Props) {
  return (
    <div className="w-full max-w-lg">
      <p className="text-xs font-medium text-sap-gray-400 uppercase tracking-wider mb-3 text-center">
        Try asking
      </p>
      <div className="flex flex-col gap-2">
        {questions.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="w-full text-left sap-card px-4 py-3 text-sm text-sap-gray-800
                       hover:border-sap-blue hover:text-sap-blue transition-colors duration-150
                       flex items-center justify-between group"
          >
            <span>{q}</span>
            <ArrowRight className="w-4 h-4 text-sap-gray-400 group-hover:text-sap-blue flex-shrink-0 ml-2" />
          </button>
        ))}
      </div>
    </div>
  )
}
