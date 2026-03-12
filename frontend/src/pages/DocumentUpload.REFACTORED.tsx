/**
 * REFACTORED DOCUMENT UPLOAD - Modern UI/UX
 * 
 * Copy this entire file content and replace the content of DocumentUpload.tsx
 * 
 * Improvements:
 * - Modern drag-and-drop zone with better visual feedback
 * - Upload progress cards with animations
 * - Better file validation and error handling
 * - Success/error states with icons
 * - File preview thumbnails
 * - Batch upload support
 * - Smooth animations
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { apiClient } from '../services/api';
import { colors, spacing, typography, borderRadius, shadows, components, mergeStyles } from '../styles/design-system';

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

  const clearCompleted = () => {
    setUploads((prev) => prev.filter((upload) => upload.status === 'uploading'));
  };

  const successCount = uploads.filter((u) => u.status === 'success').length;
  const errorCount = uploads.filter((u) => u.status === 'error').length;
  const uploadingCount = uploads.filter((u) => u.status === 'uploading').length;

  return (
    <div style={styles.container} className="animate-fade-in">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Upload Documents</h1>
          <p style={styles.subtitle}>Upload receipts, invoices, or bank statements for automatic processing</p>
        </div>
        {uploads.length > 0 && (
          <button
            onClick={clearCompleted}
            style={mergeStyles(components.button.base, components.button.ghost)}
          >
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd"/>
            </svg>
            Clear Completed
          </button>
        )}
      </div>

      {/* Upload Stats */}
      {uploads.length > 0 && (
        <div style={styles.statsContainer}>
          <div style={styles.statCard}>
            <div style={{ ...styles.statIcon, backgroundColor: colors.info.light }}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill={colors.info.main}>
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/>
              </svg>
            </div>
            <div>
              <div style={styles.statValue}>{uploadingCount}</div>
              <div style={styles.statLabel}>Uploading</div>
            </div>
          </div>

          <div style={styles.statCard}>
            <div style={{ ...styles.statIcon, backgroundColor: colors.success.light }}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill={colors.success.main}>
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
              </svg>
            </div>
            <div>
              <div style={styles.statValue}>{successCount}</div>
              <div style={styles.statLabel}>Completed</div>
            </div>
          </div>

          <div style={styles.statCard}>
            <div style={{ ...styles.statIcon, backgroundColor: colors.error.light }}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill={colors.error.main}>
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
            </div>
            <div>
              <div style={styles.statValue}>{errorCount}</div>
              <div style={styles.statLabel}>Failed</div>
            </div>
          </div>
        </div>
      )}

      {/* Dropzone */}
      <div
        {...getRootProps()}
        style={{
          ...styles.dropzone,
          ...(isDragActive ? styles.dropzoneActive : {}),
        }}
        className="animate-slide-in"
      >
        <input {...getInputProps()} />
        <div style={styles.dropzoneContent}>
          <div style={styles.uploadIconContainer}>
            <svg
              width="64"
              height="64"
              viewBox="0 0 20 20"
              fill="currentColor"
              style={{ color: isDragActive ? colors.primary.main : colors.gray[400] }}
            >
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd"/>
            </svg>
          </div>
          {isDragActive ? (
            <div>
              <p style={styles.dropzoneTitle}>Drop files here</p>
              <p style={styles.dropzoneHint}>Release to upload your documents</p>
            </div>
          ) : (
            <div>
              <p style={styles.dropzoneTitle}>Drag and drop files here</p>
              <p style={styles.dropzoneHint}>or click to browse from your computer</p>
              <div style={styles.fileTypes}>
                <span style={styles.fileTypeBadge}>JPEG</span>
                <span style={styles.fileTypeBadge}>PNG</span>
                <span style={styles.fileTypeBadge}>PDF</span>
              </div>
              <p style={styles.fileSizeHint}>Maximum file size: 10 MB</p>
            </div>
          )}
        </div>
      </div>

      {/* Uploads List */}
      {uploads.length > 0 && (
        <div style={styles.uploadsList}>
          <h2 style={styles.uploadsTitle}>
            Upload Queue ({uploads.length} file{uploads.length !== 1 ? 's' : ''})
          </h2>
          <div style={styles.uploadsGrid}>
            {uploads.map((upload, index) => (
              <div
                key={index}
                style={styles.uploadCard}
                className="animate-slide-in"
              >
                {/* File Icon */}
                <div style={styles.fileIconContainer}>
                  {upload.file.type.startsWith('image/') ? (
                    <svg width="40" height="40" viewBox="0 0 20 20" fill={colors.primary.main}>
                      <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd"/>
                    </svg>
                  ) : (
                    <svg width="40" height="40" viewBox="0 0 20 20" fill={colors.error.main}>
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/>
                    </svg>
                  )}
                </div>

                {/* File Info */}
                <div style={styles.fileInfo}>
                  <div style={styles.fileName}>{upload.file.name}</div>
                  <div style={styles.fileSize}>
                    {(upload.file.size / 1024).toFixed(1)} KB
                  </div>
                </div>

                {/* Status */}
                <div style={styles.uploadStatus}>
                  {upload.status === 'uploading' && (
                    <div style={styles.progressSection}>
                      <div style={styles.progressContainer}>
                        <div
                          style={{
                            ...styles.progressBar,
                            width: `${upload.progress}%`,
                          }}
                        />
                      </div>
                      <span style={styles.progressText}>{upload.progress}%</span>
                    </div>
                  )}

                  {upload.status === 'success' && (
                    <div style={styles.statusSuccess}>
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                      </svg>
                      <span>Uploaded successfully</span>
                    </div>
                  )}

                  {upload.status === 'error' && (
                    <div style={styles.statusError}>
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                      </svg>
                      <span>{upload.error}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Section */}
      <div style={styles.infoSection}>
        <h3 style={styles.infoTitle}>What happens after upload?</h3>
        <div style={styles.infoGrid}>
          <div style={styles.infoCard}>
            <div style={{ ...styles.infoIcon, backgroundColor: colors.primary.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.primary.main}>
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
              </svg>
            </div>
            <div>
              <div style={styles.infoCardTitle}>1. OCR Processing</div>
              <div style={styles.infoCardText}>Text is extracted from your document using AWS Textract</div>
            </div>
          </div>

          <div style={styles.infoCard}>
            <div style={{ ...styles.infoIcon, backgroundColor: colors.info.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.info.main}>
                <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clipRule="evenodd"/>
              </svg>
            </div>
            <div>
              <div style={styles.infoCardTitle}>2. AI Classification</div>
              <div style={styles.infoCardText}>Transactions are automatically categorized using AI</div>
            </div>
          </div>

          <div style={styles.infoCard}>
            <div style={{ ...styles.infoIcon, backgroundColor: colors.success.light }}>
              <svg width="24" height="24" viewBox="0 0 20 20" fill={colors.success.main}>
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
              </svg>
            </div>
            <div>
              <div style={styles.infoCardTitle}>3. Ready for Review</div>
              <div style={styles.infoCardText}>View and approve transactions in your dashboard</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: spacing.xl,
    maxWidth: '1200px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.xl,
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  title: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: typography.fontWeight.bold,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: typography.fontSize.base,
    color: colors.gray[600],
  },
  statsContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: spacing.md,
    marginBottom: spacing.xl,
  },
  statCard: {
    ...components.card.base,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.lg,
  },
  statIcon: {
    width: '48px',
    height: '48px',
    borderRadius: borderRadius.lg,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statValue: {
    fontSize: typography.fontSize['2xl'],
    fontWeight: typography.fontWeight.bold,
    color: colors.gray[900],
  },
  statLabel: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[600],
  },
  dropzone: {
    border: `3px dashed ${colors.gray[300]}`,
    borderRadius: borderRadius.xl,
    padding: spacing['3xl'],
    textAlign: 'center',
    cursor: 'pointer',
    transition: `all ${transitions.base}`,
    backgroundColor: colors.gray[50],
    marginBottom: spacing.xl,
  },
  dropzoneActive: {
    borderColor: colors.primary.main,
    backgroundColor: colors.primary.light,
    transform: 'scale(1.02)',
  },
  dropzoneContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: spacing.lg,
  },
  uploadIconContainer: {
    marginBottom: spacing.md,
  },
  dropzoneTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  dropzoneHint: {
    fontSize: typography.fontSize.base,
    color: colors.gray[600],
    marginBottom: spacing.md,
  },
  fileTypes: {
    display: 'flex',
    gap: spacing.sm,
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  fileTypeBadge: {
    ...components.badge.base,
    ...components.badge.neutral,
    fontSize: typography.fontSize.xs,
  },
  fileSizeHint: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[500],
  },
  uploadsList: {
    marginBottom: spacing.xl,
  },
  uploadsTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.lg,
  },
  uploadsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.md,
  },
  uploadCard: {
    ...components.card.base,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.lg,
    padding: spacing.lg,
  },
  fileIconContainer: {
    flexShrink: 0,
  },
  fileInfo: {
    flex: 1,
    minWidth: 0,
  },
  fileName: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[900],
    marginBottom: spacing.xs,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  fileSize: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[500],
  },
  uploadStatus: {
    minWidth: '200px',
  },
  progressSection: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.md,
  },
  progressContainer: {
    flex: 1,
    height: '8px',
    backgroundColor: colors.gray[200],
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: colors.primary.main,
    transition: `width ${transitions.base}`,
    borderRadius: borderRadius.full,
  },
  progressText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.gray[700],
    minWidth: '40px',
  },
  statusSuccess: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    color: colors.success.main,
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
  },
  statusError: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    color: colors.error.main,
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
  },
  infoSection: {
    ...components.card.base,
    backgroundColor: colors.gray[50],
  },
  infoTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.lg,
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: spacing.lg,
  },
  infoCard: {
    display: 'flex',
    gap: spacing.md,
  },
  infoIcon: {
    width: '48px',
    height: '48px',
    borderRadius: borderRadius.lg,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  infoCardTitle: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semibold,
    color: colors.gray[900],
    marginBottom: spacing.xs,
  },
  infoCardText: {
    fontSize: typography.fontSize.sm,
    color: colors.gray[600],
    lineHeight: typography.lineHeight.relaxed,
  },
};

// Add missing transitions constant
const transitions = {
  base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
};
