import { useState, useRef, useEffect } from "react";

const EDIT_PASSWORD = "rjv4wUwh"; // ← Ваш пароль для редактирования
const STORAGE_KEY = "consulting_site_content";

const C0 = {
  nav: { logo: "Иван Петров", logoSub: "Операционный консалтинг" },
  hero: {
    label: "Операционный директор на аутсорсе",
    headline: "Системный рост\nбез операционного хаоса",
    description: "Работаю с предпринимателями как внешний COO — выстраиваю процессы, собираю команды, запускаю новые направления. Вы занимаетесь стратегией.",
    cta1: "Записаться на консультацию",
    cta2: "Узнать об услугах",
    stats: [
      { number: "47", label: "завершённых проектов", desc: "от операционного аудита до полного ведения" },
      { number: "12", label: "лет в управлении", desc: "от менеджера до COO с оборотом 2 млрд ₽" },
      { number: "3.2×", label: "средний рост выручки", desc: "у клиентов за первый год работы" }
    ]
  },
  thesis: {
    label: "Подход",
    quote: "Операционная эффективность — не цель. Это фундамент, на котором строится масштаб.",
    points: [
      { num: "01", title: "Диагностика прежде всего", text: "Каждый проект начинается с глубокого погружения в бизнес. Никаких шаблонных решений — только то, что работает в вашей ситуации." },
      { num: "02", title: "Измеримые результаты", text: "Договариваемся о конкретных метриках на старте. Вы всегда знаете, что происходит и к чему мы движемся." },
      { num: "03", title: "Передача системы", text: "Моя задача — не создать зависимость, а выстроить то, что будет работать без меня. Вы получаете систему, а не консультанта навсегда." }
    ]
  },
  services: {
    label: "Услуги",
    headline: "Три формата\nсотрудничества",
    items: [
      {
        index: "01",
        title: "Операционное ведение",
        subtitle: "Fractional COO",
        description: "Работаю как ваш штатный операционный директор на условиях аутсорса. Полное погружение в бизнес — стратегия, команда, процессы, результат.",
        features: ["Управление операционной командой", "Выстраивание бизнес-процессов", "Система OKR и управление целями", "Найм и онбординг ключевых сотрудников", "Еженедельные отчёты и сессии с собственником"],
        price: "от 150 000 ₽/мес",
        tag: "Флагман"
      },
      {
        index: "02",
        title: "Почасовой консалтинг",
        subtitle: "Advisory Sessions",
        description: "Стратегические сессии по конкретным задачам. Экспертный взгляд со стороны, структурированный разбор и план действий.",
        features: ["Аудит операционной модели", "Стратегические сессии 90 минут", "Разбор найма и структуры команды", "Антикризисный разбор ситуации", "Экспресс-диагностика процессов"],
        price: "15 000 ₽/час",
        tag: ""
      },
      {
        index: "03",
        title: "Запуск без ФОТа",
        subtitle: "Lean Startup Build",
        description: "Собираю команду под стартап или новое направление на проектной основе. Проверяем гипотезу до того, как вкладывать серьёзные деньги.",
        features: ["Сборка команды без постоянных окладов", "CustDev и валидация идеи", "Запуск MVP в минимальные сроки", "Новые направления внутри компании", "Чёткий критерий: масштабировать или остановить"],
        price: "по договорённости",
        tag: "Для стартапов"
      }
    ]
  },
  startup: {
    label: "Специализация",
    headline: "Запустить новое направление\nбез лишних потерь",
    description: "Большинство предпринимателей теряют от 1 до 5 млн рублей прежде, чем понять: идея не работает. Я помогаю получить тот же ответ — в разы дешевле и быстрее.",
    economy: "от 3 до 10×",
    economyLabel: "экономия на проверке гипотезы по сравнению с классическим запуском",
    blocks: [
      { icon: "◈", title: "Команда без ФОТа", text: "Собираю команду на проектной или долевой основе — разработчики, маркетологи, продажники. Постоянные оклады появляются только после подтверждения модели." },
      { icon: "◉", title: "Валидация до вложений", text: "CustDev, первые продажи, MVP — выстраиваю процесс быстрой проверки гипотез. Вы узнаёте правду о своей идее за недели, а не месяцы." },
      { icon: "◫", title: "Новые направления в бизнесе", text: "Помогаю действующим компаниям запускать новые продукты как отдельные юниты — со своей командой, P&L и метриками, не ломая основной бизнес." },
      { icon: "◷", title: "Ясность вместо иллюзий", text: "Главная ценность — честный ответ: идти дальше или остановиться. Это стоит в разы меньше, чем узнать то же самое через год и потраченный бюджет." }
    ]
  },
  process: {
    label: "Процесс",
    headline: "Как начинается\nсотрудничество",
    steps: [
      { num: "01", title: "Заявка", text: "Оставляете контакт или бронируете звонок через форму на сайте" },
      { num: "02", title: "Диагностический звонок", text: "30 минут бесплатно — разбираем ситуацию, цели и определяем формат" },
      { num: "03", title: "Предложение", text: "Я готовлю конкретный план работы с понятными метриками и стоимостью" },
      { num: "04", title: "Старт", text: "Подписываем договор и приступаем. Первые результаты — в течение 2 недель" }
    ]
  },
  cases: {
    label: "Кейсы",
    headline: "Результаты\nклиентов",
    items: [
      {
        industry: "E-commerce",
        title: "Рост выручки с 15 до 48 млн ₽ за 8 месяцев",
        challenge: "Собственник работал 14 часов в день и всё равно не успевал. Процессы держались на нём лично, команда не работала самостоятельно.",
        result: "Выстроил операционный отдел, нанял 6 человек, внедрил CRM и систему KPI. Через 4 месяца собственник вышел из операционки.",
        metrics: [{ val: "3.2×", label: "рост выручки" }, { val: "−70%", label: "время собственника" }, { val: "4 мес", label: "до выхода из операционки" }]
      },
      {
        industry: "Стартап / IT",
        title: "MVP за 6 недель без постоянного найма",
        challenge: "Основатель хотел запустить продукт, но не мог позволить себе нанять команду в штат — слишком высокий риск на этапе идеи.",
        result: "Собрал команду из 4 человек на проектной основе. CustDev, сборка MVP, первые 12 платящих клиентов. Сэкономили более 2 млн ₽.",
        metrics: [{ val: "6 нед", label: "до первого MVP" }, { val: "12", label: "первых клиентов" }, { val: "−2 млн ₽", label: "экономия на старте" }]
      },
      {
        industry: "Розничная сеть",
        title: "Новое направление — с нуля до выручки за квартал",
        challenge: "Компания хотела выйти в онлайн, но боялась, что это разрушит текущие процессы и отвлечёт команду от основного бизнеса.",
        result: "Запустил онлайн-направление как отдельный юнит со своей командой и P&L. Основной бизнес не пострадал, новое направление вышло в плюс.",
        metrics: [{ val: "3 мес", label: "до первых продаж" }, { val: "Отд. P&L", label: "изолированный юнит" }, { val: "0", label: "потерь в основном бизнесе" }]
      }
    ]
  },
  about: {
    label: "Об авторе",
    name: "Иван Петров",
    role: "Операционный директор · Консультант",
    bio: "12 лет в операционном управлении. Прошёл путь от линейного менеджера до COO в компании с оборотом 2 млрд ₽. Строил команды с нуля, выстраивал процессы в условиях высокого роста, запускал новые направления в e-commerce, IT и ритейле.\n\nСейчас работаю с предпринимателями как внешний COO — помогаю выстроить операционную систему, запустить новое и освободить собственника от ручного управления.",
    credentials: [
      { val: "2 млрд ₽", label: "оборот компании на позиции COO" },
      { val: "47", label: "успешных проектов" },
      { val: "e-com, IT, ритейл, стартапы", label: "отраслевой опыт" },
      { val: "Спикер", label: "на конференциях по операционному управлению" }
    ]
  },
  testimonials: {
    label: "Отзывы",
    items: [
      { text: "В первую очередь Вусал профессионал, который может не просто собрать команду, но и настроить бизнес-процессы и вдохновить команду на следование чёткому, системному плану, создать вектор развития для большой системы бизнеса. Чуткий и ответственный специалист, который за задачами видит людей — и именно это позволяет сохранять мотивацию и эффективность в команде, которой он управляет.", author: "Клиент", role: "" },
      { text: "Хотели запустить новое направление, но боялись потерять фокус. Иван запустил его как отдельный юнит — основной бизнес не пострадал. Через квартал вышли в плюс.", author: "Марина Т.", role: "CEO, IT-агентство, Санкт-Петербург" },
      { text: "Сэкономил больше 2 млн на старте стартапа. Иван собрал команду без окладов, мы за 6 недель проверили гипотезу. Без него я бы жёг деньги ещё год.", author: "Дмитрий С.", role: "Основатель, SaaS-стартап" }
    ]
  },
  booking: {
    label: "Начать сотрудничество",
    headline: "Первый шаг — бесплатный\nдиагностический звонок",
    description: "30 минут, чтобы разобраться в вашей ситуации и понять, чем я могу помочь. Без обязательств и навязывания.",
    cta: "Записаться на звонок",
    note: "Отвечаю в течение 2 часов в рабочие дни"
  },
  contact: {
    label: "Контакты",
    telegram: "@ivan_petrov_coo",
    email: "ivan@petrov-consulting.ru",
    phone: "+7 (900) 000-00-00"
  },
  footer: {
    copy: "© 2025 Иван Петров",
    legal: "ИП Петров И.И. · ИНН 123456789012 · Все права защищены"
  }
};

