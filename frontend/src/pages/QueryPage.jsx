import { useEffect, useState } from "react";

import CropTable from "../components/CropTable";
import HarvestRecordFilter from "../components/HarvestRecordFilter";
import { fetchHarvestRecords } from "../services/api";

export default function QueryPage() {
  const [rows, setRows] = useState([]);
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

  return (
    <>
      <HarvestRecordFilter onFilterChange={handleFilterChange} />
      {error && (
        <div className="panel error-message">
          <strong>Error:</strong> {error}
        </div>
      )}
      {loading && (
        <div className="panel loading-message">
          Loading records...
        </div>
      )}
      {!loading && (
        <CropTable
          rows={rows}
          total={total}
          page={page}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </>
  );
}
