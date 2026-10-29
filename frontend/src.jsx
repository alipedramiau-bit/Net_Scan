import React,{useEffect,useState} from "react";import{createRoot}from"react-dom/client";import"./style.css";
const API=(()=>{
  const e=import.meta.env.VITE_API_BASE_URL;
  if(e!==undefined&&e!==null&&e!=="")return e;
  // Always use same-origin relative URLs:
  // - When loaded via Vite (port 5001): Vite proxies /scans, /devices, /health, /api, /reports to 127.0.0.1:8001
  // - When served via FastAPI directly (port 8001): same-origin relative paths hit FastAPI
  // - When behind reverse proxies or NAT/public IP (e.g. 185.110.29.189): avoids cross-origin port 8001 firewall blocks
  return "";
})();
async function readJson(r){
  const text=await r.text();
  if(r.status===401){try{window.dispatchEvent(new CustomEvent("netscan:unauthorized"))}catch(e){}}
  if(!text||!text.trim()){
    throw Error(r.ok?("پاسخ خالی از سرور (HTTP "+r.status+") — آیا بک‌اند روی پورت 8001 در حال اجراست؟"):("خطای سرور بدون متن (HTTP "+r.status+")"));
  }
  try{return JSON.parse(text)}catch(e){
    throw Error("پاسخ JSON نامعتبر (HTTP "+r.status+"): "+text.slice(0,120));
  }
}
// --- Creative brand logo: radar sweep + network blips (Net_Scan / شبکه‌بان) ---
function Logo({size=64}){
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} role="img" aria-label="Net_Scan logo" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="nsBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#10406b"/><stop offset=".55" stopColor="#0b2b48"/><stop offset="1" stopColor="#061a2d"/>
        </linearGradient>
        <linearGradient id="nsSweep" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#34d399" stopOpacity="0"/>
          <stop offset="1" stopColor="#2fd38a" stopOpacity=".9"/>
        </linearGradient>
        <radialGradient id="nsCore" cx=".5" cy=".5" r=".5">
          <stop offset="0" stopColor="#ffffff"/><stop offset="1" stopColor="#7dd3fc"/>
        </radialGradient>
      </defs>
      <rect x="2" y="2" width="60" height="60" rx="15" fill="url(#nsBg)" stroke="#2b6c93" strokeWidth="1.4"/>
      <circle cx="32" cy="31" r="23" fill="none" stroke="#1e5d85" strokeWidth="1"/>
      <circle cx="32" cy="31" r="16" fill="none" stroke="#2b7ea8" strokeWidth="1" strokeDasharray="3 3"/>
      <circle cx="32" cy="31" r="9.5" fill="none" stroke="#3ea3cc" strokeWidth="1.1"/>
      <path d="M4 4h4M4 4v4M60 4h-4M60 4v4M4 60h4M4 60v-4M60 60h-4M60 60v-4" stroke="#2b6c93" strokeWidth="1.6" strokeLinecap="round"/>
      <path d="M32 31 L32 8 A23 23 0 0 1 49.5 15.5 Z" fill="url(#nsSweep)"/>
      <path d="M32 31 L49.5 15.5" stroke="#34d399" strokeWidth="1.6" strokeLinecap="round"/>
      <circle cx="44" cy="20" r="3" fill="#34d399"/>
      <circle cx="44" cy="20" r="6.5" fill="none" stroke="#34d399" strokeWidth="1" opacity=".55"/>
      <circle cx="44" cy="20" r="9.5" fill="none" stroke="#34d399" strokeWidth=".8" opacity=".28"/>
      <circle cx="20.5" cy="41" r="2.2" fill="#7dd3fc"/>
      <circle cx="41.5" cy="42.5" r="1.8" fill="#7dd3fc" opacity=".9"/>
      <circle cx="26.5" cy="21.5" r="1.5" fill="#7dd3fc" opacity=".7"/>
      <path d="M20.5 41 L41.5 42.5" stroke="#2b7ea8" strokeWidth=".9" opacity=".7"/>
      <path d="M20.5 41 L26.5 21.5" stroke="#2b7ea8" strokeWidth=".9" opacity=".5"/>
      <circle cx="32" cy="31" r="3.4" fill="url(#nsCore)" stroke="#e0f2fe" strokeWidth=".8"/>
    </svg>
  );
}
// --- Admin login page ---
function Login({onLogin}){
  const[user,setUser]=useState("");const[pass,setPass]=useState("");
  const[showPass,setShowPass]=useState(false);
  const[busy,setBusy]=useState(false);const[err,setErr]=useState("");
  async function submit(e){
    e.preventDefault();if(busy)return;
    setBusy(true);setErr("");
    try{
      const r=await fetch(API+"/api/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:user,password:pass})});
      const d=await readJson(r);
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"ورود ناموفق بود");
      onLogin(d.username||"admin");
    }catch(e2){setErr(e2.message||"ورود ناموفق بود")}
    setBusy(false);
  }
  return (
    <div className="login-shell" dir="rtl">
      <div className="login-glow" aria-hidden="true"></div>
      <form className="login-card" onSubmit={submit}>
        <div className="login-logo"><Logo size={92}/></div>
        <h1>شبکه‌بان <span className="login-en">Net_Scan</span></h1>
        <p className="login-sub">پایش، اسکن و مدیریت دستگاه‌های MikroTik</p>
        <label>نام کاربری
          <input dir="ltr" value={user} onChange={e=>setUser(e.target.value)} autoComplete="username" autoFocus placeholder="admin"/>
        </label>
        <label>گذرواژه
          <span className="login-pass">
            <input dir="ltr" type={showPass?"text":"password"} value={pass} onChange={e=>setPass(e.target.value)} autoComplete="current-password" placeholder="••••••••"/>
            <button type="button" className="login-eye" onClick={()=>setShowPass(v=>!v)} title={showPass?"پنهان کردن گذرواژه":"نمایش گذرواژه"} aria-label={showPass?"پنهان کردن گذرواژه":"نمایش گذرواژه"}>
              {showPass
                ?<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="M1 1l22 22"/></svg>
                :<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>}
            </button>
          </span>
        </label>
        {err&&<div className="login-error" role="alert">{err}</div>}
        <button type="submit" className="login-btn" disabled={busy||!user||!pass}>{busy?"در حال ورود…":"ورود به سامانه"}</button>
        <p className="login-hint">دسترسی مدیریت — ورود با حساب ادمین سامانه</p>
      </form>
    </div>
  );
}
const keys=["ping_responders","mikrotik_candidates","potential_non_mikrotik","winbox_open_api_closed"];const labels={ping_responders:"پاسخ‌گو به پینگ",mikrotik_candidates:"دستگاه MikroTik",potential_non_mikrotik:"احتمالاً غیر MikroTik",winbox_open_api_closed:"Winbox باز / API بسته"};
// --- Backend controller (dev only; Vite plugin endpoints, loopback-restricted) ---
/** Ribbon / toolbar SVG icons (Word-style) */
function RbIcon({name, size=20}){
  const s={width:size,height:size,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor",strokeWidth:1.75,strokeLinecap:"round",strokeLinejoin:"round","aria-hidden":true};
  switch(name){
    case "network":
      return <svg {...s}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>;
    case "search":
      return <svg {...s}><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/><path d="M8 11h6M11 8v6"/></svg>;
    case "devices":
      return <svg {...s}><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/><path d="M7 8h4M7 11h10"/></svg>;
    case "system":
      return <svg {...s}><circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M3 12h2M19 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>;
    case "add":
      return <svg {...s}><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>;
    case "trash":
      return <svg {...s}><path d="M4 7h16M9 7V5h6v2M8 7l1 12h6l1-12"/></svg>;
    case "dedupe":
      return <svg {...s}><rect x="4" y="5" width="10" height="12" rx="1"/><rect x="10" y="7" width="10" height="12" rx="1"/></svg>;
    case "clear":
      return <svg {...s}><circle cx="12" cy="12" r="9"/><path d="M8 12h8"/></svg>;
    case "read":
      return <svg {...s}><path d="M4 6h16v12H4z"/><path d="M8 10h8M8 13h5"/></svg>;
    case "config":
      return <svg {...s}><path d="M5 7h14M5 12h10M5 17h12"/><circle cx="17" cy="12" r="2"/></svg>;
    case "group":
      return <svg {...s}><circle cx="9" cy="9" r="3"/><circle cx="16" cy="10" r="2.5"/><path d="M4 18c1.5-2.5 3.5-3.5 5-3.5S12.5 15.5 14 18M14 18c1-1.5 2.2-2.2 3.5-2.2S20 16.8 21 18"/></svg>;
    case "filter":
      return <svg {...s}><path d="M4 6h16l-6 7v5l-4 2v-7L4 6z"/></svg>;
    case "csv":
      return <svg {...s}><path d="M6 3h9l5 5v13H6V3z"/><path d="M15 3v5h5M9 13h6M9 17h4"/></svg>;
    case "excel":
      return <svg {...s}><path d="M6 3h9l5 5v13H6V3z"/><path d="M15 3v5h5M10 14l4 4M14 14l-4 4"/></svg>;
    case "tag":
      return <svg {...s}><path d="M3 12V5h7l9 9-7 7-9-9z"/><circle cx="8" cy="8" r="1.2" fill="currentColor" stroke="none"/></svg>;
    case "snmp":
      return <svg {...s}><path d="M5 16a7 7 0 0 1 14 0"/><path d="M8.5 16a3.5 3.5 0 0 1 7 0"/><circle cx="12" cy="16" r="1.2" fill="currentColor" stroke="none"/><path d="M12 4v4"/></svg>;
    case "winbox":
      return <svg {...s}><rect x="4" y="5" width="16" height="12" rx="2"/><path d="M8 9h8M8 12h5"/><path d="M9 19h6"/></svg>;
    case "columns":
      return <svg {...s}><rect x="4" y="5" width="5" height="14" rx="1"/><rect x="10" y="5" width="5" height="14" rx="1"/><rect x="16" y="5" width="4" height="14" rx="1"/></svg>;
    case "database":
      return <svg {...s}><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/></svg>;
    case "backup":
      return <svg {...s}><path d="M12 4v10"/><path d="M8 10l4 4 4-4"/><path d="M5 18h14"/></svg>;
    case "restore":
      return <svg {...s}><path d="M12 20V10"/><path d="M8 14l4-4 4 4"/><path d="M5 6h14"/></svg>;
    case "email":
      return <svg {...s}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 7 9-7"/></svg>;
    default:
      return <svg {...s}><circle cx="12" cy="12" r="8"/></svg>;
  }
}


function BackendCard({onNotify}){
  const[ok,setOk]=useState(null);const[msg,setMsg]=useState("");const[checking,setChecking]=useState(true);
  async function check(signal){
    setChecking(true);
    try{
      const r=await fetch(API+"/health",{cache:"no-store",signal:signal||AbortSignal.timeout(4000)});
      if(r.ok){setOk(true);setMsg("Backend فعال است (پورت 8001). فرانت و بک‌اند جدا اجرا می‌شوند.");}
      else{setOk(false);setMsg("پاسخ غیرمنتظره از API (کد "+r.status+")");}
    }catch(e){
      if(e && (e.name==="AbortError" || /aborted/i.test(String(e.message||"")))){setChecking(false);return;}
      setOk(false);
      setMsg("Backend در دسترس نیست. در ریشه پروژه اجرا کنید:  python main.py   یا start_backend.bat");
    }
    setChecking(false);
  }
  useEffect(()=>{
    const ac=new AbortController();
    check(ac.signal);
    const t=setInterval(()=>check(AbortSignal.timeout(4000)),15000);
    return()=>{ac.abort();clearInterval(t);};
  },[]);
  return <section className="panel backend-card" data-status={ok===true?"running":ok===false?"stopped":"unknown"}>
    <h2>وضعیت سرور FastAPI (Backend)</h2>
    <div className="backend-row">
      <span className={"status-dot "+(ok===true?"on":ok===false?"off":"wait")} aria-hidden="true"></span>
      <b>{checking?"در حال بررسی…":ok===true?"فعال":"قطع"}</b>
      <span className="backend-src" dir="ltr">{API||"(same-origin / proxy)"}</span>
    </div>
    <p className={"backend-msg "+(ok===true?"ok":"warn")}>{msg}</p>
    <div className="backend-actions">
      <button type="button" className="btn-stop" onClick={()=>check()} disabled={checking}>بررسی مجدد</button>
    </div>
    {ok===false&&<pre className="backend-hint" dir="ltr" style={{fontSize:".8em",background:"#0f172a",color:"#e2e8f0",padding:"10px",borderRadius:"8px",overflow:"auto"}}>{`# Terminal 1 — Backend
cd project_root
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001

# Terminal 2 — Frontend
cd frontend
npm run dev`}</pre>}
  </section>;
}


const VPN_PROTOCOLS=["wireguard","openvpn","pptp","l2tp","sstp"];
function VpnManagerCard({onNotify,onRoutes}){
  const[st,setSt]=useState(null),[profiles,setProfiles]=useState([]),[profileId,setProfileId]=useState("olom"),[protocol,setProtocol]=useState("pptp"),[host,setHost]=useState("185.110.29.205"),[port,setPort]=useState(""),[user,setUser]=useState(""),[pass,setPass]=useState(""),[routes,setRoutes]=useState(""),[configContent,setConfigContent]=useState(""),[profileName,setProfileName]=useState("Olom"),[busy,setBusy]=useState(false),[error,setError]=useState(""),[saveAsNew,setSaveAsNew]=useState(false);
  async function refreshProfiles(){try{const r=await fetch(API+"/api/vpn/profiles");const d=await r.json();if(r.ok)setProfiles(Array.isArray(d)?d:(d.profiles||[]))}catch(e){}}
  useEffect(()=>{refreshProfiles();let active=true;const t=setInterval(async()=>{try{const r=await fetch(API+"/api/vpn/status");const d=await r.json();if(active)setSt(d)}catch(e){}},2500);return()=>{active=false;clearInterval(t)}},[]);
  useEffect(()=>{const p=(profiles||[]).find(x=>x.id==="olom"||x.is_default);if(p&&!profileId){selectProfile(p.id)}},[profiles]);
  function selectProfile(id){
    setProfileId(id);setSaveAsNew(false);
    const p=(profiles||[]).find(x=>x.id===id);
    if(!p)return;
    setProtocol(p.protocol||"pptp");
    setHost(p.host||"");
    setPort(p.port!=null&&p.port!==""?String(p.port):"");
    setUser(p.username||"");
    setProfileName(p.profile_name||p.name||"");
    setRoutes(Array.isArray(p.routes)?p.routes.join(", "):(p.routes||""));
    setConfigContent(p.config_content||"");
  }
  async function connect(){setBusy(true);setError("");try{const body={protocol,routes,name:profileName||"Olom"};if(host)body.host=host;if(port)body.port=Number(port);if(user)body.username=user;if(pass)body.password=pass;if(profileName)body.profile_name=profileName;if(configContent.trim())body.config_content=configContent;const r=await fetch(API+"/api/vpn/connect",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):"اتصال VPN ناموفق بود"));setSt(d.status||d);onNotify&&onNotify("")}catch(e){setError(e.message);onNotify&&onNotify(e.message)}setBusy(false)}
  async function disconnect(){setBusy(true);setError("");try{const r=await fetch(API+"/api/vpn/disconnect",{method:"POST"});if(!r.ok)throw Error("قطع اتصال ناموفق بود");const d=await r.json();setSt(d.status||d)}catch(e){setError(e.message)}setBusy(false)}
  async function saveProfile(){setError("");try{const rawName=(profileName||host||"profile").trim()||"profile";let sid;if(saveAsNew||!profileId||!/^[a-zA-Z0-9_-]{1,48}$/.test(profileId)){sid=rawName.toLowerCase().replace(/[^a-z0-9_-]+/g,"-").replace(/^-+|-+$/g,"").slice(0,40);if(!sid||(profiles||[]).some(p=>p.id===sid))sid=(sid||"profile")+"-"+Date.now().toString(36).slice(-6)}else sid=profileId;const body={id:sid,name:rawName.slice(0,64),protocol,host:host||"",port:port||"",username:user||"",routes:routes||"",profile_name:profileName||rawName,config_content:configContent||"",is_default:sid==="olom"};const r=await fetch(API+"/api/vpn/profiles",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});const d=await r.json();if(!r.ok){const det=d.detail;throw Error(typeof det==="string"?det:(Array.isArray(det)?det.map(x=>x.msg||JSON.stringify(x)).join("; "):"ذخیره پروفایل ناموفق بود"))}await refreshProfiles();setProfileId(d.id);setSaveAsNew(false);onNotify&&onNotify("پروفایل «"+(d.name||d.id)+"» ذخیره شد")}catch(e){setError(e.message)}}
  async function deleteProfile(){if(!profileId)return;if(!confirm("پروفایل حذف شود؟"))return;try{const r=await fetch(`${API}/api/vpn/profiles/${encodeURIComponent(profileId)}`,{method:"DELETE"});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.detail||"حذف ناموفق");await refreshProfiles();setProfileId("");setHost("");setConfigContent("");setProfileName("")}catch(e){setError(e.message)}}
  function addRoutesToTargets(){const list=(routes||"").split(/[,\s]+/).map(x=>x.trim()).filter(Boolean);if(list.length&&onRoutes)onRoutes(list)}
  const state=st?.active?.connected?"connected":st?.active?"connecting":"disconnected";
  const badgeText=state==="connected"?"متصل":state==="connecting"?"در حال اتصال":"قطع";
  return <section className="panel vpn-card" dir="rtl">
    <div className="report-heading"><h2>اتصال VPN</h2><span className={"status-badge "+state} role="status">{badgeText}</span></div>
    <span style={{fontSize:".9em",opacity:.85,marginInlineStart:"8px"}}>پیش‌فرض: Olom / PPTP / 185.110.29.205 (split-tunnel)</span>
    {st?.active&&<p className="vpn-active">فعال: <bdi dir="ltr">{st.active.protocol} - {st.active.name}</bdi></p>}
    {st?.interface_ip&&<p className="vpn-active">IP تونل: <bdi dir="ltr">{st.interface_ip}</bdi></p>}
    {error&&<p className="error">{error}</p>}
    <div className="vpn-profiles-list">
      <div className="report-heading"><h3 style={{margin:0,fontSize:"1em"}}>پروفایل‌های ذخیره‌شده</h3><small>{(profiles||[]).length} مورد</small></div>
      <div className="profile-chips">{(profiles||[]).length===0&&<span className="muted">هنوز پروفایلی ذخیره نشده</span>}{(profiles||[]).map(p=><button type="button" key={p.id} className={"profile-chip"+(profileId===p.id?" active":"")} onClick={()=>selectProfile(p.id)} title={[p.protocol,p.host,p.has_config?"دارای کانفیگ":""].filter(Boolean).join(" | ")}>{(p.name&&p.name.trim())?p.name:p.id}{p.is_default?" ★":""}{p.has_config?" ⚙":""}</button>)}</div>
    </div>
    <div className="vpn-grid">
      <label>پروتکل<select value={protocol} onChange={e=>setProtocol(e.target.value)}>{VPN_PROTOCOLS.map(p=><option key={p} value={p}>{p}</option>)}</select></label>
      <label>نام پروفایل<input value={profileName} onChange={e=>setProfileName(e.target.value)} placeholder="مثلاً Olom یا Office-WG"/></label>
      <label>سرور (host)<input dir="ltr" value={host} onChange={e=>setHost(e.target.value)} placeholder="vpn.example.com"/></label>
      <label>پورت<input dir="ltr" type="number" min="1" max="65535" value={port} onChange={e=>setPort(e.target.value)} placeholder="51820"/></label>
      <label>نام کاربری<input dir="ltr" autoComplete="off" value={user} onChange={e=>setUser(e.target.value)}/></label>
      <label>رمز عبور<input dir="ltr" type="password" autoComplete="new-password" value={pass} onChange={e=>setPass(e.target.value)} placeholder="ذخیره نمی‌شود"/></label>
      <label>مسیرهای ریموت (CIDR)<input dir="ltr" value={routes} onChange={e=>setRoutes(e.target.value)} placeholder="10.10.0.0/24, 192.168.5.0/24"/></label>
      <label className="checkbox-label"><input type="checkbox" checked={saveAsNew} onChange={e=>setSaveAsNew(e.target.checked)}/> ذخیره به‌عنوان پروفایل جدید</label>
    </div>
    <label>فایل پیکربندی (WireGuard/OpenVPN) — همراه پروفایل ذخیره می‌شود<textarea dir="ltr" rows="4" value={configContent} onChange={e=>setConfigContent(e.target.value)} placeholder="[Interface]&#10;PrivateKey = ..."/></label>
    <div className="vpn-actions">
      <button type="button" disabled={busy||state==="connected"} onClick={connect}>اتصال</button>
      <button type="button" className="btn-stop" disabled={busy||state==="disconnected"} onClick={disconnect}>قطع اتصال</button>
      <button type="button" className="btn-save" disabled={busy} onClick={saveProfile}>{saveAsNew?"ذخیره پروفایل جدید":"ذخیره / به‌روزرسانی پروفایل"}</button>
      <button type="button" className="btn-delete" disabled={busy||!profileId||profileId==="olom"} onClick={deleteProfile}>حذف پروفایل</button>
      <button type="button" className="btn-routes" onClick={addRoutesToTargets}>افزودن مسیرها به اهداف اسکن</button>
    </div>
  </section>;
}

