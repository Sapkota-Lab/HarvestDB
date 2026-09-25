const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export async function fetchFields() {
  const response = await fetch(`${API_BASE_URL}/fields/`);

  if (!response.ok) {
    throw new Error("Failed to fetch fields");
  }

  return response.json();
}

export async function createHarvestEvent(fieldId, payload) {
  const response = await fetch(`${API_BASE_URL}/harvests/?field_id=${fieldId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error("Failed to create harvest event");
  }

  return response.json();
}

export async function createHarvestRecord(harvestEventId, payload) {
  const response = await fetch(`${API_BASE_URL}/harvest-records/?harvest_event_id=${harvestEventId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error("Failed to create harvest record");
  }

  return response.json();
}

export async function uploadHarvestRecordsCsv(harvestEventId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/harvest-records/upload?harvest_event_id=${harvestEventId}`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail || "Failed to upload harvest records CSV");
  }

  return response.json();
}

/**
 * Fetch harvest records with optional filtering and pagination.
 * @param {Object} filters - Filter parameters
 * @param {number} filters.harvest_event_id - Optional harvest event ID
 * @param {number} filters.field_id - Optional field ID
 * @param {string} filters.plot_number - Optional plot number (partial match)
 * @param {string} filters.harvest_date_from - Optional start date (YYYY-MM-DD)
 * @param {string} filters.harvest_date_to - Optional end date (YYYY-MM-DD)
 * @param {number} filters.page - Optional page number (default 1)
 * @param {number} filters.page_size - Optional page size (default 50)
 * @returns {Promise<{records: Array, total: number, page: number, page_size: number, total_pages: number}>}
 */
export async function fetchHarvestRecords(filters = {}) {
  const params = new URLSearchParams();
  
  // Only add non-null, non-undefined parameters
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      params.append(key, value);
    }
  });

  const query = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/harvest-records/${query}`);

  if (!response.ok) {
    throw new Error("Failed to fetch harvest records");
  }

  return response.json();
}
