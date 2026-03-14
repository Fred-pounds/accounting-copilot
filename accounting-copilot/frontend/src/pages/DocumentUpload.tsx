import React, { useState, useCallback } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { apiClient } from '../services/api';

type UploadStatus = 'uploading' | 'processing' | 'complete' | 'error';

interface UploadProgress {
  file: File;
  progress: number;
  status: UploadStatus;
  error?: string;
  documentId?: string;
}

export const DocumentUpload: React.FC = () => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);

  const updateUpload = useCallback((index: number, patch: Partial<UploadProgress>) => {
    setUploads((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], ...patch };
      return updated;
    });
  }, []);

  const processFile = useCallback(
    async (file: File, uploadIndex: number) => {
      try {
        updateUpload(uploadIndex, { progress: 20 });
        const { document_id, upload_url } = await apiClient.uploadDocument(file);
        updateUpload(uploadIndex, { progress: 50, documentId: document_id });
        await apiClient.uploadToS3(upload_url, file);
        // S3 upload done — backend pipeline runs async, mark as complete
        updateUpload(uploadIndex, { progress: 100, status: 'complete' });
      } catch (error: any) {
        updateUpload(uploadIndex, { status: 'error', error: error.message || 'Upload failed' });
      }
    },
    [updateUpload]
  );

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      const rejectedUploads: UploadProgress[] = fileRejections.map(({ file, errors }) => {
        let errorMessage = 'Upload failed';
        if (errors[0]?.code === 'file-too-large') errorMessage = 'File size exceeds 10 MB limit';
        else if (errors[0]?.code === 'file-invalid-type')
          errorMessage = 'Unsupported file type. Please upload JPEG, PNG, or PDF files.';
        return { file, progress: 0, status: 'error' as const, error: errorMessage };
      });

      const newUploads: UploadProgress[] = acceptedFiles.map((file) => ({
        file,
        progress: 0,
        status: 'uploading' as const,
      }));

      setUploads((prev) => {
        const startIndex = prev.length + rejectedUploads.length;
        acceptedFiles.forEach((file, i) => {
          setTimeout(() => processFile(file, startIndex + i), 0);
        });
        return [...prev, ...rejectedUploads, ...newUploads];
      });
    },
    [processFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'], 'application/pdf': ['.pdf'] },
    maxSize: 10 * 1024 * 1024,
  });

  const getFileIcon = (type: string) => {
    if (type === 'application/pdf') {
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#e11d48" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      );
    }
    return (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
    );
  };

  const statusConfig: Record<UploadStatus, { label: string; color: string }> = {
    uploading: { label: 'Uploading...', color: 'var(--color-primary)' },
    processing: { label: 'Processing...', color: '#d97706' },
    complete: { label: 'Uploaded — AI extraction running in background. Check Approvals shortly.', color: 'var(--color-success)' },
    error: { label: '', color: 'var(--color-danger)' },
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Upload Documents</h1>
        <p style={styles.subtitle}>Upload receipts, invoices, or bank statements for AI-powered processing</p>
      </div>

      <div {...getRootProps()} style={{ ...styles.dropzone, ...(isDragActive ? styles.dropzoneActive : {}) }}>
        <input {...getInputProps()} />
        <div style={styles.dropzoneContent}>
          <div style={{ ...styles.uploadIconWrap, ...(isDragActive ? styles.uploadIconActive : {}) }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          {isDragActive ? (
            <p style={styles.dropzoneTextActive}>Drop your files here!</p>
          ) : (
            <>
              <p style={styles.dropzoneText}><strong>Click to upload</strong> or drag and drop</p>
              <p style={styles.dropzoneHint}>JPEG, PNG, or PDF — up to 10 MB</p>
            </>
          )}
        </div>
      </div>

      <div style={styles.formatRow}>
        {[{ color: '#6366f1', label: 'Receipts' }, { color: '#059669', label: 'Invoices' }, { color: '#f59e0b', label: 'Bank Statements' }].map(({ color, label }) => (
          <div key={label} style={styles.formatItem}>
            <span style={{ ...styles.formatDot, backgroundColor: color }} />
            <span style={styles.formatLabel}>{label}</span>
          </div>
        ))}
      </div>

      {uploads.length > 0 && (
        <div style={styles.uploadsList}>
          <h2 style={styles.uploadsTitle}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
              <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
            </svg>
            Uploads
          </h2>

          {uploads.map((upload, index) => {
            const cfg = statusConfig[upload.status];
            const isSpinning = upload.status === 'uploading' || upload.status === 'processing';
            return (
              <div key={index} style={{
                ...styles.uploadItem,
                borderLeft: upload.status === 'complete' ? '3px solid var(--color-success)' :
                  upload.status === 'error' ? '3px solid var(--color-danger)' :
                  upload.status === 'processing' ? '3px solid #f59e0b' : '3px solid var(--color-primary)',
              }}>
                <div style={styles.uploadFileIcon}>{getFileIcon(upload.file.type)}</div>
                <div style={styles.uploadDetails}>
                  <div style={styles.uploadInfo}>
                    <span style={styles.fileName}>{upload.file.name}</span>
                    <span style={styles.fileSize}>
                      {upload.file.size > 1024 * 1024
                        ? `${(upload.file.size / (1024 * 1024)).toFixed(1)} MB`
                        : `${(upload.file.size / 1024).toFixed(1)} KB`}
                    </span>
                  </div>

                  {(upload.status === 'uploading' || upload.status === 'processing') && (
                    <div style={styles.progressContainer}>
                      <div style={{
                        ...styles.progressBar,
                        width: upload.status === 'processing' ? '100%' : `${upload.progress}%`,
                        background: upload.status === 'processing'
                          ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                          : 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                      }} />
                    </div>
                  )}

                  {upload.status !== 'error' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: cfg.color }}>
                      {isSpinning && (
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 1s linear infinite', flexShrink: 0 }}>
                          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                        </svg>
                      )}
                      {upload.status === 'complete' && (
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                      <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{cfg.label}</span>
                    </div>
                  )}

                  {upload.status === 'error' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-danger)', fontSize: '0.8rem', fontWeight: 600 }}>
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                      {upload.error}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: { padding: 'var(--space-page)', maxWidth: '720px', margin: '0 auto' },
  header: { marginBottom: '24px' },
  title: { fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.5px' },
  subtitle: { fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '4px' },
  dropzone: {
    border: '2px dashed #cbd5e1', borderRadius: 16, padding: '56px 24px',
    textAlign: 'center', cursor: 'pointer', transition: 'all var(--transition-base)',
    backgroundColor: 'var(--color-card)', boxShadow: 'var(--shadow-card)',
  },
  dropzoneActive: { borderColor: 'var(--color-primary)', backgroundColor: 'var(--color-primary-50)', borderStyle: 'solid', transform: 'scale(1.01)' },
  dropzoneContent: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' },
  uploadIconWrap: {
    width: '72px', height: '72px', borderRadius: '20px',
    backgroundColor: 'var(--color-primary-50)', color: 'var(--color-primary)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    marginBottom: '4px', transition: 'all var(--transition-base)',
  },
  uploadIconActive: { backgroundColor: 'var(--color-primary)', color: 'white', transform: 'scale(1.1)' },
  dropzoneText: { fontSize: '1rem', color: 'var(--color-text)', margin: 0 },
  dropzoneTextActive: { fontSize: '1.1rem', color: 'var(--color-primary)', fontWeight: 700, margin: 0 },
  dropzoneHint: { fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 },
  formatRow: { display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '20px', marginBottom: '8px' },
  formatItem: { display: 'flex', alignItems: 'center', gap: '6px' },
  formatDot: { width: '8px', height: '8px', borderRadius: '50%', display: 'inline-block' },
  formatLabel: { fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 500 },
  uploadsList: { marginTop: '32px' },
  uploadsTitle: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: '16px' },
  uploadItem: {
    display: 'flex', gap: '14px', backgroundColor: 'var(--color-card)',
    border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)',
    padding: '16px', marginBottom: '10px', animation: 'slideUp 0.3s ease-out',
  },
  uploadFileIcon: { width: '44px', height: '44px', borderRadius: '10px', backgroundColor: 'var(--color-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  uploadDetails: { flex: 1, minWidth: 0 },
  uploadInfo: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' },
  fileName: { fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const },
  fileSize: { color: 'var(--color-text-muted)', fontSize: '0.8rem', flexShrink: 0, marginLeft: '8px' },
  progressContainer: { height: '6px', backgroundColor: 'var(--color-border-light)', borderRadius: 'var(--radius-full)', overflow: 'hidden', marginBottom: '8px' },
  progressBar: { height: '100%', borderRadius: 'var(--radius-full)', transition: 'width 0.4s ease' },
};
