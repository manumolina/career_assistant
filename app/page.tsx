'use client'

import { useState, useEffect } from 'react'
import FileInput from '@/components/FileInput'
import ProgressTracker from '@/components/ProgressTracker'
import ResultsDisplay from '@/components/ResultsDisplay'
import { Copy, Check } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generate a random session ID
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
}

export default function Home() {
  const [sessionId, setSessionId] = useState<string>('')
  const [previousSessionId, setPreviousSessionId] = useState<string>('')
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [cvLink, setCvLink] = useState('')
  const [jobOfferFile, setJobOfferFile] = useState<File | null>(null)
  const [jobOfferLink, setJobOfferLink] = useState('')
  const [jobOfferText, setJobOfferText] = useState('')
  const [additionalConsiderations, setAdditionalConsiderations] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [processId, setProcessId] = useState<string | null>(null)
  const [status, setStatus] = useState<any>(null)
  const [results, setResults] = useState<any>(null)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [userIP, setUserIP] = useState<string | null>(null)

  // Generate session ID on component mount
  useEffect(() => {
    const newSessionId = generateSessionId()
    setSessionId(newSessionId)
  }, [])

  // Get user IP address on component mount
  useEffect(() => {
    const getIP = async () => {
      try {
        const response = await fetch('https://api.ipify.org?format=json')
        const data = await response.json()
        setUserIP(data.ip)
      } catch (error) {
        console.error('Error obteniendo IP:', error)
        // Continue without IP if the service fails
      }
    }
    getIP()
  }, [])

  const handleCopySessionId = async () => {
    try {
      await navigator.clipboard.writeText(sessionId)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Error copying to clipboard:', error)
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = sessionId
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleProcess = async () => {
    // If using previous session, files are not required
    const hasPreviousSession = previousSessionId.trim() !== ''
    const hasJobOffer = jobOfferFile || jobOfferLink || jobOfferText.trim()
    const hasFiles = (cvFile || cvLink) && hasJobOffer
    
    if (!hasPreviousSession && !hasFiles) {
      alert('Por favor, proporciona el CV y la oferta de trabajo, o introduce una sesión anterior')
      return
    }
    
    if (!hasPreviousSession && (!cvFile && !cvLink)) {
      alert('Por favor, proporciona el CV')
      return
    }
    
    if (!hasPreviousSession && (!jobOfferFile && !jobOfferLink && !jobOfferText.trim())) {
      alert('Por favor, proporciona la oferta de trabajo')
      return
    }

    setIsProcessing(true)
    setProcessId(null)
    setStatus(null)
    setResults(null)
    setError(null)

    try {
      const formData = new FormData()
      if (cvFile) formData.append('cv_file', cvFile)
      if (cvLink) formData.append('cv_link', cvLink)
      if (jobOfferFile) formData.append('job_offer_file', jobOfferFile)
      if (jobOfferLink) formData.append('job_offer_link', jobOfferLink)
      if (jobOfferText.trim()) formData.append('job_offer_text', jobOfferText.trim())
      if (additionalConsiderations) formData.append('additional_considerations', additionalConsiderations)
      formData.append('user_id', 'demo')
      
      // Use previous session if provided, otherwise use current session
      const sessionToUse = previousSessionId.trim() || sessionId.trim()
      if (sessionToUse) {
        formData.append('session_id', sessionToUse)
      }
      
      // Add user IP if available
      if (userIP) {
        formData.append('user_ip', userIP)
      }

      const response = await fetch(`${API_URL}/api/process`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        
        // Check if it's a session not found error
        if (response.status === 404 && errorData.detail?.error === 'session_not_found') {
          setError(errorData.detail.message + ' ' + errorData.detail.suggestion)
          setIsProcessing(false)
          return
        }
        
        // Check if it's an invalid request error (session_id + files)
        if (response.status === 400 && errorData.detail?.error === 'invalid_request') {
          setError(errorData.detail.message + ' ' + errorData.detail.suggestion)
          setIsProcessing(false)
          return
        }
        
        // Check if it's a rate limit error (per IP)
        if (response.status === 429 && errorData.detail?.error === 'rate_limit_exceeded') {
          setError(errorData.detail.message + ' ' + errorData.detail.suggestion)
          setIsProcessing(false)
          return
        }
        
        // Check if it's a global rate limit error
        if (response.status === 429 && errorData.detail?.error === 'global_rate_limit_exceeded') {
          setError(errorData.detail.message + ' ' + errorData.detail.suggestion)
          setIsProcessing(false)
          return
        }
        
        // Generic error
        const errorMessage = errorData.detail?.message || errorData.detail || 'Error al procesar la solicitud'
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setProcessId(data.process_id)
      setResults(data.results)

      // Poll for status updates
      const pollInterval = setInterval(async () => {
        if (data.process_id) {
          try {
            const statusResponse = await fetch(`${API_URL}/api/status/${data.process_id}`)
            const statusData = await statusResponse.json()
            setStatus(statusData)
            
            if (statusData.status === 'completed' || statusData.status === 'error') {
              clearInterval(pollInterval)
              setIsProcessing(false)
              if (statusData.results) {
                setResults(statusData.results)
              }
            }
          } catch (error) {
            console.error('Error polling status:', error)
          }
        }
      }, 1000)

    } catch (error) {
      console.error('Error:', error)
      setError(error instanceof Error ? error.message : 'Error al procesar la solicitud. Por favor, intenta de nuevo.')
      setIsProcessing(false)
    }
  }

  const handleDownload = async () => {
    if (!processId) return

    try {
      const response = await fetch(`${API_URL}/api/download/${processId}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `career_analysis_${processId}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error downloading PDF:', error)
      alert('Error al descargar el PDF')
    }
  }

  const handleNewProcess = () => {
    setResults(null)
    setProcessId(null)
    setStatus(null)
    setIsProcessing(false)
    setCvFile(null)
    setCvLink('')
    setJobOfferFile(null)
    setJobOfferLink('')
    setJobOfferText('')
    setAdditionalConsiderations('')
    setPreviousSessionId('')
    setError(null)
    // Generate new session ID
    const newSessionId = generateSessionId()
    setSessionId(newSessionId)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-900 mb-2">
          Career Assistant
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Analiza tu CV frente a ofertas de trabajo
        </p>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-lg shadow-md">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm text-red-700">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="ml-4 flex-shrink-0 text-red-500 hover:text-red-700"
              >
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {!results && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6 space-y-6">
            {/* Current Session ID (read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID de Sesión Actual
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={sessionId}
                  readOnly
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md bg-gray-50 font-mono text-sm cursor-not-allowed"
                />
                <button
                  onClick={handleCopySessionId}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors flex items-center gap-2"
                  title="Copiar al portapapeles"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 text-green-600" />
                      <span className="text-sm text-green-600">Copiado</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 text-gray-600" />
                      <span className="text-sm text-gray-600">Copiar</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Guarda este ID para reutilizarlo más tarde
              </p>
            </div>

            {/* Previous Session ID (editable) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reutilizar Sesión Anterior
                <span className="text-xs text-gray-500 ml-2">
                  (opcional - si introduces una sesión, no será necesario adjuntar archivos)
                </span>
              </label>
              <input
                type="text"
                value={previousSessionId}
                onChange={(e) => setPreviousSessionId(e.target.value)}
                placeholder="Pega aquí el ID de una sesión anterior..."
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                Si introduces una sesión anterior válida, se reutilizarán los resultados sin reprocesar
              </p>
            </div>
            <FileInput
              label="CV"
              file={cvFile}
              link={cvLink}
              onFileChange={setCvFile}
              onLinkChange={setCvLink}
            />

            <FileInput
              label="Oferta de Trabajo"
              file={jobOfferFile}
              link={jobOfferLink}
              onFileChange={setJobOfferFile}
              onLinkChange={setJobOfferLink}
            />

            {/* Campo de texto para pegar la oferta directamente */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                O pega el contenido de la oferta aquí (opcional)
              </label>
              <textarea
                value={jobOfferText}
                onChange={(e) => setJobOfferText(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={6}
                placeholder="Pega aquí el contenido completo de la oferta de trabajo..."
              />
              <p className="mt-1 text-xs text-gray-500">
                Útil cuando no puedes acceder directamente al enlace (ej: LinkedIn)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Consideraciones Adicionales (opcional)
              </label>
              <textarea
                value={additionalConsiderations}
                onChange={(e) => setAdditionalConsiderations(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={4}
                placeholder="Añade cualquier consideración adicional que quieras que tenga en cuenta el análisis..."
              />
            </div>

            <button
              onClick={handleProcess}
              disabled={isProcessing}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-md font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isProcessing ? 'Procesando...' : 'Iniciar Proceso'}
            </button>
          </div>
        )}

        {isProcessing && status && (
          <ProgressTracker status={status} />
        )}

        {results && (
          <ResultsDisplay 
            results={results} 
            onDownload={handleDownload}
            onNewProcess={handleNewProcess}
          />
        )}
      </div>
    </main>
  )
}

