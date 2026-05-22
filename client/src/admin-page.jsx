import { useEffect, useMemo, useState } from "react";
import {
  adminLogin,
  createDigitalBookAttributeOption,
  createDigitalBookAdmin,
  deleteDigitalBookAttributeOption,
  getAdminPersonalizedOrders,
  getAdminUserPayments,
  getAdminUsers,
  getDigitalBookAttributeOptions,
  getDigitalBookCategories,
  getDigitalBooks,
  removeDigitalBookAdmin,
  removeDigitalBookCategory,
  updateAdminPersonalizedOrderStatus,
  updateDigitalBookAdmin,
  upsertDigitalBookCategory,
} from "./lib/api";

const ADMIN_VALUE = "admin@123";
const ADMIN_SESSION_KEY = "pandatales_admin_session";

const R = "#4A1FB8";
const G = "#FFB830";
const L = "#A29BFE";
const D = "#1A0A3E";
const C = "#FFF9F0";

const panel = {
  minHeight: "100vh",
  background: `linear-gradient(135deg, #F8F0FF 0%, ${C} 50%, #FFF0E8 100%)`,
  padding: "28px 16px 60px",
  fontFamily: "'Baloo 2', cursive",
  color: D,
};

const card = {
  background: "rgba(255,255,255,.95)",
  backdropFilter: "blur(10px)",
  border: "1px solid rgba(74,31,184,.12)",
  borderRadius: 22,
  boxShadow: "0 16px 44px -24px rgba(74,31,184,.35)",
};

const inputStyle = {
  width: "100%",
  padding: "11px 13px",
  borderRadius: 14,
  border: "1px solid rgba(74,31,184,.2)",
  fontSize: 14,
  fontFamily: "inherit",
  boxSizing: "border-box",
  color: D,
  background: "#fff",
};

const button = {
  border: "none",
  borderRadius: 999,
  padding: "10px 16px",
  fontWeight: 700,
  cursor: "pointer",
  fontFamily: "inherit",
  transition: "all .2s ease",
};

const PAYMENT_STATUS_OPTIONS = ["pending", "paid", "failed"];
const ORDER_STATUS_OPTIONS = ["queued", "processing", "completed", "failed", "cancelled"];
const BOOK_TYPE_OPTIONS = [
  "digital coloring book",
  "digital story book",
  "personalized coloring book",
  "personalised story book",
];

const modalBackdrop = {
  position: "fixed",
  inset: 0,
  background: "rgba(26,10,62,.5)",
  backdropFilter: "blur(4px)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 16,
  zIndex: 5000,
};

const modalCard = {
  background: "rgba(255,255,255,.98)",
  backdropFilter: "blur(10px)",
  border: "1px solid rgba(74,31,184,.18)",
  borderRadius: 22,
  boxShadow: "0 32px 80px -20px rgba(74,31,184,.45)",
  width: "100%",
  maxWidth: 820,
  maxHeight: "92vh",
  overflow: "auto",
  padding: 22,
};

