import { useEffect, useState } from "react";

const INITIAL_FORM = {
  plot_number: "",
  dynamic_data: "{}"
};

export default function CropRecordForm({ record, onSubmit, onCancelEdit }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const isEditing = Boolean(record);

  useEffect(() => {
    if (record) {
      setForm({
        plot_number: record.plot_number ?? "",
        dynamic_data: JSON.stringify(record.dynamic_data ?? {}, null, 2)
      });
    } else {
      setForm(INITIAL_FORM);
    }
  }, [record]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    try {
      onSubmit({
        ...form,
        dynamic_data: JSON.parse(form.dynamic_data)
      });
    } catch {
      window.alert("Dynamic fields must contain valid JSON.");
    }
  };

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>{isEditing ? `Edit Harvest Record #${record.id}` : "New Harvest Record"}</h2>
      <div className="grid">
        <label>
          Plot Number
          <input name="plot_number" value={form.plot_number} onChange={handleChange} required />
        </label>
        <label>
          Dynamic Fields (JSON)
          <textarea name="dynamic_data" rows="8" value={form.dynamic_data} onChange={handleChange} />
        </label>
      </div>
      <div className="form-actions">
        <button className="primary" type="submit">
          {isEditing ? "Update Record" : "Save Record"}
        </button>
        {isEditing ? (
          <button type="button" onClick={onCancelEdit}>
            Cancel Edit
          </button>
        ) : null}
      </div>
    </form>
  );
}
