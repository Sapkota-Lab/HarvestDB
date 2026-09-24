const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

async function readError(response, fallback) {
  const detail = await response.json().catch(() => null);
  if (typeof detail?.detail === "string") {
    return detail.detail;
  }
  return fallback;
}

export async function fetchFields() {
  const response = await fetch(`${API_BASE_URL}/fields/`);

  if (!response.ok) {
    throw new Error(await readError(response, "Failed to fetch fields"));
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
    throw new Error(await readError(response, "Failed to create harvest event"));
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
    throw new Error(await readError(response, "Failed to create harvest record"));
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
    throw new Error(await readError(response, "Failed to update harvest record"));
  }

  return response.json();
}

export async function deleteHarvestRecord(recordId) {
  const response = await fetch(`${API_BASE_URL}/harvest-records/${recordId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Failed to delete harvest record"));
  }
}

export async function uploadHarvestRecordsCsv(harvestEventId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/harvest-records/upload?harvest_event_id=${harvestEventId}`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Failed to upload harvest records CSV"));
  }

  return response.json();
}

export async function fetchHarvestRecords(harvestEventId) {
  const query = harvestEventId ? `?harvest_event_id=${harvestEventId}` : "";
  const response = await fetch(`${API_BASE_URL}/harvest-records/${query}`);

  if (!response.ok) {
    throw new Error(await readError(response, "Failed to fetch harvest records"));
  }

  return response.json();
}
