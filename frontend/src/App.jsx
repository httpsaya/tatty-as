import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate, Routes, Route } from "react-router-dom";
import './App.css';

// ── API Configuration ──
const API_BASE = "http://localhost:8000";
const WS_BASE  = "ws://localhost:8000";

// ── Shared API singleton ──
const api = {
  token: null,
  onUnauthorized: null,

  setToken: (t) => { api.token = t; },
  getToken: () => api.token,

  get: async (path) => {
    if (!api.token) throw new Error("No token");
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { Authorization: `Bearer ${api.token}` },
    });
    if (res.status === 401) { api.onUnauthorized?.(); throw new Error("Unauthorized"); }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  post: async (path, body, needAuth = true) => {
    const headers = { "Content-Type": "application/json" };
    if (needAuth && api.token) headers.Authorization = `Bearer ${api.token}`;
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST", headers, body: JSON.stringify(body),
    });
    if (res.status === 401 && needAuth) { api.onUnauthorized?.(); throw new Error("Unauthorized"); }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  patch: async (path, body) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${api.token}` },
      body: JSON.stringify(body),
    });
    if (res.status === 401) { api.onUnauthorized?.(); throw new Error("Unauthorized"); }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};

// ── Auth Modal ──
function AuthModal({ onAuth }) {
  const [mode, setMode]         = useState("login");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async () => {
    setError(""); setLoading(true);
    try {
      const path = mode === "login" ? "/auth/v1/users/login/" : "/auth/v1/users/register/";
      const body = mode === "login"
        ? { email, password }
        : { email, password, full_name: fullName, username: username || fullName };

      const data = await api.post(path, body, false);
      if (data.access) {
        const authData = { token: data.access, email: data.email || email, id: data.id, schoolName: data.school_name };
        localStorage.setItem("cantine_auth", JSON.stringify(authData));
        api.setToken(data.access);
        onAuth(authData);
      } else {
        setError(data.detail || "Ошибка");
      }
    } catch {
      setError("Не удалось подключиться к серверу");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-modal">
      <div className="auth-card">
        <h2>CantineOS</h2>
        <div className="subtitle">{mode === "login" ? "Войдите в аккаунт" : "Создайте аккаунт"}</div>
        {error && <div className="error-message">{error}</div>}
        {mode === "register" && (
          <>
            <input className="auth-input" placeholder="Полное имя *" value={fullName} onChange={e => setFullName(e.target.value)} />
            <input className="auth-input" placeholder="Имя пользователя" value={username} onChange={e => setUsername(e.target.value)} />
          </>
        )}
        <input className="auth-input" placeholder="Email *" value={email} onChange={e => setEmail(e.target.value)} onKeyPress={e => e.key === "Enter" && handleSubmit()} />
        <input className="auth-input" placeholder="Пароль *" type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyPress={e => e.key === "Enter" && handleSubmit()} />
        <button className="auth-btn" onClick={handleSubmit} disabled={loading}>{loading ? "..." : mode === "login" ? "Войти" : "Зарегистрироваться"}</button>
        <div className="auth-switch">
          {mode === "login" ? "Нет аккаунта? " : "Уже есть аккаунт? "}
          <span onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
            {mode === "login" ? "Регистрация" : "Войти"}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Main Canteen Page ──
function CanteenApp() {
  const [auth, setAuth]               = useState(null);
  const [menu, setMenu]               = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedDish, setSelectedDish] = useState(null);
  const [comments, setComments]       = useState({});
  const [commentText, setCommentText] = useState("");
  const [reactions, setReactions]     = useState({});
  const [myReactions, setMyReactions] = useState({});
  const [loading, setLoading]         = useState(true);
  const [sseConnected, setSseConnected] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [toast, setToast]             = useState(null);
  const [canteenId, setCanteenId]     = useState(null);

  const navigate = useNavigate();
  const wsRef  = useRef(null);
  const sseRef = useRef(null);

  // ── Toast ──
  const showToast = useCallback((message, icon = "✅") => {
    setToast({ message, icon });
    setTimeout(() => setToast(null), 3000);
  }, []);

  // ── Session restore + unauthorized handler ──
  useEffect(() => {
    api.onUnauthorized = () => {
      localStorage.removeItem("cantine_auth");
      api.setToken(null);
      setAuth(null);
      showToast("Сессия истекла, войдите снова", "🔐");
    };
    const saved = localStorage.getItem("cantine_auth");
    if (saved) {
      try {
        const authData = JSON.parse(saved);
        if (authData.token) { api.setToken(authData.token); setAuth(authData); }
      } catch { localStorage.removeItem("cantine_auth"); }
    }
  }, [showToast]);

  // ── CSS injection ──
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  // ── Logout ──
  const handleLogout = () => {
    localStorage.removeItem("cantine_auth");
    api.setToken(null);
    sseRef.current?.close();
    wsRef.current?.close();
    setAuth(null);
    setSelectedDish(null);
    showToast("Вы вышли", "👋");
  };

  // ── Load notifications ──
  const loadNotifications = useCallback(async () => {
    if (!auth) return;
    try {
      const list  = await api.get("/notification/list/");
      const items = Array.isArray(list) ? list : list.results || [];
      setNotifications(items.map(n => ({
        id: n.id, icon: n.type?.[0]?.toUpperCase() || "📢",
        text: n.message || n.title,
        time: new Date(n.created_at).toLocaleTimeString(),
        unread: !n.is_read,
      })));
      const count = await api.get("/notification/count/");
      setUnreadCount(count.unread_count || 0);
    } catch (err) { console.error("Notif error:", err); }
  }, [auth]);

  // ── Load menu ──
  useEffect(() => {
  if (!auth) return;
  setLoading(true);
  
  Promise.all([api.get("/canteen/dishes/"), api.get("/canteen/daylymenu/")])
    .then(([dishesData, menuData]) => {
      // 1. Обработка списка блюд для реакций
      const dishesList = Array.isArray(dishesData) ? dishesData : dishesData.results || [];
      const reactionsInit = {};
      dishesList.forEach(d => { reactionsInit[d.id] = { "👍": 0, "😐": 0, "👎": 0 }; });
      setReactions(reactionsInit);

      // 2. Обработка Daily Menu (смотрим, пришел массив или объект)
      let currentMenu = null;
      if (Array.isArray(menuData)) {
        currentMenu = menuData[0];
      } else if (menuData && typeof menuData === 'object' && !menuData.results) {
        currentMenu = menuData; // Если пришел сразу объект (как на скриншоте)
      } else if (menuData.results && menuData.results.length > 0) {
        currentMenu = menuData.results[0];
      }

      if (currentMenu) {
        setCanteenId(currentMenu.canteen_id || currentMenu.canteen);
        
        // Группировка блюд (используем поле dishes_details, если оно есть)
        const dishesToMap = currentMenu.dishes_details || currentMenu.dishes || [];
        const grouped = {};
        
        dishesToMap.forEach(dish => {
          const cat = dish.category_name || dish.category || "Блюда";
          if (!grouped[cat]) grouped[cat] = [];
          grouped[cat].push(dish);
        });
        
        
        setMenu(Object.entries(grouped).map(([category, items]) => ({ category, items })));
        const reactionPromises = dishesToMap.map(dish =>
          api.get(`/canteen/reactions/?dish_id=${dish.id}`)
          .then(data => ({ dishId: dish.id, data }))
          .catch(() => null)
        );
        
        Promise.all(reactionPromises).then(results => {
          const counts = {};
          const mine   = {};
          results.forEach(r => {
            if (r) {
              counts[r.dishId] = r.data.counts;       // ← без хардкода нулей
              mine[r.dishId]   = r.data.my_reaction;
            }
          });
          setReactions(counts);
          setMyReactions(mine);
        });
      }
      loadNotifications();
    })
    .catch((err) => {
      console.error(err);
      showToast("Ошибка загрузки меню", "⚠️");
    })
    .finally(() => setLoading(false));
}, [auth, loadNotifications, showToast]);

  // ── SSE ──
  useEffect(() => {
    if (!auth || !canteenId) return;
    const url = `${API_BASE}/notification/stream/?canteen_id=${canteenId}&token=${api.getToken()}`;
    const sse = new EventSource(url);
    sseRef.current = sse;
    sse.onopen    = () => setSseConnected(true);
    sse.onerror   = () => setSseConnected(false);
    sse.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.event === "daily_menu_created" || data.event === "post.message") {
          loadNotifications();
          showToast(data.message, "🍴");
        }
      } catch {}
    };
    return () => { sse.close(); setSseConnected(false); };
  }, [auth, canteenId, loadNotifications, showToast]);

  // ── WebSocket for comments ──
  useEffect(() => {
    if (!selectedDish?.id) {
      wsRef.current?.close(); wsRef.current = null; setWsConnected(false);
      return;
    }
    if (!auth) return;
    const token = api.getToken();
    if (!token) return;

    const ws = new WebSocket(`${WS_BASE}/ws/comments/dish/${selectedDish.id}/?token=${token}`);
    wsRef.current = ws;
    ws.onopen  = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "comment.history") {
          setComments(prev => ({ ...prev, [selectedDish.id]: msg.comments || [] }));
        }
        if (msg.type === "comment.new") {
          setComments(prev => ({
            ...prev,
            [selectedDish.id]: [...(prev[selectedDish.id] || []), {
              id: msg.comment_id || Date.now(), author: msg.author || "User",
              text: msg.text, time: new Date().toLocaleTimeString(),
            }],
          }));
          showToast("Новый комментарий", "💬");
        }
      } catch {}
    };
    return () => { wsRef.current?.close(); wsRef.current = null; setWsConnected(false); };
  }, [auth, selectedDish, showToast]);

  const sendComment = () => {
    if (!commentText.trim() || !selectedDish?.id) return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      showToast("Нет подключения к чату", "⚠️"); return;
    }
    wsRef.current.send(JSON.stringify({ text: commentText }));
    setCommentText("");
  };

  const handleReaction = async (dishId, emoji) => {
  try {
    const data = await api.post("/canteen/reactions/", { dish_id: dishId, emoji });
    setReactions(r => ({ ...r, [dishId]: data.counts }));        // ← без нулей
    setMyReactions(r => ({ ...r, [dishId]: data.my_reaction }));
  } catch {
    showToast("Ошибка реакции", "⚠️");
  }
};

  const markAllRead = () => {
    api.post("/notification/read/", {})
      .then(() => { setNotifications(n => n.map(n => ({ ...n, unread: false }))); setUnreadCount(0); showToast("Все прочитаны", "✅"); })
      .catch(() => showToast("Ошибка", "⚠️"));
  };

  const dishComments = selectedDish?.id ? comments[selectedDish.id] || [] : [];

  if (!auth) {
    return <AuthModal onAuth={(authData) => { api.setToken(authData.token); setAuth(authData); }} />;
  }

  return (
    <div className="app">
      <nav className="nav">
        <div className="nav-container">
          <div className="logo"><span className="logo-text">🍽 CantineOS</span></div>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <div className="status-badge"><div className={`status-dot ${sseConnected ? "online" : "offline"}`} /><span>SSE</span></div>
            <div className="status-badge"><div className={`status-dot ${wsConnected ? "online" : "offline"}`} /><span>WS</span></div>
            <div className="user-menu" onClick={handleLogout}>
              <span>{auth.email?.split("@")[0]}</span>
              {unreadCount > 0 && <span style={{ color: "var(--accent-primary)" }}>{unreadCount}</span>}
            </div>
            <button className="user-menu2" onClick={() => navigate("/profile")}>Профиль</button>
          </div>
          <button className="user-menu2" onClick={() => navigate("/create-menu")}>Создать меню</button>
        </div>
      </nav>

      <main className="main-container">
        <div className="hero">
          <div className="hero-badge">{auth?.schoolName ? auth.schoolName.toUpperCase() : "ШКОЛА НЕ УКАЗАНА"}</div>
          <h1>Меню на <span>сегодня</span></h1>
          <div className="hero-date">{new Date().toLocaleDateString("ru-RU", { weekday: "long", year: "numeric", month: "long", day: "numeric" }).toUpperCase()}</div>
        </div>

        <div className="content-grid">
          <div className="menu-section">
            <div className="section-header"><h2>ДНЕВНОЕ МЕНЮ</h2></div>
            {loading && <div className="loading-state">Загрузка меню...</div>}
            {!loading && menu.length === 0 && <div className="empty-state">Меню на сегодня не добавлено</div>}
            {menu.map(cat => (
              <div key={cat.category} className="category">
                <div className="category-title">{cat.category}</div>
                {cat.items.map(dish => (
                  <div key={dish.id} className={`dish-card ${selectedDish?.id === dish.id ? "selected" : ""}`} onClick={() => setSelectedDish(dish)}>
                    <div className="dish-emoji">{dish.emoji || "🍽"}</div>
                    <div className="dish-info">
                      <div className="dish-name">{dish.name}</div>
                      <div className="dish-description">{dish.description || ""}</div>
                      <div className="dish-reactions" onClick={e => e.stopPropagation()}>
                        {["👍", "😐", "👎"].map(emoji => (
                          <button key={emoji} className={`reaction-btn ${myReactions[dish.id] === emoji ? "active" : ""}`} onClick={() => handleReaction(dish.id, emoji)}>
                            <span>{emoji}</span> <span>{reactions[dish.id]?.[emoji] || 0}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="dish-meta"><div className="dish-price">{dish.price} ₸</div></div>
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div className="right-panel">
            <div className="panel">
              <div className="panel-header"><h3>УВЕДОМЛЕНИЯ {unreadCount > 0 && `(${unreadCount})`}</h3><span className="panel-action" onClick={markAllRead}>ПРОЧИТАТЬ ВСЕ</span></div>
              <div className="notifications-list">
                {notifications.length === 0 && <div className="empty-state">Нет уведомлений</div>}
                {notifications.map(n => (
                  <div key={n.id} className={`notification-item ${n.unread ? "unread" : ""}`}>
                    <div className="notification-icon">{n.icon}</div>
                    <div className="notification-content"><div className="notification-text">{n.text}</div><div className="notification-time">{n.time}</div></div>
                    {n.unread && <div className="notification-dot" />}
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <h3>КОММЕНТАРИИ{selectedDish && <span style={{ color: "var(--accent-primary)", marginLeft: "8px" }}>· {selectedDish.name}</span>}</h3>
                {selectedDish && <div className={`status-dot ${wsConnected ? "online" : "offline"}`} style={{ width: "8px", height: "8px" }} />}
              </div>
              <div className="comments-list">
                {!selectedDish && <div className="empty-state">Выберите блюдо</div>}
                {selectedDish && dishComments.length === 0 && <div className="empty-state">Нет комментариев</div>}
                {dishComments.map((c, i) => (
                  <div key={c.id || i} className="comment-item">
                    <div className="comment-header">
                      <div className="comment-avatar">{(c.author?.[0] || "?").toUpperCase()}</div>
                      <div className="comment-author">{c.author || "User"}</div>
                      <div className="comment-time">{c.time}</div>
                    </div>
                    <div className="comment-text">{c.text}</div>
                  </div>
                ))}
              </div>
              <div className="comment-form">
                <input className="comment-input" placeholder={selectedDish ? "Комментарий..." : "Выберите блюдо..."} value={commentText} onChange={e => setCommentText(e.target.value)} onKeyPress={e => e.key === "Enter" && sendComment()} disabled={!selectedDish || !wsConnected} />
                <button className="send-btn" onClick={sendComment} disabled={!selectedDish || !wsConnected}>→</button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {toast && <div className="toast"><span>{toast.icon}</span><span>{toast.message}</span></div>}
    </div>
  );
}

// ── Profile Page ──
const GENDER_LABELS = { male: "Мужской", female: "Женский", other: "Другой" };
const GENDER_ICONS  = { male: "♂", female: "♀", other: "⚥" };

function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile]             = useState(null);
  const [schools, setSchools]             = useState([]);
  const [loading, setLoading]             = useState(true);
  const [saving, setSaving]               = useState(false);
  const [toast, setToast]                 = useState(null);
  const [editMode, setEditMode]           = useState(false);
  const [form, setForm]                   = useState({});
  const [interestInput, setInterestInput] = useState("");

  const showToast = useCallback((message, icon = "✅") => {
    setToast({ message, icon });
    setTimeout(() => setToast(null), 3000);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("cantine_auth");
    if (saved) {
      try {
        const authData = JSON.parse(saved);
        if (authData.token) api.setToken(authData.token);
      } catch {}
    }
    api.onUnauthorized = () => { localStorage.removeItem("cantine_auth"); navigate("/"); };
  }, [navigate]);

  useEffect(() => {
    setLoading(true);
    api.get("/auth/v1/users/my-profile/")
      .then(data => {
        setProfile(data.profile);
        setSchools(data.available_schools || []);
        setForm({
          display_name: data.profile.display_name || "",
          bio:          data.profile.bio          || "",
          location:     data.profile.location     || "",
          gender:       data.profile.gender       || "other",
          interests:    data.profile.interests    || [],
          avatar:       data.profile.avatar       || "",
          school_id:    data.profile.school_id    || "",
        });
      })
      .catch(() => showToast("Ошибка загрузки профиля", "⚠️"))
      .finally(() => setLoading(false));
  }, [showToast]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...form };
      if (!payload.school_id) delete payload.school_id;
      const updated = await api.patch("/auth/v1/users/my-profile/", payload);
      setProfile(updated);
      setEditMode(false);
      showToast("Профиль сохранён", "✅");
    } catch {
      showToast("Ошибка сохранения", "⚠️");
    } finally {
      setSaving(false);
    }
  };

  const addInterest = () => {
    const val = interestInput.trim();
    if (!val || form.interests.includes(val)) return;
    setForm(f => ({ ...f, interests: [...f.interests, val] }));
    setInterestInput("");
  };

  const removeInterest = (tag) => setForm(f => ({ ...f, interests: f.interests.filter(i => i !== tag) }));

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;700&family=Onest:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
          --bg:#0d0d0f; --bg2:#141416; --bg3:#1c1c1f;
          --border:#2a2a2e; --border-bright:#3d3d44;
          --gold:#f0a500; --gold2:#ffcc44;
          --text:#f0f0f0; --muted:#888; --danger:#e05252; --green:#4caf7d;
        }
        .profile-root { min-height:100vh; background:var(--bg); font-family:'Onest',sans-serif; color:var(--text); }
        .pnav { display:flex; align-items:center; justify-content:space-between; padding:18px 32px; border-bottom:1px solid var(--border); background:var(--bg2); position:sticky; top:0; z-index:10; }
        .pnav-logo { font-family:'Unbounded',sans-serif; font-size:15px; color:var(--gold); cursor:pointer; }
        .pnav-back { background:none; border:1px solid var(--border); color:var(--muted); padding:8px 16px; border-radius:8px; font-family:'Onest',sans-serif; font-size:13px; cursor:pointer; transition:all .18s; }
        .pnav-back:hover { border-color:var(--gold); color:var(--gold); }
        .profile-wrap { max-width:860px; margin:0 auto; padding:40px 24px 80px; }
        .profile-header { background:var(--bg2); border:1px solid var(--border); border-radius:16px; padding:32px; display:flex; align-items:center; gap:28px; margin-bottom:24px; position:relative; overflow:hidden; }
        .profile-header::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,var(--gold),var(--gold2),transparent); }
        .avatar-ring { width:80px; height:80px; border-radius:50%; border:2px solid var(--gold); display:flex; align-items:center; justify-content:center; font-family:'Unbounded',sans-serif; font-size:28px; font-weight:700; color:var(--gold); background:var(--bg3); flex-shrink:0; overflow:hidden; }
        .avatar-ring img { width:100%; height:100%; object-fit:cover; border-radius:50%; }
        .header-info { flex:1; min-width:0; }
        .header-name { font-family:'Unbounded',sans-serif; font-size:20px; font-weight:600; margin-bottom:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .header-email { font-size:13px; color:var(--muted); margin-bottom:10px; }
        .header-badges { display:flex; gap:8px; flex-wrap:wrap; }
        .badge { font-size:11px; padding:4px 10px; border-radius:20px; border:1px solid var(--border); color:var(--muted); background:var(--bg3); display:flex; align-items:center; gap:4px; }
        .badge.gold { border-color:var(--gold); color:var(--gold); background:rgba(240,165,0,.08); }
        .badge.green { border-color:var(--green); color:var(--green); background:rgba(76,175,125,.08); }
        .edit-btn { background:none; border:1px solid var(--border-bright); color:var(--text); padding:10px 20px; border-radius:10px; font-family:'Onest',sans-serif; font-size:13px; cursor:pointer; transition:all .18s; white-space:nowrap; flex-shrink:0; }
        .edit-btn:hover { border-color:var(--gold); color:var(--gold); }
        .edit-btn.active { border-color:var(--danger); color:var(--danger); }
        .psection { background:var(--bg2); border:1px solid var(--border); border-radius:16px; padding:28px; margin-bottom:20px; }
        .psection-title { font-family:'Unbounded',sans-serif; font-size:11px; letter-spacing:1.5px; color:var(--gold); text-transform:uppercase; margin-bottom:20px; display:flex; align-items:center; gap:8px; }
        .psection-title::after { content:''; flex:1; height:1px; background:var(--border); }
        .pfield { margin-bottom:18px; }
        .pfield:last-child { margin-bottom:0; }
        .pfield-label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }
        .pfield-value { font-size:15px; color:var(--text); line-height:1.5; }
        .pfield-value.muted { color:var(--muted); font-style:italic; }
        .pinput { width:100%; background:var(--bg3); border:1px solid var(--border); border-radius:10px; padding:11px 14px; color:var(--text); font-family:'Onest',sans-serif; font-size:14px; outline:none; transition:border-color .18s; }
        .pinput:focus { border-color:var(--gold); }
        .pinput::placeholder { color:var(--muted); }
        textarea.pinput { resize:vertical; min-height:80px; }
        select.pinput { cursor:pointer; appearance:none; }
        .two-col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
        @media(max-width:580px){.two-col{grid-template-columns:1fr;}}
        .gender-grid { display:flex; gap:10px; }
        .gender-opt { flex:1; padding:10px; border:1px solid var(--border); border-radius:10px; text-align:center; cursor:pointer; transition:all .18s; background:var(--bg3); font-size:13px; color:var(--muted); }
        .gender-opt .gicon { font-size:18px; display:block; margin-bottom:4px; }
        .gender-opt.sel { border-color:var(--gold); color:var(--gold); background:rgba(240,165,0,.08); }
        .gender-opt:hover:not(.sel) { border-color:var(--border-bright); color:var(--text); }
        .tags { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
        .tag { padding:5px 12px; border-radius:20px; border:1px solid var(--border); font-size:12px; color:var(--text); background:var(--bg3); display:flex; align-items:center; gap:6px; }
        .tag-remove { background:none; border:none; color:var(--muted); cursor:pointer; font-size:14px; line-height:1; padding:0; transition:color .15s; }
        .tag-remove:hover { color:var(--danger); }
        .tag-input-row { display:flex; gap:8px; }
        .tag-add-btn { background:var(--bg3); border:1px solid var(--border); color:var(--gold); padding:0 16px; border-radius:10px; cursor:pointer; font-size:18px; transition:all .15s; flex-shrink:0; }
        .tag-add-btn:hover { border-color:var(--gold); background:rgba(240,165,0,.08); }
        .save-row { display:flex; gap:12px; margin-top:24px; justify-content:flex-end; }
        .btn-cancel { background:none; border:1px solid var(--border); color:var(--muted); padding:11px 24px; border-radius:10px; font-family:'Onest',sans-serif; font-size:14px; cursor:pointer; transition:all .18s; }
        .btn-cancel:hover { border-color:var(--border-bright); color:var(--text); }
        .btn-save { background:var(--gold); border:none; color:#000; padding:11px 28px; border-radius:10px; font-family:'Unbounded',sans-serif; font-size:12px; font-weight:600; cursor:pointer; transition:all .18s; letter-spacing:.5px; }
        .btn-save:hover { background:var(--gold2); }
        .btn-save:disabled { opacity:.5; cursor:not-allowed; }
        .pskeleton { background:linear-gradient(90deg,var(--bg2) 25%,var(--bg3) 50%,var(--bg2) 75%); background-size:200% 100%; animation:shimmer2 1.4s infinite; border-radius:8px; height:18px; }
        @keyframes shimmer2 { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
        .toast-p { position:fixed; bottom:28px; left:50%; transform:translateX(-50%); background:var(--bg3); border:1px solid var(--border-bright); border-radius:12px; padding:12px 20px; display:flex; align-items:center; gap:10px; font-size:14px; z-index:100; animation:fadeUp2 .3s ease; white-space:nowrap; }
        @keyframes fadeUp2 { from{opacity:0;transform:translateX(-50%) translateY(10px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }
      `}</style>

      <div className="profile-root">
        <nav className="pnav">
          <div className="pnav-logo" onClick={() => navigate("/")}>🍽 CantineOS</div>
          <button className="pnav-back" onClick={() => navigate("/")}>← Вернуться в меню</button>
        </nav>

        <div className="profile-wrap">
          {loading ? (
            <div className="psection">
              <div className="pskeleton" style={{ width: "40%", marginBottom: 16 }} />
              <div className="pskeleton" style={{ width: "60%", marginBottom: 12 }} />
              <div className="pskeleton" style={{ width: "30%" }} />
            </div>
          ) : profile ? (
            <>
              <div className="profile-header">
                <div className="avatar-ring">
                  {profile.avatar
                    ? <img src={profile.avatar} alt="avatar" />
                    : (profile.display_name || profile.full_name || profile.email || "?")[0].toUpperCase()
                  }
                </div>
                <div className="header-info">
                  <div className="header-name">{profile.display_name || profile.full_name || "Без имени"}</div>
                  <div className="header-email">{profile.email}</div>
                  <div className="header-badges">
                    {profile.school_name && <span className="badge gold">🏫 {profile.school_name}</span>}
                    {profile.is_verified && <span className="badge green">✓ Подтверждён</span>}
                    {profile.gender && profile.gender !== "other" && <span className="badge">{GENDER_ICONS[profile.gender]} {GENDER_LABELS[profile.gender]}</span>}
                    {profile.location && <span className="badge">📍 {profile.location}</span>}
                  </div>
                </div>
                <button className={`edit-btn ${editMode ? "active" : ""}`} onClick={() => setEditMode(e => !e)}>
                  {editMode ? "✕ Отмена" : "✎ Редактировать"}
                </button>
              </div>

              {!editMode && (
                <>
                  <div className="psection">
                    <div className="psection-title">Основная информация</div>
                    <div className="two-col">
                      <div className="pfield"><div className="pfield-label">Отображаемое имя</div><div className={`pfield-value ${!profile.display_name ? "muted" : ""}`}>{profile.display_name || "Не указано"}</div></div>
                      <div className="pfield"><div className="pfield-label">Полное имя</div><div className="pfield-value">{profile.full_name || "—"}</div></div>
                      <div className="pfield"><div className="pfield-label">Email</div><div className="pfield-value">{profile.email}</div></div>
                      <div className="pfield"><div className="pfield-label">Местоположение</div><div className={`pfield-value ${!profile.location ? "muted" : ""}`}>{profile.location || "Не указано"}</div></div>
                    </div>
                    {profile.bio && <div className="pfield" style={{ marginTop: 16 }}><div className="pfield-label">О себе</div><div className="pfield-value">{profile.bio}</div></div>}
                  </div>
                  {profile.interests?.length > 0 && (
                    <div className="psection">
                      <div className="psection-title">Интересы</div>
                      <div className="tags">{profile.interests.map(t => <span key={t} className="tag">{t}</span>)}</div>
                    </div>
                  )}
                  <div className="psection">
                    <div className="psection-title">Школа</div>
                    {profile.school_name
                      ? <div className="pfield-value" style={{ display:"flex", alignItems:"center", gap:10 }}><span style={{ color:"var(--gold)", fontSize:20 }}>🏫</span>{profile.school_name}</div>
                      : <span className="pfield-value muted">Школа не привязана</span>
                    }
                  </div>
                </>
              )}

              {editMode && (
                <>
                  <div className="psection">
                    <div className="psection-title">Основная информация</div>
                    <div className="two-col">
                      <div className="pfield"><div className="pfield-label">Отображаемое имя</div><input className="pinput" placeholder="Как вас называть?" value={form.display_name} onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))} /></div>
                      <div className="pfield"><div className="pfield-label">Местоположение</div><input className="pinput" placeholder="Город, страна" value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} /></div>
                    </div>
                    <div className="pfield"><div className="pfield-label">Ссылка на аватар</div><input className="pinput" placeholder="https://..." value={form.avatar} onChange={e => setForm(f => ({ ...f, avatar: e.target.value }))} /></div>
                    <div className="pfield"><div className="pfield-label">О себе</div><textarea className="pinput" placeholder="Расскажите немного о себе..." value={form.bio} onChange={e => setForm(f => ({ ...f, bio: e.target.value }))} /></div>
                  </div>

                  <div className="psection">
                    <div className="psection-title">Пол</div>
                    <div className="gender-grid">
                      {["male","female","other"].map(g => (
                        <div key={g} className={`gender-opt ${form.gender === g ? "sel" : ""}`} onClick={() => setForm(f => ({ ...f, gender: g }))}>
                          <span className="gicon">{GENDER_ICONS[g]}</span>{GENDER_LABELS[g]}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="psection">
                    <div className="psection-title">Интересы</div>
                    {form.interests.length > 0 && (
                      <div className="tags">
                        {form.interests.map(t => (
                          <span key={t} className="tag">{t}<button className="tag-remove" onClick={() => removeInterest(t)}>×</button></span>
                        ))}
                      </div>
                    )}
                    <div className="tag-input-row">
                      <input className="pinput" placeholder="Добавить интерес..." value={interestInput} onChange={e => setInterestInput(e.target.value)} onKeyDown={e => e.key === "Enter" && addInterest()} />
                      <button className="tag-add-btn" onClick={addInterest}>+</button>
                    </div>
                  </div>

                  <div className="psection">
                    <div className="psection-title">Школа</div>
                    <div className="pfield">
                      <div className="pfield-label">Выберите школу</div>
                      <select className="pinput" value={form.school_id} onChange={e => setForm(f => ({ ...f, school_id: Number(e.target.value) }))}>
                        <option value="">— Не выбрано —</option>
                        {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                      </select>
                    </div>
                  </div>

                  <div className="save-row">
                    <button className="btn-cancel" onClick={() => setEditMode(false)}>Отмена</button>
                    <button className="btn-save" onClick={handleSave} disabled={saving}>{saving ? "СОХРАНЕНИЕ..." : "СОХРАНИТЬ"}</button>
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="psection" style={{ textAlign:"center", color:"var(--muted)", padding:60 }}>Профиль не найден</div>
          )}
        </div>

        {toast && <div className="toast-p"><span>{toast.icon}</span><span>{toast.message}</span></div>}
      </div>
    </>
  );
}

