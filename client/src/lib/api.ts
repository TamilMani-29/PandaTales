// In dev: use relative URL so Vite proxy forwards /api → http://localhost:8004
// In prod: set VITE_API_BASE_URL to your backend URL
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/+$/, "");

const TOKEN_KEY = "pandatales_access_token";
const ADMIN_USERNAME = "admin@123";
const ADMIN_PASSWORD = "admin@123";

function joinApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (!API_BASE_URL) {
    return normalizedPath;
  }

  // Avoid duplicate prefix when both base and path contain /api.
  if (API_BASE_URL.endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return `${API_BASE_URL}${normalizedPath.slice(4)}`;
  }

  return `${API_BASE_URL}${normalizedPath}`;
}

export const buildApiUrl = (path: string) => joinApiUrl(path);

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  referral_code: string;
  referral_count: number;
};

type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T;
};

async function request<T>(
  path: string,
  options: RequestInit = {},
  extraHeaders: Record<string, string> = {}
): Promise<T> {
  const token = getToken();
  const incomingHeaders = (options.headers as Record<string, string>) || {};
  const hasFormDataBody = options.body instanceof FormData;

  const headers: Record<string, string> = {
    ...incomingHeaders,
    ...extraHeaders,
  };

  if (!hasFormDataBody && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers,
  });

  const payload = (await response.json()) as ApiResponse<T> | { error?: { message?: string } };

  if (!response.ok || !(payload as ApiResponse<T>).success) {
    const message = (payload as any)?.error?.message || "Request failed";
    if (response.status === 401) {
      clearToken();
      const err = new Error(message) as Error & { isAuthError: boolean };
      err.isAuthError = true;
      throw err;
    }
    throw new Error(message);
  }

  return (payload as ApiResponse<T>).data;
}

