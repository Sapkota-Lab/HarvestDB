const AUTH_URL = "http://localhost:8000/api/v1/auth";
const TOKEN_KEY = "harvestdb_access_token";

export function getAccessToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function saveAccessToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function removeAccessToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

export async function login(email, password) {
  const response = await fetch(`${AUTH_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Invalid email or password.");
    }

    throw new Error("Unable to sign in. Please try again.");
  }

  return response.json();
}

export async function getCurrentUser(token) {
  const response = await fetch(`${AUTH_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Invalid or expired session.");
  }

  return response.json();
}

export function logout() {
  removeAccessToken();
}