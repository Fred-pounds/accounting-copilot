import React, { useState, useCallback } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { apiClient } from '../services/api';

interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export const DocumentUpload: React.FC = () => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[], fileRejections: FileRejection[]) => {
    const rejectedUploads: UploadProgress[] = fileRejections.map(({ file, errors }) => {
      let errorMessage = 'Upload failed';
      if (errors[0]?.code === 'file-too-large') errorMessage = 'File size exceeds 10 MB limit';
      else if (errors[0]?.code === 'file-invalid-type') errorMessage = 'Unsupported file type. Please upload JPEG, PNG, or PDF files.';
      return { file, progress: 0, status: 'error', error: errorMessage };
    });

    const newUploads: UploadProgress[] = acceptedFiles.map((file) => ({
      file,
      progress: 0,
      status: 'uploading' as const,
    }));

    setUploads((prev) => [...prev, ...rejectedUploads, ...newUploads]);

    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      const uploadIndex = uploads.length + rejectedUploads.length + i;

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

  const getFileIcon = (type: string) => {
    if (type === 'application/pdf') {
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e11d48" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      );
    }
    return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
    );
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Upload Documents</h1>
        <p style={styles.subtitle}>Upload receipts, invoices, or bank statements for AI-powered processing</p>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        style={{
          ...styles.dropzone,
          ...(isDragActive ? styles.dropzoneActive : {}),
        }}
      >
        <input {...getInputProps()} />
        <div style={styles.dropzoneContent}>
          <div style={{
            ...styles.uploadIconWrap,
            ...(isDragActive ? styles.uploadIconActive : {}),
          }}>
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          {isDragActive ? (
            <p style={styles.dropzoneTextActive}>Drop your files here!</p>
          ) : (
            <>
              <p style={styles.dropzoneText}>
                <strong>Click to upload</strong> or drag and drop
              </p>
              <p style={styles.dropzoneHint}>
                JPEG, PNG, or PDF — up to 10 MB
              </p>
            </>
          )}
        </div>
      </div>

      {/* Supported formats */}
      <div style={styles.formatRow}>
        <div style={styles.formatItem}>
          <span style={{ ...styles.formatDot, backgroundColor: '#6366f1' }} />
          <span style={styles.formatLabel}>Receipts</span>
        </div>
        <div style={styles.formatItem}>
          <span style={{ ...styles.formatDot, backgroundColor: '#059669' }} />
          <span style={styles.formatLabel}>Invoices</span>
        </div>
        <div style={styles.formatItem}>
          <span style={{ ...styles.formatDot, backgroundColor: '#f59e0b' }} />
          <span style={styles.formatLabel}>Bank Statements</span>
        </div>
      </div>

      {/* Upload list */}
      {uploads.length > 0 && (
        <div style={styles.uploadsList}>
          <h2 style={styles.uploadsTitle}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
              <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
            </svg>
            Uploads
          </h2>
          {uploads.map((upload, index) => (
            <div key={index} style={styles.uploadItem}>
              <div style={styles.uploadFileIcon}>
                {getFileIcon(upload.file.type)}
              </div>
              <div style={styles.uploadDetails}>
                <div style={styles.uploadInfo}>
                  <span style={styles.fileName}>{upload.file.name}</span>
                  <span style={styles.fileSize}>
                    {upload.file.size > 1024 * 1024
                      ? `${(upload.file.size / (1024 * 1024)).toFixed(1)} MB`
                      : `${(upload.file.size / 1024).toFixed(1)} KB`}
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
                  <div style={styles.statusSuccess}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Uploaded successfully — AI processing started
                  </div>
                )}

                {upload.status === 'error' && (
                  <div style={styles.statusError}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                    {upload.error}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: 'var(--space-page)',
    maxWidth: '720px',
    margin: '0 auto',
  },
  header: {
    marginBottom: '28px',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: 800,
    color: 'var(--color-text)',
    letterSpacing: '-0.5px',
  },
  subtitle: {
    color: 'var(--color-text-muted)',
    marginTop: '4px',
    fontSize: '0.9rem',
  },
  dropzone: {
    border: '2px dashed var(--color-border)',
    borderRadius: 'var(--radius-xl)',
    padding: '48px 24px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all var(--transition-base)',
    backgroundColor: 'var(--color-card)',
  },
  dropzoneActive: {
    borderColor: 'var(--color-primary)',
    backgroundColor: 'var(--color-primary-50)',
    borderStyle: 'solid',
  },
  dropzoneContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
  },
  uploadIconWrap: {
    width: '72px',
    height: '72px',
    borderRadius: '20px',
    backgroundColor: 'var(--color-primary-50)',
    color: 'var(--color-primary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '4px',
    transition: 'all var(--transition-base)',
  },
  uploadIconActive: {
    backgroundColor: 'var(--color-primary)',
    color: 'white',
    transform: 'scale(1.1)',
  },
  dropzoneText: {
    fontSize: '1rem',
    color: 'var(--color-text)',
    margin: 0,
  },
  dropzoneTextActive: {
    fontSize: '1.1rem',
    color: 'var(--color-primary)',
    fontWeight: 700,
    margin: 0,
  },
  dropzoneHint: {
    fontSize: '0.8rem',
    color: 'var(--color-text-muted)',
    margin: 0,
  },
  formatRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: '24px',
    marginTop: '20px',
    marginBottom: '8px',
  },
  formatItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  formatDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    display: 'inline-block',
  },
  formatLabel: {
    fontSize: '0.8rem',
    color: 'var(--color-text-muted)',
    fontWeight: 500,
  },
  uploadsList: {
    marginTop: '32px',
  },
  uploadsTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '1.05rem',
    fontWeight: 700,
    color: 'var(--color-text)',
    marginBottom: '16px',
  },
  uploadItem: {
    display: 'flex',
    gap: '14px',
    backgroundColor: 'var(--color-card)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    padding: '16px',
    marginBottom: '10px',
    animation: 'slideUp 0.3s ease-out',
  },
  uploadFileIcon: {
    width: '44px',
    height: '44px',
    borderRadius: '10px',
    backgroundColor: 'var(--color-surface)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  uploadDetails: {
    flex: 1,
    minWidth: 0,
  },
  uploadInfo: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  fileName: {
    fontWeight: 600,
    fontSize: '0.9rem',
    color: 'var(--color-text)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  fileSize: {
    color: 'var(--color-text-muted)',
    fontSize: '0.8rem',
    flexShrink: 0,
    marginLeft: '8px',
  },
  progressContainer: {
    height: '6px',
    backgroundColor: 'var(--color-border-light)',
    borderRadius: 'var(--radius-full)',
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
    borderRadius: 'var(--radius-full)',
    transition: 'width 0.4s ease',
  },
  statusSuccess: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    color: 'var(--color-success)',
    fontSize: '0.8rem',
    fontWeight: 600,
  },
  statusError: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    color: 'var(--color-danger)',
    fontSize: '0.8rem',
    fontWeight: 600,
  },
};
