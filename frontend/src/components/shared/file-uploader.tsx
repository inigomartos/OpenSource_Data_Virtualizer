'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface Props {
  accept?: Record<string, string[]>;
  onUpload: (file: File) => Promise<void>;
}

export default function FileUploader({ accept, onUpload }: Props) {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploading(true);
      try {
        await onUpload(acceptedFiles[0]);
      } finally {
        setUploading(false);
      }
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept || { 'text/csv': ['.csv'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        isDragActive ? 'border-brand-primary bg-brand-primary/5' : 'border-border-default hover:border-border-hover'
      }`}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <p className="text-text-secondary">Uploading...</p>
      ) : isDragActive ? (
        <p className="text-brand-primary">Drop the file here</p>
      ) : (
        <div>
          <p className="text-text-secondary mb-1">Drag & drop a CSV or Excel file here</p>
          <p className="text-xs text-text-muted">or click to browse (max 50MB)</p>
        </div>
      )}
    </div>
  );
}
