import { useEffect, useState } from "react";

import CropRecordForm from "../components/CropRecordForm";
import CropTable from "../components/CropTable";
import CsvUploadForm from "../components/CsvUploadForm";
import HarvestSelector from "../components/HarvestSelector";
import {
  createHarvestRecord,
  deleteHarvestRecord,
  fetchHarvestRecords,
  updateHarvestRecord,
  uploadHarvestRecordsCsv
} from "../services/api";

export default function FieldEntryPage() {
  const [harvestEventId, setHarvestEventId] = useState("");
  const [selectedField, setSelectedField] = useState(null);
  const [rows, setRows] = useState([]);
  const [editingRecord, setEditingRecord] = useState(null);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [loadingRows, setLoadingRows] = useState(false);
  const [retryRows, setRetryRows] = useState(0);

  const parsedEventId = Number(harvestEventId);

  const refreshRows = async () => {
    if (!Number.isInteger(parsedEventId) || parsedEventId < 1) {
      setRows([]);
      return;
    }

    const result = await fetchHarvestRecords({
      harvest_event_id: parsedEventId,
      page_size: 1000
    });
    setRows(result.records || []);
  };

  useEffect(() => {
    let active = true;
    if (!harvestEventId) {
      setRows([]);
      setLoadingRows(false);
      return;
    }

    setLoadingRows(true);
    const load = async () => {
      try {
        setError(null);
        const result = await fetchHarvestRecords({ harvest_event_id: parsedEventId, page_size: 1000 });
        if (active) setRows(result.records || []);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoadingRows(false);
      }
    };

    load();
    return () => { active = false; };
  }, [parsedEventId, retryRows]);

  const requireEventId = () => {
    if (!Number.isInteger(parsedEventId) || parsedEventId < 1) {
      throw new Error("Select a field and harvest event before saving records.");
    }
    return parsedEventId;
  };

  const submitRecord = async (payload) => {
    setError(null);
    setStatus(null);
    const eventId = requireEventId();
    setIsSaving(true);

    try {
      if (editingRecord) {
        await updateHarvestRecord(editingRecord.id, payload);
        setEditingRecord(null);
      } else {
        await createHarvestRecord(eventId, payload);
      }

      try {
        await refreshRows();
      } catch {
        setError("The record was saved, but the list could not refresh. Reload to see the latest records.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (record) => {
    if (!window.confirm(`Delete harvest record #${record.id}?`)) {
      return;
    }

    try {
      setIsSaving(true);
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
    } finally {
      setIsSaving(false);
    }
  };

  const uploadCsv = async (file) => {
    const eventId = requireEventId();
    setIsSaving(true);
    setError(null);
    setStatus(null);
    try {
      const records = await uploadHarvestRecordsCsv(eventId, file);
      try {
        await refreshRows();
      } catch {
        setError("The CSV was imported, but the list could not refresh. Reload to see the latest records.");
      }
      return records;
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <fieldset className="field-entry" disabled={isSaving}>
      <div className="panel">
        <h1>{selectedField ? `${selectedField.name} Field` : "Field Entry"}</h1>
        <p>Manual harvest record entry</p>
        <HarvestSelector onBusyChange={setIsCreating} onChange={(field, harvest) => {
          setSelectedField(field);
          setHarvestEventId(harvest ? String(harvest.id) : "");
          setRows([]);
          setEditingRecord(null);
          setStatus(null);
          setError(null);
          setLoadingRows(Boolean(harvest));
        }} />
        {error ? <p className="form-error" role="alert">{error} <button type="button" disabled={!harvestEventId} onClick={() => setRetryRows((value) => value + 1)}>Reload records</button></p> : null}
        {status ? <p className="upload-status">{status}</p> : null}
      </div>
      {!harvestEventId && <p>Select a field and harvest event to enter or upload records.</p>}
      {loadingRows && <p role="status">Loading records…</p>}
      <fieldset className="field-entry" disabled={!harvestEventId || loadingRows || isCreating}>
        <CropRecordForm
          key={`record-${harvestEventId}`}
          record={editingRecord}
          onSubmit={submitRecord}
          onCancelEdit={() => setEditingRecord(null)}
        />
        <CsvUploadForm key={`csv-${harvestEventId}`} onUpload={uploadCsv} />
        <CropTable
          rows={rows}
          onEdit={setEditingRecord}
          onDelete={handleDelete}
        />
      </fieldset>
    </fieldset>
  );
}