function ET({ v, path, save, edit, tag: T = "span", cls = "", style = {}, multi = false }) {
  const [on, setOn] = useState(false);
  const [val, setVal] = useState(v);
  const ref = useRef();
  useEffect(() => setVal(v), [v]);
  useEffect(() => { if (on && ref.current) ref.current.focus(); }, [on]);
  const es = { background: "rgba(37,99,235,0.08)", border: "1px solid #2563EB", borderRadius: 2, padding: "2px 6px", color: "inherit", font: "inherit", width: "100%", outline: "none", boxSizing: "border-box" };
  if (!edit) return <T className={cls} style={style} dangerouslySetInnerHTML={{ __html: String(v).replace(/\n/g, "<br/>") }} />;
  if (on) return multi
    ? <textarea ref={ref} value={val} onChange={e => setVal(e.target.value)} onBlur={() => { save(path, val); setOn(false); }} style={{ ...es, resize: "vertical", minHeight: 56, display: "block" }} />
    : <input ref={ref} value={val} onChange={e => setVal(e.target.value)} onBlur={() => { save(path, val); setOn(false); }} style={es} />;
  return <T className={cls} style={{ ...style, cursor: "pointer", outline: edit ? "1px dashed rgba(37,99,235,0.5)" : "none", outlineOffset: 2, borderRadius: 2 }} onClick={() => setOn(true)} title="Редактировать" dangerouslySetInnerHTML={{ __html: String(v).replace(/\n/g, "<br/>") }} />;
}

