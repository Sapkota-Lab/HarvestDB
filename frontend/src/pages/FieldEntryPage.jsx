import { useEffect, useState } from "react";

import CropRecordForm from "../components/CropRecordForm";
import CropTable from "../components/CropTable";
import CsvUploadForm from "../components/CsvUploadForm";
import {
  createHarvestRecord,
  deleteHarvestRecord,
  fetchHarvestRecords,
  updateHarvestRecord,
  uploadHarvestRecordsCsv
} from "../services/api";

export default function FieldEntryPage() {
  const [harvestEventId, setHarvestEventId] = useState("");
  const [rows, setRows] = useState([]);
  const [editingRecord, setEditingRecord] = useState(null);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);

  const parsedEventId = Number(harvestEventId);

  const refreshRows = async () => {
    if (!Number.isInteger(parsedEventId) || parsedEventId < 1) {
      setRows([]);
      return;
    }

    const records = await fetchHarvestRecords(parsedEventId);
    setRows(records);
  };

  useEffect(() => {
    if (!Number.isInteger(parsedEventId) || parsedEventId < 1) {
      setRows([]);
      return;
    }

    const load = async () => {
      try {
        setError(null);
        await refreshRows();
      } catch (err) {
        setError(err.message);
      }
    };

    load();
  }, [parsedEventId]);

  const requireEventId = () => {
    if (!Number.isInteger(parsedEventId) || parsedEventId < 1) {
      throw new Error("Enter a valid harvest event ID before saving records.");
    }
    return parsedEventId;
  };

  const submitRecord = async (payload) => {
    try {
      setError(null);
      setStatus(null);
      const eventId = requireEventId();

      if (editingRecord) {
        await updateHarvestRecord(editingRecord.id, payload);
        setEditingRecord(null);
        setStatus("Record updated.");
      } else {
        await createHarvestRecord(eventId, payload);
        setStatus("Record saved.");
      }

      await refreshRows();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (record) => {
    if (!window.confirm(`Delete harvest record #${record.id}?`)) {
      return;
    }

    try {
      setError(null);
      setStatus(null);
      await deleteHarvestRecord(record.id);
      if (editingRecord?.id === record.id) {
        setEditingRecord(null);
      }
      setStatus("Record deleted.");
      await refreshRows();
    } catch (err) {
      setError(err.message);
    }
  };

  const uploadCsv = async (file) => {
    const eventId = requireEventId();
    const records = await uploadHarvestRecordsCsv(eventId, file);
    await refreshRows();
    return records;
  };

  return (
    <>
      <div className="panel">
        <h1>Lexington Field</h1>
        <p>Manual harvest record entry</p>
        <label>
          Temporary: Harvest Event ID
          <input
            type="number"
            min="1"
            value={harvestEventId}
            onChange={(event) => {
              setHarvestEventId(event.target.value);
              setEditingRecord(null);
              setStatus(null);
              setError(null);
            }}
            placeholder="e.g. 1"
          />
        </label>
        <p className="hint">
          Field and harvest-event selectors are not wired yet. After running TEST_DB_SETUP.sh,
          use a seeded harvest event ID from testing_db (usually 1, 2, or 3). A new event is
          not created automatically.
        </p>
        {error ? <p className="form-error">{error}</p> : null}
        {status ? <p className="upload-status">{status}</p> : null}
      </div>
      <CropRecordForm
        record={editingRecord}
        onSubmit={submitRecord}
        onCancelEdit={() => setEditingRecord(null)}
      />
      <CsvUploadForm onUpload={uploadCsv} />
      <CropTable
        rows={rows}
        onEdit={setEditingRecord}
        onDelete={handleDelete}
      />
    </>
  );
}
