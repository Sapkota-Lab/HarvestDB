
import { useEffect, useState } from "react";

import {
  fetchSeeds,
  createSeed,
  updateSeed,
  deleteSeed,
} from "../services/api";

const NEW_OPTION = "__add_new__";

const emptyForm = {
  crop_type: "",
  variety_name: "",
  breeding_line: "",
  seed_weight_g: "",
  seed_count: "",
  notes: "",
};

// Get unique values from existing records
function uniqueValues(records, field) {
  return [...new Set(
    records.map((record) => record[field]?.trim()).filter(Boolean)
  )].sort((a, b) => a.localeCompare(b));
}

// Reusable dropdown with an Add New option
function InventorySelect({
  label,
  name,
  value,
  options,
  isNew,
  required = false,
  onChoose,
  onChange,
}) {
  return (
    <label>
      {label}{required ? " *" : ""}

      {options.length > 0 && (
        <select
          value={isNew ? NEW_OPTION : value}
          onChange={(event) =>
            onChoose(name, event.target.value)
          }
          required={required}
        >
          <option value="">
            {required ? `Select ${label}` : "None"}
          </option>

          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}

          <option value={NEW_OPTION}>
            + Add New {label}
          </option>
        </select>
      )}

      {(options.length === 0 || isNew) && (
        <input
          type="text"
          name={name}
          value={value}
          onChange={onChange}
          placeholder={`Enter ${label.toLowerCase()}`}
          required={required}
          maxLength={name === "crop_type" ? 100 : 150}
        />
      )}
    </label>
  );
}

