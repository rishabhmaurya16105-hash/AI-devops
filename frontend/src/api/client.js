const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin;

export async function apiRequest(path, options = {}) {
  const response = await fetch(new URL(path, API_BASE_URL), {
    ...options,
    headers: {
      Accept: "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorResponse = await response.json();
    const detail = errorResponse.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : `API request failed with status ${response.status}.`,
    );
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}
