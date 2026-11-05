import { readApiError } from "./apiError";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export async function fetchFields() {
  const response = await fetch(`${API_BASE_URL}/fields/`);

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to fetch fields"));
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
    throw new Error(await readApiError(response, "Failed to create harvest event"));
  }

  return response.json();
}

export async function createField(payload) {
  const response = await fetch(`${API_BASE_URL}/fields/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to create field"));
  }
  return response.json();
}

export async function fetchHarvestEvents(fieldId) {
  const response = await fetch(`${API_BASE_URL}/harvests/?field_id=${fieldId}`);
  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to fetch harvest events"));
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
    throw new Error(await readApiError(response, "Failed to create harvest record"));
  }

  return response.json();
}

export async function updateHarvestRecord(recordId, payload) {
  const response = await fetch(`${API_BASE_URL}/harvest-records/${recordId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to update harvest record"));
  }

  return response.json();
}

export async function deleteHarvestRecord(recordId) {
  const response = await fetch(`${API_BASE_URL}/harvest-records/${recordId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to delete harvest record"));
  }
}

export async function listHarvestUploadWorksheets(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/harvest-records/upload/worksheets`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to read workbook worksheets"));
  }

  return response.json();
}

export async function uploadHarvestRecordsCsv(harvestEventId, file, sheetEventIds = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (sheetEventIds) {
    formData.append("sheet_event_ids", JSON.stringify(sheetEventIds));
  }

  const query = harvestEventId ? `?harvest_event_id=${harvestEventId}` : "";
  const response = await fetch(`${API_BASE_URL}/harvest-records/upload${query}`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to upload harvest records"));
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
    throw new Error(await readApiError(response, "Failed to fetch harvest records"));
  }

  return response.json();
}

export function imageUrl(image) {
  const base = new URL(
    `${API_BASE_URL.replace(/\/+$/, "")}/`,
    window.location.origin
  );

  return new URL(image.url, base).href;
}

export async function fetchRecordImages(recordId) {
  const response = await fetch(`${API_BASE_URL}/harvest-records/${recordId}/images`);

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to fetch images"));
  }

  return response.json();
}

//Seed Inventory API functions

async function handleSeedResponse(response, fallbackMessage) {
  if (!response.ok) {
    const error = await response.json().catch(() => null);

    const message =
      typeof error?.detail === "string"
        ? error.detail
        : error?.detail
          ? JSON.stringify(error.detail)
          : fallbackMessage;

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}


// Fetch all seeds, optionally filtering by crop type
export async function fetchSeeds(cropType = null) {
  const query = cropType
    ? `?crop_type=${encodeURIComponent(cropType)}`
    : "";

  const response = await fetch(
    `${API_BASE_URL}/seeds/${query}`
  );

  return handleSeedResponse(
    response,
    "Failed to fetch seed inventory"
  );
}


// Create a new seed record
export async function createSeed(payload) {
  const response = await fetch(`${API_BASE_URL}/seeds/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return handleSeedResponse(
    response,
    "Failed to create seed record"
  );
}


// Fetch one seed by ID
export async function fetchSeed(seedId) {
  const response = await fetch(
    `${API_BASE_URL}/seeds/${seedId}`
  );

  return handleSeedResponse(
    response,
    "Failed to fetch seed record"
  );
}


// Update an existing seed record
export async function updateSeed(seedId, payload) {
  const response = await fetch(
    `${API_BASE_URL}/seeds/${seedId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }
  );

  return handleSeedResponse(
    response,
    "Failed to update seed record"
  );
}


// Delete a seed record
export async function deleteSeed(seedId) {
  const response = await fetch(
    `${API_BASE_URL}/seeds/${seedId}`,
    {
      method: "DELETE"
    }
  );

  return handleSeedResponse(
    response,
    "Failed to delete seed record"
  );
}
export async function uploadRecordImages(recordId, files, category, caption = "") {
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append("files", file));
  formData.append("category", category);
  if (caption) {
    formData.append("caption", caption);
  }

  const response = await fetch(`${API_BASE_URL}/harvest-records/${recordId}/images`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to upload images"));
  }

  return response.json();
}

export async function deleteRecordImage(imageId) {
  const response = await fetch(`${API_BASE_URL}/harvest-records/images/${imageId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await readApiError(response, "Failed to delete image"));
  }
}
