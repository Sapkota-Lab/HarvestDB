import { useRef, useState } from "react";

export default function CsvUploadForm({ onPreview, onUpload }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [worksheets, setWorksheets] = useState(null);
  const [sheetEventIds, setSheetEventIds] = useState({});
  const submitting = useRef(false);
  const isXlsx = file?.name.toLowerCase().endsWith(".xlsx") ?? false;
  const buttonText = isUploading
    ? "Uploading…"
    : isXlsx
      ? worksheets === null ? "Review worksheets" : "Import worksheets"
      : "Upload file";

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
    setStatus(
      worksheets === null && file.name.toLowerCase().endsWith(".xlsx")
        ? "Reading worksheets..."
        : "Uploading..."
    );
    try {
      if (worksheets === null && file.name.toLowerCase().endsWith(".xlsx")) {
        const names = await onPreview(file);
        setWorksheets(names);
        setSheetEventIds(Object.fromEntries(names.map((name) => [name, ""])));
        setStatus("Select an event ID for each worksheet, or choose Skip.");
        return;
      }

      let mappings = null;
      if (worksheets !== null) {
        mappings = {};
        for (const name of worksheets) {
          const value = sheetEventIds[name];
          if (value === "skip") {
            mappings[name] = null;
          } else if (/^[1-9]\d*$/.test(value || "")) {
            mappings[name] = Number(value);
          } else {
            setStatus(`Enter a valid harvest event ID or choose Skip for “${name}”.`);
            return;
          }
        }
      }

      const result = await onUpload(file, mappings);
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
      setWorksheets(null);
      setSheetEventIds({});
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
      <p className="hint">For .xlsx files, choose a harvest event for each worksheet. Put column names in the first row and replace formulas with values.</p>
      <input
        type="file"
        aria-label="CSV or Excel file"
        accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        disabled={isUploading}
        onChange={(event) => {
          setFile(event.target.files[0] ?? null);
          setStatus(null);
          setWorksheets(null);
          setSheetEventIds({});
        }}
      />
      {worksheets?.map((name) => (
        <div className="worksheet-mapping" key={name}>
          <label>
            {name} - Harvest Event ID
            <input
              type="number"
              min="1"
              aria-label={`Harvest event ID for ${name}`}
              value={sheetEventIds[name] === "skip" ? "" : sheetEventIds[name]}
              disabled={isUploading || sheetEventIds[name] === "skip"}
              onChange={(event) => {
                setSheetEventIds((current) => ({ ...current, [name]: event.target.value }));
              }}
            />
          </label>
          <label>
            <input
              type="checkbox"
              aria-label={`Skip ${name}`}
              checked={sheetEventIds[name] === "skip"}
              disabled={isUploading}
              onChange={(event) => {
                setSheetEventIds((current) => ({
                  ...current,
                  [name]: event.target.checked ? "skip" : ""
                }));
              }}
            />
            Skip this worksheet
          </label>
        </div>
      ))}
      <button className="primary" type="submit" disabled={!file || isUploading}>
        {buttonText}
      </button>
      {status ? <p className="upload-status" role="status">{status}</p> : null}
    </form>
  );
}
