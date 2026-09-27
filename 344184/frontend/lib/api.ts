const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function token() { return typeof window === "undefined" ? null : localStorage.getItem("careeros_token"); }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...options.headers } });
  const body = await response.json();
  if (!response.ok) throw new Error(body?.error?.message || "Request failed");
  return body.data as T;
}

export async function signUpDemo() {
  const email = `demo-${Date.now()}@careeros.local`;
  const data = await api<{access_token: string}>("/api/auth/register", { method: "POST", body: JSON.stringify({ name: "CareerOS Demo", email, password: "demo-password-123" }) });
  localStorage.setItem("careeros_token", data.access_token);
  return data;
}
