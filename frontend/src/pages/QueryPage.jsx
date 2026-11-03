import { useEffect, useState } from "react";

import CropRecordForm from "../components/CropRecordForm";
import CropTable from "../components/CropTable";
import HarvestRecordFilter from "../components/HarvestRecordFilter";
import {
  deleteHarvestRecord,
  fetchHarvestRecords,
  updateHarvestRecord
} from "../services/api";

export default function QueryPage() {
  const [rows, setRows] = useState([]);
  const [editingRecord, setEditingRecord] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    field_id: "",
    harvest_date_from: "",
    harvest_date_to: "",
    plot_number: "",
    page: 1,
    page_size: 50,
  });

  const loadRecords = async (currentFilters) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchHarvestRecords(currentFilters);
      setRows(result.records || []);
      setTotal(result.total || 0);
      setPage(result.page || 1);
      setTotalPages(result.total_pages || 0);
    } catch (err) {
      setError(err.message);
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords(filters);
  }, []);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    loadRecords(newFilters);
  };

  const handlePageChange = (newPage) => {
    const updatedFilters = { ...filters, page: newPage };
    setFilters(updatedFilters);
    loadRecords(updatedFilters);
  };

  const submitRecord = async (payload) => {
    if (!editingRecord) {
      return;
    }

    try {
      setError(null);
      await updateHarvestRecord(editingRecord.id, payload);
      setEditingRecord(null);
      await loadRecords(filters);
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
      await loadRecords(filters);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <HarvestRecordFilter onFilterChange={handleFilterChange} />
      {error ? <p className="form-error panel">{error}</p> : null}
      {editingRecord ? (
        <CropRecordForm
          record={editingRecord}
          onSubmit={submitRecord}
          onCancelEdit={() => setEditingRecord(null)}
        />
      ) : null}
      {loading ? <div className="panel loading-message">Loading records...</div> : null}
      {!loading ? (
        <CropTable
          rows={rows}
          total={total}
          page={page}
          pageSize={filters.page_size}
          totalPages={totalPages}
          onPageChange={handlePageChange}
          onEdit={setEditingRecord}
          onDelete={handleDelete}
        />
      ) : null}
    </>
  );
}
