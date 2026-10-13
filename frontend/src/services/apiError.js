export async function readApiError(response, fallback) {
  const body = await response.json().catch(() => null);
  if (typeof body?.detail === "string" && body.detail.trim()) {
    return body.detail;
  }
  if (Array.isArray(body?.detail)) {
    const messages = body.detail
      .filter((error) => typeof error?.msg === "string")
      .map((error) => {
        const field = Array.isArray(error.loc)
          ? error.loc.filter((part) => part !== "body").join(".")
          : "";
        return field ? `${field}: ${error.msg}` : error.msg;
      });
    if (messages.length) return messages.join("; ");
  }
  return fallback;
}
