export default function CropTable({ rows, onEdit, onDelete }) {
  const showActions = Boolean(onEdit || onDelete);

  return (
    <div className="panel table-wrap">
      <h2>Harvest Records</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Harvest Event</th>
            <th>Plot Number</th>
            <th>Dynamic Fields</th>
            {showActions ? <th>Actions</th> : null}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={showActions ? 5 : 4}>No records yet.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.harvest_event_id}</td>
                <td>{row.plot_number}</td>
                <td>{JSON.stringify(row.dynamic_data)}</td>
                {showActions ? (
                  <td>
                    <div className="row-actions">
                      {onEdit ? (
                        <button type="button" onClick={() => onEdit(row)}>
                          Edit
                        </button>
                      ) : null}
                      {onDelete ? (
                        <button type="button" onClick={() => onDelete(row)}>
                          Delete
                        </button>
                      ) : null}
                    </div>
                  </td>
                ) : null}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
