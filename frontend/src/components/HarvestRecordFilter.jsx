import { useState } from "react";

export default function HarvestRecordFilter({ onFilterChange }) {
  const [filters, setFilters] = useState({
    field_id: "",
    harvest_date_from: "",
    harvest_date_to: "",
    plot_number: "",
    page: 1,
    page_size: 50,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    const newFilters = {
      ...filters,
      [name]: value,
      page: 1, // Reset to first page when filters change
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleClear = () => {
    const clearedFilters = {
      field_id: "",
      harvest_date_from: "",
      harvest_date_to: "",
      plot_number: "",
      page: 1,
      page_size: 50,
    };
    setFilters(clearedFilters);
    onFilterChange(clearedFilters);
  };

  return (
    <div className="panel filter-form">
      <h3>Filter Harvest Records</h3>
      <form>
        <div className="form-group">
          <label htmlFor="field_id">Field ID:</label>
          <input
            id="field_id"
            name="field_id"
            type="number"
            value={filters.field_id}
            onChange={handleChange}
            placeholder="All fields"
          />
        </div>

        <div className="form-group">
          <label htmlFor="plot_number">Plot Number:</label>
          <input
            id="plot_number"
            name="plot_number"
            type="text"
            value={filters.plot_number}
            onChange={handleChange}
            placeholder="Search plot..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="harvest_date_from">Harvest Date From:</label>
          <input
            id="harvest_date_from"
            name="harvest_date_from"
            type="date"
            value={filters.harvest_date_from}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="harvest_date_to">Harvest Date To:</label>
          <input
            id="harvest_date_to"
            name="harvest_date_to"
            type="date"
            value={filters.harvest_date_to}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="page_size">Records Per Page:</label>
          <select
            id="page_size"
            name="page_size"
            value={filters.page_size}
            onChange={handleChange}
          >
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>

        <button type="button" onClick={handleClear} className="btn-secondary">
          Clear Filters
        </button>
      </form>
    </div>
  );
}