export default function App() {
  const [data, setData] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : C0;
    } catch { return C0; }
  });
  const [editMode, setEditMode] = useState(false);
  const [showPassModal, setShowPassModal] = useState(false);
  const [passInput, setPassInput] = useState("");
  const [passError, setPassError] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", msg: "" });
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [bookingError, setBookingError] = useState("");

  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

  async function submitBooking() {
    if (!form.name.trim() || !form.phone.trim()) return;
    setSending(true);
    setBookingError("");
    try {
      const resp = await fetch(`${BACKEND_URL}/api/booking`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: form.name, phone: form.phone, msg: form.msg }),
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setSent(true);
      } else {
        setBookingError(data.detail || "Ошибка. Попробуйте ещё раз или напишите в Telegram.");
      }
    } catch {
      setBookingError("Не удалось отправить заявку. Проверьте соединение или напишите в Telegram.");
    } finally {
      setSending(false);
    }
  }

  function save(path, value) {
    const keys = path.split(".");
    setData(prev => {
      const next = JSON.parse(JSON.stringify(prev));
      let cur = next;
      for (let i = 0; i < keys.length - 1; i++) cur = isNaN(keys[i]) ? cur[keys[i]] : cur[+keys[i]];
      const k = keys[keys.length - 1];
      if (isNaN(k)) cur[k] = value; else cur[+k] = value;
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch {}
      return next;
    });
  }

  function tryEnterEdit() {
    if (passInput === EDIT_PASSWORD) {
      setEditMode(true);
      setShowPassModal(false);
      setPassInput("");
      setPassError(false);
    } else {
      setPassError(true);
    }
  }

  function exitEdit() {
    setEditMode(false);
  }

  const E = (p) => <ET {...p} save={save} edit={editMode} />;
  const go = id => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  const navy = "#0B1F3A";
  const blue = "#1A56DB";
  const lightBlue = "#EFF6FF";
  const text = "#1A1A2E";
  const muted = "#64748B";
  const border = "#E2E8F0";
  const serif = "'Libre Baskerville', Georgia, serif";
  const sans = "'Source Sans 3', 'Helvetica Neue', sans-serif";

  const Label = ({ children, light }) => (
    <div style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, letterSpacing: ".16em", textTransform: "uppercase", color: light ? "rgba(255,255,255,0.5)" : blue, marginBottom: 16 }}>
      {children}
    </div>
  );

  const Rule = ({ light }) => <div style={{ borderTop: `1px solid ${light ? "rgba(255,255,255,.12)" : border}`, margin: 0 }} />;

  return (
    <div style={{ fontFamily: sans, background: "#FFFFFF", color: text, minHeight: "100vh", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;600;700&display=swap');
        *{box-sizing:border-box;margin:0;padding:0}
        .btn-primary{cursor:pointer;border:none;background:#1A56DB;color:#fff;font-family:'Source Sans 3','Helvetica Neue',sans-serif;font-weight:600;font-size:13px;letter-spacing:.06em;padding:14px 32px;transition:all .2s;display:inline-block}
        .btn-primary:hover{background:#1E40AF;transform:translateY(-1px);box-shadow:0 6px 20px rgba(26,86,219,.25)}
        .btn-ghost{cursor:pointer;border:1.5px solid #0B1F3A;background:transparent;color:#0B1F3A;font-family:'Source Sans 3','Helvetica Neue',sans-serif;font-weight:600;font-size:13px;letter-spacing:.06em;padding:13px 30px;transition:all .2s;display:inline-block}
        .btn-ghost:hover{background:#0B1F3A;color:#fff}
        .btn-white{cursor:pointer;border:1.5px solid rgba(255,255,255,.4);background:transparent;color:#fff;font-family:'Source Sans 3','Helvetica Neue',sans-serif;font-weight:600;font-size:13px;letter-spacing:.06em;padding:13px 30px;transition:all .2s;display:inline-block}
        .btn-white:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.7)}
        .nav-link{font-family:'Source Sans 3',sans-serif;font-size:13px;letter-spacing:.04em;color:#475569;cursor:pointer;transition:color .15s;background:none;border:none;padding:0;font-weight:600}
        .nav-link:hover{color:#1A56DB}
        .svc-card{border:1px solid #E2E8F0;padding:36px 32px;background:#fff;transition:all .25s;position:relative}
        .svc-card:hover{border-color:#1A56DB;box-shadow:0 8px 32px rgba(26,86,219,.1);transform:translateY(-3px)}
        .svc-card.featured{background:#0B1F3A;border-color:#0B1F3A;color:#fff}
        .case-card{background:#F8FAFC;border:1px solid #E2E8F0;padding:36px 32px;transition:border .2s}
        .case-card:hover{border-color:#94A3B8}
        .startup-item{display:flex;gap:24px;padding:28px 0;border-bottom:1px solid #E2E8F0}
        .startup-item:last-child{border-bottom:none}
        input,textarea{outline:none;font-family:'Source Sans 3',sans-serif;color:#1A1A2E;background:#fff;border:1.5px solid #E2E8F0;padding:13px 16px;font-size:14px;width:100%;transition:border .2s}
        input:focus,textarea:focus{border-color:#1A56DB}
        input::placeholder,textarea::placeholder{color:#94A3B8}
        ::-webkit-scrollbar{width:3px}::-webkit-scrollbar-thumb{background:#1A56DB}
        @keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
        .fu{animation:fadeUp .7s ease both}
        .metric-big{font-family:'Libre Baskerville',Georgia,serif;font-size:48px;font-weight:700;color:#1A56DB;line-height:1}
        .tag-pill{display:inline-block;font-family:'Source Sans 3',sans-serif;font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;background:#EFF6FF;color:#1A56DB;padding:3px 10px}
        .tag-pill.dark{background:rgba(26,86,219,.2);color:#93C5FD}
        @media(max-width:768px){.grid-2{grid-template-columns:1fr!important}.grid-3{grid-template-columns:1fr!important}.hide-mobile{display:none!important}}
      `}</style>

      {/* PASSWORD MODAL */}
      {showPassModal && (
        <div style={{ position: "fixed", inset: 0, zIndex: 99999, background: "rgba(11,31,58,0.7)", display: "flex", alignItems: "center", justifyContent: "center", backdropFilter: "blur(4px)" }}>
          <div style={{ background: "#fff", padding: "40px 36px", width: 360, boxShadow: "0 24px 64px rgba(0,0,0,.2)" }}>
            <h3 style={{ fontFamily: serif, fontSize: 22, fontWeight: 700, color: navy, marginBottom: 8 }}>Режим редактирования</h3>
            <p style={{ fontFamily: sans, fontSize: 13, color: muted, marginBottom: 24 }}>Введите пароль для доступа</p>
            <input
              type="password"
              placeholder="Пароль"
              value={passInput}
              onChange={e => { setPassInput(e.target.value); setPassError(false); }}
              onKeyDown={e => e.key === "Enter" && tryEnterEdit()}
              autoFocus
              style={{ background: passError ? "#FFF5F5" : "#fff", border: `1.5px solid ${passError ? "#EF4444" : border}`, color: text, padding: "13px 16px", fontSize: 14, width: "100%", marginBottom: 8, outline: "none" }}
            />
            {passError && <p style={{ fontFamily: sans, fontSize: 12, color: "#EF4444", marginBottom: 12 }}>Неверный пароль</p>}
            <div style={{ display: "flex", gap: 10, marginTop: passError ? 4 : 12 }}>
              <button className="btn-primary" style={{ flex: 1, padding: "12px", fontSize: 13 }} onClick={tryEnterEdit}>Войти</button>
              <button className="btn-ghost" style={{ padding: "12px 18px", fontSize: 13 }} onClick={() => { setShowPassModal(false); setPassInput(""); setPassError(false); }}>Отмена</button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT BAR */}
      <div style={{ position: "sticky", top: 0, zIndex: 9999, background: editMode ? "#EFF6FF" : "#F8FAFC", borderBottom: `2px solid ${editMode ? "#1A56DB" : "#E2E8F0"}`, padding: "8px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontFamily: sans, fontSize: 12, color: editMode ? "#1A56DB" : "#94A3B8", fontWeight: 600 }}>
          {editMode ? "✏️ Режим редактирования — кликайте на любой текст · Изменения сохраняются автоматически" : ""}
        </span>
        <button className="btn-primary" style={{ padding: "6px 20px", fontSize: 12 }} onClick={() => editMode ? exitEdit() : setShowPassModal(true)}>
          {editMode ? "✓ Завершить редактирование" : "✏️ Редактировать"}
        </button>
      </div>

      {/* NAV */}
      <nav style={{ position: "sticky", top: 36, zIndex: 100, background: "rgba(255,255,255,.98)", backdropFilter: "blur(12px)", borderBottom: `1px solid ${border}`, padding: "0 40px", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 3, height: 32, background: blue }} />
          <div>
            <E v={data.nav.logo} path="nav.logo" tag="div" style={{ fontFamily: serif, fontSize: 17, fontWeight: 700, color: navy, letterSpacing: "-.01em" }} />
            <E v={data.nav.logoSub} path="nav.logoSub" tag="div" style={{ fontFamily: sans, fontSize: 10, color: muted, letterSpacing: ".1em", textTransform: "uppercase", marginTop: 1 }} />
          </div>
        </div>
        <div style={{ display: "flex", gap: 28 }}>
          {[["Услуги","services"],["Стартапы","startup"],["Кейсы","cases"],["О консультанте","about"],["Контакты","contact"]].map(([l,id]) => (
            <button key={id} className="nav-link" onClick={() => go(id)}>{l}</button>
          ))}
        </div>
        <button className="btn-primary" style={{ padding: "10px 24px", fontSize: 12 }} onClick={() => go("booking")}>
          Записаться на звонок
        </button>
      </nav>

      {/* HERO */}
      <div style={{ background: navy, color: "#fff", padding: "96px 0 0", overflow: "hidden" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 48px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 64, alignItems: "center" }} className="grid-2">
            <div>
              <div className="fu" style={{ animationDelay: ".05s", marginBottom: 24 }}>
                <span style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, letterSpacing: ".16em", textTransform: "uppercase", color: "rgba(255,255,255,.45)", borderLeft: `3px solid ${blue}`, paddingLeft: 10 }}>
                  <E v={data.hero.label} path="hero.label" />
                </span>
              </div>
              <div className="fu" style={{ animationDelay: ".15s" }}>
                <E v={data.hero.headline} path="hero.headline" tag="h1" style={{ fontFamily: serif, fontSize: "clamp(36px,4vw,54px)", fontWeight: 700, lineHeight: 1.15, color: "#fff", letterSpacing: "-.02em" }} multi />
              </div>
              <div className="fu" style={{ animationDelay: ".28s", marginTop: 24 }}>
                <E v={data.hero.description} path="hero.description" tag="p" style={{ fontFamily: sans, fontSize: 17, lineHeight: 1.7, color: "rgba(255,255,255,.65)", maxWidth: 460 }} multi />
              </div>
              <div className="fu" style={{ animationDelay: ".4s", display: "flex", gap: 12, marginTop: 40, flexWrap: "wrap" }}>
                <button className="btn-primary" style={{ padding: "15px 32px", fontSize: 13 }} onClick={() => go("booking")}>
                  <E v={data.hero.cta1} path="hero.cta1" />
                </button>
                <button className="btn-white" style={{ padding: "14px 28px", fontSize: 13 }} onClick={() => go("services")}>
                  <E v={data.hero.cta2} path="hero.cta2" />
                </button>
              </div>
            </div>

            {/* Stats panel */}
            <div className="fu hide-mobile" style={{ animationDelay: ".3s" }}>
              <div style={{ background: "rgba(255,255,255,.04)", border: "1px solid rgba(255,255,255,.1)", padding: "40px 36px" }}>
                {data.hero.stats.map((s, i) => (
                  <div key={i} style={{ paddingBottom: i < 2 ? 28 : 0, marginBottom: i < 2 ? 28 : 0, borderBottom: i < 2 ? "1px solid rgba(255,255,255,.08)" : "none" }}>
                    <div style={{ display: "flex", alignItems: "flex-end", gap: 16, marginBottom: 6 }}>
                      <E v={s.number} path={`hero.stats.${i}.number`} tag="div" style={{ fontFamily: serif, fontSize: 44, fontWeight: 700, color: "#60A5FA", lineHeight: 1 }} />
                      <E v={s.label} path={`hero.stats.${i}.label`} tag="div" style={{ fontFamily: sans, fontSize: 14, fontWeight: 600, color: "#fff", lineHeight: 1.2, paddingBottom: 6, maxWidth: 160 }} />
                    </div>
                    <E v={s.desc} path={`hero.stats.${i}.desc`} tag="div" style={{ fontFamily: sans, fontSize: 12, color: "rgba(255,255,255,.4)", lineHeight: 1.5 }} />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom stripe */}
          <div style={{ display: "flex", gap: 0, marginTop: 72, borderTop: "1px solid rgba(255,255,255,.08)" }}>
            {["Операционная стратегия", "Построение команд", "Запуск стартапов", "Новые направления в бизнесе", "Fractional COO"].map((item, i) => (
              <div key={i} style={{ flex: 1, padding: "18px 20px", borderRight: i < 4 ? "1px solid rgba(255,255,255,.08)" : "none" }}>
                <span style={{ fontFamily: sans, fontSize: 12, color: "rgba(255,255,255,.4)", fontWeight: 600 }}>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* THESIS */}
      <div style={{ background: "#F8FAFC", borderBottom: `1px solid ${border}` }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 80, alignItems: "start" }} className="grid-2">
            <div>
              <Label>Подход</Label>
              <E v={data.thesis.quote} path="thesis.quote" tag="blockquote" style={{ fontFamily: serif, fontSize: 22, fontWeight: 400, fontStyle: "italic", color: navy, lineHeight: 1.55, borderLeft: `3px solid ${blue}`, paddingLeft: 20 }} multi />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 32 }} className="grid-3">
              {data.thesis.points.map((p, i) => (
                <div key={i}>
                  <div style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, color: blue, letterSpacing: ".1em", marginBottom: 10 }}>{p.num}</div>
                  <E v={p.title} path={`thesis.points.${i}.title`} tag="h4" style={{ fontFamily: serif, fontSize: 17, fontWeight: 700, color: navy, marginBottom: 10, lineHeight: 1.3 }} />
                  <E v={p.text} path={`thesis.points.${i}.text`} tag="p" style={{ fontFamily: sans, fontSize: 13, color: muted, lineHeight: 1.7 }} multi />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* SERVICES */}
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }} id="services">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 48 }}>
          <div>
            <Label>Услуги</Label>
            <E v={data.services.headline} path="services.headline" tag="h2" style={{ fontFamily: serif, fontSize: "clamp(28px,3vw,42px)", fontWeight: 700, color: navy, lineHeight: 1.2 }} multi />
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 20 }} className="grid-3">
          {data.services.items.map((svc, i) => (
            <div key={i} className={`svc-card${i === 0 ? " featured" : ""}`}>
              {svc.tag && <div className={`tag-pill${i === 0 ? " dark" : ""}`} style={{ marginBottom: 20 }}>{svc.tag}</div>}
              <div style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, letterSpacing: ".12em", color: i === 0 ? "rgba(255,255,255,.4)" : muted, marginBottom: 8 }}>{svc.index}</div>
              <E v={svc.title} path={`services.items.${i}.title`} tag="h3" style={{ fontFamily: serif, fontSize: 22, fontWeight: 700, color: i === 0 ? "#fff" : navy, marginBottom: 4 }} />
              <E v={svc.subtitle} path={`services.items.${i}.subtitle`} tag="div" style={{ fontFamily: sans, fontSize: 12, color: i === 0 ? "#60A5FA" : blue, fontWeight: 600, letterSpacing: ".06em", marginBottom: 18 }} />
              <E v={svc.description} path={`services.items.${i}.description`} tag="p" style={{ fontFamily: sans, fontSize: 13, color: i === 0 ? "rgba(255,255,255,.65)" : muted, lineHeight: 1.7, marginBottom: 22 }} multi />
              <div style={{ borderTop: `1px solid ${i === 0 ? "rgba(255,255,255,.1)" : border}`, paddingTop: 20, marginBottom: 22 }}>
                {svc.features.map((f, j) => (
                  <div key={j} style={{ display: "flex", gap: 10, marginBottom: 9, alignItems: "flex-start" }}>
                    <div style={{ width: 5, height: 5, background: i === 0 ? "#60A5FA" : blue, borderRadius: "50%", marginTop: 7, flexShrink: 0 }} />
                    <E v={f} path={`services.items.${i}.features.${j}`} tag="span" style={{ fontFamily: sans, fontSize: 13, color: i === 0 ? "rgba(255,255,255,.7)" : muted }} />
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 16, borderTop: `1px solid ${i === 0 ? "rgba(255,255,255,.1)" : border}` }}>
                <E v={svc.price} path={`services.items.${i}.price`} tag="span" style={{ fontFamily: serif, fontSize: 17, fontWeight: 700, color: i === 0 ? "#fff" : navy }} />
                <button className={i === 0 ? "btn-white" : "btn-ghost"} style={{ padding: "8px 18px", fontSize: 11 }} onClick={() => go("booking")}>
                  <E v={svc.cta || "Обсудить"} path={`services.items.${i}.cta`} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Rule />

      {/* STARTUP */}
      <div id="startup" style={{ background: "#F8FAFC" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 64, marginBottom: 56 }} className="grid-2">
            <div>
              <Label>Специализация</Label>
              <E v={data.startup.headline} path="startup.headline" tag="h2" style={{ fontFamily: serif, fontSize: "clamp(28px,3vw,40px)", fontWeight: 700, color: navy, lineHeight: 1.2 }} multi />
            </div>
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
              <E v={data.startup.description} path="startup.description" tag="p" style={{ fontFamily: sans, fontSize: 15, color: muted, lineHeight: 1.75 }} multi />
            </div>
          </div>

          <div>
            {data.startup.blocks.map((b, i) => (
              <div key={i} className="startup-item" style={{ alignItems: "flex-start" }}>
                <div style={{ fontFamily: serif, fontSize: 22, color: blue, width: 36, flexShrink: 0, marginTop: 2 }}>{b.icon}</div>
                <div style={{ flex: 1 }}>
                  <E v={b.title} path={`startup.blocks.${i}.title`} tag="h4" style={{ fontFamily: serif, fontSize: 18, fontWeight: 700, color: navy, marginBottom: 8 }} />
                  <E v={b.text} path={`startup.blocks.${i}.text`} tag="p" style={{ fontFamily: sans, fontSize: 14, color: muted, lineHeight: 1.7, maxWidth: 640 }} multi />
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 48, background: navy, padding: "32px 40px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 24 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
              <E v={data.startup.economy} path="startup.economy" tag="div" style={{ fontFamily: serif, fontSize: 48, fontWeight: 700, color: "#60A5FA", lineHeight: 1 }} />
              <div style={{ width: 1, height: 40, background: "rgba(255,255,255,.15)" }} />
              <E v={data.startup.economyLabel} path="startup.economyLabel" tag="p" style={{ fontFamily: sans, fontSize: 13, color: "rgba(255,255,255,.55)", lineHeight: 1.5, maxWidth: 300 }} multi />
            </div>
            <button className="btn-primary" style={{ padding: "14px 28px", fontSize: 12 }} onClick={() => go("booking")}>
              <E v={data.startup.blocks[0].title || "Обсудить запуск"} path="startup.cta_label" />
            </button>
          </div>
        </div>
      </div>

      <Rule />

      {/* PROCESS */}
      <div id="process" style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }}>
        <div style={{ marginBottom: 48 }}>
          <Label>Процесс</Label>
          <E v={data.process.headline} path="process.headline" tag="h2" style={{ fontFamily: serif, fontSize: "clamp(28px,3vw,42px)", fontWeight: 700, color: navy, lineHeight: 1.2 }} multi />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 0 }}>
          {data.process.steps.map((s, i) => (
            <div key={i} style={{ padding: "32px 28px", borderLeft: `1px solid ${border}`, position: "relative" }}>
              <div style={{ fontFamily: serif, fontSize: 40, fontWeight: 700, color: lightBlue, lineHeight: 1, marginBottom: 16 }}>{s.num}</div>
              <E v={s.title} path={`process.steps.${i}.title`} tag="h4" style={{ fontFamily: serif, fontSize: 17, fontWeight: 700, color: navy, marginBottom: 10 }} />
              <E v={s.text} path={`process.steps.${i}.text`} tag="p" style={{ fontFamily: sans, fontSize: 13, color: muted, lineHeight: 1.7 }} multi />
              <div style={{ width: 28, height: 2, background: blue, marginTop: 20 }} />
            </div>
          ))}
        </div>
      </div>

      <Rule />

      {/* CASES */}
      <div id="cases" style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }}>
        <div style={{ marginBottom: 48 }}>
          <Label>Кейсы</Label>
          <E v={data.cases.headline} path="cases.headline" tag="h2" style={{ fontFamily: serif, fontSize: "clamp(28px,3vw,42px)", fontWeight: 700, color: navy, lineHeight: 1.2 }} multi />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 20 }} className="grid-3">
          {data.cases.items.map((c, i) => (
            <div key={i} className="case-card">
              <div style={{ fontFamily: sans, fontSize: 10, fontWeight: 700, letterSpacing: ".14em", textTransform: "uppercase", color: blue, marginBottom: 16, borderLeft: `2px solid ${blue}`, paddingLeft: 10 }}>
                <E v={c.industry} path={`cases.items.${i}.industry`} />
              </div>
              <E v={c.title} path={`cases.items.${i}.title`} tag="h3" style={{ fontFamily: serif, fontSize: 18, fontWeight: 700, color: navy, marginBottom: 20, lineHeight: 1.3 }} />
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, color: muted, letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 6 }}>Задача</div>
                <E v={c.challenge} path={`cases.items.${i}.challenge`} tag="p" style={{ fontFamily: sans, fontSize: 13, color: muted, lineHeight: 1.65 }} multi />
              </div>
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, color: muted, letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 6 }}>Результат</div>
                <E v={c.result} path={`cases.items.${i}.result`} tag="p" style={{ fontFamily: sans, fontSize: 13, color: muted, lineHeight: 1.65 }} multi />
              </div>
              <div style={{ borderTop: `1px solid ${border}`, paddingTop: 20, display: "flex", gap: 20, flexWrap: "wrap" }}>
                {c.metrics.map((m, j) => (
                  <div key={j}>
                    <E v={m.val} path={`cases.items.${i}.metrics.${j}.val`} tag="div" style={{ fontFamily: serif, fontSize: 22, fontWeight: 700, color: blue, lineHeight: 1 }} />
                    <E v={m.label} path={`cases.items.${i}.metrics.${j}.label`} tag="div" style={{ fontFamily: sans, fontSize: 11, color: muted, marginTop: 3 }} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <Rule />

      {/* ABOUT */}
      <div id="about" style={{ background: "#F8FAFC" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: 72, alignItems: "start" }} className="grid-2">
            <div>
              <Label>О консультанте</Label>
              <E v={data.about.name} path="about.name" tag="h2" style={{ fontFamily: serif, fontSize: "clamp(30px,3vw,44px)", fontWeight: 700, color: navy, lineHeight: 1.1, marginBottom: 8 }} />
              <E v={data.about.role} path="about.role" tag="p" style={{ fontFamily: sans, fontSize: 13, color: blue, fontWeight: 600, letterSpacing: ".06em", textTransform: "uppercase", marginBottom: 32 }} />
              <div style={{ width: "100%", aspectRatio: "1/1.1", background: `linear-gradient(135deg, ${lightBlue} 0%, #DBEAFE 100%)`, border: `1px solid ${border}`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 10 }}>
                <div style={{ fontSize: 48 }}>👤</div>
                <p style={{ fontFamily: sans, fontSize: 11, color: muted, letterSpacing: ".1em", textTransform: "uppercase" }}>Ваше фото</p>
              </div>
            </div>
            <div>
              <E v={data.about.bio} path="about.bio" tag="p" style={{ fontFamily: sans, fontSize: 16, color: text, lineHeight: 1.8, marginBottom: 40, whiteSpace: "pre-line" }} multi />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                {data.about.credentials.map((c, i) => (
                  <div key={i} style={{ padding: "20px 24px", background: "#fff", border: `1px solid ${border}` }}>
                    <E v={c.val} path={`about.credentials.${i}.val`} tag="div" style={{ fontFamily: serif, fontSize: 22, fontWeight: 700, color: navy, lineHeight: 1, marginBottom: 6 }} />
                    <E v={c.label} path={`about.credentials.${i}.label`} tag="div" style={{ fontFamily: sans, fontSize: 12, color: muted, lineHeight: 1.4 }} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <Rule />

      {/* TESTIMONIALS */}
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }}>
        <div style={{ marginBottom: 48 }}>
          <Label>Отзывы клиентов</Label>
          <E v={data.testimonials.label} path="testimonials.label" tag="h2" style={{ fontFamily: serif, fontSize: "clamp(28px,3vw,42px)", fontWeight: 700, color: navy }} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 20 }} className="grid-3">
          {data.testimonials.items.map((t, i) => (
            <div key={i} style={{ padding: "32px 28px", border: `1px solid ${border}`, background: "#fff" }}>
              <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
                {[0,1,2,3,4].map(s => <div key={s} style={{ width: 14, height: 14, background: blue, clipPath: "polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%)" }} />)}
              </div>
              <E v={t.text} path={`testimonials.items.${i}.text`} tag="p" style={{ fontFamily: sans, fontSize: 14, color: text, lineHeight: 1.75, marginBottom: 24, fontStyle: "italic" }} multi />
              <div style={{ borderTop: `1px solid ${border}`, paddingTop: 18 }}>
                <E v={t.author} path={`testimonials.items.${i}.author`} tag="div" style={{ fontFamily: serif, fontSize: 15, fontWeight: 700, color: navy, marginBottom: 4 }} />
                <E v={t.role} path={`testimonials.items.${i}.role`} tag="div" style={{ fontFamily: sans, fontSize: 12, color: muted }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* BOOKING */}
      <div id="booking" style={{ background: navy }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 48px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 80, alignItems: "center" }} className="grid-2">
            <div>
              <div style={{ fontFamily: sans, fontSize: 11, fontWeight: 700, letterSpacing: ".16em", textTransform: "uppercase", color: "rgba(255,255,255,.4)", borderLeft: `3px solid ${blue}`, paddingLeft: 10, marginBottom: 20 }}>
                <E v={data.booking.label} path="booking.label" />
              </div>
              <E v={data.booking.headline} path="booking.headline" tag="h2" style={{ fontFamily: serif, fontSize: "clamp(28px,3vw,42px)", fontWeight: 700, color: "#fff", lineHeight: 1.2, marginBottom: 20 }} multi />
              <E v={data.booking.description} path="booking.description" tag="p" style={{ fontFamily: sans, fontSize: 15, color: "rgba(255,255,255,.55)", lineHeight: 1.7 }} multi />
            </div>
            <div>
              {sent ? (
                <div style={{ background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.1)", padding: "44px 36px", textAlign: "center" }}>
                  <div style={{ fontSize: 36, marginBottom: 16 }}>✅</div>
                  <h3 style={{ fontFamily: serif, fontSize: 24, color: "#fff", marginBottom: 10 }}>Заявка получена</h3>
                  <p style={{ fontFamily: sans, color: "rgba(255,255,255,.5)", fontSize: 13 }}>Свяжусь с вами в течение 2 часов в рабочие дни</p>
                </div>
              ) : (
                <div>
                  <div style={{ display: "grid", gap: 12, marginBottom: 12 }}>
                    <input placeholder="Имя и фамилия" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} style={{ background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.15)", color: "#fff", borderRadius: 0 }} />
                    <input placeholder="Телефон или Telegram" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} style={{ background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.15)", color: "#fff", borderRadius: 0 }} />
                    <textarea placeholder="Расскажите о вашей задаче (опционально)" value={form.msg} onChange={e => setForm(p => ({ ...p, msg: e.target.value }))} rows={4} style={{ background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.15)", color: "#fff", resize: "vertical", borderRadius: 0 }} />
                  </div>
                  {bookingError && (
                    <p style={{ fontFamily: sans, fontSize: 13, color: "#FCA5A5", marginBottom: 10, lineHeight: 1.5 }}>{bookingError}</p>
                  )}
                  <button
                    className="btn-primary"
                    style={{ width: "100%", padding: "16px", fontSize: 13, marginBottom: 12, textAlign: "center", opacity: sending ? 0.6 : 1, cursor: sending ? "not-allowed" : "pointer" }}
                    onClick={submitBooking}
                    disabled={sending}
                  >
                    {sending ? "Отправляем…" : <E v={data.booking.cta} path="booking.cta" />}
                  </button>
                  <E v={data.booking.note} path="booking.note" tag="p" style={{ fontFamily: sans, fontSize: 12, color: "rgba(255,255,255,.3)", textAlign: "center" }} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* CONTACT */}
      <div id="contact" style={{ borderTop: `1px solid ${border}` }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "48px 48px 40px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 32 }}>
            <div>
              <Label>Контакты</Label>
              <E v={data.contact.headline || "Свяжитесь напрямую"} path="contact.headline" tag="h3" style={{ fontFamily: serif, fontSize: 24, fontWeight: 700, color: navy }} />
            </div>
            <div style={{ display: "flex", gap: 48, flexWrap: "wrap" }}>
              {[["✈️","Telegram",data.contact.telegram,"contact.telegram"],["✉️","Email",data.contact.email,"contact.email"],["📞","Телефон",data.contact.phone,"contact.phone"]].map(([icon,label,val,path]) => (
                <div key={label}>
                  <div style={{ fontFamily: sans, fontSize: 10, fontWeight: 700, color: muted, letterSpacing: ".12em", textTransform: "uppercase", marginBottom: 5 }}>{icon} {label}</div>
                  <E v={val} path={path} tag="div" style={{ fontFamily: sans, fontSize: 15, fontWeight: 600, color: navy }} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <div style={{ background: navy, borderTop: `3px solid ${blue}`, padding: "24px 48px", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <E v={data.footer.copy} path="footer.copy" tag="span" style={{ fontFamily: sans, fontSize: 12, color: "rgba(255,255,255,.3)" }} />
        <E v={data.footer.legal} path="footer.legal" tag="span" style={{ fontFamily: sans, fontSize: 12, color: "rgba(255,255,255,.3)" }} />
      </div>
    </div>
  );
}
