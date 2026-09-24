import { useEffect, useState } from "react";

import CropRecordForm from "../components/CropRecordForm";
import CropTable from "../components/CropTable";
import {
  deleteHarvestRecord,
  fetchHarvestRecords,
  updateHarvestRecord
} from "../services/api";

export default function QueryPage() {
  const [rows, setRows] = useState([]);
  const [editingRecord, setEditingRecord] = useState(null);
  const [error, setError] = useState(null);

  const refreshRows = async () => {
    const records = await fetchHarvestRecords();
    setRows(records);
  };

  useEffect(() => {
    const load = async () => {
      try {
        setError(null);
        await refreshRows();
      } catch (err) {
        setError(err.message);
      }
    };

    load();
  }, []);

  const submitRecord = async (payload) => {
    if (!editingRecord) {
      return;
    }

    try {
      setError(null);
      await updateHarvestRecord(editingRecord.id, payload);
      setEditingRecord(null);
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
      await deleteHarvestRecord(record.id);
      if (editingRecord?.id === record.id) {
        setEditingRecord(null);
      }
      await refreshRows();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      {error ? <p className="form-error panel">{error}</p> : null}
      {editingRecord ? (
        <CropRecordForm
          record={editingRecord}
          onSubmit={submitRecord}
          onCancelEdit={() => setEditingRecord(null)}
        />
      ) : null}
      <CropTable rows={rows} onEdit={setEditingRecord} onDelete={handleDelete} />
    </>
  );
}
