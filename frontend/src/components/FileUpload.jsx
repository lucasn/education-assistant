import { useState, useRef } from 'react';
import { UploadIcon, XIcon, AlertIcon } from './icons';

export function FileUpload({ apiUrl }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const pdfFiles = selectedFiles.filter(file => file.type === 'application/pdf');

    if (pdfFiles.length !== selectedFiles.length) {
      setUploadStatus({
        type: 'error',
        message: 'Only PDF files are allowed. Some files were filtered out.'
      });
    }

    setFiles(prev => [...prev, ...pdfFiles]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setUploadStatus({
        type: 'error',
        message: 'Please select at least one PDF file to upload.'
      });
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(`${apiUrl}/ingest`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${response.status} ${errorText}`);
      }

      setUploadStatus({
        type: 'success',
        message: `Successfully uploaded ${files.length} file${files.length > 1 ? 's' : ''}`
      });
      setFiles([]);
    } catch (error) {
      console.error('Error uploading files:', error);
      setUploadStatus({
        type: 'error',
        message: error.message || 'Failed to upload files. Please try again.'
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="h-full flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="bg-gray-800 rounded-2xl p-8 shadow-lg">
          <div className="text-center mb-6">
            <div className="mx-auto mb-4 w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
              <UploadIcon />
            </div>
            <h2 className="text-2xl font-semibold mb-2">Upload Documents</h2>
            <p className="text-gray-400">Upload PDF files to add to the knowledge base</p>
          </div>

          {uploadStatus && (
            <div className={`mb-6 rounded-lg p-4 ${
              uploadStatus.type === 'success'
                ? 'bg-green-900 bg-opacity-20 border border-green-800'
                : 'bg-red-900 bg-opacity-20 border border-red-800'
            }`}>
              <div className="flex items-start gap-2">
                {uploadStatus.type === 'error' && <AlertIcon />}
                <div className="flex-1">
                  <p className={`text-sm ${
                    uploadStatus.type === 'success' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {uploadStatus.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div
            className="border-2 border-dashed border-gray-600 rounded-lg p-12 text-center cursor-pointer hover:border-blue-500 transition-colors"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const droppedFiles = Array.from(e.dataTransfer.files);
              const pdfFiles = droppedFiles.filter(file => file.type === 'application/pdf');
              setFiles(prev => [...prev, ...pdfFiles]);
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,application/pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="text-gray-400 flex flex-col items-center">
              <UploadIcon />
              <p className="mt-2">Click to browse or drag and drop PDF files here</p>
              <p className="text-sm text-gray-500 mt-1">Only PDF files are supported</p>
            </div>
          </div>

          {files.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">
                Selected Files ({files.length})
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-gray-700 rounded-lg p-3"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="ml-3 p-1 hover:bg-gray-600 rounded transition-colors"
                      disabled={uploading}
                    >
                      <XIcon />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 flex gap-3">
            <button
              onClick={handleUpload}
              disabled={uploading || files.length === 0}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
            >
              {uploading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <UploadIcon />
                  <span>Upload {files.length > 0 && `(${files.length})`}</span>
                </>
              )}
            </button>
            {files.length > 0 && (
              <button
                onClick={() => setFiles([])}
                disabled={uploading}
                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
              >
                Clear All
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
