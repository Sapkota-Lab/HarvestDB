import { useState } from "react";

const INITIAL_FORM = {
  plot_number: "",
  dynamic_data: "{}"
};

export default function CropRecordForm({ onSubmit }) {
  const [form, setForm] = useState(INITIAL_FORM);

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
      <h2>New Harvest Record</h2>
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
      <button className="primary" type="submit">Save Record</button>
    </form>
  );
}
