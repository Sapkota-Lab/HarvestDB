export default function CropTable({ rows }) {
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
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan="4">No records yet.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.harvest_event_id}</td>
                <td>{row.plot_number}</td>
                <td>{JSON.stringify(row.dynamic_data)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
