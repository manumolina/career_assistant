'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Link as LinkIcon } from 'lucide-react'

interface FileInputProps {
  label: string
  file: File | null
  link: string
  onFileChange: (file: File | null) => void
  onLinkChange: (link: string) => void
}

export default function FileInput({
  label,
  file,
  link,
  onFileChange,
  onLinkChange,
}: FileInputProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileChange(acceptedFiles[0])
    }
  }, [onFileChange])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
  })

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        {label}
      </label>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* File Upload */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
          {file ? (
            <p className="text-sm text-gray-700">{file.name}</p>
          ) : (
            <p className="text-sm text-gray-600">
              Arrastra un archivo aquí o haz clic para seleccionar
            </p>
          )}
        </div>

        {/* Link Input */}
        <div className="flex flex-col">
          <div className="flex items-center mb-2">
            <LinkIcon className="h-5 w-5 text-gray-400 mr-2" />
            <span className="text-sm text-gray-600">O introduce un enlace</span>
          </div>
          <input
            type="text"
            value={link}
            onChange={(e) => onLinkChange(e.target.value)}
            placeholder="https://..."
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {(file || link) && (
        <button
          onClick={() => {
            onFileChange(null)
            onLinkChange('')
          }}
          className="text-sm text-red-600 hover:text-red-700"
        >
          Limpiar
        </button>
      )}
    </div>
  )
}

