import { useRef, useState } from "react";

export default function CsvUploadForm({ onUpload }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const submitting = useRef(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file || submitting.current) return;
    if (!/\.(csv|xlsx)$/i.test(file.name)) {
      setStatus("Choose a .csv or .xlsx file.");
      return;
    }

    const form = event.currentTarget;
    submitting.current = true;
    setIsUploading(true);
    setStatus("Uploading...");
    try {
      const result = await onUpload(file);
      const count = result.records.length;
      let message = `Imported ${count} record${count === 1 ? "" : "s"}.`;
      if (result.imported_sheets.length) {
        const tabs = result.imported_sheets.map((sheet) =>
          `“${sheet.name}” (${sheet.record_count} record${sheet.record_count === 1 ? "" : "s"})`
        );
        message += ` Tabs imported: ${tabs.join(", ")}.`;
      }
      if (result.skipped_sheets.length) {
        message += ` Tabs not imported: ${result.skipped_sheets.map((name) => `“${name}”`).join(", ")}.`;
      }
      setStatus(message);
      setFile(null);
      form.reset();
    } catch (error) {
      setStatus(error.message);
    } finally {
      submitting.current = false;
      setIsUploading(false);
    }
  };

  return (
    <form className="panel" onSubmit={handleSubmit} aria-busy={isUploading}>
      <h2>Bulk Upload (CSV or Excel)</h2>
      <p className="hint">Use a plot_number column and an optional dynamic_data column containing JSON.</p>
      <p className="hint">For .xlsx files, only the first worksheet is imported. Put column names in the first row and replace formulas with values.</p>
      <input
        type="file"
        aria-label="CSV or Excel file"
        accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        disabled={isUploading}
        onChange={(event) => {
          setFile(event.target.files[0] ?? null);
          setStatus(null);
        }}
      />
      <button className="primary" type="submit" disabled={!file || isUploading}>
        {isUploading ? "Uploading…" : "Upload file"}
      </button>
      {status ? <p className="upload-status" role="status">{status}</p> : null}
    </form>
  );
}
