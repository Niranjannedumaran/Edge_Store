const API_BASE_URL = typeof window !== "undefined" && window.location.port === "5173"
  ? "http://127.0.0.1:8000/api"
  : "/api";

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem("edgestore_token");
  const headers = {
    ...options.headers,
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // If body is not FormData, add JSON header
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    if (typeof options.body === "object") {
      options.body = JSON.stringify(options.body);
    }
  }

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    // If token invalid, clear and trigger re-auth
    localStorage.removeItem("edgestore_token");
    localStorage.removeItem("edgestore_user");
    window.dispatchEvent(new Event("edgestore:unauthorized"));
  }

  // Handle file streaming responses
  const contentType = res.headers.get("content-type") || "";
  if (!res.ok) {
    let errorDetail = "API request failed";
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = res.statusText || errorDetail;
    }
    const err = new Error(errorDetail);
    err.status = res.status;
    throw err;
  }

  if (contentType.includes("application/json")) {
    return await res.json();
  } else if (contentType.includes("text/")) {
    return await res.text();
  } else {
    // Binary or file stream
    const blob = await res.blob();
    return {
      blob,
      headers: res.headers,
    };
  }
}
