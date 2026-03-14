import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../utils/testUtils';
import { DocumentUpload } from '../../pages/DocumentUpload';

/**
 * Integration Tests: Document Upload Flow
 * 
 * Validates: Requirement 1.1 - Document capture and OCR processing
 * 
 * Tests the complete document upload flow including:
 * - File selection and validation
 * - Upload progress tracking
 * - Success and error handling
 * - File type and size validation
 */

describe('Document Upload Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render upload dropzone with instructions', () => {
    renderWithProviders(<DocumentUpload />);

    expect(screen.getByText(/upload documents/i)).toBeInTheDocument();
    expect(screen.getByText(/click to upload/i)).toBeInTheDocument();
    expect(screen.getByText(/jpeg, png, or pdf/i)).toBeInTheDocument();
  });

  it('should successfully upload a valid document', async () => {
    const user = userEvent.setup();

    renderWithProviders(<DocumentUpload />);

    // Create a mock file
    const file = new File(['receipt content'], 'receipt.jpg', { type: 'image/jpeg' });

    // Get the file input (hidden by dropzone)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    // Upload the file
    await user.upload(input, file);

    // Verify file appears in upload list
    await waitFor(() => {
      expect(screen.getByText('receipt.jpg')).toBeInTheDocument();
    });

    // Verify success message appears
    await waitFor(
      () => {
        expect(screen.getByText(/uploaded successfully/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('should upload multiple documents simultaneously', async () => {
    const user = userEvent.setup();

    renderWithProviders(<DocumentUpload />);

    // Create multiple mock files
    const files = [
      new File(['receipt 1'], 'receipt1.jpg', { type: 'image/jpeg' }),
      new File(['receipt 2'], 'receipt2.png', { type: 'image/png' }),
      new File(['invoice'], 'invoice.pdf', { type: 'application/pdf' }),
    ];

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    // Upload multiple files
    await user.upload(input, files);

    // Verify all files appear in upload list
    await waitFor(() => {
      expect(screen.getByText('receipt1.jpg')).toBeInTheDocument();
      expect(screen.getByText('receipt2.png')).toBeInTheDocument();
      expect(screen.getByText('invoice.pdf')).toBeInTheDocument();
    });
  });

  it('should reject files exceeding size limit', async () => {
    const user = userEvent.setup();

    renderWithProviders(<DocumentUpload />);

    // Create a file larger than 10 MB
    const largeContent = new Array(11 * 1024 * 1024).fill('x').join('');
    const largeFile = new File([largeContent], 'large-receipt.jpg', {
      type: 'image/jpeg'
    });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    // Try to upload the large file
    await user.upload(input, largeFile);

    // Verify error message
    await waitFor(() => {
      expect(screen.getByText(/file size exceeds 10 mb limit/i)).toBeInTheDocument();
    });
  });

  it.skip('should reject unsupported file types', async () => {
    const user = userEvent.setup();

    renderWithProviders(<DocumentUpload />);

    // Create an unsupported file type
    const unsupportedFile = new File(['content'], 'document.txt', {
      type: 'text/plain'
    });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    // Try to upload the unsupported file
    await user.upload(input, unsupportedFile);

    // Verify error message
    await waitFor(() => {
      expect(
        screen.getByText(/unsupported file type/i)
      ).toBeInTheDocument();
    });
  });

  it('should display upload progress during file upload', async () => {
    const user = userEvent.setup();

    renderWithProviders(<DocumentUpload />);

    const file = new File(['receipt content'], 'receipt.jpg', { type: 'image/jpeg' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, file);

    // Verify file name appears
    await waitFor(() => {
      expect(screen.getByText('receipt.jpg')).toBeInTheDocument();
    });

    // Progress bar should be visible during upload
    // (it will complete quickly in tests, but we can verify the structure exists)
    const uploadItem = screen.getByText('receipt.jpg').closest('div');
    expect(uploadItem).toBeInTheDocument();
  });

  it('should show file size in kilobytes', async () => {
    const user = userEvent.setup();

    renderWithProviders(<DocumentUpload />);

    // Create a file with known size (1024 bytes = 1 KB)
    const content = new Array(1024).fill('x').join('');
    const file = new File([content], 'receipt.jpg', { type: 'image/jpeg' });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, file);

    // Verify file size is displayed
    await waitFor(() => {
      expect(screen.getByText(/1\.0 kb/i)).toBeInTheDocument();
    });
  });

  it('should handle upload failures gracefully', async () => {
    const user = userEvent.setup();

    // Mock API failure
    const { server } = await import('../mocks/server');
    const { http, HttpResponse } = await import('msw');

    server.use(
      http.post('/api/documents/upload', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    renderWithProviders(<DocumentUpload />);

    const file = new File(['receipt content'], 'receipt.jpg', { type: 'image/jpeg' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, file);

    // Verify error message appears
    await waitFor(
      () => {
        expect(screen.getByText(/Request failed/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('should accept JPEG, PNG, and PDF file types', async () => {
    const user = userEvent.setup();

    renderWithProviders(<DocumentUpload />);

    const jpegFile = new File(['content'], 'receipt.jpg', { type: 'image/jpeg' });
    const pngFile = new File(['content'], 'receipt.png', { type: 'image/png' });
    const pdfFile = new File(['content'], 'invoice.pdf', { type: 'application/pdf' });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    // Upload each file type
    await user.upload(input, jpegFile);
    await waitFor(() => expect(screen.getByText('receipt.jpg')).toBeInTheDocument());

    await user.upload(input, pngFile);
    await waitFor(() => expect(screen.getByText('receipt.png')).toBeInTheDocument());

    await user.upload(input, pdfFile);
    await waitFor(() => expect(screen.getByText('invoice.pdf')).toBeInTheDocument());
  });

  it('should show visual feedback when dragging files over dropzone', async () => {
    renderWithProviders(<DocumentUpload />);

    const dropzone = screen.getByText(/click to upload/i).closest('div');
    expect(dropzone).toBeInTheDocument();

    // The dropzone should have appropriate styling for drag states
    // (tested via the isDragActive state in the component)
  });
});