export async function registerUser(input: { full_name: string; email: string; password: string; phone: string; referral_code?: string }) {
  return request<{ access_token: string; token_type: string; user: AuthUser }>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function loginUser(input: { email: string; password: string }) {
  return request<{ access_token: string; token_type: string; user: AuthUser }>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function getCurrentUser() {
  return request<AuthUser>("/api/v1/auth/me");
}

export type DigitalBook = {
  id: number;
  title: string;
  desc: string;
  price: number;
  age?: string;
  pages: number;
  style?: string;
  emoji: string;
  rat: number;
  rev: number;
  category_id?: number | null;
  category?: number | null;       // alias for category_id
  category_tag?: string | null;
  category_tags?: string[];
  is_bestseller?: boolean;
  is_personalized?: boolean;
  personalized_kind?: "story" | "coloring" | null;
  genre_name?: string | null;
  cover_image_url?: string | null;
  cover_image_presigned_url?: string | null;
  front_image_url?: string | null;
  front_image_presigned_url?: string | null;
  back_image_url?: string | null;
  back_image_presigned_url?: string | null;
};

export async function getDigitalBooks() {
  return request<DigitalBook[]>("/api/v1/digital-books");
}

export async function getDigitalBooksByCategory(categoryId: number) {
  return request<DigitalBook[]>(`/api/v1/digital-books/category/${encodeURIComponent(String(categoryId))}`);
}

export type DigitalBookCategory = {
  id: number;
  category_id: number;
  name: string;
  tags?: string[];
  personalized_tag?: string | null;
  label?: string | null;
  description?: string | null;
  category_image_url?: string | null;
  category_image_presigned_url?: string | null;
  emoji?: string | null;
  color?: string | null;
  grad?: string | null;
  personalized: boolean;
  is_active: boolean;
  category_type?: string | null;
};

export async function getDigitalBookCategories() {
  return request<DigitalBookCategory[]>("/api/v1/digital-books/categories");
}

export type DigitalBookAttributeOptions = {
  book_type: string[];
  theme: string[];
  language: string[];
  genre: string[];
};

export async function getDigitalBookAttributeOptions() {
  return request<DigitalBookAttributeOptions>("/api/v1/digital-books/attribute-options");
}

export async function createDigitalBookAttributeOption(input: {
  option_type: "book_type" | "theme" | "language" | "genre";
  value: string;
}) {
  return request<{ option_type: string; value: string }>("/api/v1/digital-books/attribute-options", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function deleteDigitalBookAttributeOption(optionType: "book_type" | "theme" | "language" | "genre", value: string) {
  return request<{ option_type: string; value: string; deleted: boolean }>(
    `/api/v1/digital-books/attribute-options/${encodeURIComponent(optionType)}/${encodeURIComponent(value)}`,
    { method: "DELETE" }
  );
}

export type DigitalPaymentOrder = {
  order_id: number;
  user_id: string;
  book_id: number;
  amount: number;
  taxable_amount: number;
  gst_rate_percent: number;
  gst_amount: number;
  total_amount: number;
  currency: string;
  key_id: string;
  razorpay_order_id: string;
  payment_status: string;
  delivery_method: string;
  delivery_contact: string;
};

export async function createDigitalPaymentOrder(input: {
  book_id: number;
  delivery_method: string;
  delivery_contact: string;
}) {
  return request<DigitalPaymentOrder>("/api/v1/payments/digital-books/create-order", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function verifyDigitalPayment(input: {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}) {
  return request<{
    order_id: number;
    payment_status: string;
    status: string;
    book_id: number;
    invoice_email_sent?: boolean;
    invoice_razorpay_id?: string | null;
    invoice_razorpay_number?: string | null;
    download_urls?: { book?: string; cover?: string };
  }>(
    "/api/v1/payments/digital-books/verify",
    {
      method: "POST",
      body: JSON.stringify(input),
    }
  );
}

export type DigitalPaymentHistoryItem = {
  order_id: number;
  user_id: string;
  book_id: number;
  book_name: string;
  amount: number;
  taxable_amount: number;
  gst_rate_percent: number;
  gst_amount: number;
  total_amount: number;
  currency: string;
  payment_status: string;
  status: string;
  razorpay_order_id?: string | null;
  razorpay_payment_id?: string | null;
  delivery_method: string;
  delivery_contact: string;
  delivery_status: string;
  payment_error?: string | null;
  created_at: string;
  paid_at?: string | null;
  delivery_sent_at?: string | null;
};

export async function getMyDigitalPaymentHistory() {
  return request<DigitalPaymentHistoryItem[]>("/api/v1/payments/digital-books/history");
}

export async function getDigitalPaymentHistoryByUserId(userId: string) {
  return request<DigitalPaymentHistoryItem[]>(`/api/v1/payments/digital-books/history/${userId}`);
}

export async function purchaseDigitalBook(input: {
  book_id: number;
  delivery_method: string;
  delivery_contact: string;
}) {
  return request<DigitalPaymentOrder>("/api/v1/payments/digital-books/purchase", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function downloadOrderFile(
  orderId: number,
  fileType: "book" | "cover",
  maxAttempts = 3
): Promise<void> {
  const token = getToken();
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      const response = await fetch(
        buildApiUrl(`/api/v1/payments/digital-books/${orderId}/download/${fileType}`),
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      if (!response.ok) {
        throw new Error(`Failed to download ${fileType} (status ${response.status})`);
      }

      const disposition = response.headers.get("Content-Disposition") || "";
      const nameMatch = disposition.match(/filename="?([^"]+)"?/);
      const filename = nameMatch ? nameMatch[1] : `${fileType}-${orderId}`;
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      anchor.rel = "noopener";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      // Delay revocation for mobile browsers to avoid cancelling in-flight saves.
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      return;
    } catch (error) {
      lastError = error as Error;
      await new Promise((resolve) => window.setTimeout(resolve, 450));
    }
  }

  throw lastError ?? new Error(`Failed to download ${fileType}`);
}

function getAdminHeaders() {
  return {
    "X-Admin-Username": ADMIN_USERNAME,
    "X-Admin-Password": ADMIN_PASSWORD,
  };
}

export async function adminLogin(input: { username: string; password: string }) {
  return request<{ authenticated: boolean; username: string }>("/api/v1/admin/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export type AdminUserSummary = {
  id: string;
  full_name: string | null;
  email: string;
  role: string;
  payment_count: number;
  total_spend: number;
  last_payment_at: string | null;
};

export async function getAdminUsers() {
  return request<AdminUserSummary[]>("/api/v1/admin/users", { method: "GET" }, getAdminHeaders());
}

export async function getAdminUserPayments(userId: string) {
  return request<DigitalPaymentHistoryItem[]>(
    `/api/v1/admin/users/${userId}/payments`,
    { method: "GET" },
    getAdminHeaders()
  );
}

export type AdminPersonalizedOrderPhoto = {
  object_name: string;
  url: string | null;
};

export type AdminPersonalizedOrder = {
  book_id: string;
  created_at: string;
  template_type: "story_book" | "coloring_book" | string;
  child_name: string;
  child_age: number;
  child_gender: string;
  parent_email: string;
  whatsapp_number: string | null;
  payment_status: "pending" | "paid" | "failed" | string;
  order_status: "queued" | "processing" | "completed" | "failed" | "cancelled" | string;
  generation_type: string | null;
  selected_theme_name: string | null;
  is_purchased: boolean;
  purchased_at: string | null;
  photos: AdminPersonalizedOrderPhoto[];
  user_id: string;
};

export async function getAdminPersonalizedOrders(limit = 100) {
  return request<AdminPersonalizedOrder[]>(
    `/api/v1/admin/personalized-orders?limit=${encodeURIComponent(String(limit))}`,
    { method: "GET" },
    getAdminHeaders()
  );
}

export async function updateAdminPersonalizedOrderStatus(
  bookId: string,
  input: {
    payment_status?: "pending" | "paid" | "failed";
    order_status?: "queued" | "processing" | "completed" | "failed" | "cancelled";
  }
) {
  return request<{ book_id: string; payment_status: string; order_status: string }>(
    `/api/v1/admin/personalized-orders/${bookId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
    getAdminHeaders()
  );
}

export async function upsertDigitalBookCategory(input: {
  category_id?: number;
  name: string;
  tags?: string[];
  label?: string | null;
  description?: string | null;
  category_image_url?: string | null;
  category_image?: File | null;
  emoji?: string | null;
  color?: string | null;
  grad?: string | null;
  personalized?: boolean;
  is_active?: boolean;
  category_type?: string | null;
}) {
  const formData = new FormData();
  if (typeof input.category_id === "number") {
    formData.append("category_id", String(input.category_id));
  }
  formData.append("name", input.name);
  if (Array.isArray(input.tags) && input.tags.length > 0) {
    formData.append("tags", input.tags.join(","));
  }
  if (input.label != null) formData.append("label", input.label);
  if (input.description != null) formData.append("description", input.description);
  if (input.category_image_url != null) formData.append("category_image_url", input.category_image_url);
  if (input.emoji != null) formData.append("emoji", input.emoji);
  if (input.color != null) formData.append("color", input.color);
  if (input.grad != null) formData.append("grad", input.grad);
  if (typeof input.personalized === "boolean") formData.append("personalized", String(input.personalized));
  if (typeof input.is_active === "boolean") formData.append("is_active", String(input.is_active));
  if (input.category_type != null) formData.append("category_type", input.category_type);
  if (input.category_image) {
    formData.append("category_image", input.category_image);
  }

  return request<DigitalBookCategory>("/api/v1/digital-books/categories", {
    method: "POST",
    body: formData,
  });
}

export async function removeDigitalBookCategory(categoryId: number) {
  return request<{ category_id: number; deleted: boolean }>(`/api/v1/digital-books/categories/${categoryId}`, {
    method: "DELETE",
  });
}

export async function createDigitalBookAdmin(formData: FormData) {
  return request<DigitalBook>("/api/v1/digital-books", {
    method: "POST",
    body: formData,
  });
}

export async function updateDigitalBookAdmin(
  bookId: number,
  input: Partial<{
    book_name: string;
    description: string | null;
    category_id: number | null;
    emoji: string | null;
    total_pages: number | null;
    book_type: string;
    theme: string;
    language: string;
    genre: string;
    price: number | null;
    rating: number | null;
    total_ratings: number | null;
    download_count: number | null;
    is_bestseller: boolean | null;
    is_personalized?: boolean | null;
  }>
) {
  return request<DigitalBook>(`/api/v1/digital-books/${bookId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function removeDigitalBookAdmin(bookId: number) {
  return request<{ book_id: number; deleted: boolean }>(`/api/v1/digital-books/${bookId}`, {
    method: "DELETE",
  });
}

export async function getDigitalBookPreview(bookId: number) {
  return request<{ preview_url: string; expires_in_seconds: number }>(
    `/api/v1/digital-books/${bookId}/preview-pdf`
  );
}

export async function initiatePersonalizedBookOrder(input: {
  child_name: string;
  child_age: number | string;
  child_gender: "male" | "female" | "other";
  parent_email: string;
  whatsapp_number?: string;
  template_type?: "story_book" | "coloring_book";
  selected_theme_name?: string;
  photos: File[];
}) {
  const parsedAge = Number.parseInt(String(input.child_age).trim(), 10);
  if (!Number.isInteger(parsedAge) || parsedAge < 1 || parsedAge > 18) {
    throw new Error("Child age must be a whole number between 1 and 18.");
  }

  const fd = new FormData();
  fd.append("child_name", input.child_name);
  fd.append("child_age", String(parsedAge));
  fd.append("child_gender", input.child_gender);
  fd.append("parent_email", input.parent_email);
  if (input.whatsapp_number) fd.append("whatsapp_number", input.whatsapp_number);
  if (input.template_type) fd.append("template_type", input.template_type);
  if (input.selected_theme_name) fd.append("selected_theme_name", input.selected_theme_name);
  for (const photo of input.photos) {
    fd.append("photos", photo);
  }
  return request<{ generation_id: string; status: string; estimated_time: number; queue_position: number }>(
    "/api/v1/books/generate/photo-to-coloring",
    { method: "POST", body: fd }
  );
}
