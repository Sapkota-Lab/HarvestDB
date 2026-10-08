import { useEffect, useRef, useState } from "react";

import { validateRecord } from "../services/recordValidation";

const INITIAL_FORM = {
  plot_number: "",
  dynamic_data: "{}"
};

export default function CropRecordForm({ record, onSubmit, onCancelEdit }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submitting = useRef(false);
  const isEditing = Boolean(record);

  useEffect(() => {
    setForm(record ? {
      plot_number: record.plot_number ?? "",
      dynamic_data: JSON.stringify(record.dynamic_data ?? {}, null, 2)
    } : INITIAL_FORM);
    setErrors({});
    setStatus(null);
  }, [record]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setStatus(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submitting.current) return;

    const { errors: nextErrors, payload } = validateRecord(form);
    setErrors(nextErrors);
    setStatus(null);
    if (!payload) {
      event.currentTarget.elements.namedItem(Object.keys(nextErrors)[0])?.focus();
      return;
    }

    submitting.current = true;
    setIsSubmitting(true);
    try {
      await onSubmit(payload);
      setForm(INITIAL_FORM);
      setStatus({ type: "success", message: isEditing ? "Record updated." : "Record saved." });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof TypeError
          ? "Could not reach the server. Check your connection and try again."
          : error?.message || "Record submission failed. Please try again."
      });
    } finally {
      submitting.current = false;
      setIsSubmitting(false);
    }
  };

  return (
    <form className="panel" onSubmit={handleSubmit} noValidate aria-busy={isSubmitting}>
      <h2>{isEditing ? `Edit Harvest Record #${record.id}` : "New Harvest Record"}</h2>
      <div className="grid">
        <label>
          Plot Number
          <input
            name="plot_number"
            value={form.plot_number}
            onChange={handleChange}
            required
            disabled={isSubmitting}
            aria-invalid={Boolean(errors.plot_number)}
            aria-describedby={errors.plot_number ? "plot-number-error" : undefined}
          />
          {errors.plot_number && <span id="plot-number-error" className="field-error">{errors.plot_number}</span>}
        </label>
        <label>
          Dynamic Fields (JSON)
          <textarea
            name="dynamic_data"
            rows="8"
            value={form.dynamic_data}
            onChange={handleChange}
            disabled={isSubmitting}
            aria-invalid={Boolean(errors.dynamic_data)}
            aria-describedby={`dynamic-data-hint${errors.dynamic_data ? " dynamic-data-error" : ""}`}
          />
          <span id="dynamic-data-hint" className="field-hint">Enter measurements as a JSON object. Use {"{}"} if there are none.</span>
          {errors.dynamic_data && <span id="dynamic-data-error" className="field-error">{errors.dynamic_data}</span>}
        </label>
      </div>
      <div className="form-actions">
        <button className="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Submitting…" : isEditing ? "Update Record" : "Save Record"}
        </button>
        {isEditing && (
          <button type="button" onClick={onCancelEdit} disabled={isSubmitting}>
            Cancel Edit
          </button>
        )}
      </div>
      {status && (
        <p className={status.type === "error" ? "field-error" : "form-success"} role={status.type === "error" ? "alert" : "status"}>
          {status.message}
        </p>
      )}
    </form>
  );
}
