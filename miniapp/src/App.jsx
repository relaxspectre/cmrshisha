import { useEffect, useState } from "react";

export default function App() {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const tg = window.Telegram?.WebApp;

    if (!tg) {
      console.log("❌ Telegram WebApp не знайдено");
      setError("Відкрито не через Telegram");
      setStatus("error");
      return;
    }

    tg.ready();
    tg.expand();

    const initData = tg.initData;

    console.log("INIT DATA:", initData);

    if (!initData) {
      setError("initData порожній");
      setStatus("error");
      return;
    }

    fetch("https://chicanesrt.shop/api/auth", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ initData }),
    })
      .then(async (res) => {
        const text = await res.text();
        console.log("SERVER RAW:", text);

        try {
          return JSON.parse(text);
        } catch {
          throw new Error("Невалідний JSON від сервера");
        }
      })
      .then((data) => {
        console.log("SERVER JSON:", data);

        if (data.status === "ok" && data.user) {
          setUser(data.user);
          setStatus("ok");
        } else {
          setError("Сервер повернув помилку");
          setStatus("error");
        }
      })
      .catch((err) => {
        console.log("FETCH ERROR:", err);
        setError("Помилка запиту до сервера");
        setStatus("error");
      });
  }, []);

  // 🔄 LOADING
  if (status === "loading") {
    return <div style={styles.center}>⏳ Завантаження...</div>;
  }

  // ❌ ERROR
  if (status === "error") {
    return (
      <div style={styles.center}>
        ❌ Помилка авторизації
        <br />
        <small>{error}</small>
      </div>
    );
  }

  // 🛑 SAFETY
  if (!user) {
    return <div style={styles.center}>Немає даних користувача</div>;
  }

  // ✅ UI
  return (
    <div style={styles.container}>
      <h1 style={styles.title}>CMRD SHISHA</h1>

      <div style={styles.card}>
        <div><b>ID:</b> {user.telegram_id}</div>
        <div><b>Імʼя:</b> {user.name}</div>
        <div><b>Роль:</b> {user.role}</div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: 20,
    color: "#fff",
    background: "#0b0f19",
    minHeight: "100vh",
    fontFamily: "system-ui",
  },
  title: {
    fontSize: 24,
    fontWeight: 700,
  },
  center: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    color: "#fff",
    textAlign: "center",
  },
  card: {
    marginTop: 20,
    padding: 20,
    borderRadius: 16,
    background: "rgba(255,255,255,0.05)",
    backdropFilter: "blur(10px)",
  },
};