export function CreateMenuPage({ api, showToast }) {
  const [canteens, setCanteens] = useState([]);
  const [allDishes, setAllDishes] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedCanteen, setSelectedCanteen] = useState("");
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedDishes, setSelectedDishes] = useState([]);

  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.get("/canteen/canteens/"), 
      api.get("/canteen/dishes/")
    ])
      .then(([canteensData, dishesData]) => {
        setCanteens(Array.isArray(canteensData) ? canteensData : canteensData.results || []);
        setAllDishes(Array.isArray(dishesData) ? dishesData : dishesData.results || []);
        setLoading(false);
      })
      .catch(() => showToast("Ошибка загрузки данных", "⚠️"));
  }, [api, showToast]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCanteen || selectedDishes.length === 0) {
      showToast("Выберите столовую и блюда", "⚠️");
      return;
    }

    try {
      const payload = {
        canteen: parseInt(selectedCanteen),
        date: selectedDate,
        dishes: selectedDishes 
      };
      await api.post("/canteen/daylymenu/", payload);
      showToast("Меню опубликовано!", "✅");
      navigate("/"); 
    } catch (err) {
      showToast("Ошибка публикации", "❌");
    }
  };

  const toggleDish = (id) => {
    setSelectedDishes(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  return (
    <><style>{`
        @import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;700&family=Onest:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
          --bg:#0d0d0f; --bg2:#141416; --bg3:#1c1c1f;
          --border:#2a2a2e; --border-bright:#3d3d44;
          --gold:#f0a500; --gold2:#ffcc44;
          --text:#f0f0f0; --muted:#888; --danger:#e05252; --green:#4caf7d;
        }
        .profile-root { min-height:100vh; background:var(--bg); font-family:'Onest',sans-serif; color:var(--text); }
        .pnav { display:flex; align-items:center; justify-content:space-between; padding:18px 32px; border-bottom:1px solid var(--border); background:var(--bg2); position:sticky; top:0; z-index:10; }
        .pnav-logo { font-family:'Unbounded',sans-serif; font-size:15px; color:var(--gold); cursor:pointer; }
        .pnav-back { background:none; border:1px solid var(--border); color:var(--muted); padding:8px 16px; border-radius:8px; font-family:'Onest',sans-serif; font-size:13px; cursor:pointer; transition:all .18s; }
        .pnav-back:hover { border-color:var(--gold); color:var(--gold); }
        .profile-wrap { max-width:860px; margin:0 auto; padding:40px 24px 80px; }
        .profile-header { background:var(--bg2); border:1px solid var(--border); border-radius:16px; padding:32px; display:flex; align-items:center; gap:28px; margin-bottom:24px; position:relative; overflow:hidden; }
        .profile-header::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,var(--gold),var(--gold2),transparent); }
        .avatar-ring { width:80px; height:80px; border-radius:50%; border:2px solid var(--gold); display:flex; align-items:center; justify-content:center; font-family:'Unbounded',sans-serif; font-size:28px; font-weight:700; color:var(--gold); background:var(--bg3); flex-shrink:0; overflow:hidden; }
        .avatar-ring img { width:100%; height:100%; object-fit:cover; border-radius:50%; }
        .header-info { flex:1; min-width:0; }
        .header-name { font-family:'Unbounded',sans-serif; font-size:20px; font-weight:600; margin-bottom:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .header-email { font-size:13px; color:var(--muted); margin-bottom:10px; }
        .header-badges { display:flex; gap:8px; flex-wrap:wrap; }
        .badge { font-size:11px; padding:4px 10px; border-radius:20px; border:1px solid var(--border); color:var(--muted); background:var(--bg3); display:flex; align-items:center; gap:4px; }
        .badge.gold { border-color:var(--gold); color:var(--gold); background:rgba(240,165,0,.08); }
        .badge.green { border-color:var(--green); color:var(--green); background:rgba(76,175,125,.08); }
        .edit-btn { background:none; border:1px solid var(--border-bright); color:var(--text); padding:10px 20px; border-radius:10px; font-family:'Onest',sans-serif; font-size:13px; cursor:pointer; transition:all .18s; white-space:nowrap; flex-shrink:0; }
        .edit-btn:hover { border-color:var(--gold); color:var(--gold); }
        .edit-btn.active { border-color:var(--danger); color:var(--danger); }
        .psection { background:var(--bg2); border:1px solid var(--border); border-radius:16px; padding:28px; margin-bottom:20px; }
        .psection-title { font-family:'Unbounded',sans-serif; font-size:11px; letter-spacing:1.5px; color:var(--gold); text-transform:uppercase; margin-bottom:20px; display:flex; align-items:center; gap:8px; }
        .psection-title::after { content:''; flex:1; height:1px; background:var(--border); }
        .pfield { margin-bottom:18px; }
        .pfield:last-child { margin-bottom:0; }
        .pfield-label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }
        .pfield-value { font-size:15px; color:var(--text); line-height:1.5; }
        .pfield-value.muted { color:var(--muted); font-style:italic; }
        .pinput { width:100%; background:var(--bg3); border:1px solid var(--border); border-radius:10px; padding:11px 14px; color:var(--text); font-family:'Onest',sans-serif; font-size:14px; outline:none; transition:border-color .18s; }
        .pinput:focus { border-color:var(--gold); }
        .pinput::placeholder { color:var(--muted); }
        textarea.pinput { resize:vertical; min-height:80px; }
        select.pinput { cursor:pointer; appearance:none; }
        .two-col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
        @media(max-width:580px){.two-col{grid-template-columns:1fr;}}
        .gender-grid { display:flex; gap:10px; }
        .gender-opt { flex:1; padding:10px; border:1px solid var(--border); border-radius:10px; text-align:center; cursor:pointer; transition:all .18s; background:var(--bg3); font-size:13px; color:var(--muted); }
        .gender-opt .gicon { font-size:18px; display:block; margin-bottom:4px; }
        .gender-opt.sel { border-color:var(--gold); color:var(--gold); background:rgba(240,165,0,.08); }
        .gender-opt:hover:not(.sel) { border-color:var(--border-bright); color:var(--text); }
        .tags { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
        .tag { padding:5px 12px; border-radius:20px; border:1px solid var(--border); font-size:12px; color:var(--text); background:var(--bg3); display:flex; align-items:center; gap:6px; }
        .tag-remove { background:none; border:none; color:var(--muted); cursor:pointer; font-size:14px; line-height:1; padding:0; transition:color .15s; }
        .tag-remove:hover { color:var(--danger); }
        .tag-input-row { display:flex; gap:8px; }
        .tag-add-btn { background:var(--bg3); border:1px solid var(--border); color:var(--gold); padding:0 16px; border-radius:10px; cursor:pointer; font-size:18px; transition:all .15s; flex-shrink:0; }
        .tag-add-btn:hover { border-color:var(--gold); background:rgba(240,165,0,.08); }
        .save-row { display:flex; gap:12px; margin-top:24px; justify-content:flex-end; }
        .btn-cancel { background:none; border:1px solid var(--border); color:var(--muted); padding:11px 24px; border-radius:10px; font-family:'Onest',sans-serif; font-size:14px; cursor:pointer; transition:all .18s; }
        .btn-cancel:hover { border-color:var(--border-bright); color:var(--text); }
        .btn-save { background:var(--gold); border:none; color:#000; padding:11px 28px; border-radius:10px; font-family:'Unbounded',sans-serif; font-size:12px; font-weight:600; cursor:pointer; transition:all .18s; letter-spacing:.5px; }
        .btn-save:hover { background:var(--gold2); }
        .btn-save:disabled { opacity:.5; cursor:not-allowed; }
        .pskeleton { background:linear-gradient(90deg,var(--bg2) 25%,var(--bg3) 50%,var(--bg2) 75%); background-size:200% 100%; animation:shimmer2 1.4s infinite; border-radius:8px; height:18px; }
        @keyframes shimmer2 { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
        .toast-p { position:fixed; bottom:28px; left:50%; transform:translateX(-50%); background:var(--bg3); border:1px solid var(--border-bright); border-radius:12px; padding:12px 20px; display:flex; align-items:center; gap:10px; font-size:14px; z-index:100; animation:fadeUp2 .3s ease; white-space:nowrap; }
        @keyframes fadeUp2 { from{opacity:0;transform:translateX(-50%) translateY(10px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }
      `}</style>
    <div className="profile-root">
      {/* Навигация как в профиле */}
      <nav className="pnav">
        <div className="pnav-logo" onClick={() => navigate("/")}>🍽 CantineOS</div>
        <button className="pnav-back" onClick={() => navigate("/")}>← Отмена</button>
      </nav>

      <div className="profile-wrap">
        {loading ? (
          <div className="psection">
            <div className="pskeleton" style={{ width: "40%", marginBottom: 16 }} />
            <div className="pskeleton" style={{ width: "100%", height: "100px" }} />
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {/* Секция основных настроек */}
            <div className="psection">
              <div className="psection-title">Параметры нового меню</div>
              <div className="two-col">
                <div className="pfield">
                  <div className="pfield-label">Столовая</div>
                  <select 
                    className="pinput" 
                    value={selectedCanteen} 
                    onChange={e => setSelectedCanteen(e.target.value)}
                    required
                  >
                    <option value="">Выберите столовую...</option>
                    {canteens.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>

                <div className="pfield">
                  <div className="pfield-label">Дата публикации</div>
                  <input 
                    type="date" 
                    className="pinput" 
                    value={selectedDate} 
                    onChange={e => setSelectedDate(e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>

            {/* Секция выбора блюд */}
            <div className="psection">
              <div className="psection-title">Выбор блюд</div>
              <p className="pfield-label" style={{ marginBottom: '12px' }}>
                Нажмите на блюда, чтобы добавить их в меню:
              </p>
              
              <div className="tags">
                {allDishes.map(dish => {
                  const isSelected = selectedDishes.includes(dish.id);
                  return (
                    <div 
                      key={dish.id} 
                      className={`tag ${isSelected ? 'sel' : ''}`}
                      onClick={() => toggleDish(dish.id)}
                      style={{ 
                        cursor: 'pointer', 
                        padding: '10px 16px',
                        fontSize: '14px',
                        borderColor: isSelected ? 'var(--gold)' : 'var(--border)',
                        background: isSelected ? 'rgba(240,165,0,.08)' : 'var(--bg3)',
                        color: isSelected ? 'var(--gold)' : 'var(--text)',
                        transition: 'all 0.2s'
                      }}
                    >
                      <span style={{ marginRight: '6px' }}>{dish.emoji || '🥘'}</span>
                      {dish.name}
                      {isSelected && <span style={{ marginLeft: '8px', fontSize: '12px' }}>✕</span>}
                    </div>
                  );
                })}
              </div>

              {selectedDishes.length === 0 && (
                <div className="pfield-value muted" style={{ fontSize: '13px', marginTop: '10px' }}>
                  Ни одного блюда пока не выбрано
                </div>
              )}
            </div>

            {/* Кнопки действий */}
            <div className="save-row">
              <button type="button" className="btn-cancel" onClick={() => navigate("/")}>
                Отмена
              </button>
              <button 
                type="submit" 
                className="btn-save" 
                disabled={!selectedCanteen || selectedDishes.length === 0}
              >
                ОПУБЛИКОВАТЬ МЕНЮ
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
    </>
  );
}

// ── Router ──
// Измени компонент App в конце твоего кода
// Находишь в самом низу файла export function App() и заменяешь её на это:
export function App() {
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, icon = "✅") => {
    setToast({ message, icon });
    setTimeout(() => setToast(null), 3000);
  }, []);

  return (
    <>
      <Routes>
        {/* Обязательно передаем showToast как пропс! */}
        <Route path="/" element={<CanteenApp showToast={showToast} />} />
        <Route path="/profile" element={<ProfilePage showToast={showToast} />} />
        <Route path="/create-menu" element={<CreateMenuPage api={api} showToast={showToast} />} />
      </Routes>
      
      {/* Общий контейнер для уведомлений */}
      {toast && (
        <div className="toast" style={{ position: 'fixed', bottom: '20px', left: '50%', transform: 'translateX(-50%)', zIndex: 9999 }}>
          <span>{toast.icon}</span>
          <span>{toast.message}</span>
        </div>
      )}
    </>
  );
}

export default App;
