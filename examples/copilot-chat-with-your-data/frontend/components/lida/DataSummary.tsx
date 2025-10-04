"use client";

import { useMemo } from "react";
import { FileText, Database, TrendingUp, Shield, AlertTriangle } from "lucide-react";

interface DataSummaryProps {
  summary: {
    name: string;
    file_name: string;
    dataset_description: string;
    field_names: string[];
    file_size: number;
    file_type: string;
    num_rows: number;
    num_columns: number;
    sample_data: Record<string, any>[];
    statistical_summary: Record<string, any>;
    data_quality_score: number;
    focus_compliance?: {
      compliance_level: string;
      compliance_score: number;
      missing_fields: string[];
    };
  };
  detailed?: boolean;
}

export function DataSummary({ summary, detailed = false }: DataSummaryProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const qualityColor = useMemo(() => {
    const score = summary.data_quality_score;
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  }, [summary.data_quality_score]);

  const complianceColor = useMemo(() => {
    if (!summary.focus_compliance) return "text-gray-500";
    const score = summary.focus_compliance.compliance_score;
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.5) return "text-yellow-600";
    return "text-red-600";
  }, [summary.focus_compliance]);

  if (!detailed) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Rows</span>
          </div>
          <p className="text-lg font-semibold">{summary.num_rows.toLocaleString()}</p>
        </div>

        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Columns</span>
          </div>
          <p className="text-lg font-semibold">{summary.num_columns}</p>
        </div>

        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Quality</span>
          </div>
          <p className={`text-lg font-semibold ${qualityColor}`}>
            {(summary.data_quality_score * 100).toFixed(0)}%
          </p>
        </div>

        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">FOCUS</span>
          </div>
          <p className={`text-lg font-semibold ${complianceColor}`}>
            {summary.focus_compliance
              ? `${(summary.focus_compliance.compliance_score * 100).toFixed(0)}%`
              : "N/A"
            }
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center space-x-2">
          <FileText className="h-5 w-5" />
          <span>Dataset Information</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div>
              <span className="text-sm font-medium text-muted-foreground">Name:</span>
              <p className="text-sm">{summary.name}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-muted-foreground">File:</span>
              <p className="text-sm">{summary.file_name}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-muted-foreground">Type:</span>
              <p className="text-sm uppercase">{summary.file_type}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-muted-foreground">Size:</span>
              <p className="text-sm">{formatFileSize(summary.file_size)}</p>
            </div>
          </div>
          <div className="space-y-2">
            <div>
              <span className="text-sm font-medium text-muted-foreground">Rows:</span>
              <p className="text-sm">{summary.num_rows.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-muted-foreground">columns:</span>
              <p className="text-sm">{summary.num_columns}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-muted-foreground">Quality Score:</span>
              <p className={`text-sm font-medium ${qualityColor}`}>
                {(summary.data_quality_score * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Description */}
      {summary.dataset_description && (
        <div>
          <h3 className="text-lg font-semibold mb-2">Description</h3>
          <p className="text-sm text-muted-foreground">{summary.dataset_description}</p>
        </div>
      )}

      {/* Fields */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Fields ({summary.field_names.length})</h3>
        <div className="flex flex-wrap gap-2">
          {summary.field_names.map((field, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded-md"
            >
              {field}
            </span>
          ))}
        </div>
      </div>

      {/* FOCUS Compliance */}
      {summary.focus_compliance && (
        <div>
          <h3 className="text-lg font-semibold mb-3 flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>FOCUS v1.2 Compliance</span>
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Compliance Level:</span>
              <span className={`text-sm font-medium capitalize ${complianceColor}`}>
                {summary.focus_compliance.compliance_level.replace("_", " ")}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Compliance Score:</span>
              <span className={`text-sm font-medium ${complianceColor}`}>
                {(summary.focus_compliance.compliance_score * 100).toFixed(1)}%
              </span>
            </div>
            {summary.focus_compliance.missing_fields.length > 0 && (
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-600">
                    Missing Required Fields ({summary.focus_compliance.missing_fields.length})
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {summary.focus_compliance.missing_fields.map((field, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200 text-xs rounded-md"
                    >
                      {field}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sample Data */}
      {summary.sample_data && summary.sample_data.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Sample Data</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse border border-border">
              <thead>
                <tr className="bg-muted">
                  {Object.keys(summary.sample_data[0]).map((key, index) => (
                    <th key={index} className="border border-border px-2 py-1 text-left font-medium">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {summary.sample_data.slice(0, 5).map((row, rowIndex) => (
                  <tr key={rowIndex} className="even:bg-muted/50">
                    {Object.values(row).map((value, colIndex) => (
                      <td key={colIndex} className="border border-border px-2 py-1">
                        {String(value).length > 50
                          ? `${String(value).substring(0, 50)}...`
                          : String(value)
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {summary.sample_data.length > 5 && (
            <p className="text-xs text-muted-foreground mt-2">
              Showing first 5 rows of {summary.sample_data.length} sample records
            </p>
          )}
        </div>
      )}
    </div>
  );
}