function formatDate(value){if(!value)return "—";const d=new Date(value);if(Number.isNaN(d.getTime()))return String(value);const p=n=>String(n).padStart(2,"0");return `${d.getFullYear()}/${p(d.getMonth()+1)}/${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`}
function DeviceReports({mode="devices"}={}){
  const ALL_COLS=[{id:"select",label:"انتخاب",always:true},{id:"ip",label:"IP",always:true},{id:"device_name",label:"نام دستگاه (identity)",always:true},{id:"device_type",label:"نوع دستگاه"},{id:"tags",label:"تگ"},{id:"ping",label:"پینگ"},{id:"ports",label:"پورت‌های باز"},{id:"classification",label:"دسته‌بندی"},{id:"interfaces",label:"اینترفیس‌ها"},{id:"ip_addresses",label:"آدرس‌های IP"},{id:"ip_neighbors",label:"همسایه‌ها"},{id:"wireless_info",label:"وایرلس"},{id:"device_log",label:"لاگ"},{id:"mac_info",label:"MAC"},{id:"first_seen",label:"اولین مشاهده"},{id:"last_seen",label:"آخرین مشاهده"},{id:"seen_count",label:"تعداد مشاهده"},{id:"winbox",label:"Winbox (ستون جدا)"}];
  const defaultVisible=()=>{try{const s=JSON.parse(localStorage.getItem("device_cols")||"null");if(Array.isArray(s)&&s.length)return s}catch(e){}const hide=["interfaces","ip_addresses","ip_neighbors","wireless_info","device_log","mac_info","winbox"];return ALL_COLS.map(c=>c.id).filter(id=>!hide.includes(id))};
  const[rows,setRows]=useState([]),[total,setTotal]=useState(0),[classification,setClassification]=useState("mikrotik_candidate"),[deviceTypeFilter,setDeviceTypeFilter]=useState(""),[port,setPort]=useState(""),[q,setQ]=useState(""),[qInput,setQInput]=useState(""),[qField,setQField]=useState(""),[offset,setOffset]=useState(0),[pageSize,setPageSize]=useState(50),[error,setError]=useState(""),[msg,setMsg]=useState("");const[textModal,setTextModal]=useState(null);const[probeProg,setProbeProg]=useState({total:0,done:0,percent:0,current_ip:"",running:false});
  const[sortBy,setSortBy]=useState("ip"),[sortOrder,setSortOrder]=useState("asc"),[newOnly,setNewOnly]=useState(false),[showAddModal,setShowAddModal]=useState(false),[newIp,setNewIp]=useState(""),[newPorts,setNewPorts]=useState("");
  const[winboxItems,setWinboxItems]=useState([]),[winboxPath,setWinboxPath]=useState(""),[winboxName,setWinboxName]=useState(""),[showWinboxCfg,setShowWinboxCfg]=useState(false),[busyAction,setBusyAction]=useState(false),[toolsDir,setToolsDir]=useState("");
  const[visibleCols,setVisibleCols]=useState(defaultVisible),[showColCfg,setShowColCfg]=useState(false);
  const[selected,setSelected]=useState({}),[editTagIp,setEditTagIp]=useState(null),[editTagVal,setEditTagVal]=useState(""),[editNameIp,setEditNameIp]=useState(null),[editNameVal,setEditNameVal]=useState("");// selected: { [ip]: true } only — never store false
  const[snmpProfiles,setSnmpProfiles]=useState([]),[snmpId,setSnmpId]=useState(""),[snmpRaw,setSnmpRaw]=useState(""),[snmpName,setSnmpName]=useState(""),[showSnmp,setShowSnmp]=useState(false),[snmpBusy,setSnmpBusy]=useState(false);const[dbList,setDbList]=useState([]),[activeDb,setActiveDb]=useState("default"),[newDbName,setNewDbName]=useState(""),[showDbPanel,setShowDbPanel]=useState(false);const[showGroupCfg,setShowGroupCfg]=useState(false),[groupScript,setGroupScript]=useState(""),[groupUser,setGroupUser]=useState("admin"),[groupPass,setGroupPass]=useState("");const[apiUser,setApiUser]=useState("admin"),[apiPass,setApiPass]=useState(""),[apiBusy,setApiBusy]=useState(false);const apiAbortRef={current:null};
  const params=new URLSearchParams();if(classification)params.set("classification",classification);if(deviceTypeFilter)params.set("device_type",deviceTypeFilter);if(port)params.set("has_port",port);if(q)params.set("q",q);if(qField)params.set("q_fields",qField);params.set("sort",sortBy);params.set("order",sortOrder);params.set("new_only",newOnly?"true":"false");params.set("limit",String(pageSize));params.set("offset",String(offset));
  const searchAbortRef={current:null};
  function reloadRows(){
    // Abort any in-flight list request so responses never arrive out of order
    if(searchAbortRef.current){try{searchAbortRef.current.abort()}catch(e){}}
    const ctrl=new AbortController();searchAbortRef.current=ctrl;
    return fetch(`${API}/devices?${params.toString()}`,{signal:ctrl.signal}).then(async r=>{const d=await readJson(r);if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):(d.detail&&JSON.stringify(d.detail))||"خطا در دریافت"));setRows(d.devices||[]);setTotal(d.total||0);setError("")}).catch(e=>{if(e&&e.name==="AbortError")return;throw e})
  }
  useEffect(()=>{let active=true;reloadRows().catch(e=>active&&setError(e.message));return()=>{active=false}},[classification,deviceTypeFilter,port,q,qField,offset,pageSize,sortBy,sortOrder,newOnly]);
  // Debounce the free-text search: wait 350ms after the last keystroke before querying.
  // Enter in the input clears the pending timer for an immediate search.
  const searchTimerRef={current:null};
  useEffect(()=>{if(searchTimerRef.current)clearTimeout(searchTimerRef.current);searchTimerRef.current=setTimeout(()=>{setQ(qInput);setOffset(0)},350);return()=>clearTimeout(searchTimerRef.current)},[qInput]);
  // Clear selection when the visible dataset context changes (not on every poll)
  useEffect(()=>{setSelected({})},[classification,port,q,qField,pageSize,sortBy,sortOrder,newOnly,activeDb]);
  async function refreshWinbox(){try{const r=await fetch(API+"/api/winbox/list");const d=await r.json();if(r.ok){setWinboxItems(d.items||[]);setToolsDir(d.tools_dir||"")}}catch(e){}}
  async function refreshSnmp(){try{const r=await fetch(API+"/api/snmp/profiles");const d=await r.json();if(r.ok){const list=d.profiles||[];setSnmpProfiles(list);const def=list.find(x=>x.is_default)||list[0];if(def){setSnmpId(def.id);setSnmpRaw(def.raw||"");setSnmpName(def.name||def.community||"")}}}catch(e){}}
  async function refreshDb(){try{const r=await fetch(API+"/api/databases");const d=await readJson(r);if(r.ok){setDbList(d.databases||[]);setActiveDb(d.active||"default")}else{setError(typeof d.detail==="string"?d.detail:"خطا در لیست دیتابیس")}}catch(e){setError(e.message||String(e))}}
  useEffect(()=>{refreshWinbox();refreshSnmp();refreshDb()},[]);
  useEffect(()=>{try{localStorage.setItem("device_cols",JSON.stringify(visibleCols))}catch(e){}},[visibleCols]);
  function handleSort(col){if(sortBy===col)setSortOrder(o=>o==="asc"?"desc":"asc");else{setSortBy(col);setSortOrder("asc")}}
  function sortIcon(col){return sortBy===col?(sortOrder==="asc"?"▲":"▼"):"⇅"}
  function colOn(id){return visibleCols.includes(id)}
  function toggleCol(id){const meta=ALL_COLS.find(c=>c.id===id);if(meta&&meta.always)return;setVisibleCols(v=>v.includes(id)?v.filter(x=>x!==id):[...v,id])}
  function toggleSelect(ip){setSelected(s=>{const n={...s};if(n[ip])delete n[ip];else n[ip]=true;return n})}
  function toggleSelectAll(){const ids=rows.map(d=>d.ip);const allOn=ids.length>0&&ids.every(ip=>selected[ip]);setSelected(s=>{const n={...s};ids.forEach(ip=>{if(allOn)delete n[ip];else n[ip]=true});return n})}
  function clearSelection(){setSelected({})}
  const selectedIps=Object.keys(selected).filter(k=>selected[k]===true);
  async function submitNewDevice(e){e.preventDefault();setError("");try{const r=await fetch(API+"/devices/manual",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ip:newIp.trim(),open_ports:newPorts.split(",").map(x=>Number(x.trim())).filter(x=>x>=1&&x<=65535)})});const d=await r.json();if(!r.ok)throw Error(d.detail||"خطا");setShowAddModal(false);setNewIp("");setNewPorts("");setOffset(0);setMsg("دستگاه ثبت شد");reloadRows()}catch(e){setError(e.message)}}
  async function openWinbox(ip){setError("");setMsg("");try{const def=(winboxItems||[]).find(x=>x.is_default);const qid=def?("?winbox_id="+encodeURIComponent(def.id)):"";const r=await fetch(`${API}/devices/${encodeURIComponent(ip)}/winbox`+qid,{method:"POST"});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"Winbox");setMsg("Winbox: "+ip)}catch(e){setError(e.message);setShowWinboxCfg(true)}}
  async function addWinboxPath(){if(!winboxPath.trim()){setError("مسیر لازم است");return}setBusyAction(true);try{const r=await fetch(API+"/api/winbox/list",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:winboxName||"",path:winboxPath.trim(),is_default:!(winboxItems||[]).length})});const d=await r.json();if(!r.ok)throw Error(d.detail||"خطا");setWinboxItems(d.items||[]);setWinboxPath("");setWinboxName("");setMsg("مسیر اضافه شد")}catch(e){setError(e.message)}setBusyAction(false)}
  async function setDefaultWinbox(id){setBusyAction(true);try{const r=await fetch(`${API}/api/winbox/list/${encodeURIComponent(id)}/default`,{method:"PUT"});const d=await r.json();if(!r.ok)throw Error(d.detail||"خطا");setWinboxItems(d.items||[])}catch(e){setError(e.message)}setBusyAction(false)}
  async function removeWinbox(id){if(!confirm("حذف؟"))return;setBusyAction(true);try{const r=await fetch(`${API}/api/winbox/list/${encodeURIComponent(id)}`,{method:"DELETE"});const d=await r.json();if(!r.ok)throw Error(d.detail||"خطا");setWinboxItems(d.items||[])}catch(e){setError(e.message)}setBusyAction(false)}
  async function doBackup(){
    setError("");
    const label=window.prompt("نام/برچسب این نسخه پشتیبان (اختیاری):","")??null;
    if(label===null)return; // cancelled
    setBusyAction(true);
    try{
      const q=label.trim()?("?label="+encodeURIComponent(label.trim())):"";
      const r=await fetch(API+"/devices/backup"+q);
      if(!r.ok){let det="پشتیبان‌گیری ناموفق";try{const j=await r.json();det=typeof j.detail==="string"?j.detail:det}catch(_){}
        throw Error(det)}
      const blob=await r.blob();
      const disp=r.headers.get("X-Backup-Filename")||r.headers.get("Content-Disposition")||"";
      let filename=r.headers.get("X-Backup-Filename");
      if(!filename){
        const m=/filename="?([^";]+)"?/.exec(disp);
        filename=m?m[1]:`backup_${activeDb}_${new Date().toISOString().slice(0,19).replace(/[:T]/g,"")}.db`;
      }
      // Ask user where to save when File System Access API is available (Chrome/Edge)
      if(window.showSaveFilePicker){
        try{
          const handle=await window.showSaveFilePicker({
            suggestedName:filename,
            types:[{description:"SQLite database",accept:{"application/x-sqlite3":[".db"]}}]
          });
          const writable=await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          setMsg("پشتیبان ذخیره شد: "+handle.name+" (دیتابیس "+activeDb+")");
          setBusyAction(false);
          return;
        }catch(e){
          if(e&&e.name==="AbortError"){setBusyAction(false);return}
          // fall through to download
        }
      }
      const a=document.createElement("a");
      a.href=URL.createObjectURL(blob);
      a.download=filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(a.href);
      setMsg("پشتیبان دانلود شد: "+filename+" — مسیر ذخیره را در دیالوگ مرورگر انتخاب کنید");
    }catch(e){setError(e.message)}
    setBusyAction(false);
  }
  async function doRestore(e){
    const f=e.target.files&&e.target.files[0];
    if(!f)return;
    if(!confirm("فایل «"+f.name+"» روی دیتابیس فعال «"+activeDb+"» بازیابی شود؟\nنسخه فعلی به‌صورت .pre_restore نگه داشته می‌شود.")){
      e.target.value="";return}
    setBusyAction(true);setError("");
    try{
      const fd=new FormData();fd.append("file",f);
      const r=await fetch(API+"/devices/restore",{method:"POST",body:fd});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):"بازیابی ناموفق"));
      setMsg("بازیابی موفق در «"+(d.active_database||activeDb)+"»: "+(d.devices||0)+" دستگاه از "+(d.source_filename||f.name));
      setSelected({});setOffset(0);await reloadRows();await refreshDb();
    }catch(err){setError(err.message)}
    setBusyAction(false);e.target.value="";
  }
  async function importTags(e){
    const f=e.target.files&&e.target.files[0];
    if(!f)return;
    setBusyAction(true);setError("");setMsg("");
    try{
      const fd=new FormData();fd.append("file",f);
      const r=await fetch(API+"/devices/import-tags",{method:"POST",body:fd});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):"ورود تگ ناموفق"));
      const miss=d.missing_count||0;
      setMsg("انتقال تگ: "+(d.updated||0)+" به‌روز شد"+(miss?("، "+miss+" IP در دیتابیس نبود"):"")+" — فایل: "+(d.source_filename||f.name));
      setOffset(0);await reloadRows();
    }catch(err){setError(err.message)}
    setBusyAction(false);e.target.value="";
  }
  async function doFullBackup(){
    setError("");setBusyAction(true);
    try{
      const r=await fetch(API+"/api/backup/full");
      if(!r.ok){let det="پشتیبان‌گیری کامل ناموفق";try{const j=await r.json();det=typeof j.detail==="string"?j.detail:det}catch(_){}
        throw Error(det)}
      const blob=await r.blob();
      let filename=r.headers.get("X-Backup-Filename");
      if(!filename){
        const disp=r.headers.get("Content-Disposition")||"";
        const m=/filename="?([^";]+)"?/.exec(disp);
        filename=m?m[1]:`mikrotik_scanner_full_${new Date().toISOString().slice(0,19).replace(/[:T]/g,"")}.zip`;
      }
      if(window.showSaveFilePicker){
        try{
          const handle=await window.showSaveFilePicker({
            suggestedName:filename,
            types:[{description:"ZIP backup",accept:{"application/zip":[".zip"]}}]
          });
          const writable=await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          setMsg("پشتیبان کامل ذخیره شد: "+handle.name);
          setBusyAction(false);
          return;
        }catch(e){
          if(e&&e.name==="AbortError"){setBusyAction(false);return}
        }
      }
      const a=document.createElement("a");
      a.href=URL.createObjectURL(blob);
      a.download=filename;
      document.body.appendChild(a);a.click();a.remove();
      URL.revokeObjectURL(a.href);
      setMsg("پشتیبان کامل دانلود شد: "+filename);
    }catch(err){setError(err.message)}
    setBusyAction(false);
  }
  async function doFullRestore(e){
    const f=e.target.files&&e.target.files[0];
    if(!f)return;
    if(!confirm("بازیابی کامل از «"+f.name+"»؟\nهمه دیتابیس‌ها و فایل‌های کانفیگ (SNMP/VPN/…) جایگزین می‌شوند.")){
      e.target.value="";return}
    setBusyAction(true);setError("");
    try{
      const fd=new FormData();fd.append("file",f);
      const r=await fetch(API+"/api/backup/full/restore",{method:"POST",body:fd});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):"بازیابی کامل ناموفق"));
      const dbs=(d.databases||[]).map(x=>x.name+(x.devices!=null?(":"+x.devices):"")).join("، ")||"—";
      setMsg("بازیابی کامل موفق — دیتابیس‌ها: "+dbs+" — فایل‌ها: "+((d.files||[]).length));
      setSelected({});setOffset(0);await refreshDb();await reloadRows();
    }catch(err){setError(err.message)}
    setBusyAction(false);e.target.value="";
  }
  async function saveTag(ip){try{const r=await fetch(`${API}/devices/${encodeURIComponent(ip)}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({tags:editTagVal})});const d=await r.json();if(!r.ok)throw Error(d.detail||"خطا");setEditTagIp(null);reloadRows();setMsg("تگ ذخیره شد")}catch(e){setError(e.message)}}
  async function saveName(ip){try{const r=await fetch(`${API}/devices/${encodeURIComponent(ip)}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({device_name:editNameVal})});const d=await r.json();if(!r.ok)throw Error(d.detail||"خطا");setEditNameIp(null);reloadRows();setMsg("نام ذخیره شد")}catch(e){setError(e.message)}}
  async function saveSnmpProfile(){setSnmpBusy(true);setError("");try{const body={id:snmpId||undefined,name:snmpName||undefined,raw:snmpRaw,is_default:true};const r=await fetch(API+"/api/snmp/profiles",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"ذخیره SNMP ناموفق");await refreshSnmp();setMsg("پروفایل SNMP ذخیره شد: "+(d.name||d.community))}catch(e){setError(e.message)}setSnmpBusy(false)}
  async function setDefaultSnmp(id){try{const r=await fetch(`${API}/api/snmp/profiles/${encodeURIComponent(id)}/default`,{method:"PUT"});if(!r.ok)throw Error("خطا");await refreshSnmp()}catch(e){setError(e.message)}}
  async function deleteSnmp(id){if(!confirm("حذف پروفایل SNMP؟"))return;try{const r=await fetch(`${API}/api/snmp/profiles/${encodeURIComponent(id)}`,{method:"DELETE"});if(!r.ok)throw Error("خطا");await refreshSnmp()}catch(e){setError(e.message)}}
  const probeAbortRef={current:null};
  async function probeSnmp(ips){if(!ips.length){setError("دستگاهی انتخاب نشده");return}if(probeAbortRef.current){try{probeAbortRef.current.abort()}catch(e){}}const ac=new AbortController();probeAbortRef.current=ac;setSnmpBusy(true);setError("");setProbeProg({total:ips.length,done:0,percent:0,current_ip:"",running:true});setMsg("در حال خواندن اطلاعات دستگاه‌ها از SNMP…");const progTimer=setInterval(async()=>{try{const pr=await fetch(API+"/api/snmp/probe/progress");const pd=await pr.json();setProbeProg(pd)}catch(e){}},500);try{const r=await fetch(API+"/api/snmp/probe",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ips,profile_id:snmpId||undefined,save_names:true,api_username:groupUser||undefined,api_password:groupPass||undefined,api_port:8728}),signal:ac.signal});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"SNMP ناموفق");const ok=(d.results||[]).filter(x=>x.ok).length;const canceled=d.canceled?` (متوقف شد پس از ${d.probed||ok} دستگاه)`:"";setMsg(`اطلاعات ${ok} از ${ips.length} دستگاه خوانده شد${canceled} و در دیتابیس «${d.database||activeDb}» + پوشه ip_info ذخیره شد (${d.saved||0})`);reloadRows()}catch(e){if(e.name==="AbortError"){setMsg("خواندن اطلاعات متوقف شد.");reloadRows()}else setError(e.message)}finally{clearInterval(progTimer);probeAbortRef.current=null;setSnmpBusy(false);setProbeProg(p=>({...p,running:false}))}}
  async function stopProbe(){try{await fetch(API+"/api/snmp/probe/cancel",{method:"POST"});if(probeAbortRef.current)probeAbortRef.current.abort()}catch(e){}setMsg("درخواست توقف ارسال شد…")}
  async function stopApiProbe(){try{await fetch(API+"/api/devices/probe-api/cancel",{method:"POST"});if(apiAbortRef.current)apiAbortRef.current.abort()}catch(e){}setMsg("درخواست توقف API ارسال شد…")}
  async function probeApi(ips){
    if(!ips.length){setError("دستگاهی انتخاب نشده");return}
    if(!(apiUser||"").trim()){setError("نام کاربری API لازم است");return}
    if(apiAbortRef.current){try{apiAbortRef.current.abort()}catch(e){}}
    const ac=new AbortController();apiAbortRef.current=ac;
    setApiBusy(true);setError("");
    setProbeProg({total:ips.length,done:0,percent:0,current_ip:"",running:true});
    setMsg("در حال خواندن اطلاعات از RouterOS API (identity / interface / wireless mode / IP)…");
    const progTimer=setInterval(async()=>{try{const pr=await fetch(API+"/api/devices/probe-api/progress");const pd=await pr.json();setProbeProg(pd)}catch(e){}},400);
    try{
      const r=await fetch(API+"/api/devices/probe-api",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ips,username:apiUser.trim(),password:apiPass||"",port:8728,timeout:12,save:true}),signal:ac.signal});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"خواندن API ناموفق");
      const ok=d.ok||0;
      const canceled=d.canceled?` (متوقف شد پس از ${d.probed||ok})`:"";
      setMsg(`API: ${ok} از ${ips.length} موفق${canceled} — ذخیره در دیتابیس «${d.database||activeDb}» (${d.saved||0}) — نوع دستگاه از mode وایرلس (مثل station bridge → ST)`);
      reloadRows();
    }catch(e){
      if(e.name==="AbortError"){setMsg("خواندن API متوقف شد.");reloadRows()}
      else setError(e.message);
    }finally{
      clearInterval(progTimer);apiAbortRef.current=null;setApiBusy(false);
      setProbeProg(p=>({...p,running:false}));
    }
  }
  function selectedMikrotikWithApi(){
    // Prefer devices known to have 8728 open; if selection is not on this page, still include the IP
    const fromRows=rows.filter(d=>selected[d.ip]&&(d.open_ports||[]).includes(8728)).map(d=>d.ip);
    const rowSet=new Set(rows.map(d=>d.ip));
    const extras=selectedIps.filter(ip=>!rowSet.has(ip));
    const knownClosed=rows.filter(d=>selected[d.ip]&&!(d.open_ports||[]).includes(8728)).map(d=>d.ip);
    // include fromRows + extras; exclude only those on this page known without 8728
    return [...new Set([...fromRows,...extras])];
  }
  async function pushConfig(){
    const ips=selectedMikrotikWithApi();
    if(!ips.length){setError("هیچ دستگاهی با پورت API 8728 در انتخاب‌ها نیست (دستگاه‌های صفحه جاری بدون 8728 کنار گذاشته شدند)");return}
    const script=(snmpRaw||"").trim();
    if(!script){setError("متن کانفیگ خالی است — ابتدا کانفیگ را در کادر SNMP وارد کنید");setShowSnmp(true);return}
    if(!confirm("کانفیگ روی "+ips.length+" دستگاه (پورت 8728) اجرا شود؟\n\n"+script.slice(0,200)+(script.length>200?"…":"")))return;
    const username=window.prompt("نام کاربری Winbox/API دستگاه‌ها:","admin");
    if(username===null||!username.trim())return;
    const password=window.prompt("رمز عبور Winbox/API:","")??"";
    setSnmpBusy(true);setError("");setMsg("در حال انتقال کانفیگ به "+ips.length+" دستگاه از طریق API…");
    try{
      const r=await fetch(API+"/api/devices/push-config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ips,username:username.trim(),password,script,port:8728})});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):"انتقال کانفیگ ناموفق"));
      const fails=(d.results||[]).filter(x=>!x.ok);
      let msg=`انتقال کانفیگ: ${d.ok||0} موفق، ${d.failed||0} ناموفق از ${d.total||ips.length}`;
      if(fails.length)msg+=" — خطا: "+fails.slice(0,3).map(x=>x.ip+": "+(x.error||"?")).join(" | ");
      setMsg(msg);
      if(fails.length&&!d.ok)setError(msg);
    }catch(e){setError(e.message)}
    setSnmpBusy(false);
  }
  function openGroupConfig(){
    const ips=selectedMikrotikWithApi();
    if(!ips.length){setError("هیچ دستگاهی با پورت API 8728 در انتخاب‌ها نیست");return}
    setError("");
    if(!groupScript.trim())setGroupScript('/user add name=olom1 password="Olom@2026$" group=full');
    setShowGroupCfg(true);
  }
  async function submitGroupConfig(e){
    e.preventDefault();
    const ips=selectedMikrotikWithApi();
    if(!ips.length){setError("هیچ دستگاهی با پورت API 8728 در انتخاب‌ها نیست");return}
    const script=(groupScript||"").trim();
    if(!script){setError("متن کانفیگ را وارد کنید");return}
    if(!(groupUser||"").trim()){setError("نام کاربری لازم است");return}
    if(!confirm("کانفیگ گروهی روی "+ips.length+" دستگاه اجرا شود؟\n\n"+script.slice(0,240)+(script.length>240?"…":"")))return;
    setSnmpBusy(true);setError("");setMsg("در حال انتقال کانفیگ گروهی به "+ips.length+" دستگاه…");
    try{
      const r=await fetch(API+"/api/devices/push-config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ips,username:groupUser.trim(),password:groupPass||"",script,port:8728})});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):"انتقال کانفیگ ناموفق"));
      const fails=(d.results||[]).filter(x=>!x.ok);
      let msg=`کانفیگ گروهی: ${d.ok||0} موفق، ${d.failed||0} ناموفق از ${d.total||ips.length}`;
      if(fails.length)msg+=" — خطا: "+fails.slice(0,5).map(x=>x.ip+": "+(x.error||"?")).join(" | ");
      setMsg(msg);
      if(fails.length&&!d.ok)setError(msg);
      else setShowGroupCfg(false);
    }catch(err){setError(err.message)}
    setSnmpBusy(false);
  }
  async function switchDb(name){setBusyAction(true);setError("");try{const r=await fetch(API+"/api/databases/active",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({name})});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"تعویض دیتابیس ناموفق");setDbList(d.databases||[]);setActiveDb(d.active||name);setOffset(0);setSelected({});setMsg("دیتابیس فعال: "+(d.active||name));reloadRows()}catch(e){setError(e.message)}setBusyAction(false)}
  async function createDb(){if(!newDbName.trim()){setError("نام دیتابیس را وارد کنید");return}setBusyAction(true);try{const r=await fetch(API+"/api/databases",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:newDbName.trim()})});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"ایجاد ناموفق");setDbList(d.databases||[]);setNewDbName("");setMsg("دیتابیس ساخته شد");await switchDb(newDbName.trim())}catch(e){setError(e.message)}setBusyAction(false)}
  async function removeDb(name){if(!confirm("حذف دیتابیس «"+name+"»؟"))return;setBusyAction(true);try{const r=await fetch(API+"/api/databases/"+encodeURIComponent(name),{method:"DELETE"});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"حذف ناموفق");setDbList(d.databases||[]);setActiveDb(d.active||"default");reloadRows()}catch(e){setError(e.message)}setBusyAction(false)}
  async function dedupeDevices(){if(!confirm("دستگاه‌های با نام identity یکسان حذف شوند؟ (جدیدترین نگه داشته می‌شود؛ دستگاه‌هایی که تگ (tags) دارند حفظ می‌شوند)"))return;setBusyAction(true);setError("");try{const r=await fetch(API+"/devices/dedupe",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({by:"device_name"})});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:"حذف تکراری ناموفق");setMsg("تکراری‌ها: "+(d.removed||0)+" حذف، "+(d.total_remaining||0)+" باقی‌ماند");setOffset(0);reloadRows()}catch(e){setError(e.message)}setBusyAction(false)}
  async function deleteSelected(){if(!selectedIps.length)return;if(!confirm(selectedIps.length+" دستگاه حذف شوند؟"))return;setBusyAction(true);try{const r=await fetch(API+"/devices/delete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ips:selectedIps})});const d=await r.json();if(!r.ok)throw Error(d.detail||"حذف ناموفق");setMsg((d.deleted||0)+" دستگاه حذف شد");setSelected({});reloadRows()}catch(e){setError(e.message)}setBusyAction(false)}
  async function exportExcelSelected(){
    if(!selectedIps.length){setError("دستگاهی انتخاب نشده");return}
    setBusyAction(true);setError("");
    try{
      const r=await fetch(API+"/devices/export.xlsx",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ips:selectedIps})});
      if(!r.ok){
        let detail="خروجی اکسل ناموفق";
        try{const d=await r.json();detail=typeof d.detail==="string"?d.detail:detail}catch(e){}
        throw Error(detail);
      }
      const blob=await r.blob();
      const cd=r.headers.get("Content-Disposition")||"";
      let filename="devices_selected.xlsx";
      const m=cd.match(/filename="?([^"]+)"?/i);
      if(m)filename=m[1];
      const url=URL.createObjectURL(blob);
      const a=document.createElement("a");
      a.href=url;a.download=filename;
      document.body.appendChild(a);a.click();a.remove();
      URL.revokeObjectURL(url);
      setMsg("فایل اکسل برای "+selectedIps.length+" دستگاه ذخیره شد: "+filename);
    }catch(e){setError(e.message)}
    setBusyAction(false);
  }
  const pageCount=Math.max(1,Math.ceil(total/pageSize));const page=Math.min(pageCount,Math.floor(offset/pageSize)+1);
  const csvParams=new URLSearchParams(params);csvParams.delete("offset");csvParams.set("limit","100000");
  const paginationBar=<div className="report-pagination"><label className="page-size">تعداد در صفحه<select value={pageSize} onChange={e=>{setPageSize(Number(e.target.value));setOffset(0)}}><option value="50">50</option><option value="100">100</option><option value="200">200</option><option value="100000">همه</option></select></label><button type="button" disabled={page<=1} onClick={()=>setOffset(0)}>صفحه اول</button><button type="button" disabled={page<=1} onClick={()=>setOffset(Math.max(0,offset-pageSize))}>قبلی</button><span className="page-indicator">صفحه {page.toLocaleString("fa-IR")} از {pageCount.toLocaleString("fa-IR")} — کل {total.toLocaleString("fa-IR")}</span><button type="button" disabled={page>=pageCount} onClick={()=>setOffset(offset+pageSize)}>بعدی</button><button type="button" disabled={page>=pageCount} onClick={()=>setOffset((pageCount-1)*pageSize)}>صفحه آخر</button><label className="page-size db-inline">دیتابیس فعال<select value={activeDb} disabled={busyAction} onChange={e=>switchDb(e.target.value)}>{(dbList&&dbList.length?dbList:[{name:activeDb||"default",active:true,devices:0}]).map(d=><option key={d.name} value={d.name}>{d.name}{d.active?" ★":""} ({d.devices||0})</option>)}</select></label><button type="button" className="btn-db-mini" onClick={()=>setShowDbPanel(s=>!s)} title="مدیریت دیتابیس‌ها">⚙</button></div>;
  function isMikrotik(d){return d.classification==="mikrotik_candidate"||(d.open_ports||[]).some(p=>p===8291||p===8728)}
  const sortMap={ip:"ip",device_name:"device_name",device_type:"device_type",tags:"tags",ping:"ping",ports:"ports",classification:"classification",first_seen:"first_seen",last_seen:"last_seen",seen_count:"seen_count"};
  const isSystem = mode === "system";
  return <section className={"panel device-reports"+(isSystem?" system-admin":"")} dir="rtl">
    <div className="report-heading">
      <h2>{isSystem ? "راهبری سیستم" : "مدیریت دستگاه‌های شبکه"}</h2>
      <span className="muted" style={{fontSize:".9em"}}>دیتابیس فعال: <b>{activeDb}</b>{!isSystem && <> — {total.toLocaleString("fa-IR")} دستگاه</>}</span>
    </div>
    {isSystem ? (
    <div className="device-toolbar ribbon-body" role="toolbar" aria-label="راهبری سیستم">
      <div className="tool-group">
        <span className="tool-label">پیکربندی</span>
        <button type="button" className={"tool-btn"+(showSnmp?" active":"")} onClick={()=>setShowSnmp(s=>!s)}><RbIcon name="snmp"/><span>کانفیگ SNMP</span></button>
        <button type="button" className={"tool-btn"+(showWinboxCfg?" active":"")} onClick={()=>setShowWinboxCfg(s=>!s)}><RbIcon name="winbox"/><span>مسیر Winbox</span></button>
        <button type="button" className={"tool-btn"+(showColCfg?" active":"")} onClick={()=>setShowColCfg(s=>!s)}><RbIcon name="columns"/><span>نمایش فیلدها</span></button>
        <button type="button" className={"tool-btn"+(showDbPanel?" active":"")} onClick={()=>setShowDbPanel(s=>!s)}><RbIcon name="database"/><span>دیتابیس: {activeDb}</span></button>
      </div>
      <div className="tool-group">
        <span className="tool-label">پشتیبان</span>
        <button type="button" className="tool-btn primary" disabled={busyAction} onClick={doFullBackup}><RbIcon name="backup"/><span>پشتیبان‌گیری کامل</span></button>
        <label className="tool-btn tool-file primary-outline">
          <input type="file" accept=".zip,application/zip" hidden onChange={doFullRestore} disabled={busyAction}/>
          <RbIcon name="restore"/><span>بازیابی کامل</span>
        </label>
      </div>
    </div>
    ) : (
    <div className="device-toolbar ribbon-body" role="toolbar" aria-label="عملیات دستگاه‌ها">
      <div className="tool-group">
        <span className="tool-label">دستگاه‌ها</span>
        <button type="button" className="tool-btn" onClick={()=>setShowAddModal(s=>!s)}><RbIcon name="add"/><span>افزودن دستی</span></button>
        <button type="button" className="tool-btn danger" disabled={busyAction||!selectedIps.length} onClick={deleteSelected}><RbIcon name="trash"/><span>حذف ({selectedIps.length})</span></button>
        <button type="button" className="tool-btn warn" disabled={busyAction} onClick={dedupeDevices}><RbIcon name="dedupe"/><span>حذف تکراری</span></button>
        <button type="button" className="tool-btn muted-btn" disabled={!selectedIps.length} onClick={clearSelection}><RbIcon name="clear"/><span>لغو انتخاب</span></button>
      </div>
      <div className="tool-group">
        <span className="tool-label">خواندن</span>
        <button type="button" className="tool-btn" disabled={snmpBusy||!selectedIps.length} onClick={()=>probeSnmp(selectedIps)}><RbIcon name="read"/><span>خواندن اطلاعات ({selectedIps.length})</span></button>
        <button type="button" className="tool-btn" disabled={snmpBusy||!selectedIps.length} onClick={pushConfig}><RbIcon name="config"/><span>انتقال کانفیگ</span></button>
        <button type="button" className="tool-btn" disabled={snmpBusy||!selectedIps.length} onClick={openGroupConfig}><RbIcon name="group"/><span>کانفیگ گروهی</span></button>
      </div>
      <div className="tool-group">
        <span className="tool-label">نمایش</span>
        <button type="button" className={"tool-btn"+(newOnly?" active":"")} onClick={()=>{setNewOnly(v=>!v);setOffset(0)}}><RbIcon name="filter"/><span>فقط جدید</span></button>
      </div>
      <div className="tool-group">
        <span className="tool-label">خروجی</span>
        <a className="tool-btn tool-link" href={`${API}/devices/export.csv?${csvParams.toString()}`}><RbIcon name="csv"/><span>خروجی CSV</span></a>
        <button type="button" className="tool-btn" disabled={busyAction||!selectedIps.length} onClick={exportExcelSelected}><RbIcon name="excel"/><span>خروجی Excel</span></button>
        <label className="tool-btn tool-file">
          <input type="file" accept=".xlsx,.xlsm,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" hidden onChange={importTags} disabled={busyAction}/>
          <RbIcon name="tag"/><span>انتقال تگ</span>
        </label>
      </div>
    </div>
    )}

    {showColCfg&&<div className="col-cfg">{ALL_COLS.filter(c=>!c.always).map(c=><label key={c.id} className="col-cfg-item"><input type="checkbox" checked={colOn(c.id)} onChange={()=>toggleCol(c.id)}/>{c.label}</label>)}</div>}
    {showGroupCfg&&<div className="group-cfg-panel">
      <h3 style={{marginTop:0}}>انتقال کانفیگ گروهی (API / پورت 8728)</h3>
      <p className="muted">دستگاه‌های انتخاب‌شده با پورت API باز: <b>{selectedMikrotikWithApi().length}</b> — دستورات RouterOS را وارد کنید، سپس یوزر و پسورد Winbox را بزنید.</p>
      <form onSubmit={submitGroupConfig}>
        <label>دستورات کانفیگ<textarea dir="ltr" rows={5} value={groupScript} onChange={e=>setGroupScript(e.target.value)} placeholder={'/user add name=olom1 password="Olom@2026$" group=full'} required/></label>
        <div className="winbox-add-form">
          <label>نام کاربری API<input dir="ltr" value={groupUser} onChange={e=>setGroupUser(e.target.value)} required/></label>
          <label>رمز عبور API<input dir="ltr" type="password" value={groupPass} onChange={e=>setGroupPass(e.target.value)}/></label>
        </div>
        <div className="vpn-actions">
          <button type="submit" className="btn-group-cfg" disabled={snmpBusy}>{snmpBusy?"در حال اجرا…":"اجرا روی دستگاه‌های انتخاب‌شده"}</button>
          <button type="button" disabled={snmpBusy} onClick={()=>setShowGroupCfg(false)}>انصراف</button>
        </div>
      </form>
    </div>}
    {showDbPanel&&<div className="db-panel">
      <h3 style={{marginTop:0}}>مدیریت پایگاه‌داده</h3>
      <p className="muted">لیست دستگاه‌ها از دیتابیس فعال خوانده می‌شود. اسکن را می‌توانید بعداً به دیتابیس دلخواه منتقل کنید.</p>
      <div className="profile-chips">{(dbList||[]).map(d=><button type="button" key={d.name} className={"profile-chip"+(activeDb===d.name?" active":"")} onClick={()=>switchDb(d.name)}>{d.name}{d.active?" ★":""} <small>({d.devices||0})</small></button>)}</div>
      <div className="winbox-add-form"><label>نام دیتابیس جدید<input value={newDbName} onChange={e=>setNewDbName(e.target.value)} placeholder="مثلاً olom-site1"/></label><button type="button" className="btn-save" disabled={busyAction} onClick={createDb}>ایجاد و فعال‌سازی</button></div>
      <div className="vpn-actions" style={{marginTop:8}}>{(dbList||[]).filter(d=>d.name!=="default").map(d=><button key={"del-"+d.name} type="button" className="btn-delete" disabled={busyAction||d.active} onClick={()=>removeDb(d.name)}>حذف {d.name}</button>)}</div>
    </div>}
    {showAddModal&&<form className="add-device-form" onSubmit={submitNewDevice}><label>IP<input dir="ltr" required value={newIp} onChange={e=>setNewIp(e.target.value)}/></label><label>پورت‌ها<input dir="ltr" value={newPorts} onChange={e=>setNewPorts(e.target.value)} placeholder="8291,8728"/></label><button type="submit">ثبت</button></form>}
    {showSnmp&&<div className="snmp-cfg panel-inner">
      <h3 style={{marginTop:0}}>پروفایل‌های SNMP (سبک MikroTik)</h3>
      <p className="muted">community را مطابق روتر وارد کنید. نام خوانده‌شده همان <b dir="ltr">/system identity</b> میکروتیک است (از طریق SNMP sysName).<br/>مثال community: <code dir="ltr">set [ find default=yes ] addresses=0.0.0.0/0 name=Olom@Pez write-access=no</code></p>
      <div className="profile-chips">{(snmpProfiles||[]).map(p=><button type="button" key={p.id} className={"profile-chip"+(snmpId===p.id?" active":"")} onClick={()=>{setSnmpId(p.id);setSnmpRaw(p.raw||"");setSnmpName(p.name||p.community||"")}}>{p.name||p.community||p.id}{p.is_default?" ★":""}</button>)}</div>
      <label>نام / Community<input dir="ltr" value={snmpName} onChange={e=>setSnmpName(e.target.value)} placeholder="Olom@Pez"/></label>
      <label>متن کانفیگ MikroTik<textarea dir="ltr" rows={3} value={snmpRaw} onChange={e=>setSnmpRaw(e.target.value)} placeholder={"/snmp set enabled=yes trap-version=2\n/snmp community\nset [ find default=yes ] addresses=0.0.0.0/0 name=Olom@Pez write-access=no\n/snmp community remove [ find name=\"public\" ]"}/></label>
      <div className="vpn-actions">
        <button type="button" className="btn-save" disabled={snmpBusy} onClick={saveSnmpProfile}>ذخیره پروفایل SNMP (پیش‌فرض)</button>
        <button type="button" disabled={snmpBusy||!snmpId} onClick={()=>setDefaultSnmp(snmpId)}>انتخاب به‌عنوان پیش‌فرض</button>
        <button type="button" className="btn-delete" disabled={snmpBusy||!snmpId} onClick={()=>deleteSnmp(snmpId)}>حذف</button>
        <button type="button" className="btn-probe" disabled={snmpBusy||!selectedIps.length} onClick={()=>probeSnmp(selectedIps)}>خواندن اطلاعات دستگاه‌ها</button>
        <button type="button" className="btn-push" disabled={snmpBusy||!selectedIps.length} onClick={pushConfig}>انتقال کانفیگ</button>
      </div>
    </div>}
    {showWinboxCfg&&<div className="winbox-cfg"><h3 style={{marginTop:0}}>مدیریت Winbox (چند مسیر)</h3>
      {toolsDir&&<p dir="ltr" className="muted" style={{fontSize:".85em"}}>tools dir: {toolsDir}</p>}
      <div className="winbox-list">{(winboxItems||[]).map(w=><div key={w.id} className={"winbox-row"+(w.is_default?" is-default":"")}><div><b>{w.name||"Winbox"}</b>{w.is_default&&<span className="badge-default"> پیش‌فرض</span>}<div dir="ltr" className="muted" style={{fontSize:".85em"}}>{w.path}</div></div><div className="winbox-row-actions"><button type="button" disabled={busyAction||w.is_default} onClick={()=>setDefaultWinbox(w.id)}>پیش‌فرض</button><button type="button" className="btn-delete" disabled={busyAction} onClick={()=>removeWinbox(w.id)}>حذف</button></div></div>)}</div>
      <div className="winbox-add-form"><label>نام<input value={winboxName} onChange={e=>setWinboxName(e.target.value)}/></label><label>مسیر<input dir="ltr" value={winboxPath} onChange={e=>setWinboxPath(e.target.value)} placeholder="D:\\winbox64\\winbox64.exe"/></label><button type="button" disabled={busyAction} onClick={addWinboxPath}>افزودن مسیر</button></div>
    </div>}
    {!isSystem&&(
    <>
    <div className="probe-bar">
      <div className="probe-api-creds">
        <label>کاربر API<input dir="ltr" value={apiUser} onChange={e=>setApiUser(e.target.value)} placeholder="admin" disabled={apiBusy||snmpBusy}/></label>
        <label>رمز API<input dir="ltr" type="password" value={apiPass} onChange={e=>setApiPass(e.target.value)} placeholder="password" disabled={apiBusy||snmpBusy}/></label>
      </div>
      <button type="button" className="btn-action btn-probe-api" disabled={apiBusy||snmpBusy||!selectedIps.length||!(apiUser||"").trim()} onClick={()=>probeApi(selectedIps)}>
        {apiBusy?"در حال خواندن API…":`خواندن با API (${selectedIps.length})`}
      </button>
      <button type="button" className="btn-action btn-stop-probe" disabled={!apiBusy} onClick={stopApiProbe}>
        توقف API
      </button>
      <span className="probe-bar-sep"/>
      <button type="button" className="btn-action btn-probe btn-probe-main" disabled={snmpBusy||apiBusy||!selectedIps.length} onClick={()=>probeSnmp(selectedIps)}>
        {snmpBusy?"در حال خواندن SNMP…":`خواندن SNMP (${selectedIps.length})`}
      </button>
      <button type="button" className="btn-action btn-stop-probe" disabled={!snmpBusy} onClick={stopProbe}>
        توقف SNMP
      </button>
      <span className="muted" style={{fontSize:".85em",width:"100%"}}>
        <b>خواندن با API</b> برای تشخیص دقیق نوع دستگاه (مثلاً station bridge → ST) ضروری است — یوزر و رمز RouterOS را وارد کنید.
      </span>
      {(snmpBusy||apiBusy)&&<div className="probe-progress" style={{width:"100%",marginTop:8}}>
        <div className="progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={probeProg.percent||0}>
          <div className="progress-fill" style={{width:(probeProg.percent||0)+"%"}}/>
        </div>
        <div className="progress-meta" style={{marginTop:4,fontSize:".85em"}}>
          <span>{(probeProg.done||0).toLocaleString("fa-IR")} از {(probeProg.total||0).toLocaleString("fa-IR")}</span>
          <span>{probeProg.percent||0}٪</span>
          {probeProg.current_ip&&<span>هدف: <bdi dir="ltr">{probeProg.current_ip}</bdi></span>}
        </div>
      </div>}
    </div>
    {textModal&&<div className="modal-overlay" onClick={()=>setTextModal(null)}><div className="modal-box text-view-modal" dir="rtl" onClick={e=>e.stopPropagation()}>
      <h3 style={{marginTop:0}}>{textModal.title}</h3>
      {textModal.editable
        ? <textarea className="text-view-textarea" dir="ltr" rows={12} value={textModal.text} onChange={e=>setTextModal(m=>({...m,text:e.target.value}))}/>
        : <pre className="text-view-pre" dir="ltr">{textModal.text}</pre>}
      <div className="modal-actions">
        {textModal.editable&&<button type="button" className="btn-modal-save" onClick={async()=>{
          try{
            if(textModal.field==="tags"){
              const r=await fetch(`${API}/devices/${encodeURIComponent(textModal.ip)}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({tags:textModal.text})});
              const d=await r.json();if(!r.ok)throw Error(d.detail||"خطا");
              setMsg("تگ ذخیره شد");reloadRows();
            }
            setTextModal(null);
          }catch(e){setError(e.message)}
        }}>ذخیره</button>}
        <button type="button" className="btn-modal-close" onClick={()=>setTextModal(null)}>بستن</button>
      </div>
    </div></div>}
    <div className="report-filters">
      <label>دسته‌بندی<select value={classification} onChange={e=>{setClassification(e.target.value);setOffset(0)}}>
        <option value="">همه</option>
        <option value="mikrotik_candidate">دستگاه MikroTik</option>
        <option value="potential_non_mikrotik">احتمالاً غیر MikroTik</option>
        <option value="winbox_open_api_closed">Winbox باز / API بسته</option>
        <option value="non_mikrotik">غیر MikroTik</option>
        <option value="special">ویژه</option>
      </select></label>
      <label>نوع دستگاه<select value={deviceTypeFilter} onChange={e=>{setDeviceTypeFilter(e.target.value);setOffset(0)}}>
        <option value="">همه</option>
        <option value="AP">AP</option>
        <option value="ST">ST</option>
        <option value="Router">Router</option>
      </select></label>
      <label>پورت باز<select value={port} onChange={e=>{setPort(e.target.value);setOffset(0)}}>
        <option value="">همه</option>
        <option value="8291">8291 Winbox</option>
        <option value="8728">8728 API</option>
        <option value="22">22 SSH</option>
        <option value="80">80 HTTP</option>
        <option value="443">443 HTTPS</option>
      </select></label>
      <label className="filter-search">جست‌وجو در فیلدها
        <span style={{display:"flex",gap:6,alignItems:"stretch",width:"100%"}}>
          <select value={qField} onChange={e=>{setQField(e.target.value);setOffset(0)}}
            style={{width:"auto",minWidth:"9.5em",flex:"0 0 auto",padding:"8px",border:"1px solid #cbd5e1",borderRadius:7,background:"white",font:"inherit"}}
            title="محدوده جستجو — با انتخاب یک فیلد خاص، جستجو سریع‌تر انجام می‌شود">
            <option value="">همه فیلدها</option>
            <option value="ip">فقط IP</option>
            <option value="device_name">نام دستگاه</option>
            <option value="tags">تگ</option>
            <option value="device_type">نوع دستگاه</option>
            <option value="classification">دسته‌بندی</option>
            <option value="interfaces">اینترفیس‌ها</option>
            <option value="ip_addresses">آدرس‌های IP</option>
            <option value="ip_neighbors">همسایه‌ها</option>
            <option value="wireless_info">وایرلس</option>
            <option value="mac_info">MAC</option>
            <option value="device_log">لاگ دستگاه</option>
          </select>
          <input dir="ltr" value={qInput} onChange={e=>setQInput(e.target.value)}
            onKeyDown={e=>{if(e.key==="Enter"){clearTimeout(searchTimerRef.current);setQ(qInput);setOffset(0)}}}
            placeholder="واژه‌ها را با فاصله جدا کنید…"
            title="جستجوی هم‌زمان چند واژه (ترکیب AND)؛ انتخاب فیلد از منوی کناری، جستجو را سریع‌تر می‌کند"/>
        </span>
      </label>
      {(q||qInput)&&<button type="button" className="btn-clear-search" title="پاک کردن جستجو" onClick={()=>{setQInput("");setQ("");setOffset(0)}}>✕</button>}
    </div>
    {paginationBar}
    {error&&<p className="error">{error}</p>}{msg&&<p className="backend-msg ok">{msg}</p>}
    <div className="list-toolbar">
      <button type="button" className="btn-clear-selection" disabled={!selectedIps.length} onClick={clearSelection}>
        لغو انتخاب{selectedIps.length?` (${selectedIps.length})`:""}
      </button>
      <span className="muted" style={{fontSize:".85em"}}>{selectedIps.length?`${selectedIps.length} دستگاه انتخاب شده`:"هیچ دستگاهی انتخاب نشده"}</span>
    </div>
    <div className="table-scroll-top" onScroll={e=>{const b=e.currentTarget.nextElementSibling;if(b)b.scrollLeft=e.currentTarget.scrollLeft}}>
      <div className="table-scroll-top-inner"/>
    </div>
    <div className="tablewrap" onScroll={e=>{const t=e.currentTarget.previousElementSibling;if(t)t.scrollLeft=e.currentTarget.scrollLeft}}><table><thead><tr>
      {colOn("select")&&<th><input type="checkbox" checked={rows.length>0&&rows.every(d=>selected[d.ip])} onChange={toggleSelectAll} title="انتخاب همه"/></th>}
      {ALL_COLS.filter(c=>c.id!=="select"&&colOn(c.id)).map(c=><th key={c.id} className={(sortMap[c.id]?"sortable-th ":"")+"col-"+c.id} onClick={()=>sortMap[c.id]&&handleSort(sortMap[c.id])}>{sortMap[c.id]&&<span className="sort-icon">{sortIcon(sortMap[c.id])}</span>}{c.label}</th>)}
    </tr></thead><tbody>{rows.map(d=><tr key={d.ip} className={selected[d.ip]?"row-selected":undefined}>
      {colOn("select")&&<td><input type="checkbox" checked={!!selected[d.ip]} onChange={()=>toggleSelect(d.ip)}/></td>}
      {colOn("ip")&&<td className="col-ip" dir="ltr">{d.ip}</td>}
      {colOn("device_name")&&<td className="col-device_name"><div className="name-cell">
        {editNameIp===d.ip
          ? <span className="inline-edit"><input value={editNameVal} onChange={e=>setEditNameVal(e.target.value)} dir="ltr"/><button type="button" onClick={()=>saveName(d.ip)}>✓</button><button type="button" onClick={()=>setEditNameIp(null)}>✕</button></span>
          : <span className="editable name-preview" onClick={()=>{setEditNameIp(d.ip);setEditNameVal(d.device_name||"")}} title="MikroTik /system identity — کلیک برای ویرایش">{d.device_name||"—"}</span>}
        <span className="name-actions">
          {isMikrotik(d)&&<button type="button" className="btn-winbox btn-winbox-inline" title={"باز کردن Winbox — "+d.ip} onClick={e=>{e.stopPropagation();openWinbox(d.ip)}}>▣ Winbox</button>}
          <button type="button" className={"btn-detail"+(d.interfaces?"":" is-empty")} title="اینترفیس‌ها" onClick={e=>{e.stopPropagation();setTextModal({title:"اینترفیس‌ها — "+d.ip,text:d.interfaces||"(خالی)"})}}>اینترفیس‌ها</button>
          <button type="button" className={"btn-detail"+(d.ip_addresses?"":" is-empty")} title="آدرس‌های IP" onClick={e=>{e.stopPropagation();setTextModal({title:"آدرس‌های IP — "+d.ip,text:d.ip_addresses||"(خالی)"})}}>آدرس IP</button>
          <button type="button" className={"btn-detail"+(d.ip_neighbors?"":" is-empty")} title="همسایه‌ها" onClick={e=>{e.stopPropagation();setTextModal({title:"همسایه‌ها — "+d.ip,text:d.ip_neighbors||"(خالی)"})}}>همسایه‌ها</button>
          <button type="button" className={"btn-detail"+(d.wireless_info?"":" is-empty")} title="وایرلس" onClick={e=>{e.stopPropagation();setTextModal({title:"وایرلس — "+d.ip,text:d.wireless_info||"(خالی)"})}}>وایرلس</button>
          <button type="button" className={"btn-detail btn-mac"+(d.mac_info?"":" is-empty")} title="MAC آدرس اینترفیس‌ها" onClick={e=>{e.stopPropagation();setTextModal({title:"MAC — "+d.ip,text:d.mac_info||"(خالی — با API بخوانید)"})}}>MAC</button>
          <button type="button" className={"btn-detail btn-log-inline"+(d.device_log?"":" is-empty")} title="لاگ" onClick={e=>{e.stopPropagation();setTextModal({title:"لاگ — "+d.ip,text:d.device_log||"(خالی — با API بخوانید)"})}}>Log</button>
        </span>
      </div></td>}
      {colOn("device_type")&&<td className="col-device_type">{({AP:"AP",ST:"ST",Router:"Router"}[d.device_type]||d.device_type||"—")}</td>}
      {colOn("tags")&&<td className="col-tags"><div className="tag-cell"><span className="tag-preview" title={d.tags||""}>{(d.tags||"").trim()?(d.tags.length>24?d.tags.slice(0,24)+"…":d.tags):"—"}</span><button type="button" className="btn-view-text" title="مشاهده / ویرایش تگ" onClick={()=>setTextModal({title:"تگ — "+d.ip,text:d.tags||"",editable:true,field:"tags",ip:d.ip})}>تگ</button></div></td>}
      {colOn("ping")&&<td className="col-ping">{d.ping_ok?"پاسخ‌گو":"—"}</td>}
      {colOn("ports")&&<td className="col-ports" dir="ltr">{d.open_ports.length?d.open_ports.join(", "):"—"}</td>}
      {colOn("classification")&&<td className="col-classification">{{mikrotik_candidate:"دستگاه MikroTik",non_mikrotik:"غیر MikroTik",special:"ویژه"}[d.classification]||d.classification}</td>}
      {colOn("interfaces")&&<td className="col-interfaces">{(d.interfaces)?<button type="button" className="btn-view-text" onClick={()=>setTextModal({title:"اینترفیس‌ها — "+d.ip,text:d.interfaces})}>اینترفیس‌ها</button>:"—"}</td>}
      {colOn("ip_addresses")&&<td className="col-ip_addresses">{(d.ip_addresses)?<button type="button" className="btn-view-text" onClick={()=>setTextModal({title:"آدرس‌های IP — "+d.ip,text:d.ip_addresses})}>آدرس‌های IP</button>:"—"}</td>}
      {colOn("ip_neighbors")&&<td className="col-ip_neighbors">{(d.ip_neighbors)?<button type="button" className="btn-view-text" onClick={()=>setTextModal({title:"همسایه‌ها — "+d.ip,text:d.ip_neighbors})}>همسایه‌ها</button>:"—"}</td>}
      {colOn("wireless_info")&&<td className="col-wireless_info">{(d.wireless_info)?<button type="button" className="btn-view-text" onClick={()=>setTextModal({title:"وایرلس — "+d.ip,text:d.wireless_info})}>وایرلس</button>:"—"}</td>}
      {colOn("device_log")&&<td className="col-device_log">{(d.device_log)?<button type="button" className="btn-view-text" onClick={()=>setTextModal({title:"لاگ — "+d.ip,text:d.device_log})}>Log</button>:"—"}</td>}
      {colOn("mac_info")&&<td className="col-mac_info">{(d.mac_info)?<button type="button" className="btn-view-text" onClick={()=>setTextModal({title:"MAC — "+d.ip,text:d.mac_info})}>MAC</button>:"—"}</td>}
      {colOn("first_seen")&&<td dir="ltr" className="date-cell col-first_seen">{formatDate(d.first_seen)}</td>}
      {colOn("last_seen")&&<td dir="ltr" className="date-cell col-last_seen">{formatDate(d.last_seen)}</td>}
      {colOn("seen_count")&&<td className="col-seen_count">{d.seen_count}</td>}
      {colOn("winbox")&&<td className="winbox-cell col-winbox">{isMikrotik(d)?<button type="button" className="btn-winbox" onClick={()=>openWinbox(d.ip)}>▣ Winbox</button>:"—"}</td>}
    </tr>)}</tbody></table>{!rows.length&&!error&&<p>دستگاهی نیست.</p>}</div>
    {paginationBar}
  
    </>
    )}
  </section>
}


function EmailServerCard(){
  const[cfg,setCfg]=useState({mode:"direct",host:"smtp.gmail.com",port:587,use_tls:true,use_ssl:false,username:"",password:"",from_email:"",from_name:"شبکه‌بان",to_email:"",enabled:false,timeout:30,helo_host:"shabakeban.local",password_set:false});
  const[busy,setBusy]=useState(false);
  const[msg,setMsg]=useState("");
  const[err,setErr]=useState("");
  const[testMsg,setTestMsg]=useState("");
  const[testTo,setTestTo]=useState("");

  useEffect(()=>{
    fetch(API+"/api/smtp/config").then(r=>r.json()).then(d=>{
      if(d&&d.host){
        const from=d.from_email&&String(d.from_email).includes("@")?d.from_email:(d.username||"");
        const port=Number(d.port)||587;
        setCfg(c=>({...c,...d,from_email:from,password:d.password_set?"********":"",use_tls:port!==465,use_ssl:port===465}));
        if(d.to_email)setTestTo(d.to_email);
      }
    }).catch(()=>{});
  },[]);

  function setField(k,v){setCfg(c=>({...c,[k]:v}))}

  function applyPreset(name){
    if(name==="yahoo"){
      setCfg(c=>({
        ...c,
        mode:"relay",
        host:"smtp.mail.yahoo.com",
        port:587,
        use_tls:true,
        use_ssl:false,
        enabled:true,
        // keep username/password/from if already yahoo-like; user fills app password
      }));
      setMsg("پیش‌فرض Yahoo اعمال شد: smtp.mail.yahoo.com:587 — رمز باید App Password یاهو باشد");
      setErr("");
    }else if(name==="gmail"){
      setCfg(c=>({
        ...c,
        mode:"relay",
        host:"smtp.gmail.com",
        port:587,
        use_tls:true,
        use_ssl:false,
        enabled:true,
      }));
      setMsg("پیش‌فرض Gmail اعمال شد: smtp.gmail.com:587 — از App Password استفاده کنید");
      setErr("");
    }else if(name==="yahoo465"){
      setCfg(c=>({
        ...c,
        mode:"relay",
        host:"smtp.mail.yahoo.com",
        port:465,
        use_tls:false,
        use_ssl:true,
        enabled:true,
      }));
      setMsg("پیش‌فرض Yahoo SSL: smtp.mail.yahoo.com:465");
      setErr("");
    }else if(name==="mailfa"){
      setCfg(c=>({
        ...c,
        mode:"relay",
        host:"mail.mailfa.com",
        port:587,
        use_tls:true,
        use_ssl:false,
        enabled:true,
        username:c.username&&c.username.includes("@mailfa.com")?c.username:"",
        from_email:c.from_email&&c.from_email.includes("@mailfa.com")?c.from_email:"",
      }));
      setMsg("پیش‌فرض میل‌فا: mail.mailfa.com:587 — نام کاربری و From را با ایمیل کامل @mailfa.com پر کنید");
      setErr("");
    }
  }

  async function save(){
    setBusy(true);setErr("");setMsg("");
    try{
      const body={...cfg};
      if(body.password==="********")delete body.password;
      const r=await fetch(API+"/api/smtp/config",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      const txt=await r.text();
      let d={};
      try{d=txt?JSON.parse(txt):{}}catch(_){throw Error(txt&&txt.slice(0,200)||"پاسخ نامعتبر از سرور")}
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:(Array.isArray(d.detail)?d.detail.map(x=>x.msg||JSON.stringify(x)).join("; "):txt.slice(0,200)||"ذخیره ناموفق"));
      setCfg(c=>({...c,...d,password:d.password_set?"********":""}));
      setMsg("تنظیمات SMTP ذخیره شد");
    }catch(e){setErr(e.message)}
    setBusy(false);
  }

  async function testSend(){
    setBusy(true);setErr("");setMsg("");
    try{
      // save first so test uses latest fields
      const body={...cfg};
      if(body.password==="********")delete body.password;
      const sr=await fetch(API+"/api/smtp/config",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      const stxt=await sr.text();
      let sd={};
      try{sd=stxt?JSON.parse(stxt):{}}catch(_){throw Error(stxt&&stxt.slice(0,200)||"پاسخ نامعتبر")}
      if(!sr.ok)throw Error(typeof sd.detail==="string"?sd.detail:"ذخیره قبل از تست ناموفق");
      const r=await fetch(API+"/api/smtp/test",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({to_email:testTo||cfg.to_email||undefined,message:testMsg||undefined})});
      const txt=await r.text();
      let d={};
      try{d=txt?JSON.parse(txt):{}}catch(_){throw Error(txt&&txt.slice(0,200)||"پاسخ نامعتبر")}
      if(!r.ok)throw Error(typeof d.detail==="string"?d.detail:txt.slice(0,200)||"ارسال تست ناموفق");
      setMsg("ایمیل آزمایشی ارسال شد → "+(d.to||testTo||cfg.to_email));
    }catch(e){setErr(e.message)}
    setBusy(false);
  }

  return (
    <section className="panel email-panel" dir="rtl">
      <h2>سرور ایمیل (SMTP)</h2>
      <p className="muted">دو حالت ارسال:
        <b>مستقیم (Direct)</b> — بدون Gmail؛ به سرور MX گیرنده وصل می‌شود (نیاز به پورت خروجی ۲۵).
        <b>رله (Relay)</b> — از SMTP هاست/VPS/جیمیل.
        در ایران معمولاً Direct روی اینترنت خانگی محدود است؛ رله روی هاست ایرانی پایدارتر است.</p>
      <div className="email-presets">
        <span className="muted">پیش‌فرض سریع:</span>
        <button type="button" className="tool-btn" onClick={()=>applyPreset("gmail")}>Gmail (587)</button>
        <button type="button" className="tool-btn" onClick={()=>applyPreset("yahoo")}>Yahoo (587)</button>
        <button type="button" className="tool-btn" onClick={()=>applyPreset("yahoo465")}>Yahoo SSL (465)</button>
        <button type="button" className="tool-btn" onClick={()=>applyPreset("mailfa")}>میل‌فا (Mailfa)</button>
      </div>
      {err&&<p className="error">{err}</p>}
      {msg&&<p className="backend-msg ok">{msg}</p>}
      <div className="email-grid">
        <label className="chk"><input type="checkbox" checked={!!cfg.enabled} onChange={e=>setField("enabled",e.target.checked)}/> فعال‌سازی ارسال ایمیل</label>
        <label>حالت ارسال
          <select value={cfg.mode||"direct"} onChange={e=>setField("mode",e.target.value)}>
            <option value="direct">مستقیم به MX گیرنده (بدون SMTP واسط)</option>
            <option value="relay">رله SMTP (میل‌فا / Yahoo / Gmail / هاست)</option>
          </select>
        </label>
        <label>فرستنده ایمیل (From)
          <input dir="ltr" value={cfg.from_email||""} onChange={e=>setField("from_email",e.target.value)} placeholder="alert@yourdomain.com"/>
        </label>
        <label>نام فرستنده
          <input value={cfg.from_name||""} onChange={e=>setField("from_name",e.target.value)} placeholder="شبکه‌بان"/>
        </label>
        <label>گیرنده پیش‌فرض (To)
          <input dir="ltr" value={cfg.to_email||""} onChange={e=>setField("to_email",e.target.value)} placeholder="user@gmail.com"/>
        </label>
        <label>نام HELO/EHLO
          <input dir="ltr" value={cfg.helo_host||""} onChange={e=>setField("helo_host",e.target.value)} placeholder="shabakeban.local"/>
        </label>
        {(cfg.mode==="relay")&&<>
        <label>میزبان SMTP
          <input dir="ltr" value={cfg.host||""} onChange={e=>setField("host",e.target.value)} placeholder="mail.yourdomain.com"/>
        </label>
        <label>پورت
          <input dir="ltr" type="number" min={1} max={65535} value={cfg.port||587} onChange={e=>{const p=Number(e.target.value)||587;setCfg(c=>({...c,port:p,use_tls:p!==465,use_ssl:p===465}))}}/>
        </label>
        <label className="chk"><input type="checkbox" checked={!!cfg.use_tls} onChange={e=>setField("use_tls",e.target.checked)}/> STARTTLS (پورت ۵۸۷ — Yahoo / Gmail)</label>
        <label className="chk"><input type="checkbox" checked={!!cfg.use_ssl} onChange={e=>setField("use_ssl",e.target.checked)}/> SSL مستقیم (فقط پورت ۴۶۵)</label>
        <label>نام کاربری SMTP
          <input dir="ltr" value={cfg.username||""} onChange={e=>setField("username",e.target.value)} placeholder="you@yahoo.com / you@gmail.com" autoComplete="username"/>
        </label>
        <label>رمز / App Password
          <input dir="ltr" type="password" value={cfg.password||""} onChange={e=>setField("password",e.target.value)} placeholder="App Password" autoComplete="new-password"/>
        </label>
        </>}
        <label>Timeout (ثانیه)
          <input dir="ltr" type="number" min={5} max={120} value={cfg.timeout||30} onChange={e=>setField("timeout",Number(e.target.value)||30)}/>
        </label>
      </div>
      <div className="email-actions">
        <button type="button" className="tool-btn primary" disabled={busy} onClick={save}><RbIcon name="email" size={16}/><span>ذخیره تنظیمات</span></button>
      </div>
      <hr className="email-sep"/>
      <h3>تست ارسال</h3>
      <p className="muted">یک پیام آزمایشی با حالت انتخاب‌شده (مستقیم یا رله) ارسال می‌شود.</p>
      <div className="email-grid">
        <label>گیرنده تست
          <input dir="ltr" value={testTo} onChange={e=>setTestTo(e.target.value)} placeholder={cfg.to_email||"you@gmail.com"}/>
        </label>
        <label>متن پیام (اختیاری)
          <textarea rows={3} value={testMsg} onChange={e=>setTestMsg(e.target.value)} placeholder="متن دلخواه برای تست…"/>
        </label>
      </div>
      <div className="email-actions">
        <button type="button" className="tool-btn" disabled={busy} onClick={testSend}><RbIcon name="email" size={16}/><span>ارسال ایمیل آزمایشی</span></button>
      </div>
    </section>
  );
}

function App(){
const[authState,setAuthState]=useState("checking");const[authUser,setAuthUser]=useState("");
useEffect(()=>{let active=true;fetch(API+"/api/auth/check").then(async r=>{if(!active)return;if(r.ok){try{const d=await r.json();setAuthUser(d.username||"")}catch(e){}setAuthState("in")}else setAuthState("out")}).catch(()=>{active&&setAuthState("out")});return()=>{active=false}},[]);
useEffect(()=>{const h=()=>setAuthState("out");window.addEventListener("netscan:unauthorized",h);return()=>window.removeEventListener("netscan:unauthorized",h)},[]);
async function doLogout(){try{await fetch(API+"/api/logout",{method:"POST"})}catch(e){}setAuthUser("");setAuthState("out")}
if(authState!=="in")return (
<main>
  {authState==="checking"
    ?<div className="login-shell" dir="rtl"><div className="login-card login-checking">در حال بررسی نشست…</div></div>
    :<Login onLogin={u=>{setAuthUser(u||"");setAuthState("in")}}/>}
</main>
);
return <MainApp authUser={authUser} onLogout={doLogout}/>;
}

function MainApp({authUser,onLogout}){
const[mainTab,setMainTab]=useState("network");const[targets,setTargets]=useState("");const[ports,setPorts]=useState("22,80,443,8291,8728");const[workers,setWorkers]=useState(32),[ping,setPing]=useState(1000),[timeout,setTimeoutValue]=useState(1);const[job,setJob]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState("");const[resClass,setResClass]=useState(""),[resQ,setResQ]=useState(""),[resPageSize,setResPageSize]=useState(50),[resPage,setResPage]=useState(1);const[xferDb,setXferDb]=useState("default"),[dbOptions,setDbOptions]=useState([{name:"default"}]),[xferBusy,setXferBusy]=useState(false);
useEffect(()=>{fetch(API+"/api/databases").then(r=>readJson(r)).then(d=>{if(d&&d.databases){setDbOptions(d.databases);setXferDb(d.active||"default")}}).catch(()=>{})},[job?.status]);
async function transferScan(){if(!job?.scan_id)return;setXferBusy(true);setError("");try{const r=await fetch(`${API}/scans/${job.scan_id}/transfer`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({database:xferDb})});const d=await readJson(r);setError("");alert("به دیتابیس «"+d.database+"» منتقل شد: "+d.upserted+" دستگاه")}catch(e){setError(e.message)}setXferBusy(false)}
async function start(){setError("");setBusy(true);try{const res=await fetch(API+"/scans",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({targets,ports:ports.split(",").map(x=>Number(x.trim())),workers:Number(workers),ping_timeout_ms:Number(ping),port_timeout:Number(timeout)})});const data=await readJson(res);setJob({...data,progress:{completed:0,total:data.total_targets,ping_responders:0},records:[],summary:{}})}catch(e){setError(e.message);setBusy(false)}}
useEffect(()=>{if(!job?.scan_id||["completed","failed","done","error","canceled"].includes(job.status))return;let active=true;let errCount=0;const timer=setInterval(async()=>{try{let r=await fetch(`${API}/scans/${job.scan_id}`);if(r.status===401){window.dispatchEvent(new CustomEvent("netscan:unauthorized"));return;}let d=await r.json();if(active){errCount=0;setJob(d);if(["completed","failed","done","error","canceled"].includes(d.status)){setBusy(false);if(d.error)setError(d.error)}}}catch(e){errCount++;if(errCount>2&&active){setError("ارتباط با API قطع شد: "+e.message)}}},1200);return()=>{active=false;clearInterval(timer)}},[job?.scan_id,job?.status]);
async function upload(e){const f=e.target.files?.[0];if(f)setTargets(await f.text())}const[stopping,setStopping]=useState(false);
async function stopScan(){if(!job?.scan_id||!busy)return;setStopping(true);try{const r=await fetch(`${API}/scans/${job.scan_id}/cancel`,{method:"POST"});const d=await readJson(r);setError("");let tries=0;while(tries<60){const rr=await fetch(`${API}/scans/${job.scan_id}`);if(rr.status===401){window.dispatchEvent(new CustomEvent("netscan:unauthorized"));break;}const dd=await rr.json();if(rr.ok){setJob(dd);if(["canceled","done","error","completed","failed"].includes(dd.status)){setBusy(false);if(dd.status==="canceled")setError("اسکن با موفقیت متوقف شد.");else if(dd.status==="done"||dd.status==="completed")setError("اسکن در همین حین تکمیل شد.");else if(dd.status==="error"||dd.status==="failed")setError(dd.error||"اسکن ناموفق بود.");break}}await new Promise(res=>setTimeout(res,1200));tries++}if(tries>=60)setError("پاسخ وضعیت توقف دریافت نشد؛ لطفاً بعداً بررسی کنید.")}catch(e){setError(e.message)}setStopping(false)}
const isTerminal=["completed","done","canceled","error","failed"].includes(job?.status);
const liveSummary=job?.summary&&Object.keys(job.summary).length?job.summary:
  (job?.status&&!isTerminal?{ping_responders:Number(job.progress?.ping_responders)||0,mikrotik_candidates:0,potential_non_mikrotik:0,winbox_open_api_closed:0}:job?.summary||{});
const done=Number(job?.progress?.completed)||0,total=Number(job?.progress?.total)||Number(job?.total_targets)||0;const pct=total?Math.max(0,Math.min(100,Math.round(100*done/total))):0;const scanLabel=job?.status==="completed"||job?.status==="done"?"اسکن تکمیل شد":job?.status==="failed"||job?.status==="error"?"اسکن ناموفق بود":job?.status==="canceled"?"اسکن لغو شد":job?.status==="queued"?"در صف انتظار…":"در حال اسکن...";
return (
<main>
<header className="app-brand" dir="rtl">
  <div className="brand-mark" aria-hidden="true">
    <svg viewBox="0 0 48 48" width="48" height="48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0ea5e9" opacity=".2"/>
      <circle cx="24" cy="24" r="16" stroke="#7dd3fc" strokeWidth="1.5" strokeDasharray="3 3" opacity=".7"/>
      <circle cx="24" cy="24" r="9" stroke="#e0f2fe" strokeWidth="1.75"/>
      <circle cx="24" cy="24" r="3.2" fill="#e0f2fe"/>
      <path d="M24 8v4M24 36v4M8 24h4M36 24h4" stroke="#7dd3fc" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M24 24l10-8" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="35" cy="15" r="2.2" fill="#38bdf8"/>
      <path d="M14 32c2.5-3 5.5-4.5 10-4.5" stroke="#bae6fd" strokeWidth="1.5" strokeLinecap="round" opacity=".8"/>
    </svg>
  </div>
  <div className="brand-text">
    <h1>شبکه‌بان</h1>
    <p>پایش، اسکن و مدیریت دستگاه‌های MikroTik</p>
  </div>
  <button type="button" className="logout-btn" onClick={onLogout} title={authUser?("خروج از حساب "+authUser):"خروج از حساب"}>خروج{authUser?` (${authUser})`:""}</button>
</header>
{error&&<div className="error">{error}</div>}
<div className="ribbon-shell" dir="rtl">
  <nav className="ribbon-tabs" dir="ltr" aria-label="بخش‌های اصلی">
    <button type="button" className={"ribbon-tab"+(mainTab==="network"?" active":"")} onClick={()=>setMainTab("network")}>
      <RbIcon name="network" size={18}/><span>اتصال به شبکه</span>
    </button>
    <button type="button" className={"ribbon-tab"+(mainTab==="scan"?" active":"")} onClick={()=>setMainTab("scan")}>
      <RbIcon name="search" size={18}/><span>جستجوی شبکه</span>
    </button>
    <button type="button" className={"ribbon-tab"+(mainTab==="devices"?" active":"")} onClick={()=>setMainTab("devices")}>
      <RbIcon name="devices" size={18}/><span>مدیریت دستگاه‌های شبکه</span>
    </button>
    <button type="button" className={"ribbon-tab"+(mainTab==="system"?" active":"")} onClick={()=>setMainTab("system")}>
      <RbIcon name="system" size={18}/><span>راهبری سیستم</span>
    </button>
    <button type="button" className={"ribbon-tab"+(mainTab==="email"?" active":"")} onClick={()=>setMainTab("email")}>
      <RbIcon name="email" size={18}/><span>سرور ایمیل</span>
    </button>
    <button type="button" className={"ribbon-tab"+(mainTab==="smart_reports"?" active":"")} onClick={()=>setMainTab("smart_reports")}><span style={{fontSize:18,marginLeft:6}}>📊</span><span>گزارش هوشمند</span></button>
  </nav>
</div>
{mainTab==="network"&&(
  <div className="tab-panel" dir="rtl">
    <VpnManagerCard onNotify={setError} onRoutes={list=>setTargets(t=>(t?t+"\n":"")+list.join("\n"))}/>
  </div>
)}
{mainTab==="devices"&&(
  <div className="tab-panel" dir="rtl">
    <DeviceReports mode="devices"/>
  </div>
)}
{mainTab==="system"&&(
  <div className="tab-panel" dir="rtl">
    <BackendCard onNotify={setError}/>
    <DeviceReports mode="system"/>
  </div>
)}
{mainTab==="email"&&(
  <div className="tab-panel" dir="rtl">
    <EmailServerCard/>
  </div>
)}
{mainTab==="smart_reports"&&(
  <div className="tab-panel" dir="rtl">
    <SmartReports/>
  </div>
)}

{mainTab==="scan"&&(
  <div className="tab-panel" dir="rtl">

<section className="panel">
  <label>هدف‌ها (آدرس، CIDR یا بازه؛ هر خط یا سلول CSV یک ورودی — اگر خالی بماند از فایل ip_olom.txt خوانده می‌شود)
    <textarea rows="5" value={targets} onChange={e=>setTargets(e.target.value)} placeholder={"خالی = استفاده از ip_olom.txt\n192.168.1.10\n192.168.1.20-30\n10.0.0.0/30"}/>
    <small>اگر هدفی وارد نکنید، لیست پیش‌فرض از فایل ip_olom.txt بارگذاری می‌شود. سقف: ۶۵٬۵۳۶ هدف در هر اسکن.</small>
  </label>
  <label>بارگذاری فایل TXT/CSV <input type="file" accept=".txt,.csv,text/plain,text/csv" onChange={upload}/></label>
  <div className="grid">
    <label>پورت‌ها<input value={ports} onChange={e=>setPorts(e.target.value)}/></label>
    <label>هم‌زمانی<input type="number" min="1" max="256" value={workers} onChange={e=>setWorkers(e.target.value)}/></label>
    <label>مهلت پینگ (ms)<input type="number" min="100" value={ping} onChange={e=>setPing(e.target.value)}/></label>
    <label>مهلت پورت (ثانیه)<input type="number" min=".1" step=".1" value={timeout} onChange={e=>setTimeoutValue(e.target.value)}/></label>
  </div>
  <div className="vpn-actions">
    <button type="button" disabled={busy} onClick={start}>{busy?"در حال اجرا…":"شروع اسکن"}</button>
    <button type="button" className="btn-stop" disabled={!busy||stopping} onClick={stopScan}>{stopping?"در حال توقف…":"توقف اسکن"}</button>
  </div>
</section>
{job&&(
  <>
    <section className="panel scan-progress" dir="rtl" aria-label="پیشرفت اسکن">
      <div className="progress-heading">
        <div>
          <h2>پیشرفت اسکن</h2>
          <p className="scan-status" role="status">{scanLabel}</p>
        </div>
        <strong className="progress-percent" aria-live="polite">{pct}٪</strong>
      </div>
      <div className="progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={pct}>
        <div className={"progress-fill "+(job.status==="failed"?"is-failed":"")} style={{width:pct+"%"}}/>
      </div>
      <div className="progress-meta">
        <span>{done.toLocaleString("fa-IR")} از {total.toLocaleString("fa-IR")} هدف</span>
        <span>پاسخ‌گو به پینگ: {(Number(job.progress?.ping_responders)||0).toLocaleString("fa-IR")}</span>
      </div>
      {job.progress?.last_ip&&job.status!=="completed"&&job.status!=="done"&&(
        <p className="current-target">هدف جاری: <bdi dir="ltr">{job.progress.last_ip}</bdi></p>
      )}
      {job.summary&&(
        <div className="cards">{keys.map(k=>(
          <article key={k}><b>{liveSummary[k]||0}</b><span>{labels[k]}</span></article>
        ))}</div>
      )}
      {["completed","done","canceled"].includes(job.status)&&(
        <div className="downloads">{keys.map(k=>(
          <a key={k} href={`${API}/scans/${job.scan_id}/reports/${k}`}>{labels[k]} (CSV)</a>
        ))}</div>
      )}
    </section>
    <section className="panel">
      <div className="report-heading">
        <h2>نتایج اسکن</h2>
        <div className="report-actions">
          <label className="page-size">انتقال به دیتابیس
            <select value={xferDb} onChange={e=>setXferDb(e.target.value)}>
              {(dbOptions||[]).map(d=>(
                <option key={d.name} value={d.name}>{d.name}{d.active?" (فعال)":""}</option>
              ))}
            </select>
          </label>
          <button type="button" className="btn-save" disabled={xferBusy||!["done","completed","canceled"].includes(job?.status)} onClick={transferScan}>
            {xferBusy?"در حال انتقال…":"انتقال نتایج به دیتابیس"}
          </button>
        </div>
      </div>
      <div className="report-filters">
        <label>دسته‌بندی
          <select value={resClass} onChange={e=>{setResClass(e.target.value);setResPage(1)}}>
            <option value="">همه</option>
            <option value="mikrotik_candidate">دستگاه MikroTik</option>
            <option value="potential_non_mikrotik">احتمالاً غیر MikroTik</option>
            <option value="winbox_open_api_closed">Winbox باز / API بسته</option>
          </select>
        </label>
        <label>جست‌وجوی IP
          <input dir="ltr" value={resQ} onChange={e=>{setResQ(e.target.value);setResPage(1)}} placeholder="172.18."/>
        </label>
        <label className="page-size">تعداد در صفحه
          <select value={resPageSize} onChange={e=>{setResPageSize(Number(e.target.value));setResPage(1)}}>
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="200">200</option>
            <option value="100000">همه</option>
          </select>
        </label>
      </div>
      {(()=>{
        const all=(job.records||[]).filter(x=>x.ping_responded||x.is_alive||(x.open_ports||[]).length)
          .filter(x=>!resClass||x.classification===resClass)
          .filter(x=>!resQ||String(x.ip).includes(resQ.trim()));
        const pages=Math.max(1,Math.ceil(all.length/resPageSize));
        const page=Math.min(resPage,pages);
        const slice=all.slice((page-1)*resPageSize,page*resPageSize);
        const bar=(
          <div className="report-pagination">
            <button type="button" disabled={page<=1} onClick={()=>setResPage(1)}>صفحه اول</button>
            <button type="button" disabled={page<=1} onClick={()=>setResPage(p=>Math.max(1,p-1))}>قبلی</button>
            <span className="page-indicator">صفحه {page.toLocaleString("fa-IR")} از {pages.toLocaleString("fa-IR")} — {all.length.toLocaleString("fa-IR")} نتیجه</span>
            <button type="button" disabled={page>=pages} onClick={()=>setResPage(p=>p+1)}>بعدی</button>
            <button type="button" disabled={page>=pages} onClick={()=>setResPage(pages)}>صفحه آخر</button>
          </div>
        );
        return (
          <>
            {bar}
            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>IP</th><th>دسته‌بندی</th><th>پورت‌های باز</th><th>8291 Winbox</th><th>8728 API</th><th>Winbox</th>
                  </tr>
                </thead>
                <tbody>
                  {slice.map(x=>(
                    <tr key={x.ip}>
                      <td dir="ltr">{x.ip}</td>
                      <td>{labels[x.classification]||x.classification}</td>
                      <td>{(x.open_ports||[]).map(p=>`${p.port} ${p.port===8291?"Winbox":p.port===8728?"RouterOS API":""}`).join("، ")||"—"}</td>
                      <td>{x.states?.["8291"]}</td>
                      <td>{x.states?.["8728"]}</td>
                      <td className="winbox-cell">
                        {(x.classification==="mikrotik_candidate"||(x.open_ports||[]).some(p=>p.port===8291||p.port===8728))?(
                          <button type="button" className="btn-winbox" onClick={async()=>{
                            try{
                              const r=await fetch(`${API}/devices/${encodeURIComponent(x.ip)}/winbox`,{method:"POST"});
                              const d=await r.json();
                              if(!r.ok)throw Error(d.detail||"Winbox");
                            }catch(e){setError(e.message)}
                          }}>▣ Winbox</button>
                        ):"—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!slice.length&&<p>موردی با این فیلتر نیست.</p>}
            </div>
            {bar}
          </>
        );
      })()}
    </section>
  </>
)}

  </div>
)}
</main>
);
}

function SmartReports(){
  const[days,setDays]=useState(30);
  const[thresholdMinutes,setThresholdMinutes]=useState(5);
  const[flapResults,setFlapResults]=useState([]);
  const[loadingList,setLoadingList]=useState(false);
  const[progress,setProgress]=useState(0);
  const[downloadingCsv,setDownloadingCsv]=useState(false);
  const[msg,setMsg]=useState("");const[err,setErr]=useState("");
  const[dbList,setDbList]=useState([{name:"default"}]),[dbSel,setDbSel]=useState(""),[reportDb,setReportDb]=useState("");
  const[diag,setDiag]=useState(null);
  useEffect(()=>{(async()=>{
    try{
      const r=await fetch(API+"/api/databases");const d=await readJson(r);
      if(r.ok){
        const list=(d.databases&&d.databases.length)?d.databases:[{name:"default"}];
        setDbList(list);const active=d.active||"default";
        setDbSel(prev=>prev||active);
      }
    }catch(e){/* keep fallback list */}
  })()},[]);
  async function loadList(overrides){
    overrides=overrides||{};
    const dDays=overrides.days!==undefined?overrides.days:days;
    const dThr=overrides.threshold!==undefined?overrides.threshold:thresholdMinutes;
    setLoadingList(true);setProgress(8);setErr("");setMsg("در حال بررسی لاگ‌ها و بارگذاری فهرست دستگاه‌ها...");setDiag(null);
    const progressTimer=window.setInterval(()=>setProgress(value=>value>=86?20:value+7),300);
    try{
      const url=API+"/reports/interface-flaps?days="+encodeURIComponent(dDays)+"&threshold_minutes="+encodeURIComponent(dThr)+(dbSel?("&database="+encodeURIComponent(dbSel)):"");
      const response=await fetch(url);if(!response.ok)throw Error("دریافت فهرست ناموفق بود ("+response.status+")");
      const data=await readJson(response);const items=Array.isArray(data)?data:(data.items||data.events||data.results||[]);
      setFlapResults(items);setReportDb((data&&data.database)||dbSel||"");setProgress(100);setMsg("فهرست دستگاه‌ها بارگذاری شد.");
      setDiag({error:(data&&data.error)||"",scanned:data&&data.devices_scanned,withLogs:data&&data.devices_with_logs,
        newest:data&&data.newest_log_at_jalali,newestG:data&&data.newest_log_at,
        stale:!!(data&&data.stale_logs),suggested:data&&data.suggested_days});
      if(data&&data.stale_logs&&data.suggested_days){setDays(data.suggested_days);}
    }catch(e){setErr(e.message||"خطا در بارگذاری فهرست");setMsg("");}
    finally{window.clearInterval(progressTimer);setLoadingList(false);window.setTimeout(()=>setProgress(0),800);}
  }
  async function downloadCsv(){
    setDownloadingCsv(true);setErr("");setMsg("در حال آماده‌سازی فایل CSV...");
    try{
      const url=API+"/reports/interface-flaps/export.csv?days="+encodeURIComponent(days)+"&threshold_minutes="+encodeURIComponent(thresholdMinutes)+(dbSel?("&database="+encodeURIComponent(dbSel)):"");
      const response=await fetch(url);if(!response.ok)throw Error("دریافت گزارش ناموفق بود ("+response.status+")");
      const blob=await response.blob();const objectUrl=URL.createObjectURL(blob);const a=document.createElement("a");
      a.href=objectUrl;a.download="interface_flaps_report.csv";document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(objectUrl);
      setMsg("فایل CSV آماده و دانلود شد.");
    }catch(e){setErr(e.message||"خطا در دانلود");setMsg("");}
    finally{setDownloadingCsv(false);}
  }
  const cellStyle={padding:"10px 12px",borderBottom:"1px solid #e5e7eb",textAlign:"right",whiteSpace:"nowrap"};
  const headerStyle={...cellStyle,background:"#f1f5f9",fontWeight:700,color:"#1f2937"};
  return (
    <section className="panel" dir="rtl">
      <h3>گزارش هوشمند — نوسان (flap) اینترفیس‌ها</h3>
      <label>بازه (روز)<input type="number" min="1" value={days} onChange={e=>setDays(parseInt(e.target.value||"5",10))}/></label>
      <label>آستانه نوسان (دقیقه)<input type="number" min="1" value={thresholdMinutes} onChange={e=>setThresholdMinutes(parseInt(e.target.value||"5",10))}/></label>
      <label>دیتابیس گزارش
        <select value={dbSel} onChange={e=>{setDbSel(e.target.value);setFlapResults([]);setReportDb("");setDiag(null);setMsg("دیتابیس تغییر کرد؛ برای گزارش جدید روی «مشاهده و بارگذاری لیست دستگاه‌ها» کلیک کنید.")}}
          title="گزارش فقط از دیتابیس انتخاب‌شده گرفته می‌شود">
          {dbList.map(d=><option key={d.name} value={d.name}>{d.name+(typeof d.devices==="number"?" ("+d.devices+" دستگاه)":"")+(d.active?" — فعال":"")}</option>)}
        </select>
      </label>
      <div style={{display:"flex",gap:8,flexWrap:"wrap",marginTop:12}}>
        <button type="button" className="tool-btn" disabled={loadingList||downloadingCsv} onClick={loadList}>مشاهده و بارگذاری لیست دستگاه‌ها</button>
        <button type="button" className="tool-btn" disabled={downloadingCsv} onClick={downloadCsv}>دانلود فایل CSV</button>
      </div>
      {(loadingList||downloadingCsv)&&<div role="status" aria-live="polite" style={{marginTop:12}}>
        <div>{msg||"در حال آماده‌سازی..."}</div>
        <div style={{height:8,background:"#e5e7eb",borderRadius:8,overflow:"hidden",marginTop:6}}>
          <div style={{height:"100%",width:(downloadingCsv?65:progress)+"%",background:"#168a55",transition:"width .35s ease"}}/>
        </div>
      </div>}
      {!loadingList&&!downloadingCsv&&msg&&<div className="msg">{msg}</div>}
      {err&&<div className="error" role="alert">{err}</div>}
      {flapResults.length===0&&diag&&(diag.error||diag.scanned!==undefined)&&<div style={{marginTop:10,borderRadius:8,padding:"10px 14px",lineHeight:2,
        background:diag.error?"#fef2f2":"#fffbeb",border:("1px solid ")+(diag.error?"#ef4444":"#f59e0b"),color:diag.error?"#991b1b":"#92400e"}}>
        {diag.error
          ?<div role="alert"><b>خطا در خواندن دیتابیس:</b> {diag.error}</div>
          :<>
            <div>بررسی شد: <b>{diag.scanned}</b> دستگاه{typeof diag.withLogs==="number"?(" — دارای لاگ: "+diag.withLogs+" دستگاه"):""}</div>
            {diag.newest&&<div>جدیدترین رویداد لینک ثبت‌شده در لاگ‌ها: <b>{diag.newest}</b>{diag.newestG?(" ("+diag.newestG+" میلادی)"):""}</div>}
            {typeof diag.withLogs==="number"&&diag.withLogs===0&&<div>هیچ دستگاهی در این دیتابیس لاگ ذخیره‌شده ندارد؛ ابتدا از دستگاه‌ها لاگ تهیه کنید (اسکن یا دریافت لاگ).</div>}
            {diag.stale&&diag.suggested&&<div style={{marginTop:8}}>هیچ نوسانی در بازه انتخابی یافت نشد، اما لاگ‌های قدیمی‌تر موجود است:<br/>
              <button type="button" className="tool-btn" style={{marginTop:6}} onClick={()=>loadList({days:diag.suggested})}>نمایش گزارش با بازه {diag.suggested} روزه</button>
            </div>}
          </>}
      </div>}
      {flapResults!==null&&flapResults.length>=0&&<div style={{marginTop:16}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10,flexWrap:"wrap",gap:8}}>
          <strong style={{background:"#e8f5ee",color:"#176b43",borderRadius:16,padding:"6px 12px"}}>تعداد موارد یافت‌شده: {flapResults.length}</strong>
          {reportDb&&<span style={{background:"#e0f2fe",color:"#075985",borderRadius:16,padding:"6px 12px",fontSize:13}}>دیتابیس: {reportDb}</span>}
          {flapResults.length>0&&<span style={{color:"#64748b",fontSize:13}}>برای دریافت فایل، روی «دانلود فایل CSV» کلیک کنید.</span>}
        </div>
        {flapResults.length>0?<div style={{overflowX:"auto",border:"1px solid #e5e7eb",borderRadius:8}}>
          <table dir="rtl" style={{width:"100%",borderCollapse:"collapse",minWidth:800}}>
            <thead><tr>{["ردیف","نام دستگاه","آی‌پی دستگاه","تگ دستگاه","اینترفیس","تعداد تکرار لاگ","تاریخ و زمان (میلادی)","تاریخ و زمان (شمسی)","نوع رویداد"].map(h=><th key={h} style={headerStyle}>{h}</th>)}</tr></thead>
            <tbody>{flapResults.map((item,index)=><tr key={item.row||index}>
              <td style={cellStyle}>{item.row||index+1}</td>
              <td style={cellStyle}>{item.device_name||"—"}</td>
              <td style={cellStyle}>{item.ip||"—"}</td>
              <td style={cellStyle}>{item.device_tag||item.tags||"—"}</td>
              <td style={cellStyle}>{item.iface||item.interface||"—"}</td>
              <td style={cellStyle}>{item.flap_count??1}</td>
              <td style={cellStyle}>{item.datetime||item.last_flap_time||item.last_flap||"—"}</td>
              <td style={cellStyle}>{item.datetime_jalali||item.last_flap_time_jalali||item.last_flap_jalali||"—"}</td>
              <td style={cellStyle}>{item.last_event||item.last_status||item.event||"—"}</td>
            </tr>)}</tbody>
          </table>
        </div>:<div style={{padding:14,color:"#64748b",lineHeight:1.7}}>
          موردی با این بازه و آستانه یافت نشد.
          {diag&&diag.withLogs===0&&<div style={{marginTop:8,color:"#b45309"}}>هیچ لاگی در دیتابیس انتخاب‌شده ذخیره نشده است. ابتدا از بخش دستگاه‌ها، لاگ RouterOS را برای دستگاه‌ها دریافت/به‌روز کنید.</div>}
          {diag&&diag.withLogs>0&&diag.stale&&diag.suggested&&<div style={{marginTop:8}}>لاگ‌ها قدیمی‌تر از بازه فعلی هستند (جدیدترین: {diag.newest||diag.newestG||"—"}).
            <button type="button" className="tool-btn" style={{marginTop:6,marginRight:8}} onClick={()=>loadList({days:diag.suggested})}>نمایش با بازه {diag.suggested} روزه</button>
          </div>}
          {diag&&diag.withLogs>0&&!diag.stale&&<div style={{marginTop:8}}>در بازه انتخابی نوسان (flap) با آستانه فعلی ثبت نشده است. بازه را بزرگ‌تر کنید یا آستانه دقیقه را افزایش دهید.</div>}
        </div>}
      </div>}
      <AntennaIssuesReport />
    </section>
  );
}
function AntennaIssuesReport(){
  const [days,setDays]=useState(30),[items,setItems]=useState([]),[busy,setBusy]=useState(false),[downloading,setDownloading]=useState(false),[msg,setMsg]=useState(""),[err,setErr]=useState("");
  async function load(){
    setBusy(true);setErr("");setMsg("در حال بررسی لاگ‌های وایرلس ذخیره‌شده...");
    try{const r=await fetch(API+"/reports/wireless-antenna-issues?days="+encodeURIComponent(days));const d=await readJson(r);if(!r.ok)throw Error(d.detail||"دریافت گزارش ناموفق بود");setItems(Array.isArray(d)?d:(d.items||d.events||[]));setMsg("گزارش بارگذاری شد؛ MACهای بدون تطبیق نیز نمایش داده می‌شوند.");}
    catch(e){setErr(e.message||"خطا در دریافت گزارش");setMsg("");}finally{setBusy(false);}
  }
  async function download(){
    setDownloading(true);setErr("");try{const r=await fetch(API+"/reports/wireless-antenna-issues/export.csv?days="+encodeURIComponent(days));if(!r.ok)throw Error("دانلود گزارش ناموفق بود ("+r.status+")");const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="wireless_antenna_issues.csv";document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);}
    catch(e){setErr(e.message||"خطا در دانلود");}finally{setDownloading(false);}
  }
  const cell={padding:"9px 10px",borderBottom:"1px solid #e5e7eb",textAlign:"right",verticalAlign:"top"};const head={...cell,background:"#f1f5f9",fontWeight:700,whiteSpace:"nowrap"};
  return <section className="panel" dir="rtl" style={{marginTop:18}}>
    <h3>گزارش قطع و وصل شدن آنتن‌ها</h3>
    <p style={{color:"#64748b",marginTop:0}}>رویدادهای قطع ارتباط، ضعف یا از دست رفتن سیگنال و خطاهای ایستگاه‌های وایرلس از لاگ‌های ذخیره‌شده‌ی RouterOS استخراج می‌شوند.</p>
    <label>بازه بررسی (روز)<input type="number" min="1" max="365" value={days} onChange={e=>setDays(Math.max(1,Math.min(365,parseInt(e.target.value||"5",10))))}/></label>
    <div style={{display:"flex",gap:8,flexWrap:"wrap",marginTop:12}}><button type="button" className="tool-btn" disabled={busy||downloading} onClick={load}>{busy?"در حال بررسی…":"ساخت / به‌روزرسانی گزارش"}</button><button type="button" className="tool-btn" disabled={downloading} onClick={download}>{downloading?"در حال آماده‌سازی…":"دانلود CSV"}</button></div>
    {msg&&<div className="msg" style={{marginTop:10}}>{msg}</div>}{err&&<div className="error" role="alert">{err}</div>}
    <div style={{marginTop:14,overflowX:"auto",border:"1px solid #e5e7eb",borderRadius:8}}><table dir="rtl" style={{width:"100%",borderCollapse:"collapse",minWidth:1050}}>
      <thead><tr>{["ردیف","تاریخ شمسی","آنتن/روتر لاگ‌دهنده","IP آنتن","MAC ایستگاه","نام دستگاه متناظر","IP دستگاه متناظر","رویداد ثبت‌شده"].map(x=><th key={x} style={head}>{x}</th>)}</tr></thead>
      <tbody>{items.map((x,i)=><tr key={x.row||i}><td style={cell}>{x.row||i+1}</td><td style={{...cell,whiteSpace:"nowrap"}}>{x.datetime_jalali||x.datetime||"—"}</td><td style={cell}>{x.antenna_name||"—"}</td><td style={cell} dir="ltr">{x.antenna_ip||"—"}</td><td style={cell} dir="ltr">{x.station_mac||"در لاگ MAC پیدا نشد"}</td><td style={cell}>{x.matched_device_name||"در دیتابیس تطبیق نشد"}</td><td style={cell} dir="ltr">{x.matched_device_ip||"—"}</td><td style={{...cell,whiteSpace:"normal",minWidth:260}}>{x.event||x.raw_line||"—"}</td></tr>)}</tbody>
    </table>{!items.length&&<p style={{padding:12,color:"#64748b"}}>برای تولید گزارش روی «ساخت / به‌روزرسانی گزارش» کلیک کنید.</p>}</div>
  </section>;
}

createRoot(document.getElementById("root")).render(<App/>);