function csvToArray(raw) {
  return String(raw || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function dateText(value) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function titleCase(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function isPersonalizedBookType(bookType) {
  return String(bookType || "").toLowerCase().includes("personal");
}

function getExpectedCategoryTypeForBookType(bookType) {
  const bt = String(bookType || "").trim().toLowerCase();
  if (bt.startsWith("digital")) return "digital";
  if (bt.includes("color") || bt.includes("colour")) return "personalized_coloring";
  return "personalized_story";
}

function inferCategoryTypeForFiltering(category) {
  const explicit = String(category?.category_type || "").trim().toLowerCase();
  if (explicit) return explicit;

  if (!category?.personalized) return "digital";

  const text = [
    category?.label || "",
    category?.name || "",
    Array.isArray(category?.tags) ? category.tags.join(" ") : (category?.tags || ""),
  ]
    .join(" ")
    .toLowerCase();

  if (text.includes("coloring") || text.includes("colouring")) return "personalized_coloring";
  return "personalized_story";
}

function AdminModal({ title, onClose, children }) {
  return (
    <div style={modalBackdrop} onClick={onClose}>
      <div style={modalCard} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, paddingBottom: 12, borderBottom: "1px solid rgba(74,31,184,.12)" }}>
          <h3 style={{ margin: 0, fontSize: 22, color: D }}>{title}</h3>
          <button style={{ ...button, background: "#EFE9FF", color: R, padding: "8px 14px" }} onClick={onClose} type="button">✕ Close</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export default function AdminPage() {
  const [sessionOk, setSessionOk] = useState(() => sessionStorage.getItem(ADMIN_SESSION_KEY) === "1");
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [loginError, setLoginError] = useState("");
  const [loadingLogin, setLoadingLogin] = useState(false);

  const [tab, setTab] = useState("catalog");
  const [managerTab, setManagerTab] = useState("category");

  const [categories, setCategories] = useState([]);
  const [books, setBooks] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState("");

  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [categoryMode, setCategoryMode] = useState("add");
  const [categoryForm, setCategoryForm] = useState({
    category_id: "",
    name: "",
    tags: "",
    label: "",
    description: "",
    category_image_url: "",
    emoji: "",
    color: "",
    grad: "",
    personalized: false,
      is_active: true,
      cat_type: "digital",
    });
  const [categoryImageFile, setCategoryImageFile] = useState(null);
  const [categoryImagePreview, setCategoryImagePreview] = useState("");

  const [bookModalOpen, setBookModalOpen] = useState(false);
  const [bookMode, setBookMode] = useState("add");
  const [bookEditingId, setBookEditingId] = useState(null);
  const [bookForm, setBookForm] = useState({
    book_name: "",
    description: "",
    category_id: "",
    emoji: "",
    total_pages: "",
    genre: "fantasy",
    price: "",
    rating: "4.8",
    total_ratings: "0",
    download_count: "0",
    is_bestseller: false,
    book_type: "digital story book",
    theme: "human",
    language: "english",
  });
  const [bookFiles, setBookFiles] = useState({
    cover_image: null,
    front_image: null,
    back_image: null,
    book_file: null,
  });
  const [bookAttributeOptions, setBookAttributeOptions] = useState({
    book_type: BOOK_TYPE_OPTIONS,
    theme: ["human"],
    language: ["english"],
    genre: ["fantasy"],
  });
  const [optionsModalOpen, setOptionsModalOpen] = useState(false);
  const [optionsAddingType, setOptionsAddingType] = useState(null);
  const [optionsNewValue, setOptionsNewValue] = useState("");
  const [optionsSaving, setOptionsSaving] = useState(false);
  const [optionsMsg, setOptionsMsg] = useState("");

  const [actionMsg, setActionMsg] = useState("");
  const [bookModalMsg, setBookModalMsg] = useState("");
  const [saving, setSaving] = useState(false);

  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [payments, setPayments] = useState([]);
  const [paymentsLoading, setPaymentsLoading] = useState(false);
  const [usersError, setUsersError] = useState("");

  const [personalizedOrders, setPersonalizedOrders] = useState([]);
  const [personalizedLoading, setPersonalizedLoading] = useState(false);
  const [personalizedError, setPersonalizedError] = useState("");
  const [personalizedSavingId, setPersonalizedSavingId] = useState("");

  useEffect(() => {
    return () => {
      if (categoryImagePreview && categoryImagePreview.startsWith("blob:")) {
        URL.revokeObjectURL(categoryImagePreview);
      }
    };
  }, [categoryImagePreview]);

  async function loadCatalog() {
    setCatalogLoading(true);
    setCatalogError("");
    try {
      const [catRows, bookRows, attrOptions] = await Promise.all([
        getDigitalBookCategories(),
        getDigitalBooks(),
        getDigitalBookAttributeOptions(),
      ]);
      setCategories(Array.isArray(catRows) ? catRows : []);
      setBooks(Array.isArray(bookRows) ? bookRows : []);
      setBookAttributeOptions({
        book_type: BOOK_TYPE_OPTIONS,
        theme: Array.isArray(attrOptions?.theme) && attrOptions.theme.length ? attrOptions.theme : ["human"],
        language: Array.isArray(attrOptions?.language) && attrOptions.language.length ? attrOptions.language : ["english"],
        genre: Array.isArray(attrOptions?.genre) && attrOptions.genre.length ? attrOptions.genre : ["fantasy"],
      });
    } catch (err) {
      setCatalogError(err?.message || "Unable to load catalog data");
    } finally {
      setCatalogLoading(false);
    }
  }

  function getDefaultOption(optionType, fallback = "") {
    const list = bookAttributeOptions?.[optionType] || [];
    return list[0] || fallback;
  }

  async function loadUsers() {
    setUsersLoading(true);
    setUsersError("");
    try {
      const rows = await getAdminUsers();
      setUsers(Array.isArray(rows) ? rows : []);
    } catch (err) {
      setUsersError(err?.message || "Unable to load users");
    } finally {
      setUsersLoading(false);
    }
  }

  async function loadPersonalizedOrders() {
    setPersonalizedLoading(true);
    setPersonalizedError("");
    try {
      const rows = await getAdminPersonalizedOrders(150);
      setPersonalizedOrders(Array.isArray(rows) ? rows : []);
    } catch (err) {
      setPersonalizedError(err?.message || "Unable to load personalized orders");
    } finally {
      setPersonalizedLoading(false);
    }
  }

  useEffect(() => {
    if (!sessionOk) return;
    loadCatalog();
  }, [sessionOk]);

  useEffect(() => {
    if (!sessionOk || tab !== "users") return;
    loadUsers();
  }, [sessionOk, tab]);

  useEffect(() => {
    if (!sessionOk || tab !== "personalized") return;
    loadPersonalizedOrders();
  }, [sessionOk, tab]);

  const totalPaid = useMemo(
    () => payments.reduce((sum, item) => sum + (Number(item?.amount) || 0), 0),
    [payments]
  );

  const expectedCategoryType = useMemo(
    () => getExpectedCategoryTypeForBookType(bookForm.book_type),
    [bookForm.book_type]
  );

  const filteredBookCategories = useMemo(
    () => categories.filter((c) => inferCategoryTypeForFiltering(c) === expectedCategoryType),
    [categories, expectedCategoryType]
  );

  useEffect(() => {
    if (!bookForm.category_id) return;
    const selectedId = String(bookForm.category_id);
    const stillValid = filteredBookCategories.some((c) => String(c.category_id) === selectedId);
    if (!stillValid) {
      setBookForm((s) => ({ ...s, category_id: "" }));
    }
  }, [bookForm.category_id, filteredBookCategories]);

  async function handleLogin(e) {
    e.preventDefault();
    setLoadingLogin(true);
    setLoginError("");
    try {
      await adminLogin({ username: loginForm.username, password: loginForm.password });
      sessionStorage.setItem(ADMIN_SESSION_KEY, "1");
      setSessionOk(true);
    } catch (err) {
      setLoginError(err?.message || "Login failed");
    } finally {
      setLoadingLogin(false);
    }
  }

  async function saveCategory(e) {
    e.preventDefault();
    setSaving(true);
    setActionMsg("");
    try {
      await upsertDigitalBookCategory({
        category_id: categoryForm.category_id ? Number(categoryForm.category_id) : undefined,
        name: categoryForm.name.trim(),
        tags: csvToArray(categoryForm.tags),
        label: categoryForm.label || null,
        description: categoryForm.description || null,
        category_image_url: categoryForm.category_image_url || null,
        category_image: categoryImageFile,
        emoji: categoryForm.emoji || null,
        color: categoryForm.color || null,
        grad: categoryForm.grad || null,
        personalized: !!categoryForm.personalized,
        is_active: !!categoryForm.is_active,
        category_type: categoryForm.cat_type === "personalized_coloring" ? "personalized_coloring" : categoryForm.cat_type === "personalized_story" ? "personalized_story" : "digital",
      });
      setActionMsg(categoryMode === "add" ? "✅ Category added" : "✅ Category updated");
      setCategoryModalOpen(false);
      setCategoryImageFile(null);
      setCategoryImagePreview("");
      setCategoryForm({ category_id: "", name: "", tags: "", label: "", description: "", category_image_url: "", emoji: "", color: "", grad: "", personalized: false, is_active: true, cat_type: "digital" });
      await loadCatalog();
    } catch (err) {
      setActionMsg("❌ " + (err?.message || "Failed to save category"));
    } finally {
      setSaving(false);
    }
  }

  function openAddCategoryModal() {
    setCategoryMode("add");
      setCategoryImageFile(null);
      setCategoryImagePreview("");
      setCategoryForm({ category_id: "", name: "", tags: "", label: "", description: "", category_image_url: "", emoji: "", color: "", grad: "", personalized: false, is_active: true, cat_type: "digital" });
    setCategoryModalOpen(true);
  }

  function openEditCategoryModal(cat) {
    setCategoryMode("edit");
    const lbl = String(cat.label || "").toLowerCase();
    let cat_type = cat.category_type || "";
    if (!cat_type) {
      if (!cat.personalized) {
        cat_type = "digital";
      } else if (lbl === "coloring" || lbl === "colouring" || lbl === "personalized_coloring") {
        cat_type = "personalized_coloring";
      } else if (lbl === "story" || lbl === "personalized_story") {
        cat_type = "personalized_story";
      } else {
        cat_type = "personalized_story"; // fallback
      }
    }
    setCategoryForm({
      category_id: String(cat.category_id || ""),
      name: cat.name || "",
      tags: Array.isArray(cat.tags) ? cat.tags.join(", ") : "",
      label: cat.label || "",
      description: cat.description || "",
      category_image_url: cat.category_image_url || "",
      emoji: cat.emoji || "",
      color: cat.color || "",
      grad: cat.grad || "",
      personalized: !!cat.personalized,
      is_active: !!cat.is_active,
      cat_type,
    });
    setCategoryImageFile(null);
    setCategoryImagePreview(cat.category_image_presigned_url || cat.category_image_url || "");
    setCategoryModalOpen(true);
  }

  async function handleDeleteCategory(collectionId) {
    if (!window.confirm("Delete this category?")) return;
    setSaving(true);
    setActionMsg("");
    try {
      await removeDigitalBookCategory(Number(collectionId));
      setActionMsg("Category deleted");
      await loadCatalog();
    } catch (err) {
      setActionMsg(err?.message || "Failed to delete category");
    } finally {
      setSaving(false);
    }
  }

  function openAddBookModal() {
    setBookMode("add");
    setBookEditingId(null);
    setBookModalMsg("");
    setBookForm({
      book_name: "",
      description: "",
      category_id: "",
      emoji: "",
      total_pages: "",
      genre: getDefaultOption("genre", "fantasy"),
      price: "",
      rating: "4.8",
      total_ratings: "0",
      download_count: "0",
      is_bestseller: false,
      book_type: getDefaultOption("book_type", "digital story book"),
      theme: getDefaultOption("theme", "human"),
      language: getDefaultOption("language", "english"),
    });
    setBookFiles({ cover_image: null, front_image: null, back_image: null, book_file: null });
    setBookModalOpen(true);
  }

  function openEditBookModal(b) {
    setBookMode("edit");
    setBookEditingId(b.id);
    setBookModalMsg("");
    setBookForm({
      book_name: b.book_name || b.title || "",
      description: b.description || b.desc || "",
      category_id: b.category_id ? String(b.category_id) : "",
      emoji: b.emoji || "",
      total_pages: b.total_pages != null ? String(b.total_pages) : b.pages != null ? String(b.pages) : "",
      genre: b.genre_name || "fantasy",
      price: b.price != null ? String(b.price) : "",
      rating: b.rating != null ? String(b.rating) : b.rat != null ? String(b.rat) : "4.8",
      total_ratings: b.total_ratings != null ? String(b.total_ratings) : b.rev != null ? String(b.rev) : "0",
      download_count: b.download_count != null ? String(b.download_count) : "0",
      is_bestseller: !!b.is_bestseller,
      book_type: b.book_type || "digital story book",
      theme: b.theme || "human",
      language: b.language || "english",
    });
    setBookFiles({ cover_image: null, front_image: null, back_image: null, book_file: null });
    setBookModalOpen(true);
  }

  async function saveBook(e) {
    e.preventDefault();
    setSaving(true);
    setActionMsg("");
    setBookModalMsg("");
    try {
      const derivedIsPersonalized = isPersonalizedBookType(bookForm.book_type);
      if (bookMode === "add") {
        if (!bookFiles.cover_image || (!bookFiles.book_file && !derivedIsPersonalized)) {
          const msg = !bookFiles.cover_image
            ? "❌ Cover image is required"
            : "❌ PDF is required for non-personalized books";
          setActionMsg(msg);
          setBookModalMsg(msg);
          setSaving(false);
          return;
        }
        const fd = new FormData();
        fd.append("book_name", bookForm.book_name);
        fd.append("description", bookForm.description || "");
        if (bookForm.category_id) fd.append("category_id", String(Number(bookForm.category_id)));
        fd.append("emoji", bookForm.emoji || "");
        if (bookForm.total_pages) fd.append("total_pages", String(Number(bookForm.total_pages)));
        fd.append("book_type", bookForm.book_type);
        fd.append("theme", bookForm.theme);
        fd.append("language", bookForm.language);
        fd.append("genre", bookForm.genre);
        if (bookForm.price) fd.append("price", String(Number(bookForm.price)));
        if (bookForm.rating) fd.append("rating", String(Number(bookForm.rating)));
        if (bookForm.total_ratings) fd.append("total_ratings", String(Number(bookForm.total_ratings)));
        if (bookForm.download_count) fd.append("download_count", String(Number(bookForm.download_count)));
        fd.append("is_bestseller", String(!!bookForm.is_bestseller));
        fd.append("is_personalized", String(derivedIsPersonalized));
        fd.append("cover_image", bookFiles.cover_image);
        if (bookFiles.front_image) fd.append("front_image", bookFiles.front_image);
        if (bookFiles.back_image) fd.append("back_image", bookFiles.back_image);
        if (bookFiles.book_file) fd.append("book_file", bookFiles.book_file);
        await createDigitalBookAdmin(fd);
        setActionMsg("✅ Book added");
      } else {
        const payload = {
          book_name: bookForm.book_name || undefined,
          description: bookForm.description,
          category_id: bookForm.category_id ? Number(bookForm.category_id) : undefined,
          emoji: bookForm.emoji || undefined,
          total_pages: bookForm.total_pages ? Number(bookForm.total_pages) : undefined,
          genre: bookForm.genre || undefined,
          price: bookForm.price ? Number(bookForm.price) : undefined,
          rating: bookForm.rating ? Number(bookForm.rating) : undefined,
          total_ratings: bookForm.total_ratings ? Number(bookForm.total_ratings) : undefined,
          download_count: bookForm.download_count ? Number(bookForm.download_count) : undefined,
          is_bestseller: !!bookForm.is_bestseller,
          is_personalized: derivedIsPersonalized,
          book_type: bookForm.book_type,
          theme: bookForm.theme,
          language: bookForm.language,
        };
        await updateDigitalBookAdmin(bookEditingId, payload);
        setActionMsg("✅ Book updated");
      }
      setBookModalMsg("");
      setBookModalOpen(false);
      await loadCatalog();
    } catch (err) {
      const msg = "❌ " + (err?.message || "Failed to save book");
      setActionMsg(msg);
      setBookModalMsg(msg);
    } finally {
      setSaving(false);
    }
  }

  async function deleteBook(bookId) {
    if (!window.confirm("Delete this book?")) return;
    setSaving(true);
    setActionMsg("");
    try {
      await removeDigitalBookAdmin(bookId);
      setActionMsg("Book deleted");
      await loadCatalog();
    } catch (err) {
      setActionMsg(err?.message || "Failed to delete book");
    } finally {
      setSaving(false);
    }
  }

  async function addBookAttributeOption(optionType, value) {
    const v = String(value || "").trim().toLowerCase();
    if (!v) return;
    setOptionsSaving(true);
    setOptionsMsg("");
    try {
      await createDigitalBookAttributeOption({ option_type: optionType, value: v });
      setOptionsMsg(`✅ Added "${v}" to ${titleCase(optionType)}`);
      await loadCatalog();
      setOptionsNewValue("");
    } catch (err) {
      setOptionsMsg("❌ " + (err?.message || `Failed to add ${optionType}`));
    } finally {
      setOptionsSaving(false);
    }
  }

  async function deleteBookAttributeOption(optionType, value) {
    if (!value) return;
    setOptionsSaving(true);
    setOptionsMsg("");
    try {
      await deleteDigitalBookAttributeOption(optionType, value);
      setOptionsMsg(`✅ Removed "${value}" from ${titleCase(optionType)}`);
      await loadCatalog();
      // Reset book form field if it was using the deleted value
      setBookForm((s) => {
        const field = optionType;
        const remaining = (bookAttributeOptions[field] || []).filter((v) => v !== value);
        return { ...s, [field]: remaining[0] || "" };
      });
    } catch (err) {
      setOptionsMsg("❌ " + (err?.message || `Failed to delete ${optionType}: might be in use by books`));
    } finally {
      setOptionsSaving(false);
    }
  }

  async function openUserPayments(user) {
    setSelectedUser(user);
    setPaymentsLoading(true);
    setUsersError("");
    try {
      const rows = await getAdminUserPayments(user.id);
      setPayments(Array.isArray(rows) ? rows : []);
    } catch (err) {
      setUsersError(err?.message || "Unable to load payment details");
      setPayments([]);
    } finally {
      setPaymentsLoading(false);
    }
  }

  async function handlePersonalizedStatusChange(bookId, field, value) {
    if (!bookId || !field || !value) return;
    setPersonalizedSavingId(bookId);
    setActionMsg("");
    try {
      const payload = field === "payment_status"
        ? { payment_status: value }
        : { order_status: value };
      const updated = await updateAdminPersonalizedOrderStatus(bookId, payload);

      setPersonalizedOrders((items) =>
        items.map((item) =>
          item.book_id === bookId
            ? {
                ...item,
                payment_status: updated.payment_status,
                order_status: updated.order_status,
              }
            : item
        )
      );

      setActionMsg("✅ Personalized order status updated");
    } catch (err) {
      setActionMsg("❌ " + (err?.message || "Failed to update personalized order status"));
    } finally {
      setPersonalizedSavingId("");
    }
  }

  if (!sessionOk) {
    return (
      <div style={panel}>
        <div style={{ maxWidth: 520, margin: "72px auto", ...card, padding: 26, position: "relative", overflow: "hidden" }}>
          <div style={{ position: "absolute", width: 170, height: 170, borderRadius: "50%", background: "rgba(255,184,48,.25)", top: -60, right: -60 }} />
          <div style={{ position: "absolute", width: 120, height: 120, borderRadius: "50%", background: "rgba(162,155,254,.2)", bottom: -40, left: -40 }} />
          <h1 style={{ margin: 0, fontSize: 32, color: D, position: "relative" }}>PandaTales Admin</h1>
          <p style={{ marginTop: 6, color: "#5b4f7c", position: "relative" }}>Secure admin access for catalog and payments</p>
          <form onSubmit={handleLogin} style={{ display: "grid", gap: 12, marginTop: 14 }}>
            <input
              style={inputStyle}
              placeholder="Username"
              value={loginForm.username}
              onChange={(e) => setLoginForm((s) => ({ ...s, username: e.target.value }))}
            />
            <input
              style={inputStyle}
              type="password"
              placeholder="Password"
              value={loginForm.password}
              onChange={(e) => setLoginForm((s) => ({ ...s, password: e.target.value }))}
            />
            <button style={{ ...button, background: "#1e3a8a", color: "white" }} type="submit" disabled={loadingLogin}>
              {loadingLogin ? "Checking..." : "Login"}
            </button>
          </form>
          <p style={{ marginTop: 12, color: "#5b6786", fontSize: 13 }}>Hint: username {ADMIN_VALUE} and password {ADMIN_VALUE}</p>
          {loginError ? <p style={{ marginTop: 8, color: "#b00020", fontWeight: 700 }}>{loginError}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div style={panel}>
      <div style={{ maxWidth: 1240, margin: "0 auto" }}>
        <div style={{ marginBottom: 12, background: `linear-gradient(90deg, ${G}, #FFC947, ${G})`, borderRadius: 999, padding: "8px 18px", textAlign: "center", color: D, fontWeight: 800, fontSize: 14, boxShadow: "0 8px 22px -16px rgba(255,184,48,.9)" }}>
          PandaTales Admin Console: Fast updates for categories, books, users and payments
        </div>
        <div style={{ ...card, padding: 16, display: "flex", gap: 10, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
          <button
            style={{ ...button, background: "linear-gradient(135deg,#EDE7FF,#DCD0FF)", color: R }}
            onClick={() => {
              window.location.href = "/";
            }}
          >
            ← Back
          </button>
          <div style={{ flex: 1 }}>
            <h2 style={{ margin: 0, fontSize: 28, color: D }}>Admin Portal</h2>
            <p style={{ margin: "2px 0 0", fontSize: 14, color: "#6b5d92" }}>Manage categories, books, users and payment records</p>
          </div>
          <button
            style={{ ...button, background: `linear-gradient(135deg,${G},#FFC947)`, color: D }}
            onClick={() => {
              sessionStorage.removeItem(ADMIN_SESSION_KEY);
              setSessionOk(false);
              setLoginForm({ username: "", password: "" });
            }}
          >
            Logout
          </button>
        </div>

        <div style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
          <button
            style={{
              ...button,
              background: tab === "catalog" ? `linear-gradient(135deg,${R},${L})` : "#EFE9FF",
              color: tab === "catalog" ? "#fff" : R,
              boxShadow: tab === "catalog" ? "0 8px 18px rgba(74,31,184,.28)" : "none",
            }}
            onClick={() => setTab("catalog")}
          >
            📚 Catalog Manager
          </button>
          <button
            style={{
              ...button,
              background: tab === "users" ? "linear-gradient(135deg,#00B894,#00CEC9)" : "#DDF8F4",
              color: tab === "users" ? "#fff" : "#06786f",
              boxShadow: tab === "users" ? "0 8px 18px rgba(0,184,148,.24)" : "none",
            }}
            onClick={() => setTab("users")}
          >
            👥 Users & Payments
          </button>
          <button
            style={{
              ...button,
              background: tab === "personalized" ? "linear-gradient(135deg,#2563EB,#60A5FA)" : "#E0ECFF",
              color: tab === "personalized" ? "#fff" : "#1d4ed8",
              boxShadow: tab === "personalized" ? "0 8px 18px rgba(37,99,235,.24)" : "none",
            }}
            onClick={() => setTab("personalized")}
          >
            🧸 Personalized Orders
          </button>
        </div>

        {actionMsg ? <p style={{ fontWeight: 700, color: actionMsg.toLowerCase().includes("failed") ? "#b00020" : "#0f766e" }}>{actionMsg}</p> : null}

        {tab === "catalog" ? (
          <section style={{ ...card, padding: 20 }}>
            {/* inner manager tabs + add button in same row */}
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 18 }}>
              <button
                type="button"
                style={{ ...button, padding: "9px 20px", background: managerTab === "category" ? `linear-gradient(135deg,${R},${L})` : "#EFE9FF", color: managerTab === "category" ? "#fff" : R, boxShadow: managerTab === "category" ? `0 6px 16px rgba(74,31,184,.28)` : "none" }}
                onClick={() => setManagerTab("category")}
              >
                🗂 Categories
              </button>
              <button
                type="button"
                style={{ ...button, padding: "9px 20px", background: managerTab === "book" ? "linear-gradient(135deg,#00B894,#00CEC9)" : "#DDF8F4", color: managerTab === "book" ? "#fff" : "#06786f", boxShadow: managerTab === "book" ? "0 6px 16px rgba(0,184,148,.28)" : "none" }}
                onClick={() => setManagerTab("book")}
              >
                📖 Books
              </button>
              <div style={{ flex: 1 }} />
              {managerTab === "category" ? (
                <button type="button" style={{ ...button, background: `linear-gradient(135deg,${R},${L})`, color: "#fff", padding: "9px 20px", boxShadow: `0 6px 18px rgba(74,31,184,.32)` }} onClick={openAddCategoryModal}>
                  + Add Category
                </button>
              ) : (
                <button type="button" style={{ ...button, background: "linear-gradient(135deg,#00B894,#00CEC9)", color: "#fff", padding: "9px 20px", boxShadow: "0 6px 18px rgba(0,184,148,.32)" }} onClick={openAddBookModal}>
                  + Add Book
                </button>
              )}
            </div>

            {catalogLoading ? <p style={{ color: "#6b5d92" }}>Loading catalog...</p> : null}
            {catalogError ? <p style={{ color: "#b00020", fontWeight: 700 }}>{catalogError}</p> : null}

            {managerTab === "category" ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
                {categories.map((c) => (
                  <div key={c.category_id} style={{ border: "1px solid rgba(74,31,184,.14)", borderRadius: 16, padding: 14, background: "#fff", display: "flex", flexDirection: "column", gap: 6 }}>
                    {c.category_image_presigned_url || c.category_image_url ? (
                      <img
                        src={c.category_image_presigned_url || c.category_image_url}
                        alt={`${c.name} category`}
                        style={{ width: "100%", height: 120, objectFit: "cover", borderRadius: 12, border: "1px solid rgba(74,31,184,.12)" }}
                      />
                    ) : null}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 16, color: D }}>{c.emoji} {c.name}</div>
                        <div style={{ fontSize: 12, color: "#7a6d98", marginTop: 2 }}>Category ID: {c.category_id}</div>
                      </div>
                      <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 999, fontWeight: 700, background: c.is_active ? "#E7FFF7" : "#FDE2E2", color: c.is_active ? "#06786f" : "#991b1b" }}>
                        {c.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    {c.label ? <div style={{ fontSize: 12, fontWeight: 700, color: "#5b4f7c" }}>{c.label}</div> : null}
                    {c.description ? <div style={{ fontSize: 13, color: "#546181", lineHeight: 1.4 }}>{c.description}</div> : null}
                    {c.tags?.length ? (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 4 }}>
                        {c.tags.map((t) => <span key={t} style={{ background: "#EFE9FF", color: R, fontSize: 11, borderRadius: 999, padding: "2px 8px", fontWeight: 700 }}>{t}</span>)}
                      </div>
                    ) : null}
                    <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                      <button type="button" style={{ ...button, background: "#EFE9FF", color: R, padding: "7px 14px", fontSize: 13 }} onClick={() => openEditCategoryModal(c)}>✏️ Edit</button>
                      <button type="button" style={{ ...button, background: "#FEE2E2", color: "#991B1B", padding: "7px 14px", fontSize: 13 }} onClick={() => handleDeleteCategory(c.category_id)}>🗑 Delete</button>
                    </div>
                  </div>
                ))}
                {!categories.length && !catalogLoading ? <p style={{ color: "#6b5d92" }}>No categories yet. Click <strong>+ Add Category</strong> to create one.</p> : null}
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
                {books.map((b) => (
                  <div key={b.id} style={{ border: "1px solid rgba(74,31,184,.14)", borderRadius: 16, padding: 14, background: "#fff", display: "flex", flexDirection: "column", gap: 5 }}>
                    <div style={{ fontWeight: 800, fontSize: 15, color: D }}>{b.emoji} {b.title || b.book_name}</div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <span style={{ background: "#EFE9FF", color: R, fontSize: 11, borderRadius: 999, padding: "2px 8px", fontWeight: 700 }}>{b.book_type || "story"}</span>
                      {b.is_bestseller ? <span style={{ background: "#FFF7CD", color: "#854D0E", fontSize: 11, borderRadius: 999, padding: "2px 8px", fontWeight: 700 }}>⭐ Bestseller</span> : null}
                      {b.is_personalized ? <span style={{ background: "#E0ECFF", color: "#1d4ed8", fontSize: 11, borderRadius: 999, padding: "2px 8px", fontWeight: 700 }}>🧸 Personalized</span> : null}
                    </div>
                    <div style={{ fontSize: 13, color: "#546181" }}>ID: {b.id} | Category ID: {b.category_id || "—"}</div>
                    <div style={{ fontSize: 13, color: "#546181" }}>Genre: {b.genre_name || "—"} | Pages: {b.total_pages || b.pages || "—"}</div>
                    <div style={{ fontSize: 13, color: "#546181" }}>Price: ₹{b.price ?? "—"} | Rating: {b.rat ?? b.rating ?? "—"}</div>
                    <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                      <button type="button" style={{ ...button, background: "#EFE9FF", color: R, padding: "7px 14px", fontSize: 13 }} onClick={() => openEditBookModal(b)}>✏️ Edit</button>
                      <button type="button" style={{ ...button, background: "#FEE2E2", color: "#991B1B", padding: "7px 14px", fontSize: 13 }} onClick={() => deleteBook(b.id)}>🗑 Delete</button>
                    </div>
                  </div>
                ))}
                {!books.length && !catalogLoading ? <p style={{ color: "#6b5d92" }}>No books yet. Click <strong>+ Add Book</strong> to create one.</p> : null}
              </div>
            )}
          </section>
        ) : tab === "users" ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 14 }}>
            <section style={{ ...card, padding: 16, maxHeight: "70vh", overflow: "auto" }}>
              <h3 style={{ marginTop: 0, color: D }}>👤 Users</h3>
              {usersLoading ? <p>Loading users...</p> : null}
              {usersError ? <p style={{ color: "#b00020" }}>{usersError}</p> : null}
              {users.map((u) => (
                <button
                  key={u.id}
                  onClick={() => openUserPayments(u)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    border: selectedUser?.id === u.id ? "2px solid #00B894" : "1px solid rgba(74,31,184,.14)",
                    borderRadius: 14,
                    padding: 10,
                    marginBottom: 8,
                    cursor: "pointer",
                    background: selectedUser?.id === u.id ? "#E7FFF7" : "#fff",
                  }}
                >
                  <strong>{u.full_name || "No Name"}</strong>
                  <div style={{ fontSize: 13, color: "#546181", marginTop: 4 }}>{u.email}</div>
                  <div style={{ fontSize: 12, marginTop: 4, color: "#374151" }}>Orders: {u.payment_count} | Total: {u.total_spend / 100} INR</div>
                </button>
              ))}
            </section>

            <section style={{ ...card, padding: 16 }}>
              <h3 style={{ marginTop: 0, color: D }}>💳 Payment Details</h3>
              {!selectedUser ? <p>Select a user to see payment details.</p> : null}
              {selectedUser ? (
                <>
                  <p style={{ margin: "6px 0", color: "#4b5563" }}>
                    User: <strong>{selectedUser.full_name || "No Name"}</strong> ({selectedUser.email})
                  </p>
                  <p style={{ margin: "6px 0", color: "#4b5563" }}>
                    Payments: {payments.length} | Total paid: {(totalPaid / 100).toFixed(2)} INR
                  </p>
                </>
              ) : null}
              {paymentsLoading ? <p>Loading payment data...</p> : null}

              <div style={{ overflow: "auto", maxHeight: "58vh" }}>
                {payments.map((p) => (
                  <div key={p.order_id} style={{ border: "1px solid rgba(74,31,184,.14)", borderRadius: 14, padding: 10, marginBottom: 8, background: "#fff" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                      <strong>Order #{p.order_id}</strong>
                      <span style={{ fontSize: 12, padding: "2px 8px", borderRadius: 999, background: "#e0f2fe", color: "#075985" }}>{p.payment_status}</span>
                    </div>
                    <div style={{ fontSize: 13, color: "#4b5563", marginTop: 6 }}>Book: {p.book_name}</div>
                    <div style={{ fontSize: 13, color: "#4b5563" }}>Amount: {(Number(p.amount || 0) / 100).toFixed(2)} {p.currency}</div>
                    <div style={{ fontSize: 13, color: "#4b5563" }}>Delivery: {p.delivery_method} - {p.delivery_contact}</div>
                    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>Created: {dateText(p.created_at)}</div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>Paid: {dateText(p.paid_at)}</div>
                  </div>
                ))}
                {selectedUser && !paymentsLoading && payments.length === 0 ? <p>No payments for this user.</p> : null}
              </div>
            </section>
          </div>
        ) : (
          <section style={{ ...card, padding: 18 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
              <div>
                <h3 style={{ margin: 0, color: D }}>🧸 Personalized Orders</h3>
                <p style={{ margin: "4px 0 0", color: "#5b4f7c", fontSize: 13 }}>
                  View user-entered details, uploaded photos, payment state, and order lifecycle in one place.
                </p>
              </div>
              <button
                type="button"
                style={{ ...button, background: "#E0ECFF", color: "#1d4ed8" }}
                onClick={loadPersonalizedOrders}
                disabled={personalizedLoading}
              >
                {personalizedLoading ? "Refreshing..." : "↻ Refresh"}
              </button>
            </div>

            {personalizedLoading ? <p style={{ color: "#6b5d92" }}>Loading personalized orders...</p> : null}
            {personalizedError ? <p style={{ color: "#b00020", fontWeight: 700 }}>{personalizedError}</p> : null}

            {!personalizedLoading && !personalizedOrders.length ? (
              <p style={{ color: "#6b5d92" }}>No personalized orders found yet.</p>
            ) : null}

            <div style={{ display: "grid", gap: 12 }}>
              {personalizedOrders.map((o) => (
                <article key={o.book_id} style={{ border: "1px solid rgba(74,31,184,.14)", borderRadius: 16, padding: 14, background: "#fff" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap", marginBottom: 8 }}>
                    <div>
                      <div style={{ fontWeight: 800, fontSize: 16, color: D }}>Order #{o.book_id.slice(0, 8)}</div>
                      <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>Submitted: {dateText(o.created_at)} | Purchased: {dateText(o.purchased_at)}</div>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "minmax(160px,1fr) minmax(170px,1fr)", gap: 8 }}>
                      <div style={{ display: "grid", gap: 4 }}>
                        <label style={{ fontSize: 11, fontWeight: 800, color: "#075985", textTransform: "uppercase", letterSpacing: ".04em" }}>Payment Status</label>
                        <select
                          style={{ ...inputStyle, padding: "8px 10px", borderColor: "rgba(14,116,144,.35)", background: "#ECFEFF" }}
                          value={String(o.payment_status || "pending").toLowerCase()}
                          disabled={personalizedSavingId === o.book_id}
                          onChange={(e) => handlePersonalizedStatusChange(o.book_id, "payment_status", e.target.value)}
                        >
                          {PAYMENT_STATUS_OPTIONS.map((statusValue) => (
                            <option key={statusValue} value={statusValue}>{titleCase(statusValue)}</option>
                          ))}
                        </select>
                      </div>
                      <div style={{ display: "grid", gap: 4 }}>
                        <label style={{ fontSize: 11, fontWeight: 800, color: "#1d4ed8", textTransform: "uppercase", letterSpacing: ".04em" }}>Order Status</label>
                        <select
                          style={{ ...inputStyle, padding: "8px 10px", borderColor: "rgba(37,99,235,.35)", background: "#EFF6FF" }}
                          value={String(o.order_status || "queued").toLowerCase()}
                          disabled={personalizedSavingId === o.book_id}
                          onChange={(e) => handlePersonalizedStatusChange(o.book_id, "order_status", e.target.value)}
                        >
                          {ORDER_STATUS_OPTIONS.map((statusValue) => (
                            <option key={statusValue} value={statusValue}>{titleCase(statusValue)}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10, marginTop: 8 }}>
                    <div style={{ border: "1px dashed rgba(74,31,184,.22)", borderRadius: 12, padding: 10, background: "#faf8ff" }}>
                      <div style={{ fontSize: 11, color: "#6b5d92", fontWeight: 800, textTransform: "uppercase" }}>Contact Details</div>
                      <div style={{ fontSize: 13, marginTop: 4 }}><strong>Parent Email:</strong> {o.parent_email || "-"}</div>
                      <div style={{ fontSize: 13 }}><strong>WhatsApp:</strong> {o.whatsapp_number || "-"}</div>
                    </div>

                    <div style={{ border: "1px dashed rgba(74,31,184,.22)", borderRadius: 12, padding: 10, background: "#faf8ff" }}>
                      <div style={{ fontSize: 11, color: "#6b5d92", fontWeight: 800, textTransform: "uppercase" }}>Child + Input Info</div>
                      <div style={{ fontSize: 13, marginTop: 4 }}><strong>Child:</strong> {o.child_name || "-"}</div>
                      <div style={{ fontSize: 13 }}><strong>Age/Gender:</strong> {o.child_age ?? "-"} / {titleCase(o.child_gender || "-")}</div>
                      <div style={{ fontSize: 13 }}><strong>Template:</strong> {titleCase(o.template_type || "-")}</div>
                      <div style={{ fontSize: 13 }}><strong>Generation:</strong> {titleCase(o.generation_type || "-")}</div>
                      <div style={{ fontSize: 13 }}><strong>Theme:</strong> {o.selected_theme_name || "-"}</div>
                    </div>

                    <div style={{ border: "1px dashed rgba(74,31,184,.22)", borderRadius: 12, padding: 10, background: "#faf8ff" }}>
                      <div style={{ fontSize: 11, color: "#6b5d92", fontWeight: 800, textTransform: "uppercase" }}>Payment + Delivery</div>
                      <div style={{ fontSize: 13, marginTop: 4 }}><strong>Format:</strong> {titleCase(o.format || "-")}</div>
                      <div style={{ fontSize: 13 }}><strong>Amount:</strong> {(Number(o.amount || 0) / 100).toFixed(2)} {o.currency}</div>
                      <div style={{ fontSize: 13 }}><strong>Purchased:</strong> {o.is_purchased ? "Yes" : "No"}</div>
                      <div style={{ fontSize: 13 }}><strong>Purchased At:</strong> {dateText(o.purchased_at)}</div>
                    </div>
                  </div>

                  <div style={{ marginTop: 10 }}>
                    <div style={{ fontSize: 11, color: "#6b5d92", fontWeight: 800, textTransform: "uppercase", marginBottom: 6 }}>Uploaded Photos</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {Array.isArray(o.photos) && o.photos.length ? o.photos.map((photo, idx) => (
                        <a
                          key={`${o.order_id}-${photo.object_name}-${idx}`}
                          href={photo.url || "#"}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            border: "1px solid rgba(74,31,184,.2)",
                            borderRadius: 10,
                            padding: 6,
                            textDecoration: "none",
                            color: D,
                            background: "#fff",
                            width: 96,
                            display: "grid",
                            gap: 4,
                          }}
                          onClick={(e) => {
                            if (!photo.url) e.preventDefault();
                          }}
                        >
                          {photo.url ? (
                            <img src={photo.url} alt={`uploaded-${idx + 1}`} style={{ width: "100%", height: 64, objectFit: "cover", borderRadius: 8, background: "#f3f4f6" }} />
                          ) : (
                            <div style={{ width: "100%", height: 64, borderRadius: 8, background: "#f3f4f6", display: "grid", placeItems: "center", fontSize: 11, color: "#6b7280" }}>Unavailable</div>
                          )}
                          <span style={{ fontSize: 11, fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>Photo {idx + 1}</span>
                        </a>
                      )) : <span style={{ fontSize: 13, color: "#6b7280" }}>No uploaded photos</span>}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>

      {/* Category Modal */}
      {categoryModalOpen ? (
        <AdminModal title={categoryMode === "add" ? "Add Category" : "Edit Category"} onClose={() => setCategoryModalOpen(false)}>
          <form onSubmit={saveCategory} style={{ display: "grid", gap: 10 }}>
            {categoryMode === "edit" ? (
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Category ID</label>
                <input style={inputStyle} value={categoryForm.category_id} readOnly />
              </div>
            ) : null}
            <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Category Type *</label>
                <select
                  style={{ ...inputStyle, fontWeight: 700 }}
                  value={categoryForm.cat_type}
                  onChange={(e) => {
                    const t = e.target.value;
                    const isP = t !== "digital";
                    const lbl = t === "personalized_coloring" ? "coloring" : t === "personalized_story" ? "story" : "";
                    setCategoryForm((s) => ({ ...s, cat_type: t, personalized: isP, label: lbl }));
                  }}
                >
                  <option value="digital">📱 Digital (non-personalized)</option>
                  <option value="personalized_story">📖 Personalized Story Book</option>
                  <option value="personalized_coloring">🎨 Personalized Coloring Book</option>
                </select>
            </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Name *</label>
                <input style={inputStyle} required placeholder="Category Name" value={categoryForm.name} onChange={(e) => setCategoryForm((s) => ({ ...s, name: e.target.value }))} />
              </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div style={{ display: "grid", gap: 6 }}>
                  <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>{categoryForm.cat_type === "digital" ? "Label (badge)" : "Kind"}</label>
                  {categoryForm.cat_type === "digital" ? (
                    <input style={inputStyle} placeholder="e.g. NEW, BESTSELLER" value={categoryForm.label} onChange={(e) => setCategoryForm((s) => ({ ...s, label: e.target.value }))} />
                  ) : (
                    <input style={{ ...inputStyle, background: "#f5f3ff", color: "#6b21a8", fontWeight: 700 }} value={categoryForm.cat_type === "personalized_coloring" ? "🎨 Coloring Book" : "📖 Story Book"} readOnly />
                  )}
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Emoji</label>
                <input style={inputStyle} placeholder="🌟" value={categoryForm.emoji} onChange={(e) => setCategoryForm((s) => ({ ...s, emoji: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Color (#hex)</label>
                <input style={inputStyle} placeholder="#8B5CF6" value={categoryForm.color} onChange={(e) => setCategoryForm((s) => ({ ...s, color: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Gradient CSS</label>
                <input style={inputStyle} placeholder="linear-gradient(...)" value={categoryForm.grad} onChange={(e) => setCategoryForm((s) => ({ ...s, grad: e.target.value }))} />
              </div>
            </div>
            <div style={{ display: "grid", gap: 6 }}>
              <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Tags (comma separated)</label>
              <input style={inputStyle} placeholder="fantasy, adventure" value={categoryForm.tags} onChange={(e) => setCategoryForm((s) => ({ ...s, tags: e.target.value }))} />
            </div>
            <div style={{ display: "grid", gap: 6 }}>
              <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Description</label>
              <textarea style={{ ...inputStyle, minHeight: 70 }} placeholder="Short description..." value={categoryForm.description} onChange={(e) => setCategoryForm((s) => ({ ...s, description: e.target.value }))} />
            </div>
            <div style={{ display: "grid", gap: 6 }}>
              <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Category Image</label>
              <input
                type="file"
                accept="image/*"
                style={inputStyle}
                onChange={(e) => {
                  const file = e.target.files?.[0] || null;
                  setCategoryImageFile(file);
                  if (file) {
                    setCategoryImagePreview(URL.createObjectURL(file));
                  }
                }}
              />
              {(categoryImagePreview || categoryForm.category_image_url) ? (
                <div style={{ display: "grid", gap: 6 }}>
                  <img
                    src={categoryImagePreview || categoryForm.category_image_url}
                    alt="Category preview"
                    style={{ width: "100%", maxWidth: 260, height: 140, objectFit: "cover", borderRadius: 12, border: "1px solid rgba(74,31,184,.15)" }}
                  />
                  {categoryImageFile ? <span style={{ fontSize: 12, color: "#6b5d92" }}>New image selected: {categoryImageFile.name}</span> : null}
                </div>
              ) : null}
            </div>
            <div style={{ display: "flex", gap: 16 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>
                <input type="checkbox" checked={categoryForm.is_active} onChange={(e) => setCategoryForm((s) => ({ ...s, is_active: e.target.checked }))} /> Active
              </label>
            </div>
            <div style={{ display: "flex", gap: 10, marginTop: 6 }}>
              <button type="submit" style={{ ...button, flex: 1, background: `linear-gradient(135deg,${R},${L})`, color: "#fff", padding: "11px 0" }} disabled={saving}>
                {saving ? "Saving..." : categoryMode === "add" ? "Add Category" : "Update Category"}
              </button>
              <button type="button" style={{ ...button, background: "#e5e7eb", color: "#374151", padding: "11px 18px" }} onClick={() => setCategoryModalOpen(false)}>Cancel</button>
            </div>
          </form>
        </AdminModal>
      ) : null}

      {/* Book Modal */}
      {bookModalOpen ? (
        <AdminModal title={bookMode === "add" ? "Add Book" : "Edit Book"} onClose={() => setBookModalOpen(false)}>
          <form onSubmit={saveBook} style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div style={{ display: "grid", gap: 6, gridColumn: "1/-1" }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Book Name *</label>
                <input style={inputStyle} required placeholder="Book Name" value={bookForm.book_name} onChange={(e) => setBookForm((s) => ({ ...s, book_name: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6, gridColumn: "1/-1" }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Description</label>
                <textarea style={{ ...inputStyle, minHeight: 60 }} placeholder="Description..." value={bookForm.description} onChange={(e) => setBookForm((s) => ({ ...s, description: e.target.value }))} />
              </div>
              <div style={{ gridColumn: "1/-1", display: "flex", justifyContent: "flex-end" }}>
                <button type="button" style={{ ...button, background: "#F5F3FF", color: "#5b4f7c", border: "1px solid #DDD6FE", padding: "8px 16px", borderRadius: 10, fontSize: 13, fontWeight: 700 }} onClick={() => { setOptionsMsg(""); setOptionsModalOpen(true); }}>⚙️ Manage Dropdown Options</button>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Book Type</label>
                <select style={inputStyle} value={bookForm.book_type} onChange={(e) => setBookForm((s) => ({ ...s, book_type: e.target.value }))}>
                  {(bookAttributeOptions.book_type || []).map((value) => <option key={value} value={value}>{titleCase(value)}</option>)}
                </select>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Genre</label>
                <select style={inputStyle} value={bookForm.genre} onChange={(e) => setBookForm((s) => ({ ...s, genre: e.target.value }))}>
                  {(bookAttributeOptions.genre || []).map((value) => <option key={value} value={value}>{titleCase(value)}</option>)}
                </select>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Theme</label>
                <select style={inputStyle} value={bookForm.theme} onChange={(e) => setBookForm((s) => ({ ...s, theme: e.target.value }))}>
                  {(bookAttributeOptions.theme || []).map((value) => <option key={value} value={value}>{titleCase(value)}</option>)}
                </select>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Language</label>
                <select style={inputStyle} value={bookForm.language} onChange={(e) => setBookForm((s) => ({ ...s, language: e.target.value }))}>
                  {(bookAttributeOptions.language || []).map((value) => <option key={value} value={value}>{titleCase(value)}</option>)}
                </select>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Category (by ID)</label>
                <select style={inputStyle} value={bookForm.category_id} onChange={(e) => setBookForm((s) => ({ ...s, category_id: e.target.value }))}>
                  <option value="">— None —</option>
                  {filteredBookCategories.map((c) => <option key={c.category_id} value={String(c.category_id)}>{c.emoji} {c.name}</option>)}
                </select>
                <span style={{ fontSize: 11, color: "#8B5CF6" }}>
                  {expectedCategoryType === "digital"
                    ? "Showing digital categories only"
                    : expectedCategoryType === "personalized_coloring"
                      ? "Showing personalized coloring categories only"
                      : "Showing personalized story categories only"}
                </span>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Price (₹)</label>
                <input style={inputStyle} placeholder="99" type="number" min="0" step="0.01" value={bookForm.price} onChange={(e) => setBookForm((s) => ({ ...s, price: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Rating</label>
                <input style={inputStyle} placeholder="4.8" type="number" min="0" max="5" step="0.1" value={bookForm.rating} onChange={(e) => setBookForm((s) => ({ ...s, rating: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Total Pages</label>
                <input style={inputStyle} placeholder="24" type="number" min="1" value={bookForm.total_pages} onChange={(e) => setBookForm((s) => ({ ...s, total_pages: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Total Ratings</label>
                <input style={inputStyle} placeholder="0" type="number" min="0" value={bookForm.total_ratings} onChange={(e) => setBookForm((s) => ({ ...s, total_ratings: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Download Count</label>
                <input style={inputStyle} placeholder="0" type="number" min="0" value={bookForm.download_count} onChange={(e) => setBookForm((s) => ({ ...s, download_count: e.target.value }))} />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Emoji</label>
                <input style={inputStyle} placeholder="📖" value={bookForm.emoji} onChange={(e) => setBookForm((s) => ({ ...s, emoji: e.target.value }))} />
              </div>
              <div style={{ gridColumn: "1/-1" }}>
                <label style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, color: "#5b4f7c", fontSize: 13, cursor: "pointer" }}>
                  <input type="checkbox" checked={bookForm.is_bestseller} onChange={(e) => setBookForm((s) => ({ ...s, is_bestseller: e.target.checked }))} /> Mark as Bestseller ⭐
                </label>
              </div>
            </div>
            {bookMode === "add" ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, borderTop: "1px solid #EFE9FF", paddingTop: 10, marginTop: 4 }}>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Cover Image <span style={{ color: "#b00020" }}>(required)</span></label>
                  <input type="file" accept="image/*" style={inputStyle} onChange={(e) => setBookFiles((s) => ({ ...s, cover_image: e.target.files?.[0] || null }))} />
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Book PDF {isPersonalizedBookType(bookForm.book_type) ? <span style={{ color: "#2563EB" }}>(optional — generated per order)</span> : <span style={{ color: "#b00020" }}>(required)</span>}</label>
                  <input type="file" accept="application/pdf" style={inputStyle} onChange={(e) => setBookFiles((s) => ({ ...s, book_file: e.target.files?.[0] || null }))} />
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Front Image <span style={{ color: "#2563EB" }}>(shown on card)</span></label>
                  <input type="file" accept="image/*" style={inputStyle} onChange={(e) => setBookFiles((s) => ({ ...s, front_image: e.target.files?.[0] || null }))} />
                </div>
                <div style={{ display: "grid", gap: 6 }}>
                  <label style={{ fontWeight: 700, color: "#5b4f7c", fontSize: 13 }}>Back Image (optional)</label>
                  <input type="file" accept="image/*" style={inputStyle} onChange={(e) => setBookFiles((s) => ({ ...s, back_image: e.target.files?.[0] || null }))} />
                </div>
              </div>
            ) : null}
            {bookModalMsg ? (
              <p style={{ margin: 0, marginTop: 4, color: "#b00020", fontWeight: 700 }}>{bookModalMsg}</p>
            ) : null}
            <div style={{ display: "flex", gap: 10, marginTop: 6 }}>
              <button type="submit" style={{ ...button, flex: 1, background: "linear-gradient(135deg,#00B894,#00CEC9)", color: "#fff", padding: "11px 0" }} disabled={saving}>
                {saving ? "Saving..." : bookMode === "add" ? "Add Book" : "Update Book"}
              </button>
              <button type="button" style={{ ...button, background: "#e5e7eb", color: "#374151", padding: "11px 18px" }} onClick={() => setBookModalOpen(false)}>Cancel</button>
            </div>
          </form>
        </AdminModal>
      ) : null}

      {optionsModalOpen ? (
        <AdminModal title="⚙️ Manage Dropdown Options" onClose={() => { setOptionsModalOpen(false); setOptionsMsg(""); setOptionsAddingType(null); setOptionsNewValue(""); }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {optionsMsg && (
              <div style={{ padding: "8px 14px", borderRadius: 10, background: optionsMsg.startsWith("✅") ? "#F0FDF4" : "#FEF2F2", color: optionsMsg.startsWith("✅") ? "#166534" : "#b91c1c", fontWeight: 600, fontSize: 13 }}>{optionsMsg}</div>
            )}
            {[["genre", "🎭 Genre"], ["theme", "🎨 Theme"], ["language", "🌐 Language"]].map(([type, label]) => (
              <div key={type} style={{ background: "#FAFAFA", borderRadius: 14, padding: "16px 18px", border: "1px solid #E5E7EB" }}>
                <div style={{ fontWeight: 700, color: "#374151", fontSize: 14, marginBottom: 10 }}>{label}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
                  {(bookAttributeOptions[type] || []).map((val) => (
                    <span key={val} style={{ display: "inline-flex", alignItems: "center", gap: 5, background: "#EDE9FE", color: "#5b21b6", borderRadius: 999, padding: "4px 12px", fontSize: 13, fontWeight: 600 }}>
                      {titleCase(val)}
                      <button
                        type="button"
                        title={`Remove "${val}"`}
                        disabled={optionsSaving}
                        onClick={() => deleteBookAttributeOption(type, val)}
                        style={{ background: "none", border: "none", color: "#7c3aed", cursor: "pointer", fontWeight: 900, fontSize: 15, lineHeight: 1, padding: "0 2px", opacity: optionsSaving ? 0.4 : 1 }}
                      >×</button>
                    </span>
                  ))}
                  {(bookAttributeOptions[type] || []).length === 0 && (
                    <span style={{ fontSize: 12, color: "#9CA3AF", fontStyle: "italic" }}>No options yet</span>
                  )}
                </div>
                {optionsAddingType === type ? (
                  <div style={{ display: "flex", gap: 6 }}>
                    <input
                      autoFocus
                      style={{ ...inputStyle, flex: 1, padding: "7px 12px", fontSize: 13 }}
                      placeholder={`New ${titleCase(type)} value…`}
                      value={optionsNewValue}
                      onChange={(e) => setOptionsNewValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") { e.preventDefault(); addBookAttributeOption(type, optionsNewValue); setOptionsAddingType(null); }
                        if (e.key === "Escape") { setOptionsAddingType(null); setOptionsNewValue(""); }
                      }}
                    />
                    <button type="button" disabled={optionsSaving || !optionsNewValue.trim()} style={{ ...button, background: "#7c3aed", color: "#fff", padding: "7px 14px", fontSize: 13, opacity: (!optionsNewValue.trim() || optionsSaving) ? 0.5 : 1 }} onClick={() => { addBookAttributeOption(type, optionsNewValue); setOptionsAddingType(null); }}>Add</button>
                    <button type="button" style={{ ...button, background: "#F3F4F6", color: "#6B7280", padding: "7px 12px", fontSize: 13 }} onClick={() => { setOptionsAddingType(null); setOptionsNewValue(""); }}>Cancel</button>
                  </div>
                ) : (
                  <button type="button" disabled={optionsSaving} style={{ ...button, background: "#F5F3FF", color: "#7c3aed", border: "1px dashed #C4B5FD", padding: "6px 14px", fontSize: 13, fontWeight: 700, borderRadius: 10 }} onClick={() => { setOptionsAddingType(type); setOptionsNewValue(""); }}>+ Add option</button>
                )}
              </div>
            ))}
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button type="button" style={{ ...button, background: "#E5E7EB", color: "#374151", padding: "9px 22px" }} onClick={() => { setOptionsModalOpen(false); setOptionsMsg(""); setOptionsAddingType(null); setOptionsNewValue(""); }}>Done</button>
            </div>
          </div>
        </AdminModal>
      ) : null}
    </div>
  );
}
