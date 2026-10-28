import { useEffect, useRef, useState } from "react";

import { createField, createHarvestEvent, fetchFields, fetchHarvestEvents } from "../services/api";

export default function HarvestSelector({ onChange, onBusyChange }) {
  const [fields, setFields] = useState([]);
  const [fieldId, setFieldId] = useState("");
  const [harvests, setHarvests] = useState([]);
  const [harvestId, setHarvestId] = useState("");
  const [loadingFields, setLoadingFields] = useState(true);
  const [loadingHarvests, setLoadingHarvests] = useState(false);
  const [fieldError, setFieldError] = useState(null);
  const [harvestError, setHarvestError] = useState(null);
  const [formError, setFormError] = useState(null);
  const [retryFields, setRetryFields] = useState(0);
  const [retryHarvests, setRetryHarvests] = useState(0);
  const [showFieldForm, setShowFieldForm] = useState(false);
  const [showHarvestForm, setShowHarvestForm] = useState(false);
  const [fieldName, setFieldName] = useState("");
  const [harvestDate, setHarvestDate] = useState("");
  const [harvestNumber, setHarvestNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const field = fields.find((item) => String(item.id) === fieldId);

  useEffect(() => {
    let active = true;
    setLoadingFields(true);
    setFieldError(null);
    fetchFields().then((items) => {
      if (active) setFields(items);
    }).catch((error) => {
      if (active) setFieldError(error.message);
    }).finally(() => {
      if (active) setLoadingFields(false);
    });
    return () => { active = false; };
  }, [retryFields]);

  useEffect(() => {
    if (!fieldId) return;
    let active = true;
    setLoadingHarvests(true);
    setHarvestError(null);
    fetchHarvestEvents(fieldId).then((items) => {
      if (active) setHarvests(items);
    }).catch((error) => {
      if (active) setHarvestError(error.message);
    }).finally(() => {
      if (active) setLoadingHarvests(false);
    });
    return () => { active = false; };
  }, [fieldId, retryHarvests]);

  const selectField = (nextField) => {
    setFieldId(nextField ? String(nextField.id) : "");
    setHarvestId("");
    setHarvests([]);
    setLoadingHarvests(Boolean(nextField));
    setHarvestError(null);
    setShowHarvestForm(false);
    setFormError(null);
    setHarvestDate("");
    setHarvestNumber("");
    setNotes("");
    onChange(nextField, null);
  };

  const saveField = async (event) => {
    event.preventDefault();
    if (submitting.current) return;
    if (!fieldName.trim()) {
      setFormError("Enter a field name.");
      return;
    }
    submitting.current = true;
    setBusy(true);
    onBusyChange(true);
    setFormError(null);
    try {
      const created = await createField({ name: fieldName.trim() });
      setFieldError(null);
      setFields((items) => [...items, created].sort((a, b) => a.name.localeCompare(b.name)));
      selectField(created);
      setFieldName("");
      setShowFieldForm(false);
    } catch (error) {
      setFormError(error.message);
    } finally {
      submitting.current = false;
      setBusy(false);
      onBusyChange(false);
    }
  };

  const saveHarvest = async (event) => {
    event.preventDefault();
    if (submitting.current || !field) return;
    if (!harvestDate || (harvestNumber && (!Number.isInteger(Number(harvestNumber)) || Number(harvestNumber) < 1))) {
      setFormError("Enter a harvest date and a positive whole number if providing a harvest number.");
      return;
    }
    submitting.current = true;
    setBusy(true);
    onBusyChange(true);
    setFormError(null);
    try {
      const created = await createHarvestEvent(field.id, {
        harvest_date: harvestDate,
        harvest_number: harvestNumber ? Number(harvestNumber) : null,
        notes: notes.trim() || null
      });
      setHarvestError(null);
      setHarvests((items) => [...items, created].sort((a, b) =>
        b.harvest_date.localeCompare(a.harvest_date) || b.id - a.id
      ));
      setHarvestId(String(created.id));
      onChange(field, created);
      setShowHarvestForm(false);
      setHarvestDate("");
      setHarvestNumber("");
      setNotes("");
    } catch (error) {
      setFormError(error.message);
    } finally {
      submitting.current = false;
      setBusy(false);
      onBusyChange(false);
    }
  };

  return (
    <fieldset className="field-entry" disabled={busy} aria-busy={busy}>
      <div className="grid">
        <label>
          Field
          <select name="field_id" value={fieldId} disabled={loadingFields} onChange={(event) => {
            selectField(fields.find((item) => String(item.id) === event.target.value) || null);
          }}>
            <option value="">{loadingFields ? "Loading fields…" : "Select a field"}</option>
            {fields.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <label>
          Harvest Event
          <select name="harvest_event_id" value={harvestId} disabled={!fieldId || loadingHarvests || Boolean(harvestError)} onChange={(event) => {
            const harvest = harvests.find((item) => String(item.id) === event.target.value) || null;
            setHarvestId(harvest ? String(harvest.id) : "");
            onChange(field, harvest);
          }}>
            <option value="">{loadingHarvests ? "Loading harvest events…" : "Select a harvest event"}</option>
            {harvests.map((item) => (
              <option key={item.id} value={item.id}>
                {item.harvest_date}{item.harvest_number != null ? ` · Harvest ${item.harvest_number}` : ""}{` · Event #${item.id}`}
              </option>
            ))}
          </select>
        </label>
      </div>
      {fieldError && <p className="form-error" role="alert">{fieldError} <button type="button" onClick={() => setRetryFields((value) => value + 1)}>Retry fields</button></p>}
      {harvestError && <p className="form-error" role="alert">{harvestError} <button type="button" onClick={() => setRetryHarvests((value) => value + 1)}>Retry harvest events</button></p>}
      {!loadingFields && !fieldError && fields.length === 0 && <p>No fields yet. Add a field to get started.</p>}
      {fieldId && !loadingHarvests && !harvestError && harvests.length === 0 && <p>No harvest events for this field. Create one below.</p>}
      <div className="form-actions">
        <button type="button" disabled={loadingFields} aria-expanded={showFieldForm} onClick={() => {
          setShowFieldForm(!showFieldForm);
          setShowHarvestForm(false);
          setFormError(null);
        }}>Add field</button>
        <button type="button" disabled={!fieldId || loadingHarvests} aria-expanded={showHarvestForm} onClick={() => {
          setShowHarvestForm(!showHarvestForm);
          setShowFieldForm(false);
          setFormError(null);
        }}>New harvest event</button>
      </div>
      {showFieldForm && (
        <form className="selection-form" aria-label="Add field" onSubmit={saveField}>
          <label>Field name<input name="field_name" value={fieldName} onChange={(event) => setFieldName(event.target.value)} required maxLength={128} /></label>
          <button className="primary" type="submit" disabled={loadingFields}>{busy ? "Saving…" : "Create field"}</button>
        </form>
      )}
      {showHarvestForm && (
        <form className="selection-form" aria-label="New harvest event" onSubmit={saveHarvest}>
          <h2>New harvest event for {field?.name}</h2>
          <div className="grid">
            <label>Harvest date<input name="harvest_date" type="date" value={harvestDate} onChange={(event) => setHarvestDate(event.target.value)} required /></label>
            <label>Harvest number (optional)<input name="harvest_number" type="number" min="1" step="1" value={harvestNumber} onChange={(event) => setHarvestNumber(event.target.value)} /></label>
          </div>
          <label>Notes (optional)<textarea name="harvest_notes" rows="2" maxLength={2048} value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
          <button className="primary" type="submit">{busy ? "Saving…" : "Create harvest event"}</button>
        </form>
      )}
      {formError && <p className="form-error" role="alert">{formError}</p>}
    </fieldset>
  );
}
