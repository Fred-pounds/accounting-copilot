import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '../services/api';

interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export const DocumentUpload: React.FC = () => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const newUploads: UploadProgress[] = acceptedFiles.map((file) => ({
      file,
      progress: 0,
      status: 'uploading' as const,
    }));

    setUploads((prev) => [...prev, ...newUploads]);

    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      const uploadIndex = uploads.length + i;

      try {
        // Validate file
        if (file.size > 10 * 1024 * 1024) {
          throw new Error('File size exceeds 10 MB limit');
        }

        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
        if (!allowedTypes.includes(file.type)) {
          throw new Error('Unsupported file type. Please upload JPEG, PNG, or PDF files.');
        }

        // Get pre-signed URL
        setUploads((prev) => {
          const updated = [...prev];
          updated[uploadIndex].progress = 10;
          return updated;
        });

        const { upload_url } = await apiClient.uploadDocument(file);

        // Upload to S3
        setUploads((prev) => {
          const updated = [...prev];
          updated[uploadIndex].progress = 30;
          return updated;
        });

        await apiClient.uploadToS3(upload_url, file);

        // Success
        setUploads((prev) => {
          const updated = [...prev];
          updated[uploadIndex].progress = 100;
          updated[uploadIndex].status = 'success';
          return updated;
        });
      } catch (error: any) {
        setUploads((prev) => {
          const updated = [...prev];
          updated[uploadIndex].status = 'error';
          updated[uploadIndex].error = error.message || 'Upload failed';
          return updated;
        });
      }
    }
  }, [uploads.length]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'application/pdf': ['.pdf'],
    },
    maxSize: 10 * 1024 * 1024, // 10 MB
  });

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Upload Documents</h1>
      <p style={styles.subtitle}>Upload receipts, invoices, or bank statements</p>

      <div
        {...getRootProps()}
        style={{
          ...styles.dropzone,
          ...(isDragActive ? styles.dropzoneActive : {}),
        }}
      >
        <input {...getInputProps()} />
        <div style={styles.dropzoneContent}>
          <svg
            style={styles.uploadIcon}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          {isDragActive ? (
            <p style={styles.dropzoneText}>Drop files here...</p>
          ) : (
            <>
              <p style={styles.dropzoneText}>
                Drag and drop files here, or click to select
              </p>
              <p style={styles.dropzoneHint}>
                Supported formats: JPEG, PNG, PDF (max 10 MB)
              </p>
            </>
          )}
        </div>
      </div>

      {uploads.length > 0 && (
        <div style={styles.uploadsList}>
          <h2 style={styles.uploadsTitle}>Uploads</h2>
          {uploads.map((upload, index) => (
            <div key={index} style={styles.uploadItem}>
              <div style={styles.uploadInfo}>
                <span style={styles.fileName}>{upload.file.name}</span>
                <span style={styles.fileSize}>
                  {(upload.file.size / 1024).toFixed(1)} KB
                </span>
              </div>

              {upload.status === 'uploading' && (
                <div style={styles.progressContainer}>
                  <div
                    style={{
                      ...styles.progressBar,
                      width: `${upload.progress}%`,
                    }}
                  />
                </div>
              )}

              {upload.status === 'success' && (
                <div style={styles.statusSuccess}>✓ Uploaded successfully</div>
              )}

              {upload.status === 'error' && (
                <div style={styles.statusError}>✗ {upload.error}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '2rem',
    maxWidth: '800px',
    margin: '0 auto',
  },
  title: {
    fontSize: '1.875rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
  },
  subtitle: {
    color: '#666',
    marginBottom: '2rem',
  },
  dropzone: {
    border: '2px dashed #ddd',
    borderRadius: '8px',
    padding: '3rem',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s',
    backgroundColor: '#fafafa',
  },
  dropzoneActive: {
    borderColor: '#007bff',
    backgroundColor: '#f0f8ff',
  },
  dropzoneContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem',
  },
  uploadIcon: {
    width: '48px',
    height: '48px',
    color: '#999',
  },
  dropzoneText: {
    fontSize: '1.125rem',
    color: '#333',
    margin: 0,
  },
  dropzoneHint: {
    fontSize: '0.875rem',
    color: '#999',
    margin: 0,
  },
  uploadsList: {
    marginTop: '2rem',
  },
  uploadsTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    marginBottom: '1rem',
  },
  uploadItem: {
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '0.75rem',
  },
  uploadInfo: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.5rem',
  },
  fileName: {
    fontWeight: '500',
  },
  fileSize: {
    color: '#999',
    fontSize: '0.875rem',
  },
  progressContainer: {
    height: '8px',
    backgroundColor: '#f0f0f0',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#007bff',
    transition: 'width 0.3s',
  },
  statusSuccess: {
    color: '#28a745',
    fontSize: '0.875rem',
    fontWeight: '500',
  },
  statusError: {
    color: '#dc3545',
    fontSize: '0.875rem',
    fontWeight: '500',
  },
};
