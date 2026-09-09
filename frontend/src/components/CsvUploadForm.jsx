import { useState } from "react";

export default function CsvUploadForm({ onUpload }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) return;

    setStatus("Uploading...");
    try {
      const records = await onUpload(file);
      setStatus(`Imported ${records.length} record${records.length === 1 ? "" : "s"}.`);
      setFile(null);
      event.target.reset();
    } catch (error) {
      setStatus(error.message);
    }
  };

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>Bulk Upload (CSV)</h2>
      <p className="hint">Use the same columns as the manual entry form above. Genotype is required.</p>
      <input
        type="file"
        accept=".csv,text/csv"
        onChange={(event) => setFile(event.target.files[0] ?? null)}
      />
      <button className="primary" type="submit" disabled={!file}>
        Upload CSV
      </button>
      {status ? <p className="upload-status">{status}</p> : null}
    </form>
  );
}
