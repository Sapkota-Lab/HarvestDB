function formatFieldLabel(fieldName) {
  return fieldName.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatFieldValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

export default function CropTable({ rows, total, page, totalPages, onPageChange }) {
  return (
    <div className="panel table-wrap">
      <h2>Harvest Records</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Field</th>
            <th>Harvest Date</th>
            <th>Harvest Event</th>
            <th>Plot Number</th>
            <th>Dynamic Fields</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan="6">No records yet.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.field_name}</td>
                <td>{row.harvest_date}</td>
                <td>{row.harvest_event_id}</td>
                <td>{row.plot_number}</td>
                <td>
                  <dl className="dynamic-fields">
                    {Object.entries(row.dynamic_data || {}).map(([fieldName, value]) => (
                      <div key={fieldName}>
                        <dt>{formatFieldLabel(fieldName)}</dt>
                        <dd>{formatFieldValue(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      {total > 0 && (
        <div className="pagination">
          <p>
            Showing {rows.length > 0 ? (page - 1) * rows.length + 1 : 0} to{" "}
            {Math.min(page * rows.length, total)} of {total} records
          </p>
          <div className="pagination-controls">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 1}
              type="button"
            >
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page === totalPages}
              type="button"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