export default function SeedInventory() {
  const [seeds, setSeeds] = useState([]);
  const [form, setForm] = useState({ ...emptyForm });

  const [newFields, setNewFields] = useState({
    crop_type: false,
    variety_name: false,
    breeding_line: false,
  });

  const [editingId, setEditingId] = useState(null);
  const [search, setSearch] = useState("");

  // Inventory filtering
  const [filterCrop, setFilterCrop] = useState("");
  const [filterVariety, setFilterVariety] = useState("");
  const [filterLine, setFilterLine] = useState("");
  const [sortOrder, setSortOrder] = useState("newest");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function loadSeeds() {
    const records = await fetchSeeds();
    setSeeds(records);
  }

  useEffect(() => {
    let active = true;

    fetchSeeds()
      .then((records) => {
        if (active) setSeeds(records);
      })
      .catch((err) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  // Existing values for dropdowns
  const cropTypes = uniqueValues(seeds, "crop_type");

  // Only suggest varieties and breeding lines
  // associated with the selected crop
  const cropSeeds = seeds.filter(
    (seed) => seed.crop_type === form.crop_type
  );

  const varieties = uniqueValues(cropSeeds, "variety_name");
  const breedingLines = uniqueValues(cropSeeds, "breeding_line");

  // Options for the inventory filters
  const filterCropSeeds = filterCrop
    ? seeds.filter((seed) => seed.crop_type === filterCrop)
    : seeds;

  const filterVarieties = uniqueValues(
    filterCropSeeds,
    "variety_name"
  );

  const filterLines = uniqueValues(
    filterCropSeeds,
    "breeding_line"
  );

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  // Handle selection of existing or new values
  function handleChoose(field, selected) {
    const isNew = selected === NEW_OPTION;
    const value = isNew ? "" : selected;

    setNewFields((previous) => ({
      ...previous,
      [field]: isNew,
      ...(field === "crop_type"
        ? { variety_name: false, breeding_line: false }
        : {}),
    }));

    setForm((previous) => ({
      ...previous,
      [field]: value,
      ...(field === "crop_type"
        ? { variety_name: "", breeding_line: "" }
        : {}),
    }));
  }

  function resetForm() {
    setForm({ ...emptyForm });
    setEditingId(null);
    setNewFields({
      crop_type: false,
      variety_name: false,
      breeding_line: false,
    });
  }

  // Create or update inventory record
  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    const payload = {
      crop_type: form.crop_type.trim(),
      variety_name: form.variety_name.trim() || null,
      breeding_line: form.breeding_line.trim() || null,
      seed_weight_g:
        form.seed_weight_g === ""
          ? null
          : form.seed_weight_g,
      seed_count:
        form.seed_count === ""
          ? null
          : Number(form.seed_count),
      notes: form.notes.trim() || null,
    };

    try {
      if (editingId !== null) {
        await updateSeed(editingId, payload);
      } else {
        await createSeed(payload);
      }

      resetForm();
      await loadSeeds();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function handleEdit(seed) {
    setEditingId(seed.id);

    setForm({
      crop_type: seed.crop_type,
      variety_name: seed.variety_name ?? "",
      breeding_line: seed.breeding_line ?? "",
      seed_weight_g: seed.seed_weight_g ?? "",
      seed_count: seed.seed_count ?? "",
      notes: seed.notes ?? "",
    });

    setNewFields({
      crop_type: false,
      variety_name: false,
      breeding_line: false,
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this seed record?")) return;

    try {
      setError("");
      await deleteSeed(id);

      if (editingId === id) resetForm();

      await loadSeeds();
    } catch (err) {
      setError(err.message);
    }
  }

  // Search, filter, and sort
  const filteredSeeds = seeds
    .filter((seed) => {
      const searchable = [
        seed.crop_type,
        seed.variety_name,
        seed.breeding_line,
        seed.notes,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return (
        searchable.includes(search.toLowerCase()) &&
        (!filterCrop || seed.crop_type === filterCrop) &&
        (!filterVariety || seed.variety_name === filterVariety) &&
        (!filterLine || seed.breeding_line === filterLine)
      );
    })
    .sort((a, b) => {
      const difference =
        Date.parse(b.date_recorded) -
        Date.parse(a.date_recorded);

      if (difference !== 0) {
        return sortOrder === "newest"
          ? difference
          : -difference;
      }

      return sortOrder === "newest"
        ? b.id - a.id
        : a.id - b.id;
    });

  return (
    <div className="seed-inventory-page">
      <header className="seed-header">
        <h1>Seed Inventory</h1>
        <p>Record and manage seeds currently stored in the lab.</p>
      </header>

      {error && <div className="seed-error">{error}</div>}

      {/* ADD / EDIT FORM */}
      <section className="panel seed-card">
        <h2>
          {editingId !== null
            ? "Edit Seed Record"
            : "Add New Seed"}
        </h2>

        <form onSubmit={handleSubmit}>
          <div className="grid seed-form-grid">
            <InventorySelect
              label="Crop Type"
              name="crop_type"
              value={form.crop_type}
              options={cropTypes}
              isNew={newFields.crop_type}
              required
              onChoose={handleChoose}
              onChange={handleChange}
            />

            <InventorySelect
              label="Variety Name"
              name="variety_name"
              value={form.variety_name}
              options={varieties}
              isNew={newFields.variety_name}
              onChoose={handleChoose}
              onChange={handleChange}
            />

            <InventorySelect
              label="Breeding Line"
              name="breeding_line"
              value={form.breeding_line}
              options={breedingLines}
              isNew={newFields.breeding_line}
              onChoose={handleChoose}
              onChange={handleChange}
            />

            <label>
              Seed Weight (grams)
              <input
                type="number"
                name="seed_weight_g"
                value={form.seed_weight_g}
                onChange={handleChange}
                min="0"
                step="0.0001"
              />
            </label>

            <label>
              Seed Count
              <input
                type="number"
                name="seed_count"
                value={form.seed_count}
                onChange={handleChange}
                min="0"
                step="1"
              />
            </label>

            <label className="seed-full-width">
              Additional Notes
              <textarea
                name="notes"
                value={form.notes}
                onChange={handleChange}
                rows={3}
              />
            </label>
          </div>

          <div className="seed-form-actions">
            <button
              type="submit"
              className="primary"
              disabled={saving}
            >
              {saving
                ? "Saving..."
                : editingId !== null
                  ? "Update Seed"
                  : "Add Seed"}
            </button>

            {editingId !== null && (
              <button
                type="button"
                onClick={resetForm}
                className="seed-cancel"
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </section>

      {/* CURRENT INVENTORY */}
      <section className="panel seed-card">
        <h2>Current Inventory ({filteredSeeds.length})</h2>

        <div className="seed-filter-grid">
          <label>
            Search
            <input
              type="search"
              placeholder="Search inventory..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <label>
            Crop Type
            <select
              value={filterCrop}
              onChange={(event) => {
                setFilterCrop(event.target.value);
                setFilterVariety("");
                setFilterLine("");
              }}
            >
              <option value="">All Crops</option>
              {cropTypes.map((crop) => (
                <option key={crop} value={crop}>{crop}</option>
              ))}
            </select>
          </label>

          <label>
            Variety
            <select
              value={filterVariety}
              onChange={(event) => setFilterVariety(event.target.value)}
            >
              <option value="">All Varieties</option>
              {filterVarieties.map((variety) => (
                <option key={variety} value={variety}>
                  {variety}
                </option>
              ))}
            </select>
          </label>

          <label>
            Breeding Line
            <select
              value={filterLine}
              onChange={(event) => setFilterLine(event.target.value)}
            >
              <option value="">All Lines</option>
              {filterLines.map((line) => (
                <option key={line} value={line}>{line}</option>
              ))}
            </select>
          </label>

          <label>
            Sort by Date
            <select
              value={sortOrder}
              onChange={(event) => setSortOrder(event.target.value)}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>
          </label>
        </div>

        {loading ? (
          <p>Loading inventory...</p>
        ) : (
          <div className="table-wrap">
            <table className="seed-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Crop</th>
                  <th>Variety</th>
                  <th>Breeding Line</th>
                  <th>Weight (g)</th>
                  <th>Count</th>
                  <th>Date Recorded</th>
                  <th>Notes</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {filteredSeeds.map((seed) => (
                  <tr key={seed.id}>
                    <td>{seed.id}</td>
                    <td>{seed.crop_type}</td>
                    <td>{seed.variety_name || "—"}</td>
                    <td>{seed.breeding_line || "—"}</td>
                    <td>{seed.seed_weight_g ?? "—"}</td>
                    <td>{seed.seed_count ?? "—"}</td>
                    <td>
                      {new Date(
                        seed.date_recorded
                      ).toLocaleDateString()}
                    </td>
                    <td>{seed.notes || "—"}</td>
                    <td>
                      <div className="seed-row-actions">
                        <button
                          type="button"
                          onClick={() => handleEdit(seed)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="seed-delete"
                          onClick={() => handleDelete(seed.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}

                {filteredSeeds.length === 0 && (
                  <tr>
                    <td colSpan={9}>No matching seed records.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
