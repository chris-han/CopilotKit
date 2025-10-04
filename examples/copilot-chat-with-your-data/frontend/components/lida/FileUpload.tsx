"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";

interface FileUploadProps {
  onFileUploaded: (fileName: string, summary: any) => void;
  baseApiUrl: string;
}

export function FileUpload({ onFileUploaded, baseApiUrl }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (files: FileList) => {
    if (files.length === 0) return;

    const file = files[0];
    const allowedTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/json'
    ];

    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(csv|xlsx?|json)$/i)) {
      setError("Please upload a CSV, Excel, or JSON file");
      return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      setError("File size must be less than 50MB");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${baseApiUrl}/lida/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.summary) {
        setSuccess(`Successfully uploaded ${file.name}`);
        onFileUploaded(file.name, result.summary);
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [baseApiUrl, onFileUploaded]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className="space-y-4">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${dragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25"}
          ${uploading ? "pointer-events-none opacity-50" : "hover:border-primary hover:bg-primary/5"}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.json"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploading}
        />

        <div className="space-y-3">
          {uploading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
          )}

          <div>
            <p className="text-sm font-medium text-foreground">
              {uploading ? "Uploading and processing..." : "Drop your file here or click to browse"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Supports CSV, Excel (.xlsx, .xls), and JSON files up to 50MB
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center space-x-2 text-destructive bg-destructive/10 border border-destructive/20 rounded-md p-3">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {success && (
        <div className="flex items-center space-x-2 text-green-600 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-3">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{success}</span>
        </div>
      )}

      <div className="text-xs text-muted-foreground space-y-1">
        <p>• CSV files should have headers in the first row</p>
        <p>• Excel files will use the first worksheet</p>
        <p>• JSON files should contain an array of objects</p>
        <p>• Files are processed for FOCUS v1.2 compliance assessment</p>
      </div>
    </div>
  );
}