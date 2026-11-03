const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

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

export async function fetchHarvestRecords(harvestEventId) {
  const query = harvestEventId ? `?harvest_event_id=${harvestEventId}` : "";
  const response = await fetch(`${API_BASE_URL}/harvest-records/${query}`);

  if (!response.ok) {
    throw new Error("Failed to fetch harvest records");
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
      method: "PATCH",
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