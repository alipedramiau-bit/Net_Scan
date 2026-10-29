import React, { useState, useEffect, useRef, useMemo, useCallback, startTransition } from 'react'

/** آیکون SVG کارت شناسایی */
function IconIdCard({ size = 28, color = '#2b6cb0' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      style={{ display: 'block' }}
    >
      {/* بدنه کارت */}
      <rect
        x="4"
        y="10"
        width="40"
        height="28"
        rx="3"
        fill="#EBF4FF"
        stroke={color}
        strokeWidth="2"
      />
      {/* نوار بالای کارت */}
      <path d="M4 16h40" stroke={color} strokeWidth="2" opacity="0.35" />
      {/* عکس پرسنلی روی کارت */}
      <rect x="9" y="20" width="10" height="12" rx="1.5" fill="#fff" stroke={color} strokeWidth="1.5" />
      <circle cx="14" cy="24.5" r="2.2" fill={color} opacity="0.85" />
      <path d="M10.5 30c0-1.8 1.6-3 3.5-3s3.5 1.2 3.5 3" fill={color} opacity="0.75" />
      {/* خطوط اطلاعات */}
      <rect x="23" y="21" width="16" height="2.2" rx="1" fill={color} opacity="0.55" />
      <rect x="23" y="26" width="12" height="2.2" rx="1" fill={color} opacity="0.4" />
      <rect x="23" y="31" width="14" height="2.2" rx="1" fill={color} opacity="0.3" />
    </svg>
  )
}

/** آیکون SVG عکس پرسنلی — قاب پرتره + شخص + نشان دوربین */
function IconPersonnelPhoto({ size = 28, color = '#2b6cb0' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      style={{ display: 'block' }}
    >
      <rect
        x="10"
        y="6"
        width="28"
        height="36"
        rx="3"
        fill="#EBF4FF"
        stroke={color}
        strokeWidth="2"
      />
      <rect
        x="13"
        y="9"
        width="22"
        height="30"
        rx="2"
        fill="#fff"
        stroke={color}
        strokeWidth="1"
        opacity="0.9"
      />
      <circle cx="24" cy="20" r="5.5" fill={color} opacity="0.9" />
      <path
        d="M14 36c1.5-6 5.5-9 10-9s8.5 3 10 9"
        fill={color}
        opacity="0.75"
      />
      <circle cx="34" cy="34" r="7" fill="#fff" stroke={color} strokeWidth="1.5" />
      <rect x="30.5" y="31.5" width="7" height="5.5" rx="1.2" fill="none" stroke={color} strokeWidth="1.4" />
      <circle cx="34" cy="34.2" r="1.6" fill={color} />
      <path
        d="M32 31.5h1.2l0.6-1.2h1.4l0.6 1.2H37"
        stroke={color}
        strokeWidth="1.2"
        fill="none"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function IconSvg({ path, size = 28, color = '#2b6cb0' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {path}
    </svg>
  )
}

function renderRibbonIcon(icon, label, small = false) {
  const t = String(label || '').replace(/\n/g, ' ')
  const s = small ? 18 : 28
  const c = '#2b6cb0'
  if (t.includes('صدور کارت')) return <IconIdCard size={s} color={c} />
  if (t.includes('عکس پرسنلی') || (t.includes('عکس') && t.includes('پرسنل'))) return <IconPersonnelPhoto size={s} color={c} />
  // SVG اختصاصی پشتیبان / بازیابی (همیشه، نه فقط وقتی icon خالی است)
  if (t.includes('بازیابی') && t.includes('پشتیبان')) {
    return <IconSvg size={s} color={c} path={<><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" /><path d="M12 8v8" /><path d="M8 12h8" /></>} />
  }
  if (t.includes('گرفتن') && t.includes('پشتیبان')) {
    return <IconSvg size={s} color={c} path={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></>} />
  }
  if (t.includes('بازیابی')) {
    return <IconSvg size={s} color={c} path={<><polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" /></>} />
  }
  if (t.includes('پشتیبان') || t.includes('بکاپ')) {
    return <IconSvg size={s} color={c} path={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></>} />
  }
  if (!icon || icon === '' || icon === '?' || icon === '•') {
    if (t.includes('کاربر') || t.includes('پرسنل')) {
      return <IconSvg size={s} color={c} path={<><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></>} />
    }
    if (t.includes('گزارش')) {
      return <IconSvg size={s} color={c} path={<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></>} />
    }
    if (t.includes('تنظیمات') || t.includes('سیستم')) {
      return <IconSvg size={s} color={c} path={<><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></>} />
    }
    return <IconSvg size={s} color={c} path={<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></>} />
  }
  return icon
}


/** برند سازمان و نرم‌افزار */
const ORG_SHORT = 'تأسیسات دریایی ایران'

/** سایزهای استاندارد کارت PVC برای پرینترهای کارت */
const PVC_CARD_SIZES = [
  {
    id: 'CR80',
    label: 'CR80 / ID-1 (استاندارد بانکی)',
    wMm: 85.60,
    hMm: 53.98,
    note: 'رایج‌ترین — ISO/IEC 7810 ID-1',
  },
  {
    id: 'CR79',
    label: 'CR79',
    wMm: 84.15,
    hMm: 52.40,
    note: 'کمی کوچک‌تر از CR80',
  },
  {
    id: 'CR100',
    label: 'CR100',
    wMm: 88.90,
    hMm: 63.50,
    note: '۳٫۵ × ۲٫۵ اینچ',
  },
  {
    id: 'CR90',
    label: 'CR90',
    wMm: 92.07,
    hMm: 60.33,
    note: '۳٫۶۲۵ × ۲٫۳۷۵ اینچ',
  },
  {
    id: 'CR80_THICK',
    label: 'CR80 ضخیم (۳۰ mil)',
    wMm: 85.60,
    hMm: 53.98,
    note: 'همان ابعاد CR80 — ضخامت بیشتر',
  },
  {
    id: 'ID2',
    label: 'ID-2',
    wMm: 105.00,
    hMm: 74.00,
    note: 'ISO/IEC 7810 ID-2',
  },
  {
    id: 'BADGE',
    label: 'Badge / گردن‌آویز',
    wMm: 85.60,
    hMm: 53.98,
    note: 'ابعاد CR80 با محل پانچ بالا',
  },
]

const ORG_FULL = 'تأسیسات دریایی ایران'
const ORG_LEGAL = 'شرکت مهندسی و ساخت تأسیسات دریایی ایران (IOEC)'
const APP_TITLE = 'سیستم جامع حراست'

/** لوگوی IOEC — تأسیسات دریایی ایران */
function OilFundLogo({ size = 64 }) {
  const s = size
  return (
    <img
      src="/logo-ioec.png"
      alt="IOEC — تأسیسات دریایی ایران"
      width={s}
      height={Math.round(s * 0.83)}
      style={{ width: s, height: Math.round(s * 0.83), objectFit: 'contain', display: 'block' }}
    />
  )
}

/** SVG پشتیبان لوگوی IOEC (شعله + موج + دایره آبی) */
function IoecLogoSvg({ size = 64 }) {
  const s = size
  return (
    <svg width={s} height={s} viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style={{ display: 'none' }}>
      <circle cx="60" cy="52" r="42" fill="#1e4a9a" />
      <path d="M60 18c-3 10-2 18 0 26 2-8 3-16 0-26z" fill="#e11d2e" />
      <path d="M60 24c-8 10-10 22-6 32 5-5 8-14 6-32z" fill="#f43f5e" />
      <path d="M60 24c8 10 10 22 6 32-5-5-8-14-6-32z" fill="#be123c" />
      <path d="M28 58c8 4 16 6 32 6s24-2 32-6c-4 8-14 14-32 14s-28-6-32-14z" fill="#fff" opacity="0.95" />
      <path d="M30 68c8 3 14 5 30 5s22-2 30-5c-4 7-12 12-30 12s-26-5-30-12z" fill="#fff" opacity="0.9" />
      <path d="M34 76c6 2 12 4 26 4s20-2 26-4c-3 6-10 10-26 10s-23-4-26-10z" fill="#fff" opacity="0.85" />
      <text x="60" y="112" textAnchor="middle" fontFamily="Arial,sans-serif" fontWeight="700" fontSize="18" fill="#1e4a9a">IOEC</text>
    </svg>
  )
}

/** کارت PVC رو (جلو) — عدد پرسنلی زیر عکس چپ؛ لوگو وسط بالای متن پایین */
function IdCardFront({ person, companyName, logoUrl }) {
  const p = person || {}
  const fullName = [p.first_name, p.last_name].filter(Boolean).join(' ') || '—'
  const photo = p.photo || ''
  const indicator = toPersianDigits(p.indicator_num || p.card_number || '—')
  const org = companyName || p.company || ORG_SHORT
  const place = org
  const logoSrc = logoUrl || ''
  const vfont = { fontFamily: "'Vazirmatn', Vazirmatn, Tahoma, sans-serif" }
  const namePlaceSize = '2.85mm'
  return (
    <div
      className="pvc-card pvc-card-preview"
      dir="rtl"
      style={{
        ...vfont,
        background: '#ffffff',
        direction: 'rtl',
      }}
    >
      {/* واترمارک */}
      <div
        className="pvc-watermark"
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          overflow: 'hidden',
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gridTemplateRows: 'repeat(3, 1fr)',
          alignItems: 'center',
          justifyItems: 'center',
          gap: '0.6mm',
          padding: '1.5mm 2mm',
          boxSizing: 'border-box',
        }}
      >
        {Array.from({ length: 12 }).map((_, i) => (
          <img
            key={i}
            src={logoSrc || '/logo-ioec.png'}
            alt=""
            style={{
              width: '12mm',
              height: '10mm',
              objectFit: 'contain',
              opacity: 0.09,
              filter: 'grayscale(12%)',
            }}
          />
        ))}
      </div>

      {/* عکس — بالا چپ */}
      <div style={{
        position: 'absolute',
        top: '2.8mm',
        left: '3mm',
        width: '22mm',
        height: '28mm',
        background: '#c41e3a',
        overflow: 'hidden',
        zIndex: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {photo ? (
          <img
            src={photo}
            alt=""
            style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center top' }}
          />
        ) : (
          <span style={{ color: '#fecaca', fontSize: '2.8mm', ...vfont }}>عکس</span>
        )}
      </div>

      {/* لوگو + نام شرکت — وسط کارت (روی نقطه مشخص‌شده)، بالای متن پایین */}
      <div style={{
        position: 'absolute',
        top: '3mm',
        left: '28mm',
        right: '8mm',
        zIndex: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        gap: '1.5mm',
      }}>
        <div style={{
          width: '28mm',
          height: '22mm',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {logoSrc ? (
            <img src={logoSrc} alt="" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />
          ) : (
            <OilFundLogo size={96} />
          )}
        </div>
        <div style={{
          textAlign: 'center',
          fontSize: '2.55mm',
          fontWeight: 700,
          color: '#0f172a',
          lineHeight: 1.35,
          maxWidth: '52mm',
          ...vfont,
        }}>
          {org}
        </div>
      </div>

      {/* فضای خالی هولوگرام — مرکز پایین */}
      <div
        aria-hidden="true"
        title="محل هولوگرام"
        style={{
          position: 'absolute',
          bottom: '3.5mm',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '13mm',
          height: '13mm',
          borderRadius: '50%',
          zIndex: 1,
          background: 'transparent',
        }}
      />

      {/* پایین چپ زیر عکس — RTL: عدد سمت چپ، «شماره پرسنلی:» سمت راست آن */}
      <div
        dir="rtl"
        style={{
          position: 'absolute',
          bottom: '11mm',
          left: '3mm',
          maxWidth: '38mm',
          zIndex: 2,
          textAlign: 'right',
          fontSize: namePlaceSize,
          fontWeight: 700,
          color: '#0f172a',
          whiteSpace: 'nowrap',
          ...vfont,
        }}
      >
        <span>شماره پرسنلی:</span>
        {' '}
        <span style={{ letterSpacing: '0.25mm', fontWeight: 800 }}>{indicator}</span>
      </div>

      {/* نام شرکت به‌عنوان محل — زیر شماره، چپ زیر عکس */}
      <div style={{
        position: 'absolute',
        bottom: '4mm',
        left: '3mm',
        maxWidth: '36mm',
        zIndex: 2,
        textAlign: 'right',
        fontSize: namePlaceSize,
        fontWeight: 700,
        color: '#0f172a',
        lineHeight: 1.3,
        ...vfont,
      }} dir="rtl">
        {place}
      </div>

      {/* نام پرسنل — پایین راست */}
      <div style={{
        position: 'absolute',
        bottom: '11mm',
        right: '3.5mm',
        zIndex: 2,
        textAlign: 'right',
        fontSize: namePlaceSize,
        fontWeight: 800,
        color: '#0f172a',
        ...vfont,
      }}>
        {fullName}
      </div>

      {/* برچسب محل کار — زیر نام */}
      <div style={{
        position: 'absolute',
        bottom: '4mm',
        right: '3.5mm',
        zIndex: 2,
        textAlign: 'right',
        fontSize: namePlaceSize,
        fontWeight: 700,
        color: '#0f172a',
        ...vfont,
      }}>
        محل کار:
      </div>
    </div>
  )
}

/** کارت PVC پشت — طرح افقی مطابق کارت واقعی */
function IdCardBack({ person, companyName, logoUrl }) {
  const p = person || {}
  const nid = toPersianDigits(p.national_id || '')
  const postal = toPersianDigits(p.postal_code || p.card_number || p.indicator_num || '')
  const org = companyName || p.company || ORG_SHORT
  const expiry = p.validity_end || 'پایان قرارداد'
  const logoSrc = logoUrl || ''
  const vfont = { fontFamily: "'Vazirmatn', Vazirmatn, Tahoma, sans-serif" }
  return (
    <div
      className="pvc-card pvc-card-preview"
      dir="rtl"
      style={{
        ...vfont,
        background: '#ffffff',
        direction: 'rtl',
      }}
    >
      {/* واترمارک: تکرار لوگوی هم‌اندازه با فاصله منطقی */}
      <div
        className="pvc-watermark"
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          overflow: 'hidden',
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gridTemplateRows: 'repeat(3, 1fr)',
          alignItems: 'center',
          justifyItems: 'center',
          gap: '0.6mm',
          padding: '2mm 2.5mm',
          boxSizing: 'border-box',
        }}
      >
        {Array.from({ length: 12 }).map((_, i) => (
          <img
            key={i}
            src={logoSrc || '/logo-ioec.png'}
            alt=""
            style={{
              width: '12mm',
              height: '10mm',
              objectFit: 'contain',
              opacity: 0.08,
              filter: 'grayscale(15%)',
            }}
          />
        ))}
      </div>

      {/* کادر بالای کارت: شماره ملی + کد پستی */}
      <div style={{
        position: 'absolute',
        top: '3mm',
        left: '3mm',
        right: '3mm',
        height: '14mm',
        border: '0.45mm solid #0f172a',
        borderRadius: '0.8mm',
        zIndex: 2,
        boxSizing: 'border-box',
        padding: '1.8mm 2.5mm',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        gap: '1.6mm',
        background: '#fff',
      }}>
        <div
          dir="rtl"
          style={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '2.8mm',
            fontWeight: 700,
            color: '#0f172a',
            direction: 'rtl',
            ...vfont,
          }}
        >
          <span>شماره ملی:</span>
          <span style={{ letterSpacing: '0.35mm', fontWeight: 800 }}>{nid || '—'}</span>
        </div>
        <div
          dir="rtl"
          style={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '2.8mm',
            fontWeight: 700,
            color: '#0f172a',
            direction: 'rtl',
            ...vfont,
          }}
        >
          <span>کد پستی:</span>
          <span style={{ letterSpacing: '0.35mm', fontWeight: 800 }}>{postal || '—'}</span>
        </div>
      </div>

      {/* متن حقوقی */}
      <div style={{
        position: 'absolute',
        top: '20mm',
        left: '4mm',
        right: '4mm',
        zIndex: 2,
        textAlign: 'center',
        fontSize: '2.5mm',
        fontWeight: 600,
        color: '#0f172a',
        lineHeight: 1.7,
        ...vfont,
      }}>
        هرگونه سوء استفاده از این کارت پیگرد قانونی دارد.
      </div>
      <div style={{
        position: 'absolute',
        top: '26.5mm',
        left: '4mm',
        right: '4mm',
        zIndex: 2,
        textAlign: 'center',
        fontSize: '2.4mm',
        fontWeight: 600,
        color: '#0f172a',
        lineHeight: 1.65,
        ...vfont,
      }}>
        از یابنده تقاضا می‌شود این کارت را به صندوق پستی بیاندازد.
      </div>

      {/* تاریخ انقضاء — قرمز */}
      <div style={{
        position: 'absolute',
        top: '34.5mm',
        left: '3mm',
        right: '3mm',
        zIndex: 2,
        textAlign: 'center',
        fontSize: '3mm',
        fontWeight: 800,
        color: '#dc2626',
        ...vfont,
      }}>
        تاریخ انقضاء: {toPersianDigits(expiry)}
      </div>

      {/* نام سازمان پایین */}
      <div style={{
        position: 'absolute',
        bottom: '3.5mm',
        left: '3mm',
        right: '3mm',
        zIndex: 2,
        textAlign: 'center',
        fontSize: '2.35mm',
        fontWeight: 700,
        color: '#0f172a',
        lineHeight: 1.4,
        ...vfont,
      }}>
        ({org})
      </div>
    </div>
  )
}





const TABS = [
  { id: 'personnel', label: 'پرسنل' },
  { id: 'companies', label: 'شرکت‌های تابعه' },
  { id: 'monitoring', label: 'گشت و پایش' },
  { id: 'mojaz', label: 'صدور مجوز تردد' },
  { id: 'peymankar', label: 'پیمانکاران' },
  { id: 'entezamat', label: 'انتظامات' },
  { id: 'herasat', label: 'حراست' },
  { id: 'monaghese', label: 'مناقصات و مزایدات' },
  { id: 'kartabl', label: 'کارتابل' },
  { id: 'baskool', label: 'باسکول' },
  { id: 'pelakhwan', label: 'پلاک‌خوان' },
  { id: 'access', label: 'کنترل دسترسی' },
  { id: 'workflow', label: 'جریان کار' },
  { id: 'sodor_kart', label: 'صدور کارت' },
  { id: 'baseinfo', label: 'اطلاعات پایه' },
  { id: 'gozaresh', label: 'گزارشات' },
  { id: 'modiriat', label: 'مدیریت سیستم' },
]

const RIBBONS = {
  herasat: [
    {
      title: 'ارزشیابی پرسنل',
      items: [
        { type: 'large', icon: '📊', code: 'HR_EVAL_OPTS', label: 'گزینه‌های\nارزشیابی' },
        { type: 'large', icon: '📝', code: 'HR_EVAL_TITLES', label: 'عناوین\nارزشیابی' },
        { type: 'large', icon: '📅', code: 'HR_EVAL_PERIOD', label: 'تعریف دوره\nارزشیابی' },
        { type: 'large', icon: '👤', code: 'HR_EVAL_MONTHLY', label: 'ارزشیابی ماهانه\nپرسنل' },
      ],
    },
    {
      title: 'منازل و اماکن',
      items: [
        { type: 'large', icon: '🗺️', code: 'HR_AREAS', label: 'تعریف\nنواحی' },
        { type: 'large', icon: '🏠', code: 'HR_HOUSES', label: 'تعریف\nمنازل' },
        { type: 'large', icon: '🔑', code: 'HR_HOUSE_DELIVERY', label: 'تحویل منازل\nو اماکن' },
      ],
    },
    {
      title: 'کنترل حراست',
      items: [
        { type: 'large', icon: '⚠️', code: 'HR_VIOL_PERS', label: 'ثبت تخلفات\nپرسنل و پیمانکار' },
        { type: 'large', icon: '🚗', code: 'HR_VIOL_VEH', label: 'ثبت تخلفات\nخودرویی' },
        { type: 'large', icon: '📋', code: 'HR_INCIDENT', label: 'صورتجلسه\nحوادث' },
        { type: 'large', icon: '🧪', code: 'HR_DRUG', label: 'ثبت مصرف\nمواد مخدر' },
        { type: 'large', icon: '🏆', code: 'HR_REWARD', label: 'تقدیر و تشویق\nسازمانی' },
      ],
    },
    {
      title: 'اتباع و مدارک',
      items: [
        { type: 'large', icon: '🌍', code: 'HR_FOREIGN', label: 'مشخصات اتباع\nخارجی' },
        { type: 'large', icon: '🏳️', code: 'HR_COUNTRIES', label: 'مشخصات\nکشورها' },
        { type: 'large', icon: '📁', code: 'HR_ARCHIVE', label: 'بایگانی\nمدارک' },
      ],
    },
    {
      title: 'سفر و خروج',
      items: [
        { type: 'large', icon: '✈️', code: 'HR_TRAVEL_OUT', label: 'پرسشنامه اعزام\nبه خارج' },
        { type: 'large', icon: '🧳', code: 'HR_TRAVEL_PERS', label: 'پرسشنامه\nسفرهای شخصی' },
        { type: 'large', icon: '📄', code: 'HR_EXIT_ADMIN', label: 'خروج دیپ و\nمدارک اداری' },
        { type: 'large', icon: '📚', code: 'HR_EXIT_SCI', label: 'خروج دیپ و\nمدارک علمی' },
      ],
    },
    {
      title: 'گزارش‌ها',
      items: [
        { type: 'large', icon: '📢', code: 'ENT_NEWS', label: 'گزارش\nخبر' },
      ],
    },
  ],

  monaghese: [
    {
      title: 'شرکت‌ها',
      items: [
        { type: 'large', icon: '🏢', code: 'TND_COMPANIES', label: 'شرکت‌های حاضر\nدر مناقصه/مزایده' },
      ],
    },
    {
      title: 'مناقصه و مزایده',
      items: [
        { type: 'large', icon: '📢', code: 'TND_TENDERS', label: 'مناقصات' },
        { type: 'large', icon: '🔨', code: 'TND_AUCTIONS', label: 'مزایده' },
      ],
    },
    {
      title: 'قرارداد',
      items: [
        { type: 'large', icon: '📄', code: 'TND_CONTRACTS', label: 'قراردادها' },
      ],
    },
  ],


  kartabl: [
    {
      title: 'نامه‌ها',
      items: [
        { type: 'large', icon: '📤', code: 'KRT_OUTGOING', label: 'نامه‌های\nصادره' },
        { type: 'large', icon: '📥', code: 'KRT_INBOX', label: 'نامه‌های\nوارده' },
      ],
    },
    {
      title: 'مدیریت',
      items: [
        { type: 'large', icon: '📬', code: 'KRT_MANAGE', label: 'مدیریت\nکارتابل' },
        { type: 'large', icon: '📁', code: 'KRT_FOLDERS', label: 'پوشه‌های\nبایگانی' },
      ],
    },
  ],


  baskool: [
    {
      title: 'عملیات',
      items: [
        { type: 'large', icon: '⚖️', code: 'BSK_WEIGH', label: 'ثبت\nتوزین' },
        { type: 'large', icon: '🎫', code: 'BSK_TURN', label: 'سیستم ثبت\nنوبت' },
        { type: 'large', icon: '🚫', code: 'BSK_BAN', label: 'ممنوعیت\nتردد' },
      ],
    },
    {
      title: 'اطلاعات پایه',
      items: [
        { type: 'large', icon: '🏢', code: 'BSK_CO', label: 'تعریف\nشرکت‌ها' },
        { type: 'large', icon: '📦', code: 'BSK_TON', label: 'حداکثر تناژ\nپیمانکاران' },
        { type: 'large', icon: '⚙️', code: 'BSK_SET', label: 'تنظیمات\nباسکول' },
      ],
    },
    {
      title: 'گزارشات',
      items: [
        { type: 'large', icon: '📊', code: 'BSK_RPT', label: 'گزارش\nتوزین' },
      ],
    },
  ],


  pelakhwan: [
    {
      title: 'عملیات',
      items: [
        { type: 'large', icon: '🔍', code: 'PLK_PROCESS', label: 'فرم پردازش\nپلاک‌خوان' },
        { type: 'large', icon: '🚗', code: 'PLK_TRAFFIC', label: 'تردد\nپلاک‌خوان' },
        { type: 'large', icon: '📡', code: 'PLK_MON', label: 'مانیتورینگ\nپلاک‌خوان' },
        { type: 'large', icon: '🅿️', code: 'PLK_PARK', label: 'فرم\nپارکینگ' },
      ],
    },
    {
      title: 'گزارشات',
      items: [
        { type: 'large', icon: '📊', code: 'PLK_RPT', label: 'گزارش تردد\nپلاک‌خوان' },
        { type: 'large', icon: '📋', code: 'PLK_FULL_RPT', label: 'گزارش تردد\nکامل' },
        { type: 'large', icon: '🔐', code: 'PLK_ACCESS', label: 'سطح دسترسی\nخودروها' },
        { type: 'large', icon: '🏢', code: 'PLK_INSIDE', label: 'خودروهای داخل\nسازمان' },
      ],
    },
    {
      title: 'تنظیمات',
      items: [
        { type: 'large', icon: '📷', code: 'PLK_CAM', label: 'تعریف دوربین‌های\nپلاک‌خوان' },
        { type: 'large', icon: '📺', code: 'PLK_ONLINE', label: 'مانیتورینگ آنلاین\nپلاک‌خوان' },
      ],
    },
  ],


  access: [
    {
      title: 'تردد',
      items: [
        { type: 'large', icon: '🚶', code: 'AC_TRAFFIC', label: 'فرم تردد\nRFID' },
        { type: 'large', icon: '🔑', code: 'AC_ACCESS', label: 'تعریف\nدسترسی' },
      ],
    },
    {
      title: 'مهمان',
      items: [
        { type: 'large', icon: '👤', code: 'AC_GUEST', label: 'مهمان' },
        { type: 'large', icon: '💳', code: 'AC_GCARD', label: 'کارت\nمهمان‌ها' },
        { type: 'large', icon: '🗺️', code: 'AC_GZONE', label: 'محدوده تردد\nمهمان' },
        { type: 'large', icon: '📤', code: 'AC_GDEL', label: 'کارت‌های\nتحویل‌شده' },
        { type: 'large', icon: '📊', code: 'AC_GRPT', label: 'گزارش تردد\nمهمانان' },
      ],
    },
    {
      title: 'تخصیص و دستگاه',
      items: [
        { type: 'large', icon: '✅', code: 'AC_ASSIGN', label: 'فرم\nتخصیص' },
        { type: 'large', icon: '🖥️', code: 'AC_TERM', label: 'ترمینال‌ها' },
        { type: 'large', icon: '📡', code: 'AC_TSTAT', label: 'وضعیت\nترمینال‌ها' },
        { type: 'large', icon: '🔄', code: 'AC_SYNC', label: 'همسان‌سازی\nکاربران' },
        { type: 'large', icon: '📋', code: 'AC_RPT', label: 'گزارشات\nکلی' },
      ],
    },
  ],

  personnel: [
    {
      title: 'ثبت مشخصات',
      items: [
        { type: 'large', icon: '📋', code: 'PER_LIST', label: 'لیست\nپرسنل' },
        { type: 'large', icon: '👤', code: 'PER_REG_NEW', label: 'ثبت مشخصات\nپرسنل' },
        { type: 'large', icon: '📝', code: 'PER_REG_EDIT', label: 'ویرایش\nاطلاعات' },
        {
          type: 'stack',
          buttons: [
            { icon: '🔍', code: 'PER_REG_SEARCH', label: 'جستجوی پرسنل' },
            { icon: '📂', code: 'PER_REG_ARCHIVE', label: 'آرشیو پرسنل' },
          ],
        },
      ],
    },
    {
      title: 'مدارک و عکس',
      items: [
        { type: 'large', icon: '📁', code: 'PER_DOC_PHOTO', label: 'عکس\nپرسنلی' },
        { type: 'large', icon: '📄', code: 'PER_DOC_ID', label: 'مدارک\nشناسایی' },
        {
          type: 'stack',
          buttons: [
            { icon: '📎', code: 'PER_DOC_ATTACH', label: 'پیوست فایل' },
            { icon: '🖨️', code: 'PER_DOC_PRINT', label: 'چاپ پرونده' },
          ],
        },
      ],
    },
    {
      title: 'کارت',
      items: [
        { type: 'large', icon: '🪪', code: 'PER_CARD_ISSUE', label: 'صدور کارت\nشناسایی' },
        { type: 'large', icon: '🏢', code: 'PER_ASSIGN_ORG', label: 'تخصیص شرکت\nمرکز و واحد' },
        {
          type: 'stack',
          buttons: [
            { icon: '🚫', code: 'PER_CARD_BLOCK', label: 'مسدودسازی کارت' },
            { icon: '🔄', code: 'PER_CARD_RENEW', label: 'تمدید کارت' },
          ],
        },
      ],
    },
    {
      title: 'سوابق و وابستگان',
      items: [
        { type: 'large', icon: '👨👦', code: 'PER_REL_REG', label: 'ثبت\nوابستگان' },
        { type: 'large', icon: '📋', code: 'PER_REL_SERVICE', label: 'سوابق\nخدماتی' },
        {
          type: 'stack',
          buttons: [
            { icon: '✈️', code: 'PER_REL_TRAVEL', label: 'سفر خارجی' },
            { icon: '🏥', code: 'PER_REL_MEDICAL', label: 'سوابق پزشکی' },
          ],
        },
      ],
    },
  ],
  companies: [
    {
      title: 'ثبت شرکت',
      items: [
        { type: 'large', icon: '🏢', code: 'CO_REG_NEW', label: 'ثبت شرکت\nتابعه' },
        { type: 'large', icon: '📝', code: 'CO_REG_EDIT', label: 'ویرایش\nاطلاعات' },
        {
          type: 'stack',
          buttons: [
            { icon: '🔍', code: 'CO_REG_SEARCH', label: 'جستجوی شرکت' },
            { icon: '📂', code: 'CO_REG_ARCHIVE', label: 'آرشیو شرکت‌ها' },
          ],
        },
      ],
    },
    {
      title: 'ساختار سازمانی',
      items: [
        { type: 'large', icon: '🏛️', code: 'CO_ORG_UNITS', label: 'تعریف واحد\nو مرکز' },
        { type: 'large', icon: '📍', code: 'CO_ORG_SITES', label: 'محل‌های\nاستقرار' },
        {
          type: 'stack',
          buttons: [
            { icon: '🗺️', code: 'CO_ORG_CHART', label: 'چارت سازمانی' },
            { icon: '📞', code: 'CO_ORG_CONTACT', label: 'اطلاعات تماس' },
          ],
        },
      ],
    },
    {
      title: 'دسترسی و ایزوله',
      items: [
        { type: 'large', icon: '🔐', code: 'CO_ACL_ASSIGN', label: 'تخصیص\nشرکت به کاربر' },
        { type: 'large', icon: '👁️', code: 'CO_ACL_LIMIT', label: 'محدودیت\nمشاهده پرسنل' },
        {
          type: 'stack',
          buttons: [
            { icon: '✅', code: 'CO_ACL_TOGGLE', label: 'فعال/غیرفعال شرکت' },
            { icon: '🔗', code: 'CO_ACL_LINK', label: 'ارتباط شرکت‌ها' },
          ],
        },
      ],
    },
    {
      title: 'گزارش شرکت‌ها',
      items: [
        { type: 'large', icon: '📊', code: 'CO_RPT_STATS', label: 'آمار پرسنل\nهر شرکت' },
        { type: 'large', icon: '📋', code: 'CO_RPT_ACTIVE', label: 'لیست\nشرکت‌های فعال' },
      ],
    },
  ],
  baseinfo: [
    {
      title: 'جداول پرسنلی',
      items: [
        { type: 'large', icon: '🎓', code: 'BI_EDU', label: 'رشته\nتحصیلی' },
        { type: 'large', icon: '💼', code: 'BI_RESP', label: 'گروه\nمسئولیت' },
        { type: 'large', icon: '📋', code: 'BI_EMP', label: 'انواع\nاستخدام' },
      ],
    },
    {
      title: 'تردد و دسترسی',
      items: [
        { type: 'large', icon: '🚪', code: 'BI_DOORS', label: 'تعریف درب‌های\nتردد' },
        { type: 'large', icon: '🔑', code: 'BI_DOOR_ACCESS', label: 'دسترسی\nدرب' },
        { type: 'large', icon: '↔️', code: 'BI_ENTRY_EXIT', label: 'نوع ورود\nو خروج' },
      ],
    },
    {
      title: 'کالا و سرویس',
      items: [
        { type: 'large', icon: '📦', code: 'BI_GOODS_DEST', label: 'تعریف\nمقصد کالا' },
        { type: 'large', icon: '🚌', code: 'BI_SERVICES', label: 'تعریف\nسرویس' },
        { type: 'large', icon: '🏢', code: 'BI_CLIENTS', label: 'تعریف شرکت\n/مشتری' },
      ],
    },
    {
      title: 'کالاها',
      items: [
        { type: 'large', icon: '📥', code: 'BI_GOODS_IO', label: 'انواع ورود\nو خروج کالا' },
        { type: 'large', icon: '📦', code: 'BI_GOODS_PROD', label: 'تعریف کالا\nو محصولات' },
      ],
    },
    {
      title: 'خودروها',
      items: [
        { type: 'large', icon: '🚘', code: 'BI_VEH_TYPE', label: 'تعریف نوع\nخودروها' },
        { type: 'large', icon: '🚗', code: 'BI_VEHICLES', label: 'تعریف\nخودروها' },
        { type: 'large', icon: '🚛', code: 'BI_CARGO_VEH', label: 'تعریف خودروهای\nباری' },
        { type: 'large', icon: '📝', code: 'BI_CARGO_REASON', label: 'علت تردد\nخودروهای باری' },
      ],
    },
  ],
  monitoring: [
    {
      title: 'تنظیمات',
      items: [
        { type: 'large', icon: '📟', code: 'PAT_DEVICES', label: 'لیست\nدستگاه‌ها' },
        { type: 'large', icon: '📋', code: 'PAT_EVENTS', label: 'لیست\nرخدادها' },
        { type: 'large', icon: '📍', code: 'PAT_CHECKPOINTS', label: 'لیست نقاط\nبازدید' },
        { type: 'large', icon: '🛡️', code: 'PAT_GUARDS', label: 'لیست\nنگهبانان' },
      ],
    },
    {
      title: 'پیکربندی عملیاتی',
      items: [
        { type: 'large', icon: '🗺️', code: 'PAT_ROUTE_CFG', label: 'پیکربندی\nمسیر' },
        { type: 'large', icon: '🛤️', code: 'PAT_ROUTES', label: 'مسیرها و\nساعات شروع' },
        { type: 'large', icon: '⏰', code: 'PAT_SHIFT_TIMES', label: 'تعیین ساعت\nشروع و پایان' },
      ],
    },
  ],
  mojaz: [
    {
      title: 'صدور مجوز تردد',
      items: [
        { type: 'large', icon: '👤', code: 'MJZ_PERSON', label: 'مجوز تردد\nنفر' },
        { type: 'large', icon: '🚗', code: 'MJZ_VEHICLE', label: 'مجوز تردد\nخودرو' },
        { type: 'large', icon: '📦', code: 'MJZ_GOODS', label: 'مجوز خروج\nکالا' },
      ],
    },
    {
      title: 'نظارت نگهبانی',
      items: [
        { type: 'large', icon: '📋', code: 'MJZ_LIST', label: 'لیست و تأیید\nمجوزها' },
        { type: 'large', icon: '📊', code: 'MJZ_RPT', label: 'گزارش مجوزها\n(خروجی CSV)' },
      ],
    },
    {
      title: 'ترددهای خاص',
      items: [
        { type: 'large', icon: '🚂', code: 'TRD_TRAIN', label: 'قطار و\nواگن باری' },
        { type: 'large', icon: '🚢', code: 'TRD_SHIP', label: 'تردد کشتی\nدر اسکله' },
        {
          type: 'stack',
          buttons: [
            { icon: '👤', code: 'TRD_FOREIGN', label: 'اتباع خارج‌شده از کشتی' },
            { icon: '💧', code: 'TRD_WATER', label: 'آبگیری شناورها' },
            { icon: '🔒', code: 'TRD_SEC', label: 'اطلاعات امنیتی کشتی' },
          ],
        },
      ],
    },
  ],
  peymankar: [
    {
      title: 'شرکت و قرارداد',
      items: [
        { type: 'large', icon: '🏢', code: 'PYM_CO_REG', label: 'شرکت‌های\nپیمانکار' },
        { type: 'large', icon: '📄', code: 'PYM_CONTRACT', label: 'قرارداد شرکت‌های\nپیمانکار' },
      ],
    },
    {
      title: 'پرسنل',
      items: [
        { type: 'large', icon: '👷', code: 'PYM_STAFF', label: 'پرسنل شرکت‌های\nپیمانکار' },
      ],
    },
    {
      title: 'خودرو و راننده',
      items: [
        { type: 'large', icon: '🚛', code: 'PYM_VEHICLE', label: 'ثبت خودروهای\nپیمانکاران' },
        { type: 'large', icon: '🪪', code: 'PYM_DRIVER', label: 'ثبت راننده‌های\nپیمانکاران' },
      ],
    },
    {
      title: 'گزارش‌گیری',
      items: [
        { type: 'large', icon: '📊', code: 'PYM_REPORT', label: 'گزارش‌گیری\nپیمانکاران' },
        { type: 'large', icon: '📥', code: 'PYM_REPORT_CSV', label: 'خروجی CSV\nگزارش' },
      ],
    },
  ],
  entezamat: [
    {
      title: 'عملیات شیفت',
      items: [
        { type: 'large', icon: '📋', code: 'ENT_GUARD_BOARD', label: 'لوح\nنگهبانی' },
        { type: 'large', icon: '📝', code: 'ENT_SHIFT_EVENTS', label: 'ثبت وقایع\nشیفت' },
        { type: 'large', icon: '📅', code: 'ENT_SHIFT_SCHED', label: 'برنامه\nنوبتکاری' },
        { type: 'large', icon: '📻', code: 'ENT_ELEC', label: 'تجهیزات الکترونیک\nپرسنل' },
      ],
    },
    {
      title: 'درخواست و مجوز',
      items: [
        { type: 'large', icon: '🔁', code: 'ENT_REPLACE', label: 'درخواست\nجایگزینی' },
        { type: 'large', icon: '📄', code: 'ENT_PERMIT', label: 'صدور\nمجوز' },
      ],
    },
    {
      title: 'مانیتورینگ',
      items: [
        { type: 'large', icon: '🖥️', code: 'ENT_MON_EVT', label: 'وقایع شیفت\nاتاق مانیتورینگ' },
        { type: 'large', icon: '👤', code: 'ENT_MON_STAFF', label: 'مسئولین اتاق\nمانیتورینگ' },
      ],
    },
    {
      title: 'گزارش‌ها',
      items: [
        { type: 'large', icon: '📊', code: 'ENT_G_RPT', label: 'گزارش\nنگهبانی' },
        { type: 'large', icon: '↪️', code: 'ENT_G_REF', label: 'گزارش ارجاع\nنگهبانی' },
        { type: 'large', icon: '✅', code: 'ENT_ROLL', label: 'رول‌کال\n/ رونوشت' },
      ],
    },
    {
      title: 'وقایع و استقرار',
      items: [
        { type: 'large', icon: '📌', code: 'ENT_BOARD_SUM', label: 'لوح نگهبانی\nاجمالی' },
        { type: 'large', icon: '📓', code: 'ENT_G_EVT', label: 'ثبت وقایع\nنگهبانی' },
        { type: 'large', icon: '📍', code: 'ENT_DEPLOY', label: 'شناسه محل\nاستقرار' },
        { type: 'large', icon: '🛡️', code: 'ENT_OFF_EVT', label: 'وقایع افسر\nنگهبانی' },
      ],
    },
    {
      title: 'تعاریف پایه',
      items: [
        { type: 'large', icon: '👥', code: 'ENT_GROUP', label: 'تعریف\nگروه' },
        { type: 'large', icon: '🏛️', code: 'ENT_PROT_CENTER', label: 'مراکز حفاظتی' },
        { type: 'large', icon: '⏰', code: 'ENT_SHIFT_HOURS', label: 'ساعت شیفت' },
        { type: 'large', icon: '🛡️', code: 'ENT_EQUIPMENT', label: 'تجهیزات\nنگهبانی' },
      ],
    },
  ],

  workflow: [
    {
      title: 'تعاریف',
      items: [
        { type: 'large', icon: '📋', code: 'WF_TYPES', label: 'انواع\nدرخواست' },
        { type: 'large', icon: '✅', code: 'WF_APPROVERS', label: 'تاییدکننده\nدرخواست' },
      ],
    },
    {
      title: 'تفویض و تایید',
      items: [
        { type: 'large', icon: '🔀', code: 'WF_DELEGATE', label: 'تفویض\nاختیار' },
        { type: 'large', icon: '🅿️', code: 'WF_PARKING', label: 'تاییدات پارکینگ\nو خروج مدارک' },
      ],
    },
  ],

  sodor_kart: [
    {
      title: 'کارت پرسنل',
      items: [
        { type: 'large', icon: '🪪', code: 'CARD_PERS_PRINT', label: 'چاپ کارت\nپرسنل' },
        { type: 'large', icon: '📊', code: 'CARD_ISSUED_RPT', label: 'گزارش کارت‌های\nصادر شده' },
      ],
    },
    {
      title: 'کارت پیمانکار',
      items: [
        { type: 'large', icon: '🪪', code: 'CARD_CTR_PRINT', label: 'چاپ کارت\nپیمانکاران' },
      ],
    },
    {
      title: 'کارت خودرو',
      items: [
        { type: 'large', icon: '🚗', code: 'CARD_VEH_PERS', label: 'چاپ کارت خودروی\nپرسنل' },
        { type: 'large', icon: '🚛', code: 'CARD_VEH_CTR', label: 'چاپ کارت خودروی\nپیمانکاران' },
        { type: 'large', icon: '📋', code: 'CARD_VEH_RPT', label: 'گزارش کارت‌های\nخودروی صادر شده' },
      ],
    },
  ],
  gozaresh: [
    {
      title: 'تردد و میهمان',
      items: [
        { type: 'large', icon: '🧑', code: 'RPT_GUEST', label: 'گزارشات\nمیهمان' },
        { type: 'large', icon: '🚶', code: 'RPT_PERS_TR', label: 'تردد پرسنل\nو پیمانکاران' },
        { type: 'large', icon: '🚗', code: 'RPT_VEH_TR', label: 'تردد خودرو\nپرسنل/پیمانکار' },
        { type: 'large', icon: '👤', code: 'RPT_MISC', label: 'تردد افراد\nمتفرقه' },
      ],
    },
    {
      title: 'کالا و خودرو',
      items: [
        { type: 'large', icon: '📦', code: 'RPT_GOODS_IO', label: 'ورود و\nخروج کالا' },
        { type: 'large', icon: '🔧', code: 'RPT_GOODS_REP', label: 'کالای تعمیری\nو خدمات' },
        { type: 'large', icon: '🚛', code: 'RPT_CARGO', label: 'تردد خودرو\nباری' },
        { type: 'large', icon: '🏢', code: 'RPT_CTR_GOODS', label: 'کالای\nپیمانکار' },
      ],
    },
    {
      title: 'پرسنل و انتظامات',
      items: [
        { type: 'large', icon: '👥', code: 'RPT_PERS', label: 'گزارش\nپرسنل' },
        { type: 'large', icon: '👷', code: 'RPT_CTR_PERS', label: 'پرسنل\nپیمانکار' },
        { type: 'large', icon: '📋', code: 'RPT_BOARD', label: 'لوح\nنگهبانی' },
        { type: 'large', icon: '🔁', code: 'RPT_REPLACE', label: 'درخواست\nجایگزینی' },
      ],
    },
    {
      title: 'رزرو و لاگ',
      items: [
        { type: 'large', icon: '📝', code: 'RPT_TR_REQ', label: 'درخواست\nتردد' },
        { type: 'large', icon: '🗓️', code: 'RPT_GUEST_RSV', label: 'رزرو\nمیهمان' },
        { type: 'large', icon: '📜', code: 'RPT_PERS_HIST', label: 'تاریخچه\nپرسنل' },
        { type: 'large', icon: '📥', code: 'RPT_GOODS_RSV', label: 'رزرو\nکالا' },
        { type: 'large', icon: '🧾', code: 'RPT_LOG', label: 'گزارش\nلاگ' },
        { type: 'large', icon: '📊', code: 'RPT_MJZ', label: 'گزارش مجوزهای\nتردد (CSV)' },
      ],
    },
  ],
  modiriat: [
    {
      title: 'پشتیبان‌گیری',
      items: [
        { type: 'large', icon: '', code: 'ADM_BACKUP', label: 'گرفتن نسخه\nپشتیبان' },
        { type: 'large', icon: '', code: 'ADM_RESTORE', label: 'بازیابی نسخه\nپشتیبان' },
      ],
    },
    {
      title: 'کاربران و شرکت',
      items: [
        { type: 'large', icon: '👥', code: 'ADM_USERS', label: 'تعریف\nکاربران' },
        { type: 'large', icon: '🏢', code: 'ADM_USER_CO', label: 'اختصاص\nشرکت به کاربر' },
        {
          type: 'stack',
          buttons: [
            { icon: '🔒', code: 'ADM_ROLES', label: 'تعریف سطح\nدسترسی' },
            { icon: '👁️', code: 'ADM_SCOPE', label: 'فقط پرسنل شرکت خود' },
          ],
        },
      ],
    },
    {
      title: 'امنیت و تنظیمات',
      items: [
        { type: 'large', icon: '⚙️', code: 'ADM_SETTINGS', label: 'تنظیمات\nسیستم' },
        { type: 'large', icon: '📘', code: 'ADM_DOCS', label: 'مستندات\nمعماری' },
        { type: 'large', icon: '🔑', code: 'ADM_ISOLATION', label: 'سیاست\nایزوله‌سازی' },
      ],
    },
  ],
}

const STATUS_COLORS = {
  yellow: 'badge-yellow',
  red: 'badge-red',
  green: 'badge-green',
  blue: 'badge-blue',
}

/** اکشن‌های ریبون — id/code داخلی یکتا؛ در UI فقط label نمایش داده می‌شود */
const BUILTIN_QAT = [
  { id: 'SYS_SAVE', code: 'SYS_SAVE', label: 'ذخیره', icon: '💾', tab: null, kind: 'system' },
  { id: 'SYS_PRINT', code: 'SYS_PRINT', label: 'چاپ', icon: '🖨️', tab: null, kind: 'system' },
  { id: 'SYS_BACK', code: 'SYS_BACK', label: 'بازگشت', icon: '↩️', tab: null, kind: 'system' },
  { id: 'SYS_SEARCH', code: 'SYS_SEARCH', label: 'جستجو سریع', icon: '🔍', tab: null, kind: 'system' },
]

function buildRibbonCatalog() {
  const items = []
  Object.entries(RIBBONS).forEach(([tabId, groups]) => {
    const tabMeta = TABS.find((t) => t.id === tabId)
    const tabLabel = tabMeta?.label || tabId
    ;(groups || []).forEach((group) => {
      ;(group.items || []).forEach((item) => {
        if (item.type === 'large') {
          const flat = String(item.label || '').replace(/\n/g, ' ').trim()
          const code = item.code
          if (!code) return
          items.push({
            id: code,
            code,
            label: flat,
            icon: item.icon,
            tab: tabId,
            tabLabel,
            group: group.title,
            kind: 'ribbon',
          })
        } else if (item.type === 'stack') {
          ;(item.buttons || []).forEach((btn) => {
            const flat = String(btn.label || '').replace(/\n/g, ' ').trim()
            const code = btn.code
            if (!code) return
            items.push({
              id: code,
              code,
              label: flat,
              icon: btn.icon,
              tab: tabId,
              tabLabel,
              group: group.title,
              kind: 'ribbon',
            })
          })
        }
      })
    })
  })
  return items
}

const RIBBON_CATALOG = buildRibbonCatalog()
const QAT_CATALOG = [...BUILTIN_QAT, ...RIBBON_CATALOG]
const ACTION_BY_CODE = Object.fromEntries(
  QAT_CATALOG.map((a) => [a.code || a.id, a])
)
const QAT_STORAGE_KEY = 'dejban_qat_codes_v2'
const DEFAULT_QAT_IDS = BUILTIN_QAT.map((x) => x.code)

function loadQatIds() {
  try {
    const raw = localStorage.getItem(QAT_STORAGE_KEY)
    if (!raw) return [...DEFAULT_QAT_IDS]
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed) || parsed.length === 0) return [...DEFAULT_QAT_IDS]
    return parsed.filter((id) => Boolean(ACTION_BY_CODE[id]))
  } catch {
    return [...DEFAULT_QAT_IDS]
  }
}


/** حروف مجاز پلاک ملی ایران */
const IRAN_PLATE_LETTERS = [
  'الف', 'ب', 'پ', 'ت', 'ث', 'ج', 'د', 'ز', 'س', 'ش', 'ص', 'ط',
  'ع', 'ف', 'ق', 'ک', 'گ', 'ل', 'م', 'ن', 'و', 'ه', 'ی',
]

/** فقط رقم (لاتین یا فارسی) نگه می‌دارد */
function onlyPlateDigits(s, maxLen) {
  return String(s || '')
    .replace(/[^0-9۰-۹٠-٩]/g, '')
    .slice(0, maxLen)
}

/** پارس پلاک ذخیره‌شده «۱۲ ب ۳۴۵ - ۱۱» — برای مقدار ناقص هم بخش‌ها را حفظ می‌کند */
function parseIranPlate(value) {
  const s = String(value || '').trim()
  if (!s) return { a: '', letter: 'ب', b: '', c: '' }
  // کامل
  let m = s.match(/^([۰-۹0-9]{1,2})\s+(\S{1,3})\s+([۰-۹0-9]{0,3})\s*-\s*([۰-۹0-9]{0,2})$/)
  if (m) return { a: m[1], letter: m[2], b: m[3] || '', c: m[4] || '' }
  // بدون فاصله‌های استاندارد
  m = s.match(/^([۰-۹0-9]{1,2})\s*(\S{1,3})\s*([۰-۹0-9]{0,3})\s*-?\s*([۰-۹0-9]{0,2})$/)
  if (m) return { a: m[1], letter: m[2], b: m[3] || '', c: m[4] || '' }
  return { a: '', letter: 'ب', b: '', c: '' }
}

function joinIranPlate(parts) {
  const a = onlyPlateDigits(parts.a, 2)
  const b = onlyPlateDigits(parts.b, 3)
  const c = onlyPlateDigits(parts.c, 2)
  const letter = parts.letter || 'ب'
  if (!a && !b && !c) return ''
  // همیشه با ساختار ثابت تا parse دوباره کار کند
  return `${a} ${letter} ${b} - ${c}`
}

/** SVG کوچک پرچم/بخش ایران روی پلاک */
function IranPlateBadge() {
  return (
    <svg width="36" height="40" viewBox="0 0 36 40" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0, display: 'block' }}>
      <rect x="0" y="0" width="36" height="40" rx="2" fill="#1a365d" />
      <text x="18" y="14" textAnchor="middle" fill="#fff" fontSize="7" fontFamily="Tahoma,sans-serif" fontWeight="bold">I.R.</text>
      <text x="18" y="24" textAnchor="middle" fill="#fff" fontSize="7" fontFamily="Tahoma,sans-serif" fontWeight="bold">IRAN</text>
      <rect x="6" y="28" width="24" height="3" fill="#c53030" />
      <rect x="6" y="32" width="24" height="3" fill="#fff" />
      <rect x="6" y="36" width="24" height="2" fill="#276749" />
    </svg>
  )
}

/** ورودی ترکیبی پلاک ایران — ظاهر: ۱۲ - ب - ۳۴۵ - [I.R.IRAN] - ۱۱ */
function IranPlateInput({ value, onChange, required }) {
  const [parts, setParts] = useState(() => parseIranPlate(value))
  const lastValue = useRef(value)

  useEffect(() => {
    if (value !== lastValue.current) {
      lastValue.current = value
      setParts(parseIranPlate(value))
    }
  }, [value])

  const setPart = (key, val) => {
    setParts((prev) => {
      const next = { ...prev, [key]: val }
      const joined = joinIranPlate(next)
      lastValue.current = joined
      if (typeof onChange === 'function') onChange(joined)
      return next
    })
  }

  const box = {
    width: 44, height: 38, textAlign: 'center', fontSize: 16, fontWeight: 700,
    border: '1.5px solid #a0aec0', borderRadius: 6, fontFamily: 'Tahoma, Vazirmatn, sans-serif',
    background: '#fff', color: '#1a202c', boxSizing: 'border-box', outline: 'none',
  }
  const letterBox = { ...box, width: 56, fontSize: 14, cursor: 'pointer' }

  return (
    <div
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5, direction: 'ltr',
        padding: '5px 8px', background: '#fff', border: '1.5px solid #90cdf4',
        borderRadius: 8, boxShadow: '0 1px 2px rgba(43,108,176,0.08)',
      }}
      title="فرمت پلاک ملی ایران — ۱۲ ب ۳۴۵ - ۱۱"
      onMouseDown={(e) => e.stopPropagation()}
    >
      <input
        type="text"
        inputMode="numeric"
        autoComplete="off"
        maxLength={2}
        placeholder="۱۲"
        required={!!required}
        value={parts.a}
        onChange={(e) => setPart('a', onlyPlateDigits(e.target.value, 2))}
        style={box}
      />
      <span style={{ fontWeight: 600, color: '#718096', fontSize: 14 }}>–</span>
      <select
        value={parts.letter || 'ب'}
        onChange={(e) => setPart('letter', e.target.value)}
        style={letterBox}
      >
        {IRAN_PLATE_LETTERS.map((L) => (
          <option key={L} value={L}>{L}</option>
        ))}
      </select>
      <span style={{ fontWeight: 600, color: '#718096', fontSize: 14 }}>–</span>
      <input
        type="text"
        inputMode="numeric"
        autoComplete="off"
        maxLength={3}
        placeholder="۳۴۵"
        value={parts.b}
        onChange={(e) => setPart('b', onlyPlateDigits(e.target.value, 3))}
        style={{ ...box, width: 56 }}
      />
      <span style={{ fontWeight: 600, color: '#718096', fontSize: 14 }}>–</span>
      <IranPlateBadge />
      <span style={{ fontWeight: 600, color: '#718096', fontSize: 14 }}>–</span>
      <input
        type="text"
        inputMode="numeric"
        autoComplete="off"
        maxLength={2}
        placeholder="۱۱"
        value={parts.c}
        onChange={(e) => setPart('c', onlyPlateDigits(e.target.value, 2))}
        style={box}
      />
    </div>
  )
}



/** فقط ارقام تاریخ/ساعت (فارسی یا لاتین) */
function onlyDigitsLimited(val, maxLen) {
  const s = String(val || '').replace(/[۰-۹]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/\D/g, '')
  return s.slice(0, maxLen)
}

function parseJalaliDate(value) {
  const s = String(value || '').trim().replace(/[۰-۹]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
  const m = s.match(/(\d{2,4})\D+(\d{1,2})\D+(\d{1,2})/)
  if (m) return { y: m[1], m: m[2].padStart(2, '0'), d: m[3].padStart(2, '0') }
  if (/^\d{8}$/.test(s)) return { y: s.slice(0, 4), m: s.slice(4, 6), d: s.slice(6, 8) }
  return { y: '', m: '', d: '' }
}

function joinJalaliDate(parts) {
  const y = onlyDigitsLimited(parts.y, 4)
  const m = onlyDigitsLimited(parts.m, 2)
  const d = onlyDigitsLimited(parts.d, 2)
  if (!y && !m && !d) return ''
  return `${y}/${m.padStart(2, '0')}/${d.padStart(2, '0')}`
}

/** ورودی تاریخ جلالی: ۱۴۰۵ / ۰۷ / ۲۰ — با انتقال خودکار فوکوس */
function JalaliDateInput({ value, onChange, required }) {
  const [parts, setParts] = useState(() => parseJalaliDate(value))
  const last = useRef(value)
  const yRef = useRef(null)
  const mRef = useRef(null)
  const dRef = useRef(null)
  useEffect(() => {
    if (value !== last.current) {
      last.current = value
      setParts(parseJalaliDate(value))
    }
  }, [value])
  const emit = (next) => {
    const joined = joinJalaliDate(next)
    last.current = joined
    if (typeof onChange === 'function') onChange(joined)
  }
  const setPart = (key, val, maxLen, nextRef) => {
    const digits = onlyDigitsLimited(val, maxLen)
    setParts((prev) => {
      const next = { ...prev, [key]: digits }
      emit(next)
      return next
    })
    if (digits.length >= maxLen && nextRef && nextRef.current) {
      nextRef.current.focus()
      nextRef.current.select()
    }
  }
  const onKeyDown = (e, prevRef, nextRef) => {
    if (e.key === 'ArrowLeft' && nextRef?.current) { e.preventDefault(); nextRef.current.focus() }
    if (e.key === 'ArrowRight' && prevRef?.current) { e.preventDefault(); prevRef.current.focus() }
    if (e.key === '/' || e.key === '-' || e.key === '.') {
      e.preventDefault()
      if (nextRef?.current) nextRef.current.focus()
    }
  }
  const box = {
    width: 28, height: 28, textAlign: 'center', fontSize: 12, fontWeight: 600,
    border: '1px solid #a0aec0', borderRadius: 4, fontFamily: 'Tahoma, Vazirmatn, sans-serif',
    background: '#fff', boxSizing: 'border-box', outline: 'none', padding: 0,
  }
  return (
    <div
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 2, direction: 'ltr',
        padding: '2px 4px', background: '#fff', border: '1px solid #9ae6b4',
        borderRadius: 6, flexWrap: 'nowrap', whiteSpace: 'nowrap',
        boxSizing: 'border-box', width: 'fit-content', maxWidth: '100%',
      }}
      title="تاریخ جلالی — سال / ماه / روز"
      onMouseDown={(e) => e.stopPropagation()}
    >
      <input ref={yRef} type="text" inputMode="numeric" maxLength={4} placeholder="1405" required={!!required}
        value={parts.y} onChange={(e) => setPart('y', e.target.value, 4, mRef)}
        onKeyDown={(e) => onKeyDown(e, null, mRef)}
        style={{ ...box, width: 40 }} />
      <span style={{ color: '#718096', fontWeight: 700, fontSize: 11 }}>/</span>
      <input ref={mRef} type="text" inputMode="numeric" maxLength={2} placeholder="07"
        value={parts.m} onChange={(e) => setPart('m', e.target.value, 2, dRef)}
        onKeyDown={(e) => onKeyDown(e, yRef, dRef)}
        style={box} />
      <span style={{ color: '#718096', fontWeight: 700, fontSize: 11 }}>/</span>
      <input ref={dRef} type="text" inputMode="numeric" maxLength={2} placeholder="20"
        value={parts.d} onChange={(e) => setPart('d', e.target.value, 2, null)}
        onKeyDown={(e) => onKeyDown(e, mRef, null)}
        style={box} />
    </div>
  )
}

function parseJalaliTime(value) {
  const s = String(value || '').trim().replace(/[۰-۹]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
  const m = s.match(/(\d{1,2})\D+(\d{1,2})/)
  if (m) return { h: m[1].padStart(2, '0'), mi: m[2].padStart(2, '0') }
  return { h: '', mi: '' }
}

function joinJalaliTime(parts) {
  const h = onlyDigitsLimited(parts.h, 2)
  const mi = onlyDigitsLimited(parts.mi, 2)
  if (!h && !mi) return ''
  return `${h.padStart(2, '0')}:${mi.padStart(2, '0')}`
}

/** ورودی ساعت: ۰۸ : ۳۰ — با انتقال خودکار فوکوس */
function JalaliTimeInput({ value, onChange, required }) {
  const [parts, setParts] = useState(() => parseJalaliTime(value))
  const last = useRef(value)
  const hRef = useRef(null)
  const miRef = useRef(null)
  useEffect(() => {
    if (value !== last.current) {
      last.current = value
      setParts(parseJalaliTime(value))
    }
  }, [value])
  const emit = (next) => {
    const joined = joinJalaliTime(next)
    last.current = joined
    if (typeof onChange === 'function') onChange(joined)
  }
  const setPart = (key, val, maxLen, nextRef) => {
    const digits = onlyDigitsLimited(val, maxLen)
    setParts((prev) => {
      const next = { ...prev, [key]: digits }
      emit(next)
      return next
    })
    if (digits.length >= maxLen && nextRef && nextRef.current) {
      nextRef.current.focus()
      nextRef.current.select()
    }
  }
  const box = {
    width: 28, height: 28, textAlign: 'center', fontSize: 12, fontWeight: 600,
    border: '1px solid #a0aec0', borderRadius: 4, fontFamily: 'Tahoma, Vazirmatn, sans-serif',
    background: '#fff', boxSizing: 'border-box', outline: 'none', padding: 0,
  }
  return (
    <div
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 2, direction: 'ltr',
        padding: '2px 4px', background: '#fff', border: '1px solid #90cdf4',
        borderRadius: 6, flexWrap: 'nowrap', whiteSpace: 'nowrap',
        boxSizing: 'border-box', width: 'fit-content',
      }}
      title="ساعت — ساعت : دقیقه"
      onMouseDown={(e) => e.stopPropagation()}
    >
      <input ref={hRef} type="text" inputMode="numeric" maxLength={2} placeholder="08" required={!!required}
        value={parts.h} onChange={(e) => setPart('h', e.target.value, 2, miRef)}
        style={box} />
      <span style={{ color: '#718096', fontWeight: 700, fontSize: 11 }}>:</span>
      <input ref={miRef} type="text" inputMode="numeric" maxLength={2} placeholder="30"
        value={parts.mi} onChange={(e) => setPart('mi', e.target.value, 2, null)}
        style={box} />
    </div>
  )
}

function isDateFieldKey(key, type, label) {
  // نوع صریح متنی/انتخابی نباید تاریخ شود
  if (type === 'text' || type === 'select' || type === 'bool' || type === 'iran_plate' || type === 'time' || type === 'jalali_time') return false
  if (type === 'date' || type === 'jalali_date') return true
  const k = String(key || '').toLowerCase()
  const lb = String(label || '')
  // نام مدیرعامل و فیلدهای نام نباید تاریخ شوند
  if (k.includes('name') || k.includes('ceo') || k.includes('mobile') || k.includes('phone') || k.includes('national')) {
    if (!k.includes('date') && !lb.includes('تاریخ')) return false
  }
  // اگر برچسب فارسی با «تاریخ» شروع شود یا شامل «تاریخ » باشد
  if ((lb.startsWith('تاریخ') || lb.includes('تاریخ ')) && !lb.includes('ساعت') && !k.includes('time')) return true
  if (lb.includes('تاریخ') && !lb.includes('ساعت') && (k.includes('date') || k.includes('valid') || k.endsWith('_at'))) return true
  if (k.includes('time') && !k.includes('date')) return false
  return /(^|_)(date|valid_from|valid_to|from_date|to_date|issue_date|weigh_date|register_date|traffic_date|entry_date|exit_date|birth_date|start_date|end_date|validity_start|validity_end|expiry|travel_from|travel_to|process_date)(_|$)/.test(k)
    || k.endsWith('_date') || k === 'date' || k === 'valid_from' || k === 'valid_to'
    || k.includes('birth_date') || k.includes('validity_')
    || k === 'travel_from' || k === 'travel_to'
}

function isTimeFieldKey(key, type) {
  if (type === 'time' || type === 'jalali_time') return true
  const k = String(key || '').toLowerCase()
  return /(^|_)(time|entry_time|exit_time|traffic_time|process_time|time_from|time_to)(_|$)/.test(k)
    || k.endsWith('_time') || k === 'time'
}

/** تبدیل ارقام لاتین به فارسی برای نمایش */
function toPersianDigits(val) {
  if (val == null || val === '') return ''
  return String(val).replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[Number(d)])
}


/** پارس ساده CSV با پشتیبانی ویرگول داخل کوتیشن و BOM */
function parseCsvText(text) {
  let s = String(text || '').replace(/^\uFEFF/, '')
  const rows = []
  let row = []
  let cur = ''
  let inQ = false
  for (let i = 0; i < s.length; i++) {
    const ch = s[i]
    if (inQ) {
      if (ch === '"') {
        if (s[i + 1] === '"') { cur += '"'; i++ }
        else inQ = false
      } else cur += ch
    } else {
      if (ch === '"') inQ = true
      else if (ch === ',') { row.push(cur); cur = '' }
      else if (ch === '\n') { row.push(cur); rows.push(row); row = []; cur = '' }
      else if (ch === '\r') { /* skip */ }
      else cur += ch
    }
  }
  if (cur.length || row.length) { row.push(cur); rows.push(row) }
  if (!rows.length) return []
  const headers = rows[0].map((h) => String(h || '').trim())
  const out = []
  for (let r = 1; r < rows.length; r++) {
    const cells = rows[r]
    if (!cells || cells.every((c) => !String(c || '').trim())) continue
    const obj = {}
    headers.forEach((h, i) => { obj[h] = cells[i] != null ? String(cells[i]).trim() : '' })
    out.push(obj)
  }
  return out
}

function downloadUrl(url, filename) {
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'template.csv'
  document.body.appendChild(a)
  a.click()
  a.remove()
}


/** اجرای کار سنگین بعد از رنگ‌آمیزی UI تا تعویض برگه فوری حس شود */
function scheduleAfterPaint(fn) {
  let cancelled = false
  const rid = requestAnimationFrame(() => {
    const t = setTimeout(() => {
      if (!cancelled) {
        try { fn() } catch (e) { console.warn(e) }
      }
    }, 0)
    scheduleAfterPaint._timers = scheduleAfterPaint._timers || new Set()
    scheduleAfterPaint._timers.add(t)
  })
  return () => {
    cancelled = true
    try { cancelAnimationFrame(rid) } catch (_) {}
  }
}

function App() {
  const [activeTab, setActiveTab] = useState('herasat')
  // برگه ترددهای خاص حذف شده — هدایت به صدور مجوز تردد
  useEffect(() => {
    if (activeTab === 'taraddod') setActiveTab('mojaz')
  }, [activeTab])
  const [qatIds, setQatIds] = useState(() => loadQatIds())
  const [showQatCustomize, setShowQatCustomize] = useState(false)
  const [qatMenu, setQatMenu] = useState(null) // { x, y, action }
  const [qatFilter, setQatFilter] = useState('')
  const [stats, setStats] = useState({
    violations_today: 0,
    open_incidents: 0,
    inspections_done: 0,
    guest_visits: 0,
  })
  const [violations, setViolations] = useState([])
  const [apiStatus, setApiStatus] = useState('offline')
  const [personnel, setPersonnel] = useState([])
  const [personnelTotal, setPersonnelTotal] = useState(0)
  const [personnelScopeNote, setPersonnelScopeNote] = useState('')
  const PAGE_SIZE_OPTIONS = [10, 50, 100, 250, 500, 'all']
  const [personnelPageSize, setPersonnelPageSize] = useState(50)
  const [personnelPage, setPersonnelPage] = useState(1)
  const [personnelLoading, setPersonnelLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [showRegisterForm, setShowRegisterForm] = useState(false)
  const [formData, setFormData] = useState({
    indicator_num: '', first_name: '', last_name: '', previous_last_name: '',
    nickname: '', nickname_family: '',
    father_name: '', national_id: '', id_cert_number: '', id_cert_place: '',
    gender: '', birth_date: '', birth_place: '', religion: '', denomination: '',
    blood_type: '', nationality: '', marital_status: '', children_count: '',
    is_native: 'خیر',
    company_code: '', center: '', department: '', position: '', workplace: '',
    room_floor: '', rank: '', membership_type: '', responsibility_group: '', hire_date: '',
    employment_type: '', education_degree: '', education_field: '',
    military_status: '', military_exemption_type: '', is_retired: 'خیر', active_status: 'فعال',
    phone: '', landline: '', internal_phone1: '', internal_phone2: '', internal_phone3: '',
    email: '', postal_code: '', address: '', issued_from: '',
    card_number: '', card_status: '', time_card_code: '',
    validity_start: '', validity_end: '', card_return_date: '', return_code: '',
    license_type: '', license_number: '', license_issue_place: '',
    access_group: '', online_display_name: '', print_count: '',
    banned_entry: 'خیر', banned_security: 'خیر', settlement_done: 'خیر',
    show_on_internet: 'خیر', description: '', photo: '', signature: '',
  })
  const [formMsg, setFormMsg] = useState('')
  const [companies, setCompanies] = useState([])
  const [ctrCompanies, setCtrCompanies] = useState([])
  const [showCompanyForm, setShowCompanyForm] = useState(false)
  /** list | form | units — زیرمنوی شرکت‌های تابعه */
  const [companySubView, setCompanySubView] = useState('list')
  /** تخصیص شرکت/مرکز/واحد به پرسنل */
  const [showAssignOrg, setShowAssignOrg] = useState(false)
  const [assignOrgForm, setAssignOrgForm] = useState({ company_code: '', center: '', department: '' })
  const [assignOrgMsg, setAssignOrgMsg] = useState('')
  const [editingCompanyCode, setEditingCompanyCode] = useState(null)
  const [baseClientCompanies, setBaseClientCompanies] = useState([])
  const [companyForm, setCompanyForm] = useState({
    name: '',
    short_name: '',
    description: '',
  })
  const [companyMsg, setCompanyMsg] = useState('')
  const [companySearch, setCompanySearch] = useState('')
  const [companyStatusFilter, setCompanyStatusFilter] = useState('all') // all | active | inactive
  const [currentUser, setCurrentUser] = useState({
    role: 'admin',
    username: 'admin',
    can_see_all_companies: true,
  })
  const isAdmin = currentUser?.role === 'admin'
  /** ورود سیستم — AdminUser / AdminUser */
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    try { return sessionStorage.getItem('dejban_auth') === '1' } catch { return false }
  })
  // بازیابی کاربر و مجوزها بعد از رفرش

  /* سایدبار با تعویض برگه جمع نمی‌شود تا UI کند نشود */

  useEffect(() => {
    if (!isLoggedIn) return
    try {
      const raw = sessionStorage.getItem('dejban_user')
      if (raw) {
        const user = JSON.parse(raw)
        if (user && user.username) {
          setCurrentUser({
            role: user.role || 'user',
            username: user.username,
            full_name: user.full_name || user.username,
            can_see_all_companies: !!user.can_see_all_companies,
            company_code: user.company_code,
            access_level_id: user.access_level_id,
          })
          if (user.username === 'AdminUser') {
            applyPermissions({ is_full_admin: true, tabs: [], actions: [] })
          } else {
            fetch(`/api/auth/permissions?username=${encodeURIComponent(user.username)}`)
              .then((r) => r.json())
              .then((perms) => applyPermissions(perms))
              .catch(() => {})
          }
        }
      }
    } catch {}
  }, [])
  const [loginUser, setLoginUser] = useState('')
  const [loginPass, setLoginPass] = useState('')
  const [loginError, setLoginError] = useState('')
  const [showUserMenu, setShowUserMenu] = useState(false)
  /** مجوزهای سطح دسترسی کاربر جاری */
  const [userPerms, setUserPerms] = useState(() => {
    try {
      const raw = sessionStorage.getItem('dejban_perms')
      if (raw) return JSON.parse(raw)
    } catch {}
    return { is_full_admin: true, tabs: [], actions: [] }
  })
  const [cardPrintPerson, setCardPrintPerson] = useState(null)
  const [cardPrintSide, setCardPrintSide] = useState('both') // front | back | both
  const [cardPrintSizeId, setCardPrintSizeId] = useState('CR80')
  const cardPrintSize = PVC_CARD_SIZES.find((s) => s.id === cardPrintSizeId) || PVC_CARD_SIZES[0]

  const [cardPrintLoading, setCardPrintLoading] = useState(false)
  const [editingId, setEditingId] = useState(null)
  /** پرسنل انتخاب‌شده در لیست (برای عملیات ریبون تک‌نفره: ویرایش، مدارک، کارت و ...) */
  const [selectedPersonnel, setSelectedPersonnel] = useState(null)
  /** انتخاب گروهی با چک‌باکس (برای تخصیص شرکت / مرکز / واحد) */
  const [selectedPersonnelList, setSelectedPersonnelList] = useState([])
  const [showPhotoModal, setShowPhotoModal] = useState(false)
  const [photoModalMsg, setPhotoModalMsg] = useState('')
  const [photoModalBusy, setPhotoModalBusy] = useState(false)
  const [photoPreview, setPhotoPreview] = useState('')
  const [docsPhotoCandidates, setDocsPhotoCandidates] = useState([])
  const photoFileRef = useRef(null)
  // پیوست فایل — دو حالت: انتقال فولدر / انتقال فایل‌ها
  const [showAttachModal, setShowAttachModal] = useState(false)
  const [attachMode, setAttachMode] = useState(null) // 'folder' | 'files' | null
  const [attachMsg, setAttachMsg] = useState('')
  const [attachBusy, setAttachBusy] = useState(false)
  const [attachDestPath, setAttachDestPath] = useState('')
  const [attachDestSearch, setAttachDestSearch] = useState('')
  const [attachDestItems, setAttachDestItems] = useState([])
  const [attachDestLoading, setAttachDestLoading] = useState(false)
  const [attachDestRoot, setAttachDestRoot] = useState('')
  const [attachPersonFolder, setAttachPersonFolder] = useState('')
  const [attachSourceInfo, setAttachSourceInfo] = useState('')
  const attachFolderRef = useRef(null)
  const attachFilesRef = useRef(null)
  const [columnFilters, setColumnFilters] = useState({
    indicator_num: '', first_name: '', last_name: '', national_id: '', company: '',
    department: '', position: '', active_status: '',
  })
  // تنظیمات مسیر ریشه مدارک پرسنل
  const [showSettings, setShowSettings] = useState(false)
  const [showArchDocs, setShowArchDocs] = useState(false)
  const [docsRootInput, setDocsRootInput] = useState('')
  const [settingsMsg, setSettingsMsg] = useState('')
  const [settingsSaving, setSettingsSaving] = useState(false)
  // مرورگر آرشیو پرسنل (ریشه / شرکت / کدملی)
  const [showArchive, setShowArchive] = useState(false)
  const [archivePath, setArchivePath] = useState('')
  const [archiveItems, setArchiveItems] = useState([])
  const [archiveRoot, setArchiveRoot] = useState('')
  const [archiveLoading, setArchiveLoading] = useState(false)
  const [archiveError, setArchiveError] = useState('')
  const [archiveSearch, setArchiveSearch] = useState('')
  const [archiveMsg, setArchiveMsg] = useState('')

  const [archiveBusy, setArchiveBusy] = useState(false)
  // —— اطلاعات پایه ——
  const [baseSubView, setBaseSubView] = useState('edu') // edu | resp | emp
  const [entezamatSubView, setEntezamatSubView] = useState('guard_board')
  const [cardSubView, setCardSubView] = useState('personnel_card')
  const [peymankarSubView, setPeymankarSubView] = useState('companies')
  const [pymReportKind, setPymReportKind] = useState('summary')
  const [pymReportQ, setPymReportQ] = useState('')
  const [pymReportCompany, setPymReportCompany] = useState('')
  const [pymReportData, setPymReportData] = useState(null)
  const [pymReportLoading, setPymReportLoading] = useState(false)
  const [pymReportMsg, setPymReportMsg] = useState('')
  const [mojazSubView, setMojazSubView] = useState('list')
  const [mjzList, setMjzList] = useState([])
  const [mjzLoading, setMjzLoading] = useState(false)
  const [mjzMsg, setMjzMsg] = useState('')
  const [mjzForm, setMjzForm] = useState({
    permit_type: 'person', holder_name: '', national_id: '', personnel_code: '',
    company_name: '', unit_name: '', vehicle_plate: '', vehicle_type: '', driver_name: '',
    goods_desc: '', goods_count: '', purpose: '', destination: '', gate_name: '',
    valid_from: '', valid_to: '',
    allowed_entry_date: '', allowed_entry_time: '', allowed_exit_date: '', allowed_exit_time: '',
    notes: '', issued_by: '',
  })
  const [mjzSearchNo, setMjzSearchNo] = useState('')
  const [mjzViewItem, setMjzViewItem] = useState(null)
  const [sidebarPinned, setSidebarPinned] = useState(false)
  const [mjzGuardName, setMjzGuardName] = useState('')

  const [patrolSubView, setPatrolSubView] = useState('devices')
  const [herasatSubView, setHerasatSubView] = useState('eval_options')
  const [monagheseSubView, setMonagheseSubView] = useState('companies')
  const [kartablSubView, setKartablSubView] = useState('outgoing')
  const [baskoolSubView, setBaskoolSubView] = useState('weighings')
  const [pelakhwanSubView, setPelakhwanSubView] = useState('process')
  const [accessSubView, setAccessSubView] = useState('traffic')
  const [workflowSubView, setWorkflowSubView] = useState('request_types')
  const [backupMsg, setBackupMsg] = useState('')
  const [backupList, setBackupList] = useState([])
  // —— سطوح دسترسی و کاربران سیستم ——
  const [accessLevels, setAccessLevels] = useState([])
  const [accessLevelMsg, setAccessLevelMsg] = useState('')
  const [editingLevelId, setEditingLevelId] = useState(null)
  const [levelForm, setLevelForm] = useState({
    name: '', description: '', is_full_admin: false, is_active: true, tabs: [], actions: [],
  })
  const [showLevelForm, setShowLevelForm] = useState(false)
  const [sysUsers, setSysUsers] = useState([])
  const [sysUserMsg, setSysUserMsg] = useState('')
  const [editingUserId, setEditingUserId] = useState(null)
  const [userForm, setUserForm] = useState({
    username: '', password: '', full_name: '', access_level_id: '', company_code: '100',
    is_active: true, can_see_all_companies: false,
  })
  const [showUserForm, setShowUserForm] = useState(false)
  const [reportKey, setReportKey] = useState('personnel')
  const [reportData, setReportData] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [shiftHoursList, setShiftHoursList] = useState([])
  const [workShiftsList, setWorkShiftsList] = useState([])
  const [units, setUnits] = useState([])
  const [unitForm, setUnitForm] = useState({ code: '', name: '', parent_name: '', center_name: '', company_code: '', show_on_guard_board: true, show_on_internet: false, image_path: '', symbol_path: '' })
  const [editingUnitId, setEditingUnitId] = useState(null)
  const [unitMsg, setUnitMsg] = useState('')
  const [eduFields, setEduFields] = useState([])
  const [eduName, setEduName] = useState('')
  const [respGroups, setRespGroups] = useState([])
  const [respName, setRespName] = useState('')
  const [empTypes, setEmpTypes] = useState([])
  const [empName, setEmpName] = useState('')
  const [namedMsg, setNamedMsg] = useState('')
  // جداول پایه عمومی (درب، مقصد کالا، ...)
  const [lookupItems, setLookupItems] = useState([])
  const [lookupName, setLookupName] = useState('')
  const [lookupDesc, setLookupDesc] = useState('')
  const [lookupMsg, setLookupMsg] = useState('')
  const [entityForm, setEntityForm] = useState({})
  /** شناسه رکورد در حال ویرایش برای فرم‌های entity (پیمانکاران و …) */
  const [editingEntityId, setEditingEntityId] = useState(null)
  // —— وابستگان ——
  const [showDependents, setShowDependents] = useState(false)
  const [dependents, setDependents] = useState([])
  const [depForm, setDepForm] = useState({ first_name: '', last_name: '', national_id: '', relation: '', birth_date: '', gender: '', phone: '', description: '' })
  const [editingDepId, setEditingDepId] = useState(null)
  const [depMsg, setDepMsg] = useState('')
  const [personnelRecordKind, setPersonnelRecordKind] = useState(null)
  const [personnelRecords, setPersonnelRecords] = useState([])
  const [recForm, setRecForm] = useState({})
  const [editingRecId, setEditingRecId] = useState(null)
  const [recMsg, setRecMsg] = useState('')
  // —— کارت شناسایی ——
  const [showCards, setShowCards] = useState(false)
  const [cards, setCards] = useState([])
  const [cardForm, setCardForm] = useState({ card_number: '', card_type: 'شناسایی', issue_date: '', expiry_date: '', status: 'فعال', printed: false, description: '' })
  const [editingCardId, setEditingCardId] = useState(null)
  const [cardMsg, setCardMsg] = useState('')

  const archiveFileRef = useRef(null)
  const filteredPersonnel = useMemo(() => {
    const entries = Object.entries(columnFilters).filter(([, value]) => normSearchText(value))
    if (!entries.length) return personnel
    return personnel.filter((p) =>
      entries.every(([key, value]) => normSearchText(p[key]).includes(normSearchText(value)))
    )
  }, [personnel, columnFilters])
  const emptyForm = {
    indicator_num: '', first_name: '', last_name: '', previous_last_name: '',
    nickname: '', nickname_family: '',
    father_name: '', national_id: '', id_cert_number: '', id_cert_place: '',
    gender: '', birth_date: '', birth_place: '', religion: '', denomination: '',
    blood_type: '', nationality: '', marital_status: '', children_count: '',
    is_native: 'خیر',
    company_code: '', center: '', department: '', position: '', workplace: '',
    room_floor: '', rank: '', membership_type: '', responsibility_group: '', hire_date: '',
    employment_type: '', education_degree: '', education_field: '',
    military_status: '', military_exemption_type: '', is_retired: 'خیر', active_status: 'فعال',
    phone: '', landline: '', internal_phone1: '', internal_phone2: '', internal_phone3: '',
    email: '', postal_code: '', address: '', issued_from: '',
    card_number: '', card_status: '', time_card_code: '',
    validity_start: '', validity_end: '', card_return_date: '', return_code: '',
    license_type: '', license_number: '', license_issue_place: '',
    access_group: '', online_display_name: '', print_count: '',
    banned_entry: 'خیر', banned_security: 'خیر', settlement_done: 'خیر',
    show_on_internet: 'خیر', description: '', photo: '', signature: '',
  }

  const loadSettings = () => {
    fetch('/api/settings')
      .then((r) => r.json())
      .then((data) => {
        setDocsRootInput(data.personnel_docs_root || '')
      })
      .catch(() => setDocsRootInput(''))
  }

  const saveSettings = (e) => {
    e?.preventDefault?.()
    setSettingsMsg('')
    setSettingsSaving(true)
    fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ personnel_docs_root: docsRootInput }),
    })
      .then(async (r) => {
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || 'خطا در ذخیره تنظیمات')
        return data
      })
      .then((data) => {
        setDocsRootInput(data.personnel_docs_root || docsRootInput)
        setSettingsMsg(data.message || 'ذخیره شد')
        setTimeout(() => setSettingsMsg(''), 2500)
      })
      .catch((err) => setSettingsMsg(err.message || 'خطا'))
      .finally(() => setSettingsSaving(false))
  }

  /** نرمال‌سازی جستجو برای فارسی/عربی: ی/ک، ارقام، نیم‌فاصله */
  function normSearchText(text) {
    if (text == null || text === '') return ''
    let t = String(text).trim()
    const digitMap = {
      '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
      '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
      '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
      '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    }
    t = t.replace(/[۰-۹٠-٩]/g, (ch) => digitMap[ch] || ch)
    t = t
      .replace(/ي/g, 'ی')
      .replace(/ك/g, 'ک')
      .replace(/ة/g, 'ه')
      .replace(/[أإآ]/g, 'ا')
      .replace(/[\u200c\u200d\u0640]/g, '')
    try {
      t = t.toLocaleLowerCase('fa')
    } catch {
      t = t.toLowerCase()
    }
    return t
  }

  const loadArchive = (relPath = '', searchQ) => {
    setArchiveLoading(true)
    setArchiveError('')
    const qVal = searchQ !== undefined ? searchQ : archiveSearch
    const params = new URLSearchParams()
    if (relPath) params.set('path', relPath)
    if (qVal && String(qVal).trim()) params.set('q', String(qVal).trim())
    const qs = params.toString() ? `?${params.toString()}` : ''
    fetch(`/api/docs/list${qs}`)
      .then(async (r) => {
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || 'خطا در خواندن آرشیو')
        return data
      })
      .then((data) => {
        setArchivePath(data.path || '')
        setArchiveItems(Array.isArray(data.items) ? data.items : [])
        setArchiveRoot(data.docs_root || '')
      })
      .catch((err) => {
        setArchiveItems([])
        setArchiveError(err.message || 'خطا')
      })
      .finally(() => setArchiveLoading(false))
  }

  const openArchive = (relPath = '') => {
    setShowArchive(true)
    setArchiveSearch('')
    setArchiveMsg('')
    setArchivePath(relPath || '')
    loadArchive(relPath || '', '')
  }

  /** باز کردن فولدر مدارک پرسنل انتخاب‌شده در آرشیو */
  const openPersonnelDocs = async (p) => {
    const person = p || selectedPersonnel
    if (!person) {
      window.alert('ابتدا یک پرسنل را از لیست انتخاب کنید.')
      return
    }
    setSelectedPersonnel(person)
    setArchiveBusy(true)
    setArchiveMsg('')
    try {
      const code = person.company_code || ''
      const res = await fetch(
        `/api/personnel/${person.id}/docs-folder?company_code=${encodeURIComponent(code)}`
      )
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'خطا در باز کردن فولدر مدارک')
      const rel = data.relative_path || ''
      setShowArchive(true)
      setArchiveSearch('')
      setArchivePath(rel)
      setArchiveMsg(
        `مدارک: ${data.full_name || ''} — کدملی ${data.national_id || '—'}` +
          (data.count === 0 ? ' (فولدر خالی است)' : ` (${data.count} مورد)`)
      )
      // اگر API لیست را داد، مستقیم نمایش؛ وگرنه از list بخوان
      if (Array.isArray(data.items)) {
        setArchiveItems(data.items)
        setArchiveRoot(data.docs_root || '')
        setArchiveLoading(false)
      } else {
        loadArchive(rel, '')
      }
    } catch (err) {
      window.alert(err.message || 'خطا در باز کردن مدارک')
    } finally {
      setArchiveBusy(false)
    }
  }

  const archiveGoUp = () => {
    if (!archivePath) return
    const parts = archivePath.split('/').filter(Boolean)
    parts.pop()
    loadArchive(parts.join('/'))
  }

  const formatFileSize = (n) => {
    if (n == null || n === '') return '—'
    const num = Number(n)
    if (Number.isNaN(num)) return '—'
    if (num < 1024) return `${num} B`
    if (num < 1024 * 1024) return `${(num / 1024).toFixed(1)} KB`
    return `${(num / (1024 * 1024)).toFixed(1)} MB`
  }

  const archiveApiJson = async (url, options = {}) => {
    const res = await fetch(url, options)
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail = data.detail
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg || JSON.stringify(d)).join('؛ ')
        : detail || data.message || 'خطا'
      throw new Error(msg)
    }
    return data
  }

  const archiveCreateFolder = async () => {
    const name = window.prompt('نام پوشه جدید:')
    if (!name || !name.trim()) return
    setArchiveBusy(true)
    setArchiveMsg('')
    try {
      const data = await archiveApiJson('/api/docs/folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parent_path: archivePath || '', name: name.trim() }),
      })
      setArchiveMsg(data.message || 'پوشه ایجاد شد')
      loadArchive(archivePath)
    } catch (err) {
      setArchiveMsg(err.message || 'خطا در ایجاد پوشه')
    } finally {
      setArchiveBusy(false)
    }
  }

  const archiveRenameItem = async (item) => {
    const name = window.prompt('نام جدید:', item.name)
    if (!name || !name.trim() || name.trim() === item.name) return
    setArchiveBusy(true)
    setArchiveMsg('')
    try {
      const data = await archiveApiJson('/api/docs/folder', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: item.relative_path, new_name: name.trim() }),
      })
      setArchiveMsg(data.message || 'تغییر نام انجام شد')
      loadArchive(archivePath)
    } catch (err) {
      setArchiveMsg(err.message || 'خطا در تغییر نام')
    } finally {
      setArchiveBusy(false)
    }
  }

  const archiveDeleteItem = async (item) => {
    const kind = item.is_dir ? 'پوشه' : 'فایل'
    if (!window.confirm(`آیا از حذف ${kind} «${item.name}» مطمئن هستید؟`)) return
    setArchiveBusy(true)
    setArchiveMsg('')
    try {
      const data = await archiveApiJson('/api/docs/folder', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: item.relative_path, recursive: true }),
      })
      setArchiveMsg(data.message || 'حذف شد')
      loadArchive(archivePath)
    } catch (err) {
      setArchiveMsg(err.message || 'خطا در حذف')
    } finally {
      setArchiveBusy(false)
    }
  }

  const archiveUploadFiles = async (fileList) => {
    if (!fileList || !fileList.length) return
    setArchiveBusy(true)
    setArchiveMsg('')
    try {
      const fd = new FormData()
      fd.append('path', archivePath || '')
      Array.from(fileList).forEach((f) => fd.append('files', f))
      const data = await archiveApiJson('/api/docs/upload', { method: 'POST', body: fd })
      setArchiveMsg(data.message || 'آپلود انجام شد')
      loadArchive(archivePath)
    } catch (err) {
      setArchiveMsg(err.message || 'خطا در آپلود')
    } finally {
      setArchiveBusy(false)
      if (archiveFileRef.current) archiveFileRef.current.value = ''
    }
  }

  const companiesCacheRef = useRef({ ts: 0, loading: false })
  const loadCompanies = (force = false) => {
    const now = Date.now()
    if (!force && companiesCacheRef.current.ts && now - companiesCacheRef.current.ts < 8000) {
      return
    }
    if (companiesCacheRef.current.loading) return
    companiesCacheRef.current.loading = true
    fetch('/api/companies')
      .then((r) => r.json())
      .then((data) => {
        setCompanies(Array.isArray(data) ? data : [])
        companiesCacheRef.current.ts = Date.now()
      })
      .catch(() => setCompanies([]))
      .finally(() => { companiesCacheRef.current.loading = false })
    if (typeof loadBaseClientCompanies === 'function') loadBaseClientCompanies()
  }

  /** لیست شرکت‌های پیمانکار ثبت‌شده در تب پیمانکاران — برای استفاده در سایر فرم‌های همین تب */
  const loadCtrCompanies = () => {
    fetch('/api/baseinfo/ctr_companies')
      .then((r) => r.json())
      .then((d) => setCtrCompanies(Array.isArray(d) ? d : []))
      .catch(() => setCtrCompanies([]))
  }

  const filteredCompanies = (() => {
    const q = String(companySearch || '').trim().toLowerCase()
    const qEn = q.replace(/[۰-۹]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
    return (companies || []).filter((c) => {
      if (companyStatusFilter === 'active' && !c.is_active) return false
      if (companyStatusFilter === 'inactive' && c.is_active) return false
      if (!q) return true
      const parent = (companies || []).find((x) => String(x.code) === String(c.parent_code))
      const hay = [
        c.code, c.name, c.short_name, c.description, c.db_name, c.parent_code,
        parent?.name, parent?.short_name,
        c.is_active ? 'فعال' : 'غیرفعال',
      ].map((x) => String(x ?? '').toLowerCase()).join(' ')
      return hay.includes(q) || hay.includes(qEn)
    })
  })()

  const focusCompanySearch = () => {
    setTimeout(() => {
      const el = document.getElementById('company-search-input')
      if (el) { el.focus(); el.select() }
    }, 80)
  }

  const getPersonnelLimitOffset = (page = personnelPage, pageSize = personnelPageSize) => {
    if (pageSize === 'all') {
      return { limit: 100000, offset: 0 }
    }
    const size = Number(pageSize) || 50
    const p = Math.max(1, Number(page) || 1)
    return { limit: size, offset: (p - 1) * size }
  }

  const personnelPageCount =
    personnelPageSize === 'all' || !personnelTotal
      ? 1
      : Math.max(1, Math.ceil(personnelTotal / Number(personnelPageSize)))

  const importAssignOrgCsvFile = async (file) => {
    if (!file) return
    try {
      setAssignOrgMsg('در حال پردازش فایل CSV…')
      const text = await file.text()
      const rows = parseCsvText(text)
      if (!rows.length) {
        setAssignOrgMsg('فایل CSV خالی است یا قالب نادرست است')
        return
      }
      const res = await fetch('/api/personnel/assign-org-csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'خطا در تخصیص گروهی CSV')
      const msg =
        data.message ||
        (`تخصیص گروهی CSV: ${data.imported || 0} موفق` +
          (data.failed ? ` — ${data.failed} ناموفق` : ''))
      const errTail = data.errors?.length ? ` | ${data.errors.slice(0, 3).join('؛ ')}` : ''
      setAssignOrgMsg(msg + errTail)
      loadPersonnel(searchQuery, personnelPage, personnelPageSize)
      loadCompanies()
      loadUnits()
    } catch (e) {
      setAssignOrgMsg(e.message || 'خطا در خواندن CSV')
    }
  }

  const importPersonnelCsvFile = async (file) => {
    if (!file) return
    try {
      const text = await file.text()
      const rows = parseCsvText(text)
      if (!rows.length) { setFormMsg('فایل CSV خالی است یا قالب نادرست است'); return }
      const res = await fetch('/api/personnel/import-csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'خطا در ورود CSV')
      setFormMsg(`ورود CSV: ${data.imported || 0} موفق` + (data.failed ? ` — ${data.failed} ناموفق` : '') + (data.errors?.length ? ` | ${data.errors.slice(0, 3).join('؛ ')}` : ''))
      loadPersonnel()
    } catch (e) {
      setFormMsg(e.message || 'خطا در خواندن CSV')
    }
  }

  const importBaseinfoCsvFile = async (table, file, onDone) => {
    if (!file || !table) return
    try {
      const text = await file.text()
      const rows = parseCsvText(text)
      if (!rows.length) { if (onDone) onDone('فایل CSV خالی است'); return }
      const res = await fetch(`/api/baseinfo/${table}/import-csv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'خطا در ورود CSV')
      const msg = `ورود CSV: ${data.imported || 0} موفق` + (data.failed ? ` — ${data.failed} ناموفق` : '')
      if (onDone) onDone(msg)
    } catch (e) {
      if (onDone) onDone(e.message || 'خطا')
    }
  }

    const loadPersonnel = async (q = searchQuery, page = personnelPage, pageSize = personnelPageSize) => {
    setPersonnelLoading(true)
    const { limit, offset } = getPersonnelLimitOffset(page, pageSize)
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    })
    if (q) params.set('q', q)
    let response = await fetch(`/api/admin/personnel?${params.toString()}`)
    if (!response.ok) {
      response = await fetch(`/api/personnel?${params.toString()}`)
    }

    try {
      if (!response.ok) throw new Error(`Personnel request failed: ${response.status}`)
      const data = await response.json()
      setPersonnel(data.items || [])
      setPersonnelTotal(data.total || 0)
      setPersonnelScopeNote(
        data.database_errors?.length ? 'برخی دیتابیس‌ها در دسترس نبودند.' : ''
      )
      // اگر صفحه فعلی خالی شد (مثلاً بعد از حذف)، به صفحه قبل برگرد
      const total = data.total || 0
      if (pageSize !== 'all' && page > 1 && (data.items || []).length === 0 && total > 0) {
        const lastPage = Math.max(1, Math.ceil(total / Number(pageSize)))
        const newPage = Math.min(page - 1, lastPage)
        setPersonnelPage(newPage)
        return loadPersonnel(q, newPage, pageSize)
      }
    } catch (error) {
      setPersonnel([])
      setPersonnelTotal(0)
      setPersonnelScopeNote('دریافت فهرست پرسنل با خطا مواجه شد.')
    } finally {
      setPersonnelLoading(false)
    }
  }

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))

    fetch('/api/users/me')
      .then((r) => r.json())
      .then((data) => {
        if (data && data.role) setCurrentUser(data)
      })
      .catch(() => {})

    fetch('/api/dashboard/stats')
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})

    fetch('/api/violations/recent')
      .then((r) => r.json())
      .then((data) => setViolations(Array.isArray(data) ? data : []))
      .catch(() => setViolations([]))

    loadCompanies()
  }, [])

  const loadUnits = () => {
    fetch('/api/units')
      .then((r) => r.json())
      .then((d) => setUnits(Array.isArray(d) ? d : []))
      .catch(() => setUnits([]))
  }
  /** مرکز / نام شیفت / نوبت کار از تعاریف مرجع (اطلاعات پایه و انتظامات) */
  const loadShiftRefs = () => {
    loadUnits()
    fetch('/api/baseinfo/ent_shift_hours')
      .then((r) => r.json())
      .then((d) => setShiftHoursList(Array.isArray(d) ? d : []))
      .catch(() => setShiftHoursList([]))
    fetch('/api/baseinfo/ent_work_shifts')
      .then((r) => r.json())
      .then((d) => setWorkShiftsList(Array.isArray(d) ? d : []))
      .catch(() => setWorkShiftsList([]))
  }
  const centerOptions = () => {
    const s = new Set()
    ;(units || []).forEach((u) => { if (u.center_name) s.add(u.center_name) })
    return Array.from(s)
  }
  const shiftNameOptions = () => {
    const s = new Set()
    ;(shiftHoursList || []).forEach((x) => { if (x.name) s.add(x.name) })
    return Array.from(s)
  }
  const workShiftOptions = () => {
    const s = new Set()
    ;(workShiftsList || []).forEach((x) => { if (x.name) s.add(x.name) })
    return Array.from(s)
  }
  const optionsForField = (key) => {
    if (key === 'center_name') return centerOptions()
    if (key === 'shift_name') return shiftNameOptions()
    if (key === 'work_shift') return workShiftOptions()
    // شرکت کارفرما از لیست شرکت‌های اصلی سیستم
    if (key === 'employer_company') {
      const names = (companies || []).map((c) => c.name).filter(Boolean)
      return names.length ? names : null
    }
    // شرکت والد در فرم شرکت‌های پیمانکار: از خود لیست پیمانکاران
    if (key === 'parent_company') {
      if (activeTab === 'peymankar') {
        const names = (ctrCompanies || []).map((c) => c.name).filter(Boolean)
        return names.length ? names : []
      }
      const names = (companies || []).map((c) => c.name).filter(Boolean)
      return names.length ? names : null
    }
    // نام شرکت پیمانکار در قرارداد / پرسنل / خودرو / راننده — فقط از شرکت‌های ثبت‌شده در همین تب
    if (key === 'company_name' && activeTab === 'peymankar') {
      const names = (ctrCompanies || []).map((c) => c.name).filter(Boolean)
      return names.length ? names : []
    }
    return null
  }
  const loadEduFields = () => {
    fetch('/api/education-fields')
      .then((r) => r.json())
      .then((d) => setEduFields(Array.isArray(d) ? d : []))
      .catch(() => setEduFields([]))
  }
  const loadRespGroups = () => {
    fetch('/api/responsibility-groups')
      .then((r) => r.json())
      .then((d) => setRespGroups(Array.isArray(d) ? d : []))
      .catch(() => setRespGroups([]))
  }
  const loadEmpTypes = () => {
    fetch('/api/employment-types')
      .then((r) => r.json())
      .then((d) => setEmpTypes(Array.isArray(d) ? d : []))
      .catch(() => setEmpTypes([]))
  }

  const LOOKUP_VIEW_MAP = {
    services: { table: 'services', title: 'تعریف مسیر سرویس', mode: 'named' },
  }

  const ENTITY_VIEW_MAP = {
    doors: {
      table: 'access_doors', title: 'تعریف درب‌های تردد',
      fields: [
        { key: 'name', label: 'نام درب', required: true },
        { key: 'code', label: 'کد درب' },
        { key: 'door_type', label: 'نوع درب', type: 'select', options: ['تردد پرسنل و ارباب رجوع', 'پارکینگ', 'ورودی سازمان', 'خروجی سازمان'] },
        { key: 'direction', label: 'ورود/خروج', type: 'select', options: ['ورود', 'خروج'] },
        { key: 'center_name', label: 'مرکز' },
        { key: 'ip_address', label: 'IP' },
        { key: 'road_address', label: 'آدرس راه' },
        { key: 'device_type', label: 'نوع دستگاه اکسس کنترل' },
        { key: 'device_name', label: 'نام دستگاه' },
        { key: 'terminal_id', label: 'شناسه ترمینال' },
        { key: 'is_active', label: 'فعال', type: 'bool' },
      ],
      columns: ['code', 'name', 'door_type', 'direction', 'center_name', 'ip_address', 'device_name', 'is_active'],
    },
    goods: {
      table: 'goods_destinations', title: 'مقصد کالا',
      fields: [
        { key: 'name', label: 'مقصد', required: true },
        { key: 'phone1', label: 'تلفن ۱' },
        { key: 'phone2', label: 'تلفن ۲' },
        { key: 'address', label: 'آدرس' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['name', 'phone1', 'phone2', 'address', 'description'],
    },
    clients: {
      table: 'client_companies', title: 'شرکت‌ها/مشتری‌ها',
      fields: [
        { key: 'name', label: 'نام', required: true },
        { key: 'code', label: 'کد' },
        { key: 'phone', label: 'شماره تماس' },
        { key: 'address', label: 'آدرس' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['name', 'code', 'phone', 'address'],
    },
    entry_exit: {
      table: 'entry_exit_types', title: 'نوع ورود و خروج پرسنل و پیمانکاران',
      fields: [
        { key: 'name', label: 'عنوان', required: true },
        { key: 'is_entry', label: 'ورود', type: 'bool' },
        { key: 'is_exit', label: 'خروج', type: 'bool' },
      ],
      columns: ['name', 'is_entry', 'is_exit'],
    },
    door_access: {
      table: 'door_user_access', title: 'دسترسی کاربران به درب',
      fields: [
        { key: 'door_name', label: 'درب', required: true },
        { key: 'user_name', label: 'کاربر' },
      ],
      columns: ['door_name', 'user_name'],
    },
    veh_types: {
      table: 'vehicle_types', title: 'تعریف نوع خودروها',
      fields: [
        { key: 'name', label: 'نوع خودرو', required: true },
      ],
      columns: ['name'],
    },
    vehicles: {
      table: 'vehicles', title: 'تعریف خودروها',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', required: true, type: 'iran_plate' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'color', label: 'رنگ خودرو' },
        { key: 'ownership', label: 'مالکیت', type: 'select', options: ['ملکی', 'استیجاری'] },
        { key: 'category', label: 'دسته', type: 'select', options: ['خودرو', 'دستگاه'] },
        { key: 'chassis_number', label: 'شماره شاسی' },
        { key: 'center_name', label: 'مرکز' },
        { key: 'unit_name', label: 'نام واحد' },
        { key: 'personnel_name', label: 'پرسنل' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'company_name', label: 'نام شرکت' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'vehicle_type', 'color', 'center_name', 'driver_name', 'ownership'],
    },
    cargo_vehicles: {
      table: 'cargo_vehicles', title: 'تعریف خودروهای باری',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', required: true, type: 'iran_plate' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'chassis_number', label: 'شماره شاسی' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'driver_phone', label: 'تلفن همراه راننده' },
        { key: 'company_name', label: 'نام شرکت' },
        { key: 'vehicle_weight', label: 'وزن خودرو' },
        { key: 'max_weight', label: 'حداکثر وزن مجاز' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'vehicle_type', 'driver_name', 'company_name', 'vehicle_weight'],
    },
    cargo_reasons: {
      table: 'cargo_traffic_reasons', title: 'علت تردد خودروهای باری',
      fields: [
        { key: 'reason', label: 'علت تردد', required: true },
        { key: 'traffic_type', label: 'نوع تردد', type: 'select', options: ['ورود', 'خروج'] },
      ],
      columns: ['reason', 'traffic_type'],
    },
    goods_io: {
      table: 'goods_entry_exit_types', title: 'انواع ورود و خروج کالا',
      fields: [
        { key: 'name', label: 'انواع ورود و خروج کالا', required: true },
      ],
      columns: ['name'],
    },
    goods_products: {
      table: 'goods_products', title: 'تعریف کالا و محصولات',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'barcode', label: 'بارکد/شناسه', required: true },
        { key: 'name', label: 'نام کالا', required: true },
        { key: 'goods_type', label: 'نوع کالا' },
        { key: 'count_unit', label: 'واحد شمارش' },
        { key: 'serial_number', label: 'شماره سریال' },
        { key: 'product_specs', label: 'مشخصات محصول' },
        { key: 'is_active', label: 'فعال', type: 'bool' },
      ],
      columns: ['center_name', 'barcode', 'name', 'goods_type', 'count_unit', 'serial_number'],
    },
  }

  const ENTEZAMAT_VIEW_MAP = {
    groups: {
      table: 'ent_groups', title: 'تعریف گروه',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'name', label: 'نام', required: true },
      ],
      columns: ['center_name', 'name'],
    },
    prot_centers: {
      table: 'ent_protection_centers', title: 'تعریف مراکز حفاظتی و نگهبانی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'name', label: 'نام مرکز', required: true },
      ],
      columns: ['center_name', 'name'],
    },
    prot_places: {
      table: 'ent_protection_places', title: 'تعریف اماکن حفاظتی و نگهبانی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'protection_center_name', label: 'نام مرکز' },
        { key: 'place_name', label: 'مکان', required: true },
      ],
      columns: ['center_name', 'protection_center_name', 'place_name'],
    },
    shift_hours: {
      table: 'ent_shift_hours', title: 'تعریف ساعت‌های شیفت',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'name', label: 'نام شیفت', required: true },
        { key: 'start_time', label: 'ساعت شروع (مثال: ۰۷:۰۰)', required: true, placeholder: '۰۷:۰۰' },
        { key: 'end_time', label: 'ساعت پایان (مثال: ۱۵:۰۰)', required: true, placeholder: '۱۵:۰۰' },
      ],
      columns: ['center_name', 'name', 'start_time', 'end_time'],
    },
    shift_leaders: {
      table: 'ent_shift_leaders', title: 'تعریف مسئول و جانشین شیفت',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'unit_name', label: 'واحد مسئول شیفت' },
        { key: 'person_name', label: 'شخص مسئول شیفت' },
        { key: 'shift_name', label: 'نام شیفت' },
        { key: 'role_type', label: 'نوع', type: 'select', options: ['مسئول شیفت', 'جانشین شیفت'] },
      ],
      columns: ['center_name', 'person_name', 'role_type', 'shift_name'],
    },
    work_shifts: {
      table: 'ent_work_shifts', title: 'تعریف نوبت کار',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'name', label: 'نوبت کار', required: true },
      ],
      columns: ['center_name', 'name'],
    },
    staff_status: {
      table: 'ent_staff_status', title: 'تعریف وضعیت پرسنل انتظامات',
      fields: [
        { key: 'name', label: 'وضعیت', required: true },
      ],
      columns: ['name'],
    },
    equipment: {
      table: 'ent_guard_equipment', title: 'تجهیزات نگهبانی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'device_name', label: 'نام وسیله', required: true },
        { key: 'serial_number', label: 'شماره سریال' },
        { key: 'asset_number', label: 'شماره اموال' },
      ],
      columns: ['center_name', 'device_name', 'serial_number', 'asset_number'],
    },
    guard_board: {
      table: 'ent_guard_board', title: 'لوح نگهبانی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'shift_name', label: 'نام شیفت' },
        { key: 'work_shift', label: 'نوبت کار' },
        { key: 'shift_date', label: 'تاریخ شیفت' },
        { key: 'shift_leader', label: 'مسئول شیفت' },
        { key: 'shift_deputy', label: 'جانشین شیفت' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['center_name', 'shift_date', 'shift_name', 'work_shift', 'shift_leader'],
    },
    shift_events: {
      table: 'ent_shift_events', title: 'ثبت وقایع شیفت',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'shift_name', label: 'نام شیفت' },
        { key: 'event_date', label: 'تاریخ' },
        { key: 'event_text', label: 'شرح واقعه', required: true },
        { key: 'reporter', label: 'ثبت‌کننده' },
      ],
      columns: ['event_date', 'center_name', 'shift_name', 'event_text', 'reporter'],
    },
    shift_schedule: {
      table: 'ent_shift_schedule', title: 'برنامه نوبتکاری',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'work_shift', label: 'نوبت کار' },
        { key: 'personnel_name', label: 'نام پرسنل', required: true },
        { key: 'date_from', label: 'از تاریخ' },
        { key: 'date_to', label: 'تا تاریخ' },
        { key: 'notes', label: 'یادداشت' },
      ],
      columns: ['center_name', 'work_shift', 'personnel_name', 'date_from', 'date_to'],
    },
    electronics: {
      table: 'ent_personnel_electronics', title: 'تجهیزات الکترونیک پرسنل',
      fields: [
        { key: 'personnel_name', label: 'نام پرسنل', required: true },
        { key: 'device_name', label: 'نام وسیله' },
        { key: 'serial_number', label: 'سریال' },
        { key: 'center_name', label: 'مرکز' },
      ],
      columns: ['personnel_name', 'device_name', 'serial_number', 'center_name'],
    },
    replacement: {
      table: 'ent_replacement_requests', title: 'درخواست جایگزینی',
      fields: [
        { key: 'requester_name', label: 'درخواست‌دهنده', required: true },
        { key: 'replacement_name', label: 'جایگزین' },
        { key: 'shift_name', label: 'شیفت' },
        { key: 'request_date', label: 'تاریخ' },
        { key: 'reason', label: 'علت' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['در انتظار', 'تأیید', 'رد'] },
      ],
      columns: ['request_date', 'requester_name', 'replacement_name', 'shift_name', 'status'],
    },
    permits: {
      table: 'ent_permits', title: 'صدور مجوز',
      fields: [
        { key: 'permit_type', label: 'نوع مجوز' },
        { key: 'personnel_name', label: 'پرسنل', required: true },
        { key: 'center_name', label: 'مرکز' },
        { key: 'date_from', label: 'از تاریخ' },
        { key: 'date_to', label: 'تا تاریخ' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['permit_type', 'personnel_name', 'center_name', 'date_from', 'date_to'],
    },
    mon_events: {
      table: 'ent_monitoring_events', title: 'وقایع شیفت اتاق مانیتورینگ',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'shift_name', label: 'شیفت' },
        { key: 'event_date', label: 'تاریخ' },
        { key: 'event_text', label: 'شرح واقعه', required: true },
      ],
      columns: ['event_date', 'center_name', 'shift_name', 'event_text'],
    },
    mon_staff: {
      table: 'ent_monitoring_staff', title: 'مسئولین اتاق مانیتورینگ',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'person_name', label: 'نام', required: true },
        { key: 'role_name', label: 'سمت' },
        { key: 'shift_name', label: 'شیفت' },
      ],
      columns: ['center_name', 'person_name', 'role_name', 'shift_name'],
    },
    guard_reports: {
      table: 'ent_guard_reports', title: 'گزارش نگهبانی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'report_date', label: 'تاریخ' },
        { key: 'title', label: 'عنوان', required: true },
        { key: 'body', label: 'متن گزارش' },
      ],
      columns: ['report_date', 'center_name', 'title'],
    },
    guard_referrals: {
      table: 'ent_guard_referrals', title: 'گزارش ارجاع نگهبانی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'report_date', label: 'تاریخ' },
        { key: 'referred_to', label: 'ارجاع به' },
        { key: 'body', label: 'شرح' },
      ],
      columns: ['report_date', 'center_name', 'referred_to'],
    },
    roll_call: {
      table: 'ent_roll_call', title: 'رول‌کال / رونوشت',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'call_date', label: 'تاریخ' },
        { key: 'personnel_name', label: 'نام پرسنل', required: true },
        { key: 'status', label: 'وضعیت' },
        { key: 'notes', label: 'توضیح' },
      ],
      columns: ['call_date', 'personnel_name', 'status', 'center_name'],
    },

    board_summary: {
      table: 'ent_guard_board_summary', title: 'لوح نگهبانی اجمالی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'summary_date', label: 'تاریخ' },
        { key: 'summary_text', label: 'خلاصه', required: true },
      ],
      columns: ['summary_date', 'center_name', 'summary_text'],
    },
    guard_events: {
      table: 'ent_guard_events', title: 'ثبت وقایع نگهبانی',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'event_date', label: 'تاریخ' },
        { key: 'event_text', label: 'شرح واقعه', required: true },
        { key: 'officer_name', label: 'افسر' },
      ],
      columns: ['event_date', 'center_name', 'officer_name', 'event_text'],
    },
    deploy: {
      table: 'ent_deployment_locations', title: 'شناسه محل استقرار',
      fields: [
        { key: 'code', label: 'کد' },
        { key: 'name', label: 'نام محل', required: true },
        { key: 'center_name', label: 'مرکز' },
      ],
      columns: ['code', 'name', 'center_name'],
    },
    officer_events: {
      table: 'ent_officer_events', title: 'ثبت وقایع افسر نگهبانی',
      fields: [
        { key: 'officer_name', label: 'نام افسر', required: true },
        { key: 'event_date', label: 'تاریخ' },
        { key: 'event_text', label: 'شرح واقعه', required: true },
        { key: 'center_name', label: 'مرکز' },
      ],
      columns: ['event_date', 'officer_name', 'center_name', 'event_text'],
    },
  }

  const CARD_VIEW_MAP = {
    personnel_card: {
      table: 'card_personnel', title: 'چاپ کارت پرسنل',
      fields: [
        { key: 'personnel_code', label: 'کد پرسنلی', required: true },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی', required: true },
        { key: 'unit_name', label: 'واحد' },
        { key: 'membership_type', label: 'نوع عضویت', type: 'select', options: ['رسمی', 'پیمانی', 'قراردادی', 'سایر'] },
        { key: 'card_status', label: 'وضعیت کارت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی', 'ابطال'] },
        { key: 'issue_date', label: 'تاریخ صدور کارت' },
        { key: 'expiry_date', label: 'تاریخ پایان اعتبار' },
        { key: 'alphabetical', label: 'الفبایی', type: 'bool' },
        { key: 'print_front', label: 'چاپ روی کارت', type: 'bool' },
        { key: 'print_batch', label: 'چاپ به‌صورت یکجا', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['personnel_code', 'national_id', 'first_name', 'last_name', 'unit_name', 'card_status', 'issue_date', 'expiry_date'],
    },
    contractor_card: {
      table: 'card_contractor', title: 'چاپ کارت پیمانکاران',
      fields: [
        { key: 'personnel_code', label: 'کد پرسنلی', required: true },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی', required: true },
        { key: 'company_name', label: 'نام شرکت' },
        { key: 'activity_unit', label: 'واحد محل فعالیت' },
        { key: 'card_status', label: 'وضعیت کارت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی', 'ابطال'] },
        { key: 'issue_date', label: 'تاریخ صدور کارت' },
        { key: 'expiry_date', label: 'تاریخ پایان اعتبار' },
        { key: 'alphabetical', label: 'الفبایی', type: 'bool' },
        { key: 'print_front', label: 'چاپ روی کارت', type: 'bool' },
        { key: 'print_back', label: 'چاپ پشت کارت', type: 'bool' },
        { key: 'print_batch', label: 'چاپ به‌صورت یکجا', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['personnel_code', 'national_id', 'first_name', 'last_name', 'company_name', 'activity_unit', 'card_status', 'issue_date'],
    },
    vehicle_personnel: {
      table: 'card_vehicle_personnel', title: 'چاپ کارت خودروی پرسنل',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', required: true, type: 'iran_plate' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'unit_name', label: 'نام واحد' },
        { key: 'personnel_code', label: 'کد پرسنلی' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'card_status', label: 'وضعیت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی', 'ابطال'] },
        { key: 'issue_date', label: 'تاریخ صدور کارت' },
        { key: 'expiry_date', label: 'تاریخ پایان اعتبار' },
        { key: 'alphabetical', label: 'الفبایی', type: 'bool' },
        { key: 'print_front', label: 'چاپ روی کارت', type: 'bool' },
        { key: 'print_batch', label: 'چاپ به‌صورت یکجا', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'vehicle_type', 'unit_name', 'personnel_code', 'driver_name', 'card_status', 'issue_date'],
    },
    vehicle_contractor: {
      table: 'card_vehicle_contractor', title: 'چاپ کارت خودروی پیمانکاران',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', required: true, type: 'iran_plate' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'company_name', label: 'شرکت طرف قرارداد' },
        { key: 'activity_unit', label: 'واحد محل فعالیت' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'traffic_area', label: 'محدوده تردد' },
        { key: 'card_number', label: 'شماره کارت' },
        { key: 'certificate_number', label: 'شماره گواهینامه' },
        { key: 'card_status', label: 'وضعیت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی', 'ابطال'] },
        { key: 'issue_date', label: 'تاریخ صدور کارت' },
        { key: 'expiry_date', label: 'تاریخ پایان اعتبار' },
        { key: 'alphabetical', label: 'الفبایی', type: 'bool' },
        { key: 'print_front', label: 'چاپ روی کارت', type: 'bool' },
        { key: 'print_back', label: 'چاپ پشت کارت', type: 'bool' },
        { key: 'print_batch', label: 'چاپ به‌صورت یکجا', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'vehicle_type', 'company_name', 'driver_name', 'traffic_area', 'card_status', 'issue_date'],
    },
    issued_report: {
      table: 'card_personnel', title: 'گزارش کارت‌های صادر شده',
      fields: [
        { key: 'personnel_code', label: 'کد پرسنلی' },
        { key: 'first_name', label: 'نام' },
        { key: 'last_name', label: 'نام خانوادگی' },
        { key: 'unit_name', label: 'واحد' },
        { key: 'card_status', label: 'وضعیت کارت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی', 'ابطال'] },
        { key: 'issue_date', label: 'تاریخ صدور کارت' },
      ],
      columns: ['personnel_code', 'first_name', 'last_name', 'unit_name', 'card_status', 'issue_date', 'expiry_date'],
      readOnly: true,
    },
    vehicle_report: {
      table: 'card_vehicle_personnel', title: 'گزارش کارت‌های خودروی صادر شده',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'unit_name', label: 'نام واحد' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'card_status', label: 'وضعیت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی', 'ابطال'] },
        { key: 'issue_date', label: 'تاریخ صدور کارت' },
      ],
      columns: ['plate_number', 'vehicle_type', 'unit_name', 'driver_name', 'card_status', 'issue_date'],
      readOnly: true,
    },
  }

  const PEYMANKAR_VIEW_MAP = {
    companies: {
      table: 'ctr_companies', title: 'شرکت‌های پیمانکار',
      fields: [
        { key: 'name', label: 'نام پیمانکار', required: true },
        { key: 'company_code', label: 'کد شرکت پیمانکار' },
        { key: 'parent_company', label: 'شرکت والد', type: 'select' },
        { key: 'employer_company', label: 'شرکت کارفرما', required: true, type: 'select' },
        { key: 'register_date', label: 'تاریخ ثبت شرکت', type: 'date' },
        { key: 'ceo_name', label: 'نام مدیرعامل شرکت', type: 'text' },
        { key: 'ceo_mobile', label: 'تلفن همراه مدیر عامل', type: 'text' },
        { key: 'ceo_national_id', label: 'کد ملی مدیرعامل', type: 'text' },
        { key: 'ceo_education', label: 'مدرک تحصیلی مدیر عامل' },
        { key: 'rep1_name', label: 'نماینده شماره یک شرکت' },
        { key: 'rep1_mobile', label: 'تلفن همراه نماینده یک' },
        { key: 'rep1_national_id', label: 'کد ملی نماینده' },
        { key: 'supervisor_name', label: 'نام ناظر' },
        { key: 'supervisor_personnel_code', label: 'کد پرسنلی ناظر' },
        { key: 'company_phone', label: 'شماره تلفن شرکت' },
        { key: 'company_email', label: 'آدرس ایمیل شرکت' },
        { key: 'company_website', label: 'آدرس سایت شرکت' },
        { key: 'company_address', label: 'آدرس شرکت' },
        { key: 'company_history', label: 'سوابق شرکت' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['name', 'company_code', 'employer_company', 'parent_company', 'ceo_name', 'ceo_mobile', 'rep1_name', 'register_date'],
    },
    contracts: {
      table: 'ctr_contracts', title: 'قرارداد شرکت‌های پیمانکار',
      fields: [
        { key: 'company_name', label: 'نام شرکت', required: true, type: 'select' },
        { key: 'contract_subject', label: 'موضوع قرارداد', required: true },
        { key: 'activity_location', label: 'محل انجام فعالیت' },
        { key: 'tender_number', label: 'شماره مناقصه' },
        { key: 'contract_number', label: 'شماره قرارداد', required: true },
        { key: 'settlement_date', label: 'تاریخ تسویه حساب' },
        { key: 'start_date', label: 'تاریخ شروع قرارداد' },
        { key: 'end_date', label: 'تاریخ پایان قرارداد' },
        { key: 'contract_amount', label: 'مبلغ قرارداد' },
        { key: 'credit_duration', label: 'مدت قرارداد اعتبار' },
        { key: 'duration_notes', label: 'توضیحات مدت قرارداد' },
        { key: 'work_location', label: 'محل فعالیت' },
        { key: 'supervisor_unit', label: 'واحد ناظر' },
        { key: 'contract_status', label: 'وضعیت قرارداد', type: 'select', options: ['فعال', 'راکد', 'خاتمه یافته', 'فسخ'] },
        { key: 'status_description', label: 'شرح وضعیت' },
        { key: 'is_inactive', label: 'وضعیت راکد', type: 'bool' },
        { key: 'transport', label: 'ایاب و ذهاب' },
        { key: 'vehicle_count', label: 'تعداد خودرو' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'vehicle_entry_permit', label: 'مجوز ورود خودرو', type: 'bool' },
        { key: 'restaurant', label: 'رستوران', type: 'bool' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['contract_number', 'company_name', 'contract_subject', 'start_date', 'end_date', 'contract_amount', 'contract_status'],
    },
    personnel: {
      table: 'ctr_personnel', title: 'پرسنل شرکت‌های پیمانکار',
      fields: [
        { key: 'company_name', label: 'شرکت پیمانکار', required: true, type: 'select' },
        { key: 'contract_number', label: 'شماره قرارداد' },
        { key: 'nationality', label: 'تابعیت', type: 'select', options: ['ایرانی', 'غیرایرانی'] },
        { key: 'personnel_code', label: 'کد پرسنلی' },
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی', required: true },
        { key: 'father_name', label: 'نام پدر' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'supervisor_name', label: 'نام سرپرست / ناظر' },
        { key: 'job_type', label: 'نوع کار شرکت' },
        { key: 'activity_unit', label: 'واحد محل فعالیت' },
        { key: 'end_of_service_date', label: 'تاریخ پایان خدمت' },
        { key: 'mobile_phone', label: 'تلفن همراه' },
        { key: 'fixed_phone', label: 'تلفن ثابت' },
        { key: 'emergency_phone', label: 'شماره تماس اضطراری' },
        { key: 'card_number', label: 'شماره کارت' },
        { key: 'card_status', label: 'وضعیت کارت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی', 'ابطال'] },
        { key: 'card_type', label: 'نوع کارت' },
        { key: 'education_degree', label: 'مدرک تحصیلی' },
        { key: 'education_field', label: 'رشته تحصیلی' },
        { key: 'birth_date', label: 'تاریخ تولد' },
        { key: 'birth_place', label: 'محل تولد' },
        { key: 'gender', label: 'جنسیت', type: 'select', options: ['مرد', 'زن'] },
        { key: 'job_title', label: 'شغل' },
        { key: 'marital_status', label: 'وضعیت تاهل', type: 'select', options: ['مجرد', 'متاهل'] },
        { key: 'military_status', label: 'وضعیت نظام وظیفه' },
        { key: 'membership_type', label: 'نوع عضویت' },
        { key: 'blood_type', label: 'گروه خونی' },
        { key: 'credit_start_date', label: 'تاریخ شروع اعتبار' },
        { key: 'credit_end_date', label: 'تاریخ پایان اعتبار' },
        { key: 'is_inactive', label: 'وضعیت راکد', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['personnel_code', 'first_name', 'last_name', 'father_name', 'national_id', 'company_name', 'card_status'],
    },
    vehicles: {
      table: 'ctr_vehicles', title: 'ثبت خودروهای پیمانکاران',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', required: true, type: 'iran_plate' },
        { key: 'company_name', label: 'شرکت طرف قرارداد', required: true, type: 'select' },
        { key: 'owner_last_name', label: 'نام خانوادگی مالک خودرو' },
        { key: 'owner_first_name', label: 'نام مالک خودرو' },
        { key: 'owner_national_id', label: 'شماره ملی مالک خودرو' },
        { key: 'vehicle_class', label: 'کلاس خودرو' },
        { key: 'vehicle_type', label: 'نوع خودرو', required: true },
        { key: 'vehicle_color', label: 'رنگ خودرو' },
        { key: 'equipment', label: 'تجهیزات خودرو' },
        { key: 'usage_purpose', label: 'مورد استفاده خودرو' },
        { key: 'activity_unit', label: 'واحد محل فعالیت' },
        { key: 'chassis_number', label: 'شماره شاسی' },
        { key: 'insurance_end_date', label: 'پایان بیمه' },
        { key: 'card_status', label: 'وضعیت کارت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی'] },
        { key: 'traffic_status', label: 'وضعیت تردد' },
        { key: 'traffic_area', label: 'محدوده تردد' },
        { key: 'credit_end_date', label: 'تاریخ پایان اعتبار' },
        { key: 'last_inspection_date', label: 'تاریخ معاینه فنی' },
        { key: 'is_inactive', label: 'وضعیت راکد', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'company_name', 'vehicle_type', 'vehicle_class', 'vehicle_color', 'owner_last_name', 'card_status'],
    },
    drivers: {
      table: 'ctr_drivers', title: 'ثبت راننده‌های پیمانکاران',
      fields: [
        { key: 'company_name', label: 'شرکت طرف قرارداد', required: true, type: 'select' },
        { key: 'personnel_code', label: 'کد پرسنلی' },
        { key: 'driver_name', label: 'نام راننده', required: true },
        { key: 'father_name', label: 'نام پدر' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'activity_unit', label: 'واحد محل فعالیت' },
        { key: 'position', label: 'سمت' },
        { key: 'license_type', label: 'نوع گواهینامه' },
        { key: 'license_number', label: 'شماره گواهینامه' },
        { key: 'license_issue_place', label: 'محل صدور گواهینامه' },
        { key: 'license_end_date', label: 'تاریخ پایان اعتبار' },
        { key: 'card_status', label: 'وضعیت کارت', type: 'select', options: ['فعال', 'غیرفعال', 'منقضی'] },
        { key: 'validity_type', label: 'نوع اعتبار', type: 'select', options: ['دائم', 'موقت'] },
        { key: 'is_inactive', label: 'وضعیت راکد', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['driver_name', 'father_name', 'national_id', 'company_name', 'license_type', 'license_number', 'license_end_date'],
    },
  }

  const PATROL_VIEW_MAP = {
    devices: {
      table: 'patrol_devices', title: 'لیست دستگاه‌ها',
      fields: [
        { key: 'device_name', label: 'نام دستگاه', required: true },
        { key: 'device_code', label: 'کد دستگاه' },
        { key: 'connected_port', label: 'پورت متصل به دستگاه' },
        { key: 'usb_port', label: 'پورت USB' },
        { key: 'center_name', label: 'مرکز' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['center_name', 'device_code', 'device_name', 'usb_port', 'connected_port'],
    },
    events: {
      table: 'patrol_events', title: 'لیست رخدادها',
      fields: [
        { key: 'event_code', label: 'کد' },
        { key: 'event_name', label: 'نام', required: true },
        { key: 'importance', label: 'درجه اهمیت', type: 'select', options: ['عادی', 'مهم', 'بحرانی', 'اطلاعاتی'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['event_code', 'event_name', 'importance'],
    },
    checkpoints: {
      table: 'patrol_checkpoints', title: 'لیست نقاط بازدید',
      fields: [
        { key: 'checkpoint_code', label: 'کد محل نگهبانی' },
        { key: 'checkpoint_name', label: 'نام محل نگهبانی', required: true },
        { key: 'center_name', label: 'مرکز' },
        { key: 'connected_port', label: 'پورت متصل به دستگاه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['center_name', 'checkpoint_code', 'checkpoint_name', 'connected_port'],
    },
    guards: {
      table: 'patrol_guards', title: 'لیست نگهبانان',
      fields: [
        { key: 'guard_id', label: 'شناسه نگهبان' },
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی', required: true },
        { key: 'personnel_code', label: 'کد پرسنلی' },
        { key: 'unit_name', label: 'واحد' },
        { key: 'center_name', label: 'مرکز' },
        { key: 'connected_port', label: 'پورت متصل به دستگاه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['center_name', 'guard_id', 'first_name', 'last_name', 'personnel_code', 'unit_name'],
    },
    route_config: {
      table: 'patrol_route_config', title: 'پیکربندی مسیر',
      fields: [
        { key: 'route_name', label: 'نام مسیر', required: true },
        { key: 'guard_name', label: 'نام نگهبان' },
        { key: 'device_name', label: 'نام دستگاه' },
        { key: 'sequence_order', label: 'ترتیب' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['route_name', 'guard_name', 'device_name', 'sequence_order'],
    },
    routes: {
      table: 'patrol_routes', title: 'مسیرها و ساعات شروع',
      fields: [
        { key: 'route_name', label: 'نام مسیر', required: true },
        { key: 'center_name', label: 'مرکز' },
        { key: 'start_time', label: 'ساعت شروع', placeholder: '۰۷:۰۰' },
        { key: 'end_time', label: 'ساعت پایان', placeholder: '۱۵:۰۰' },
        { key: 'checkpoint_names', label: 'نقاط بازدید' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['route_name', 'center_name', 'start_time', 'end_time', 'checkpoint_names'],
    },
    shift_times: {
      table: 'patrol_shift_times', title: 'تعیین ساعت شروع و پایان',
      fields: [
        { key: 'center_name', label: 'مرکز' },
        { key: 'route_name', label: 'نام مسیر' },
        { key: 'shift_name', label: 'نام شیفت' },
        { key: 'start_time', label: 'ساعت شروع', placeholder: '۰۷:۰۰' },
        { key: 'end_time', label: 'ساعت پایان', placeholder: '۱۵:۰۰' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['center_name', 'route_name', 'shift_name', 'start_time', 'end_time'],
    },
  }


  const HERASAT_VIEW_MAP = {
    news: {
      table: 'ent_news_reports', title: 'گزارش خبر',
      fields: [
        { key: 'title', label: 'عنوان', required: true },
        { key: 'report_date', label: 'تاریخ' },
        { key: 'body', label: 'متن' },
      ],
      columns: ['report_date', 'title'],
    },
    eval_options: {
      table: 'hr_eval_options', title: 'گزینه‌های ارزشیابی',
      fields: [
        { key: 'group_name', label: 'نام گروه' },
        { key: 'option1', label: 'گزینه اول' }, { key: 'score1', label: 'امتیاز گزینه اول' },
        { key: 'option2', label: 'گزینه دوم' }, { key: 'score2', label: 'امتیاز گزینه دوم' },
        { key: 'option3', label: 'گزینه سوم' }, { key: 'score3', label: 'امتیاز گزینه سوم' },
        { key: 'option4', label: 'گزینه چهارم' }, { key: 'score4', label: 'امتیاز گزینه چهارم' },
        { key: 'option5', label: 'گزینه پنجم' }, { key: 'score5', label: 'امتیاز گزینه پنجم' },
        { key: 'option6', label: 'گزینه ششم' }, { key: 'score6', label: 'امتیاز گزینه ششم' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['group_name', 'option1', 'score1', 'option2', 'score2', 'option3', 'score3'],
    },
    eval_titles: {
      table: 'hr_eval_titles', title: 'عناوین ارزشیابی',
      fields: [
        { key: 'title_text', label: 'شرح عنوان', required: true },
        { key: 'score', label: 'امتیاز' },
        { key: 'answer_type', label: 'نوع پاسخ', type: 'select', options: ['امتیازی', 'تشریحی', 'چندگزینه‌ای'] },
        { key: 'option_count', label: 'تعداد گزینه‌های عنوان' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['title_text', 'score', 'answer_type', 'option_count'],
    },
    eval_periods: {
      table: 'hr_eval_periods', title: 'تعریف دوره ارزشیابی',
      fields: [
        { key: 'period_title', label: 'عنوان دوره', required: true },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['period_title', 'notes'],
    },
    eval_monthly: {
      table: 'hr_eval_monthly', title: 'ارزشیابی ماهانه پرسنل',
      fields: [
        { key: 'personnel_name', label: 'پرسنل', required: true },
        { key: 'unit_name', label: 'واحد' },
        { key: 'period_title', label: 'عنوان دوره' },
        { key: 'supervisor_name', label: 'سرپرست' },
        { key: 'supervisor_opinion', label: 'نظر سرپرست' },
        { key: 'eval_date', label: 'تاریخ' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['personnel_name', 'unit_name', 'period_title', 'supervisor_name', 'supervisor_opinion'],
    },
    areas: {
      table: 'hr_areas', title: 'تعریف نواحی',
      fields: [
        { key: 'area_name', label: 'ناحیه', required: true },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['area_name'],
    },
    houses: {
      table: 'hr_houses', title: 'تعریف منازل',
      fields: [
        { key: 'house_name', label: 'منزل', required: true },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['house_name'],
    },
    house_delivery: {
      table: 'hr_house_delivery', title: 'تحویل منازل و اماکن',
      fields: [
        { key: 'area_name', label: 'ناحیه' },
        { key: 'house_name', label: 'منزل' },
        { key: 'personnel_name', label: 'نام پرسنل' },
        { key: 'personnel_code', label: 'کد پرسنلی' },
        { key: 'related_office', label: 'اداره مربوطه' },
        { key: 'house_number', label: 'شماره منزل' },
        { key: 'phone', label: 'تلفن' },
        { key: 'mobile', label: 'موبایل' },
        { key: 'delivery_date', label: 'تاریخ تحویل' },
        { key: 'eviction_date', label: 'تاریخ تخلیه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['area_name', 'house_name', 'personnel_name', 'related_office', 'delivery_date'],
    },
    doc_archive: {
      table: 'hr_doc_archive', title: 'بایگانی مدارک',
      fields: [
        { key: 'page_description', label: 'شرح صفحه' },
        { key: 'keyword', label: 'کلید واژه' },
        { key: 'file_name', label: 'نام فایل صفحه' },
        { key: 'file_type', label: 'نوع صفحه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['page_description', 'keyword', 'file_name', 'file_type'],
    },
    foreign_nationals: {
      table: 'hr_foreign_nationals', title: 'مشخصات اتباع خارجی',
      fields: [
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی', required: true },
        { key: 'father_name', label: 'نام پدر' },
        { key: 'nationality', label: 'تابعیت' },
        { key: 'passport_number', label: 'شماره گذرنامه' },
        { key: 'gender', label: 'جنسیت', type: 'select', options: ['مرد', 'زن'] },
        { key: 'birth_date', label: 'تاریخ تولد' },
        { key: 'birth_place', label: 'محل تولد' },
        { key: 'job_title', label: 'شغل' },
        { key: 'mobile', label: 'تلفن همراه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['first_name', 'last_name', 'nationality', 'passport_number', 'gender'],
    },
    countries: {
      table: 'hr_countries', title: 'مشخصات کشورها',
      fields: [
        { key: 'country_name', label: 'نام کشور', required: true },
        { key: 'residence_city', label: 'شهر محل اقامت' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['country_name', 'residence_city'],
    },
    viol_personnel: {
      table: 'hr_violations_personnel', title: 'ثبت تخلفات پرسنل و پیمانکاران',
      fields: [
        { key: 'person_type', label: 'نوع فرد', type: 'select', options: ['پرسنل شرکتی', 'پرسنل پیمانکار', 'متفرقه'] },
        { key: 'unit_name', label: 'واحد' },
        { key: 'person_name', label: 'نام فرد', required: true },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'violation_code', label: 'کد تخلف' },
        { key: 'violation_subject', label: 'مورد تخلف' },
        { key: 'occurrence_time', label: 'زمان وقوع' },
        { key: 'register_date', label: 'تاریخ ثبت' },
        { key: 'fine_amount', label: 'مبلغ' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['person_type', 'person_name', 'unit_name', 'violation_code', 'violation_subject', 'register_date', 'fine_amount'],
    },
    viol_vehicle: {
      table: 'hr_violations_vehicle', title: 'ثبت تخلفات خودرویی',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', required: true, type: 'iran_plate' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'unit_name', label: 'واحد / شرکت' },
        { key: 'violation_code', label: 'کد تخلف' },
        { key: 'violation_subject', label: 'مورد تخلف' },
        { key: 'occurrence_time', label: 'زمان وقوع' },
        { key: 'register_date', label: 'تاریخ ثبت' },
        { key: 'fine_amount', label: 'مبلغ' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'vehicle_type', 'driver_name', 'violation_code', 'violation_subject', 'register_date', 'fine_amount'],
    },
    incidents: {
      table: 'hr_incidents', title: 'صورتجلسه حوادث',
      fields: [
        { key: 'incident_datetime', label: 'زمان و تاریخ حادثه' },
        { key: 'incident_location', label: 'محل حادثه' },
        { key: 'expert1_name', label: 'کارشناس ۱' },
        { key: 'expert1_unit', label: 'واحد کارشناس ۱' },
        { key: 'expert1_opinion', label: 'نظریه کارشناس ۱' },
        { key: 'expert2_name', label: 'کارشناس ۲' },
        { key: 'expert2_unit', label: 'واحد کارشناس ۲' },
        { key: 'expert2_opinion', label: 'نظریه کارشناس ۲' },
        { key: 'commission_result', label: 'نتیجه کمیته بررسی' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['incident_datetime', 'incident_location', 'expert1_name', 'commission_result'],
    },
    drug_tests: {
      table: 'hr_drug_tests', title: 'ثبت مصرف مواد مخدر',
      fields: [
        { key: 'person_type', label: 'نوع فرد', type: 'select', options: ['پرسنل شرکتی', 'پرسنل پیمانکار'] },
        { key: 'unit_name', label: 'واحد' },
        { key: 'person_name', label: 'نام', required: true },
        { key: 'father_name', label: 'نام پدر' },
        { key: 'birth_date', label: 'تاریخ تولد' },
        { key: 'birth_place', label: 'محل تولد' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'mobile', label: 'شماره همراه' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['person_name', 'unit_name', 'father_name', 'national_id', 'mobile'],
    },
    rewards: {
      table: 'hr_rewards', title: 'تقدیر و تشویق سازمانی',
      fields: [
        { key: 'person_type', label: 'نوع فرد', type: 'select', options: ['پرسنل شرکتی', 'پرسنل پیمانکار', 'متفرقه'] },
        { key: 'unit_name', label: 'واحد' },
        { key: 'person_name', label: 'نام فرد', required: true },
        { key: 'reward_code', label: 'کد' },
        { key: 'reward_subject', label: 'مورد تشویق' },
        { key: 'register_date', label: 'تاریخ ثبت' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['person_name', 'unit_name', 'reward_code', 'reward_subject', 'register_date'],
    },
    travel_abroad: {
      table: 'hr_travel_abroad', title: 'پرسشنامه اعزام به خارج از کشور',
      fields: [
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی', required: true },
        { key: 'father_name', label: 'نام پدر' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'passport_number', label: 'شماره گذرنامه' },
        { key: 'destination_country', label: 'کشور مقصد' },
        { key: 'travel_from', label: 'از تاریخ' },
        { key: 'travel_to', label: 'تا تاریخ' },
        { key: 'purpose', label: 'اهداف ماموریت / سفر' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['first_name', 'last_name', 'national_id', 'destination_country', 'travel_from', 'travel_to', 'purpose'],
    },
    travel_personal: {
      table: 'hr_travel_personal', title: 'پرسشنامه سفرهای شخصی',
      fields: [
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی', required: true },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'destination_country', label: 'کشور مقصد' },
        { key: 'travel_from', label: 'از تاریخ' },
        { key: 'travel_to', label: 'تا تاریخ' },
        { key: 'purpose', label: 'علت سفر' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['first_name', 'last_name', 'destination_country', 'travel_from', 'travel_to', 'purpose'],
    },
    exit_admin: {
      table: 'hr_exit_admin', title: 'درخواست خروج دیپ و مدارک اداری',
      fields: [
        { key: 'requester_name', label: 'نام درخواست‌کننده', required: true },
        { key: 'unit_name', label: 'واحد' },
        { key: 'document_type', label: 'نوع مدرک' },
        { key: 'request_date', label: 'تاریخ درخواست' },
        { key: 'description', label: 'شرح' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['در انتظار', 'تأیید', 'رد'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['requester_name', 'unit_name', 'document_type', 'request_date', 'status'],
    },
    exit_scientific: {
      table: 'hr_exit_scientific', title: 'درخواست خروج دیپ و مدارک علمی',
      fields: [
        { key: 'requester_name', label: 'نام درخواست‌کننده', required: true },
        { key: 'unit_name', label: 'واحد' },
        { key: 'document_type', label: 'نوع مدرک' },
        { key: 'request_date', label: 'تاریخ درخواست' },
        { key: 'description', label: 'شرح' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['در انتظار', 'تأیید', 'رد'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['requester_name', 'unit_name', 'document_type', 'request_date', 'status'],
    },
  }


  const MONAGHESE_VIEW_MAP = {
    companies: {
      table: 'tnd_companies', title: 'شرکت‌های حاضر در مناقصه/مزایده',
      fields: [
        { key: 'company_name', label: 'نام شرکت', required: true },
        { key: 'registration_place', label: 'محل ثبت' },
        { key: 'registration_number', label: 'شماره ثبت' },
        { key: 'registration_date', label: 'تاریخ ثبت' },
        { key: 'activity_type', label: 'نوع فعالیت' },
        { key: 'rank_level', label: 'رتبه' },
        { key: 'address', label: 'آدرس' },
        { key: 'postal_code', label: 'کد پستی' },
        { key: 'email', label: 'ایمیل' },
        { key: 'phone', label: 'تلفن' },
        { key: 'fax', label: 'فکس' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['company_name', 'registration_number', 'registration_place', 'rank_level', 'postal_code', 'email', 'phone', 'fax', 'registration_date'],
    },
    tenders: {
      table: 'tnd_tenders', title: 'مناقصات',
      fields: [
        { key: 'main_company', label: 'شرکت اصلی' },
        { key: 'subsidiary_company', label: 'شرکت فرعی' },
        { key: 'main_organization', label: 'سازمان اصلی' },
        { key: 'tender_subject', label: 'موضوع مناقصه', required: true },
        { key: 'tender_type', label: 'مناقصه از نظر نوع و روش دعوت', type: 'select', options: ['مناقصه از نظر فراخوان بررسی', 'عمومی', 'محدود', 'ترک تشریفات'] },
        { key: 'cancellation_reason', label: 'انجام معامله به دلیل انحصار' },
        { key: 'exclusive_method', label: 'روش احراز انحصار' },
        { key: 'security_rep', label: 'نماینده حراست' },
        { key: 'inspection_rep', label: 'نماینده بازرسی' },
        { key: 'inspection_rep2', label: 'نماینده بازرسی ۲' },
        { key: 'packet_open_date', label: 'تاریخ گشایش پاکت' },
        { key: 'agreement_amount', label: 'مبلغ/درصد مورد توافق' },
        { key: 'agreement_amount_prev', label: 'مبلغ/درصد مورد توافق سال گذشته' },
        { key: 'expert_amount', label: 'مبلغ/درصد مورد کارشناسی' },
        { key: 'expert_amount_prev', label: 'مبلغ/درصد مورد کارشناسی سال گذشته' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['main_company', 'subsidiary_company', 'main_organization', 'tender_subject', 'packet_open_date', 'agreement_amount'],
    },
    auctions: {
      table: 'tnd_auctions', title: 'مزایده',
      fields: [
        { key: 'main_company', label: 'شرکت اصلی' },
        { key: 'subsidiary_company', label: 'شرکت فرعی' },
        { key: 'main_organization', label: 'سازمان اصلی' },
        { key: 'auction_subject', label: 'موضوع مزایده', required: true },
        { key: 'auction_type', label: 'مزایده از نظر نوع و روش دعوت', type: 'select', options: ['مزایده از نظر فراخوان بررسی', 'عمومی', 'محدود'] },
        { key: 'cancellation_reason', label: 'انجام معامله به دلیل انحصار' },
        { key: 'security_rep', label: 'نماینده حراست' },
        { key: 'inspection_rep', label: 'نماینده بازرسی' },
        { key: 'inspection_rep2', label: 'نماینده بازرسی ۲' },
        { key: 'packet_open_date', label: 'تاریخ گشایش پاکت' },
        { key: 'agreement_amount', label: 'مبلغ/درصد مورد توافق' },
        { key: 'agreement_amount_prev', label: 'مبلغ/درصد مورد توافق سال گذشته' },
        { key: 'expert_amount', label: 'مبلغ/درصد مورد کارشناسی' },
        { key: 'expert_amount_prev', label: 'مبلغ/درصد مورد کارشناسی سال گذشته' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['main_company', 'subsidiary_company', 'main_organization', 'auction_subject', 'packet_open_date', 'agreement_amount'],
    },
    contracts: {
      table: 'tnd_contracts', title: 'قراردادها',
      fields: [
        { key: 'main_company', label: 'شرکت اصلی' },
        { key: 'subsidiary_company', label: 'شرکت فرعی' },
        { key: 'main_organization', label: 'سازمان اصلی' },
        { key: 'contractor_name', label: 'پیمانکار' },
        { key: 'contract_number', label: 'شماره قرارداد' },
        { key: 'contract_date', label: 'تاریخ قرارداد' },
        { key: 'contract_amount', label: 'مبلغ قرارداد' },
        { key: 'execution_place', label: 'محل اجرای قرارداد' },
        { key: 'contract_subject', label: 'موضوع قرارداد', required: true },
        { key: 'start_date', label: 'تاریخ شروع' },
        { key: 'end_date', label: 'تاریخ پایان' },
        { key: 'guarantee_type', label: 'نوع و میزان ضمانت‌نامه' },
        { key: 'guarantee_amount', label: 'نوع و میزان ضمانت‌نامه پیش‌پرداخت' },
        { key: 'duration', label: 'مدت زمان انجام قرارداد' },
        { key: 'request_reason', label: 'دلایل موافقت با درخواست' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['contract_number', 'contract_subject', 'contractor_name', 'main_company', 'execution_place', 'contract_date'],
    },
  }


  const KARTABL_VIEW_MAP = {
    outgoing: {
      table: 'krt_outgoing', title: 'نامه‌های صادره',
      fields: [
        { key: 'letter_number', label: 'شماره نامه' },
        { key: 'subject', label: 'موضوع نامه', required: true },
        { key: 'letter_date', label: 'تاریخ نامه' },
        { key: 'secretary_number', label: 'شماره دبیرخانه' },
        { key: 'secretary_date', label: 'تاریخ دبیرخانه' },
        { key: 'letter_body', label: 'متن نامه' },
        { key: 'recipients', label: 'گیرندگان' },
        { key: 'file_name', label: 'نام فایل' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['subject', 'letter_date', 'letter_number', 'secretary_number', 'recipients', 'file_name'],
    },
    inbox: {
      table: 'krt_inbox', title: 'نامه‌های وارده',
      fields: [
        { key: 'letter_number', label: 'شماره نامه' },
        { key: 'subject', label: 'موضوع نامه', required: true },
        { key: 'letter_date', label: 'تاریخ نامه' },
        { key: 'secretary_number', label: 'شماره دبیرخانه' },
        { key: 'secretary_date', label: 'تاریخ دبیرخانه' },
        { key: 'sender_name', label: 'فرستنده' },
        { key: 'letter_body', label: 'متن نامه' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['مشاهده نشده', 'باز شده', 'ارسال شده', 'بایگانی شده'] },
        { key: 'folder_name', label: 'پوشه' },
        { key: 'file_name', label: 'نام فایل' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['subject', 'letter_date', 'sender_name', 'status', 'folder_name', 'letter_number'],
    },
    management: {
      table: 'krt_management', title: 'مدیریت کارتابل',
      fields: [
        { key: 'sender_name', label: 'فرستنده' },
        { key: 'subject', label: 'موضوع', required: true },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['مشاهده نشده', 'باز شده', 'ارسال شده', 'بایگانی شده'] },
        { key: 'send_date', label: 'تاریخ ارسال' },
        { key: 'hour_sent', label: 'ساعت ارسال' },
        { key: 'folder_name', label: 'نام پوشه' },
        { key: 'file_name', label: 'نام فایل' },
        { key: 'letter_body', label: 'متن نامه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['sender_name', 'subject', 'status', 'send_date', 'hour_sent', 'folder_name', 'file_name'],
    },
    folders: {
      table: 'krt_folders', title: 'پوشه‌های بایگانی',
      fields: [
        { key: 'folder_name', label: 'نام پوشه', required: true },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['folder_name', 'notes'],
    },
  }


  const BASKOOL_VIEW_MAP = {
    weighings: {
      table: 'bsk_weighings', title: 'ثبت توزین',
      fields: [
        { key: 'ticket_number', label: 'شماره قبض' },
        { key: 'queue_number', label: 'شماره نوبت' },
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate', required: true },
        { key: 'card_serial', label: 'سریال کارت‌نامه' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'origin_company', label: 'شرکت مبدأ' },
        { key: 'destination_unit', label: 'واحد/شرکت مقصد' },
        { key: 'location_name', label: 'مکان تخلیه' },
        { key: 'cargo_code', label: 'کد کالا' },
        { key: 'cargo_title', label: 'عنوان کالا' },
        { key: 'first_weight', label: 'وزن ناخالص / توزین اول' },
        { key: 'first_date', label: 'تاریخ توزین اول' },
        { key: 'first_time', label: 'ساعت توزین اول' },
        { key: 'first_operator', label: 'نام نشان‌دهنده اول' },
        { key: 'first_status', label: 'وضعیت توزین اول', type: 'select', options: ['خالی', 'پر'] },
        { key: 'second_weight', label: 'وزن توزین دوم' },
        { key: 'second_date', label: 'تاریخ توزین دوم' },
        { key: 'second_time', label: 'ساعت توزین دوم' },
        { key: 'second_operator', label: 'نام نشان‌دهنده دوم' },
        { key: 'net_weight', label: 'وزن خالص' },
        { key: 'weigh_type', label: 'وضعیت توزین', type: 'select', options: ['بار ورودی', 'بار خروجی', 'جا به جایی داخلی'] },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['ticket_number', 'plate_number', 'driver_name', 'vehicle_type', 'first_weight', 'second_weight', 'net_weight', 'weigh_type'],
    },
    turns: {
      table: 'bsk_turns', title: 'سیستم ثبت نوبت',
      fields: [
        { key: 'turn_number', label: 'شماره نوبت' },
        { key: 'card_serial', label: 'سریال کارت‌نامه' },
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate', required: true },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'vehicle_weight', label: 'وزن خودرو' },
        { key: 'allowed_max_weight', label: 'حداکثر وزن مجاز' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'driver_phone', label: 'تلفن همراه راننده' },
        { key: 'license_number', label: 'شماره گواهینامه' },
        { key: 'origin_company', label: 'شرکت مبدأ' },
        { key: 'destination_unit', label: 'واحد/شرکت مقصد' },
        { key: 'cargo_type', label: 'نوع بار' },
        { key: 'location_name', label: 'مکان تخلیه' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['turn_number', 'plate_number', 'driver_name', 'vehicle_type', 'origin_company', 'created_at'],
    },
    traffic_ban: {
      table: 'bsk_traffic_ban', title: 'ممنوعیت تردد',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'person_name', label: 'نام فرد' },
        { key: 'issuer_order', label: 'دستور دهنده' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'person_name', 'national_id', 'issuer_order', 'description'],
    },
    companies: {
      table: 'bsk_companies', title: 'تعریف شرکت‌ها',
      fields: [
        { key: 'company_code', label: 'کد' },
        { key: 'company_name', label: 'نام شرکت', required: true },
        { key: 'is_approved', label: 'مصوب شود', type: 'bool' },
        { key: 'is_origin', label: 'شرکت مبدأ', type: 'bool' },
        { key: 'is_destination', label: 'مقصد', type: 'bool' },
        { key: 'is_evac', label: 'مکان تخلیه', type: 'bool' },
        { key: 'phone', label: 'شماره همراه' },
        { key: 'location_name', label: 'مکان' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['company_code', 'company_name', 'is_approved', 'is_origin', 'phone'],
    },
    max_tonnage: {
      table: 'bsk_max_tonnage', title: 'حداکثر تناژ پیمانکاران',
      fields: [
        { key: 'company_name', label: 'شرکت' },
        { key: 'cargo_name', label: 'نام کالا' },
        { key: 'destination_unit', label: 'واحد مقصد' },
        { key: 'amount', label: 'مقدار' },
        { key: 'warning_amount', label: 'مقدار هشدار' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['company_name', 'cargo_name', 'amount', 'warning_amount'],
    },
    settings: {
      table: 'bsk_settings', title: 'تنظیمات باسکول',
      fields: [
        { key: 'scale_name', label: 'نام باسکول', required: true },
        { key: 'scale_code', label: 'کد باسکول' },
        { key: 'center_name', label: 'نام مرکز' },
        { key: 'port_name', label: 'پورت باسکول' },
        { key: 'baud_rate', label: 'BaudRate' },
        { key: 'data_bits', label: 'Data Bits' },
        { key: 'parity_bit', label: 'Parity Bit' },
        { key: 'stop_bit', label: 'Stop Bit' },
        { key: 'region_code', label: 'کد منطقه' },
        { key: 'region_name', label: 'نام منطقه' },
        { key: 'is_active', label: 'باسکول فعال', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['scale_name', 'scale_code', 'center_name', 'port_name', 'baud_rate', 'is_active'],
    },
    weigh_reports: {
      table: 'bsk_weigh_reports', title: 'گزارش توزین',
      fields: [
        { key: 'ticket_number', label: 'شماره قبض' },
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'first_weight', label: 'توزین اول' },
        { key: 'second_weight', label: 'توزین دوم' },
        { key: 'net_weight', label: 'وزن خالص' },
        { key: 'weigh_date', label: 'تاریخ' },
        { key: 'origin_company', label: 'شرکت مبدأ' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['ticket_number', 'plate_number', 'vehicle_type', 'driver_name', 'first_weight', 'second_weight', 'net_weight', 'weigh_date'],
    },
  }


  const PELAKHWAN_VIEW_MAP = {
    process: {
      table: 'plk_process', title: 'فرم پردازش پلاک‌خوان',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate', required: true },
        { key: 'camera_name', label: 'نام دوربین' },
        { key: 'process_date', label: 'تاریخ' },
        { key: 'process_time', label: 'ساعت' },
        { key: 'direction', label: 'جهت', type: 'select', options: ['ورود', 'خروج'] },
        { key: 'confidence', label: 'اطمینان تشخیص' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['ثبت شده', 'رد شده', 'در انتظار'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'camera_name', 'process_date', 'process_time', 'direction', 'confidence', 'status'],
    },
    traffic: {
      table: 'plk_traffic', title: 'تردد پلاک‌خوان',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate', required: true },
        { key: 'camera_name', label: 'نام دوربین' },
        { key: 'entry_date', label: 'تاریخ ورود' },
        { key: 'entry_time', label: 'ساعت ورود' },
        { key: 'exit_date', label: 'تاریخ خروج' },
        { key: 'exit_time', label: 'ساعت خروج' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'gate_name', label: 'درب / گیت' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'camera_name', 'entry_date', 'entry_time', 'vehicle_type', 'gate_name'],
    },
    monitoring: {
      table: 'plk_monitoring', title: 'مانیتورینگ پلاک‌خوان',
      fields: [
        { key: 'camera_name', label: 'نام دوربین', required: true },
        { key: 'location_name', label: 'محل' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['فعال', 'غیرفعال', 'خطا'] },
        { key: 'last_read_plate', label: 'آخرین پلاک خوانده‌شده', type: 'iran_plate' },
        { key: 'last_read_time', label: 'زمان آخرین خوانش' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['camera_name', 'location_name', 'status', 'last_read_plate', 'last_read_time'],
    },
    traffic_report: {
      table: 'plk_traffic_report', title: 'گزارش تردد پلاک‌خوان',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate' },
        { key: 'report_date', label: 'تاریخ گزارش' },
        { key: 'traffic_count', label: 'تعداد تردد' },
        { key: 'gate_name', label: 'درب / گیت' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'report_date', 'traffic_count', 'gate_name'],
    },
    full_traffic_report: {
      table: 'plk_full_traffic_report', title: 'گزارش تردد کامل پلاک‌خوان',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate' },
        { key: 'from_date', label: 'از تاریخ' },
        { key: 'to_date', label: 'تا تاریخ' },
        { key: 'total_entries', label: 'کل ورود' },
        { key: 'total_exits', label: 'کل خروج' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'from_date', 'to_date', 'total_entries', 'total_exits'],
    },
    access_level: {
      table: 'plk_access_level_report', title: 'گزارش سطح دسترسی خودروها',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate', required: true },
        { key: 'access_level', label: 'سطح دسترسی', type: 'select', options: ['مجاز', 'محدود', 'ممنوع'] },
        { key: 'vehicle_owner', label: 'مالک خودرو' },
        { key: 'unit_name', label: 'واحد' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'access_level', 'vehicle_owner', 'unit_name'],
    },
    inside_vehicles: {
      table: 'plk_inside_vehicles', title: 'گزارش خودروهای داخل سازمان',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate', required: true },
        { key: 'entry_time', label: 'ساعت ورود' },
        { key: 'camera_name', label: 'دوربین' },
        { key: 'duration', label: 'مدت حضور' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['داخل سازمان', 'خارج شده'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'entry_time', 'camera_name', 'duration', 'status'],
    },
    parking: {
      table: 'plk_parking', title: 'فرم پارکینگ',
      fields: [
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate', required: true },
        { key: 'parking_zone', label: 'منطقه پارکینگ' },
        { key: 'slot_number', label: 'شماره جای پارک' },
        { key: 'entry_date', label: 'تاریخ ورود' },
        { key: 'entry_time', label: 'ساعت ورود' },
        { key: 'exit_time', label: 'ساعت خروج' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['پارک شده', 'خالی', 'رزرو'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['plate_number', 'parking_zone', 'slot_number', 'entry_date', 'entry_time', 'status'],
    },
    cameras: {
      table: 'plk_cameras', title: 'تعریف دوربین‌های پلاک‌خوان',
      fields: [
        { key: 'camera_name', label: 'نام دوربین', required: true },
        { key: 'camera_code', label: 'کد دوربین' },
        { key: 'location_name', label: 'محل نصب' },
        { key: 'ip_address', label: 'آدرس IP' },
        { key: 'direction', label: 'جهت', type: 'select', options: ['ورود', 'خروج', 'دوطرفه'] },
        { key: 'is_active', label: 'فعال', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['camera_name', 'camera_code', 'location_name', 'ip_address', 'direction', 'is_active'],
    },
    online_monitor: {
      table: 'plk_online_monitor', title: 'مانیتورینگ آنلاین پلاک‌خوان',
      fields: [
        { key: 'camera_name', label: 'نام دوربین' },
        { key: 'live_plate', label: 'پلاک لحظه‌ای', type: 'iran_plate' },
        { key: 'event_time', label: 'زمان رویداد' },
        { key: 'event_type', label: 'نوع رویداد', type: 'select', options: ['تشخیص', 'ورود', 'خروج', 'هشدار'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['camera_name', 'live_plate', 'event_time', 'event_type'],
    },
  }


  const ACCESS_VIEW_MAP = {
    traffic: {
      table: 'ac_traffic', title: 'فرم تردد RFID',
      fields: [
        { key: 'person_type', label: 'نوع', type: 'select', options: ['پرسنل', 'پیمانکار', 'مهمان'] },
        { key: 'plate_number', label: 'شماره پلاک', type: 'iran_plate' },
        { key: 'personnel_code', label: 'کد پرسنلی' },
        { key: 'card_code', label: 'کد کارت' },
        { key: 'first_name', label: 'نام' },
        { key: 'last_name', label: 'نام خانوادگی' },
        { key: 'company_unit', label: 'شرکت/واحد' },
        { key: 'door_name', label: 'نام درب' },
        { key: 'traffic_date', label: 'تاریخ' },
        { key: 'traffic_time', label: 'ساعت' },
        { key: 'vehicle_type', label: 'نوع خودرو' },
        { key: 'driver_name', label: 'نام راننده' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['first_name', 'last_name', 'card_code', 'traffic_date', 'traffic_time', 'company_unit', 'door_name', 'plate_number'],
    },
    access_def: {
      table: 'ac_access_def', title: 'تعریف دسترسی',
      fields: [
        { key: 'def_type', label: 'نوع تعریف', type: 'select', options: ['محدوده زمانی', 'ساعت دسترسی', 'محدوده دسترسی', 'مجموعه دسترسی'] },
        { key: 'code', label: 'کد' },
        { key: 'name', label: 'نام', required: true },
        { key: 'time_from', label: 'از زمان' },
        { key: 'time_to', label: 'تا زمان' },
        { key: 'access_hour', label: 'ساعت دسترسی' },
        { key: 'zone_name', label: 'محدوده / ناحیه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['code', 'name', 'def_type', 'time_from', 'time_to'],
    },
    guests: {
      table: 'ac_guests', title: 'مهمان',
      fields: [
        { key: 'first_name', label: 'نام', required: true },
        { key: 'last_name', label: 'نام خانوادگی' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'host_name', label: 'میزبان' },
        { key: 'visit_date', label: 'از تاریخ' },
        { key: 'visit_to_date', label: 'تا تاریخ' },
        { key: 'access_group', label: 'مجموعه دسترسی' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['first_name', 'last_name', 'national_id', 'host_name', 'visit_date', 'access_group'],
    },
    guest_cards: {
      table: 'ac_guest_cards', title: 'کارت مهمان‌ها',
      fields: [
        { key: 'card_type', label: 'نوع کارت' },
        { key: 'card_code', label: 'کد کارت' },
        { key: 'card_number', label: 'شماره کارت' },
        { key: 'restriction_type', label: 'نوع محدودیت' },
        { key: 'access_group', label: 'مجموعه دسترسی' },
        { key: 'from_date', label: 'از تاریخ' },
        { key: 'to_date', label: 'تا تاریخ' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['card_code', 'card_number', 'from_date', 'to_date', 'access_group'],
    },
    guest_zone: {
      table: 'ac_guest_traffic_zone', title: 'محدوده تردد مهمان',
      fields: [
        { key: 'zone_name', label: 'نام محدوده تردد', required: true },
        { key: 'door_name', label: 'نام درب' },
        { key: 'device_code', label: 'کد دستگاه' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['zone_name', 'door_name', 'device_code'],
    },
    guest_delivered: {
      table: 'ac_guest_delivered_cards', title: 'کارت‌های تحویل‌شده مهمان',
      fields: [
        { key: 'card_number', label: 'شماره کارت' },
        { key: 'guest_name', label: 'نام مهمان' },
        { key: 'deliver_date', label: 'تاریخ تحویل' },
        { key: 'deliver_time', label: 'ساعت' },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['تحویل شده', 'برگشت داده شده'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['card_number', 'guest_name', 'deliver_date', 'status'],
    },
    guest_report: {
      table: 'ac_guest_traffic_report', title: 'گزارش تردد مهمانان',
      fields: [
        { key: 'guest_name', label: 'نام' },
        { key: 'last_name', label: 'نام خانوادگی' },
        { key: 'card_number', label: 'شماره کارت' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'terminal_name', label: 'نام ترمینال' },
        { key: 'traffic_date', label: 'تاریخ' },
        { key: 'entry_time', label: 'ساعت ورود' },
        { key: 'exit_time', label: 'ساعت خروج' },
        { key: 'unit_name', label: 'واحد' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['guest_name', 'last_name', 'card_number', 'traffic_date', 'entry_time', 'terminal_name'],
    },
    assign: {
      table: 'ac_assign', title: 'فرم تخصیص',
      fields: [
        { key: 'person_type', label: 'نوع', type: 'select', options: ['پرسنل', 'پیمانکار', 'مهمان'] },
        { key: 'person_code', label: 'کد' },
        { key: 'first_name', label: 'نام' },
        { key: 'last_name', label: 'نام خانوادگی' },
        { key: 'national_id', label: 'کد ملی' },
        { key: 'display_name', label: 'نام نمایشی آنلاین' },
        { key: 'access_group', label: 'مجموعه دسترسی' },
        { key: 'card_code', label: 'کد کارت' },
        { key: 'pin_code', label: 'پین کد' },
        { key: 'auth_type', label: 'نوع احراز هویت' },
        { key: 'access_level', label: 'سطح دسترسی' },
        { key: 'issue_date', label: 'تاریخ صدور' },
        { key: 'expire_date', label: 'تاریخ انقضا' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['person_code', 'first_name', 'last_name', 'national_id', 'access_group', 'issue_date'],
    },
    terminals: {
      table: 'ac_terminals', title: 'ترمینال‌ها',
      fields: [
        { key: 'device_name', label: 'نام دستگاه', required: true },
        { key: 'ip_address', label: 'IP' },
        { key: 'mac_address', label: 'MAC Address' },
        { key: 'serial_number', label: 'شماره سریال' },
        { key: 'group_name', label: 'نام گروه' },
        { key: 'device_type', label: 'نوع دستگاه' },
        { key: 'is_active', label: 'فعال', type: 'bool' },
        { key: 'is_online', label: 'آنلاین', type: 'bool' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['device_name', 'ip_address', 'mac_address', 'serial_number', 'group_name', 'is_active', 'is_online'],
    },
    terminal_status: {
      table: 'ac_terminal_status', title: 'وضعیت ترمینال‌ها',
      fields: [
        { key: 'device_name', label: 'نام دستگاه', required: true },
        { key: 'status', label: 'وضعیت', type: 'select', options: ['آنلاین', 'آفلاین', 'خطا'] },
        { key: 'last_sync', label: 'آخرین همسان‌سازی' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['device_name', 'status', 'last_sync'],
    },
    user_sync: {
      table: 'ac_user_sync', title: 'همسان‌سازی کاربران',
      fields: [
        { key: 'user_code', label: 'کد کاربر' },
        { key: 'user_name', label: 'نام کاربر' },
        { key: 'last_name', label: 'نام خانوادگی' },
        { key: 'access_level', label: 'سطح دسترسی' },
        { key: 'person_type', label: 'نوع', type: 'select', options: ['پرسنل', 'پیمانکار', 'مهمان'] },
        { key: 'sync_status', label: 'وضعیت همسان‌سازی', type: 'select', options: ['در انتظار', 'همسان‌سازی شده', 'خطا'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['user_code', 'user_name', 'last_name', 'access_level', 'person_type', 'sync_status'],
    },
    general_report: {
      table: 'ac_general_report', title: 'گزارشات کلی',
      fields: [
        { key: 'report_title', label: 'عنوان گزارش' },
        { key: 'report_date', label: 'تاریخ' },
        { key: 'person_name', label: 'نام فرد' },
        { key: 'event_type', label: 'نوع رویداد', type: 'select', options: ['ورود', 'خروج', 'رد دسترسی', 'هشدار'] },
        { key: 'door_name', label: 'نام درب' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['report_title', 'report_date', 'person_name', 'event_type', 'door_name'],
    },
  }


  const WORKFLOW_VIEW_MAP = {
    request_types: {
      table: 'wf_request_types', title: 'انواع درخواست',
      fields: [
        { key: 'request_type', label: 'نوع درخواست', required: true },
        { key: 'approver_count', label: 'تعداد کاربران تاییدکننده' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['request_type', 'approver_count', 'notes'],
    },
    approvers: {
      table: 'wf_approvers', title: 'تاییدکننده درخواست',
      fields: [
        { key: 'request_type', label: 'نوع درخواست', required: true },
        { key: 'approver_name', label: 'نام کاربر تاییدکننده' },
        { key: 'approver_username', label: 'نام کاربری تاییدکننده' },
        { key: 'user_order', label: 'ترتیب کاربر' },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['request_type', 'approver_name', 'approver_username', 'user_order'],
    },
    delegation: {
      table: 'wf_delegation', title: 'تفویض اختیار',
      fields: [
        { key: 'request_type', label: 'نوع درخواست' },
        { key: 'from_user', label: 'نام کاربر تاییدکننده' },
        { key: 'from_username', label: 'نام کاربری تاییدکننده' },
        { key: 'to_user', label: 'نام کاربر جایگزین' },
        { key: 'access_levels', label: 'سطوح دسترسی' },
        { key: 'date_from', label: 'از تاریخ' },
        { key: 'date_to', label: 'تا تاریخ' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['request_type', 'from_user', 'from_username', 'to_user', 'date_from', 'date_to'],
    },
    parking_docs: {
      table: 'wf_parking_docs', title: 'تاییدات پارکینگ و خروج مدارک',
      fields: [
        { key: 'request_type', label: 'نوع درخواست', required: true },
        { key: 'company_name', label: 'شرکت' },
        { key: 'personnel_name', label: 'پرسنل تاییدکننده' },
        { key: 'approval_stage', label: 'مرحله تایید', type: 'select', options: ['مرحله اول', 'مرحله دوم', 'مرحله سوم'] },
        { key: 'notes', label: 'توضیحات' },
      ],
      columns: ['request_type', 'personnel_name', 'approval_stage', 'company_name'],
    },
  }

  const loadPymReport = (kind = pymReportKind, q = pymReportQ, companyName = pymReportCompany) => {
    setPymReportLoading(true)
    setPymReportMsg('')
    const params = new URLSearchParams({ kind: kind || 'summary', limit: '5000' })
    if (q) params.set('q', q)
    if (companyName) params.set('company_name', companyName)
    fetch(`/api/peymankar/report?${params.toString()}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.detail) throw new Error(typeof d.detail === 'string' ? d.detail : 'خطا')
        setPymReportData(d)
        setPymReportMsg(d.count != null ? `${d.count} ردیف` : '')
      })
      .catch((e) => {
        setPymReportData(null)
        setPymReportMsg(e.message || 'خطا در دریافت گزارش')
      })
      .finally(() => setPymReportLoading(false))
  }

  const loadLookup = (viewKey, mapSource = 'base') => {
    const named = LOOKUP_VIEW_MAP[viewKey]
    const ent = mapSource === 'entezamat' ? ENTEZAMAT_VIEW_MAP[viewKey]
      : mapSource === 'card' ? CARD_VIEW_MAP[viewKey]
      : mapSource === 'peymankar' ? PEYMANKAR_VIEW_MAP[viewKey]
      : mapSource === 'patrol' ? PATROL_VIEW_MAP[viewKey]
      : mapSource === 'herasat' ? HERASAT_VIEW_MAP[viewKey]
      : mapSource === 'monaghese' ? MONAGHESE_VIEW_MAP[viewKey]
      : mapSource === 'kartabl' ? KARTABL_VIEW_MAP[viewKey]
      : mapSource === 'baskool' ? BASKOOL_VIEW_MAP[viewKey]
      : mapSource === 'pelakhwan' ? PELAKHWAN_VIEW_MAP[viewKey]
      : mapSource === 'access' ? ACCESS_VIEW_MAP[viewKey]
      : mapSource === 'workflow' ? WORKFLOW_VIEW_MAP[viewKey]
      : ENTITY_VIEW_MAP[viewKey]
    if (named && mapSource !== 'entezamat' && mapSource !== 'card' && mapSource !== 'peymankar' && mapSource !== 'patrol' && mapSource !== 'herasat' && mapSource !== 'monaghese' && mapSource !== 'kartabl' && mapSource !== 'baskool' && mapSource !== 'pelakhwan' && mapSource !== 'access' && mapSource !== 'workflow') {
      fetch(`/api/lookups/${named.table}`)
        .then((r) => r.json())
        .then((d) => setLookupItems(Array.isArray(d) ? d : []))
        .catch(() => setLookupItems([]))
      return
    }
    if (ent) {
      fetch(`/api/baseinfo/${ent.table}`)
        .then((r) => r.json())
        .then((d) => setLookupItems(Array.isArray(d) ? d : []))
        .catch(() => setLookupItems([]))
    }
  }

  const loadDependents = (p) => {
    if (!p) { setDependents([]); return }
    const code = p.company_code || ''
    fetch(`/api/dependents?company_code=${encodeURIComponent(code)}&personnel_id=${p.id}`)
      .then((r) => r.json())
      .then((d) => setDependents(Array.isArray(d) ? d : []))
      .catch(() => setDependents([]))
  }

  const PERSONNEL_RECORD_META = {
    service: {
      title: 'سوابق خدماتی',
      fields: [
        { key: 'from_date', label: 'از تاریخ', type: 'date' },
        { key: 'to_date', label: 'تا تاریخ', type: 'date' },
        { key: 'organization', label: 'سازمان / محل خدمت' },
        { key: 'position', label: 'سمت' },
        { key: 'unit_name', label: 'واحد' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['from_date', 'to_date', 'organization', 'position', 'unit_name'],
    },
    travel: {
      title: 'سفر خارجی',
      fields: [
        { key: 'country', label: 'کشور مقصد' },
        { key: 'from_date', label: 'از تاریخ', type: 'date' },
        { key: 'to_date', label: 'تا تاریخ', type: 'date' },
        { key: 'purpose', label: 'هدف سفر' },
        { key: 'visa_no', label: 'شماره ویزا' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['country', 'from_date', 'to_date', 'purpose', 'visa_no'],
    },
    medical: {
      title: 'سوابق پزشکی',
      fields: [
        { key: 'record_date', label: 'تاریخ', type: 'date' },
        { key: 'record_type', label: 'نوع سابقه' },
        { key: 'diagnosis', label: 'تشخیص / موضوع' },
        { key: 'physician', label: 'پزشک / مرکز' },
        { key: 'description', label: 'توضیحات' },
      ],
      columns: ['record_date', 'record_type', 'diagnosis', 'physician'],
    },
  }

  const loadPersonnelRecords = (person, kind) => {
    if (!person || !kind) return
    const code = person.company_code
    fetch(`/api/personnel-records/${kind}?company_code=${encodeURIComponent(code)}&personnel_id=${person.id}`)
      .then((r) => r.json())
      .then((d) => setPersonnelRecords(Array.isArray(d) ? d : []))
      .catch(() => setPersonnelRecords([]))
  }

  const openPersonnelRecords = (kind, title) => {
    const person = requireSelectedPersonnel(title)
    if (!person) return
    setShowRegisterForm(false)
    setShowDependents(false)
    setShowCards(false)
    setPersonnelRecordKind(kind)
    setEditingRecId(null)
    setRecForm({})
    setRecMsg('')
    loadPersonnelRecords(person, kind)
  }

  const loadCards = (p) => {
    if (!p) { setCards([]); return }
    const code = p.company_code || ''
    fetch(`/api/cards?company_code=${encodeURIComponent(code)}&personnel_id=${p.id}`)
      .then((r) => r.json())
      .then((d) => setCards(Array.isArray(d) ? d : []))
      .catch(() => setCards([]))
  }


  // جستجوی پرسنل با تأخیر کوتاه تا با هر حرف درخواست نرود
  useEffect(() => {
    const t = setTimeout(() => {
      const next = (searchInput || '').trim()
      if (next !== searchQuery) {
        setPersonnelPage(1)
        setSearchQuery(next)
      }
    }, 350)
    return () => clearTimeout(t)
  }, [searchInput])

  // بارگذاری داده‌های مرجع بعد از paint تا کلیک برگه فوری بماند
  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'personnel') {
        loadCompanies()
        loadUnits()
        loadEduFields()
        loadRespGroups()
        loadEmpTypes()
      } else if (activeTab === 'companies') {
        loadCompanies()
      } else if (activeTab === 'baseinfo') {
        loadUnits()
        loadEduFields()
        loadRespGroups()
        loadEmpTypes()
        loadCompanies()
        loadShiftRefs()
        if (LOOKUP_VIEW_MAP[baseSubView] || ENTITY_VIEW_MAP[baseSubView]) loadLookup(baseSubView)
      }
    })
  }, [activeTab])

  // لیست پرسنل: بعد از paint تا تعویض برگه سریع بماند
  useEffect(() => {
    if (activeTab !== 'personnel') return
    const ac = new AbortController()
    const cancelPaint = scheduleAfterPaint(() => {
      ;(async () => {
        setPersonnelLoading(true)
        const { limit, offset } = getPersonnelLimitOffset(personnelPage, personnelPageSize)
        const params = new URLSearchParams({
          limit: String(limit),
          offset: String(offset),
        })
        if (searchQuery) params.set('q', searchQuery)
        try {
          let response = await fetch(`/api/admin/personnel?${params.toString()}`, { signal: ac.signal })
          if (!response.ok) {
            response = await fetch(`/api/personnel?${params.toString()}`, { signal: ac.signal })
          }
          if (!response.ok) throw new Error(`Personnel request failed: ${response.status}`)
          const data = await response.json()
          if (ac.signal.aborted) return
          setPersonnel(data.items || [])
          setPersonnelTotal(data.total || 0)
          setPersonnelScopeNote(
            data.database_errors?.length ? 'برخی دیتابیس‌ها در دسترس نبودند.' : ''
          )
          const total = data.total || 0
          if (personnelPageSize !== 'all' && personnelPage > 1 && (data.items || []).length === 0 && total > 0) {
            const lastPage = Math.max(1, Math.ceil(total / Number(personnelPageSize)))
            setPersonnelPage(Math.min(personnelPage - 1, lastPage))
          }
        } catch (error) {
          if (error?.name === 'AbortError') return
          setPersonnel([])
          setPersonnelTotal(0)
          setPersonnelScopeNote('دریافت فهرست پرسنل با خطا مواجه شد.')
        } finally {
          if (!ac.signal.aborted) setPersonnelLoading(false)
        }
      })()
    })
    return () => {
      ac.abort()
      cancelPaint()
    }
  }, [activeTab, searchQuery, personnelPage, personnelPageSize])

  useEffect(() => {
    if (activeTab === 'baseinfo' && (LOOKUP_VIEW_MAP[baseSubView] || ENTITY_VIEW_MAP[baseSubView])) {
      setLookupName('')
      setLookupDesc('')
      setLookupMsg('')
      loadLookup(baseSubView)
    }
  }, [baseSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'entezamat' && ENTEZAMAT_VIEW_MAP[entezamatSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(entezamatSubView, 'entezamat')
        loadShiftRefs()
      }
    })
  }, [activeTab, entezamatSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'sodor_kart' && CARD_VIEW_MAP[cardSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(cardSubView, 'card')
      }
    })
  }, [activeTab, cardSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'peymankar' || activeTab === 'mojaz') {
        loadCompanies()
        if (typeof loadBaseClientCompanies === 'function') loadBaseClientCompanies()
      }
      if (activeTab === 'peymankar') {
        loadCtrCompanies()
      }
      if (activeTab === 'peymankar' && peymankarSubView === 'report') {
        loadPymReport(pymReportKind || 'summary')
      }
      if (activeTab === 'peymankar' && PEYMANKAR_VIEW_MAP[peymankarSubView]) {
        setLookupMsg('')
        setEntityForm({})
        setEditingEntityId(null)
        loadLookup(peymankarSubView, 'peymankar')
      }
    })
  }, [activeTab, peymankarSubView])

  // تب صدور مجوز تردد: پیش‌فرض لیست و تأیید مجوزها — بارگذاری خودکار لیست
  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'mojaz' && (mojazSubView === 'list' || mojazSubView === 'report')) {
        loadMjzPermits({ q: (mjzSearchNo || '').trim() || undefined })
      }
    })
  }, [activeTab, mojazSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'monitoring' && PATROL_VIEW_MAP[patrolSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(patrolSubView, 'patrol')
      }
    })
  }, [activeTab, patrolSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'herasat' && HERASAT_VIEW_MAP[herasatSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(herasatSubView, 'herasat')
      }
    })
  }, [activeTab, herasatSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'monaghese' && MONAGHESE_VIEW_MAP[monagheseSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(monagheseSubView, 'monaghese')
      }
    })
  }, [activeTab, monagheseSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'kartabl' && KARTABL_VIEW_MAP[kartablSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(kartablSubView, 'kartabl')
      }
    })
  }, [activeTab, kartablSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'baskool' && BASKOOL_VIEW_MAP[baskoolSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(baskoolSubView, 'baskool')
      }
    })
  }, [activeTab, baskoolSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'pelakhwan' && PELAKHWAN_VIEW_MAP[pelakhwanSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(pelakhwanSubView, 'pelakhwan')
      }
    })
  }, [activeTab, pelakhwanSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'access' && ACCESS_VIEW_MAP[accessSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(accessSubView, 'access')
      }
    })
  }, [activeTab, accessSubView])

  useEffect(() => {
    return scheduleAfterPaint(() => {
      if (activeTab === 'workflow' && WORKFLOW_VIEW_MAP[workflowSubView]) {
        setLookupMsg('')
        setEntityForm({})
        loadLookup(workflowSubView, 'workflow')
      }
    })
  }, [activeTab, workflowSubView])


  const handleLogin = async (e) => {
    e?.preventDefault?.()
    const u = (loginUser || '').trim()
    const pw = loginPass || ''
    if (!u || !pw) {
      setLoginError('نام کاربری و رمز عبور را وارد کنید')
      return
    }
    setLoginError('')
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: u, password: pw }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setLoginError(typeof data.detail === 'string' ? data.detail : 'نام کاربری یا رمز عبور نادرست است')
        return
      }
      const user = data.user || {}
      setCurrentUser({
        role: user.role || 'user',
        username: user.username || u,
        full_name: user.full_name || user.username || u,
        can_see_all_companies: !!user.can_see_all_companies,
        company_code: user.company_code,
        access_level_id: user.access_level_id,
      })
      const perms = data.permissions || {
        is_full_admin: user.role === 'admin' || user.username === 'AdminUser',
        tabs: [],
        actions: [],
      }
      applyPermissions(perms)
      try {
        sessionStorage.setItem('dejban_auth', '1')
        sessionStorage.setItem('dejban_user', JSON.stringify(user))
      } catch {}
      setIsLoggedIn(true)
    } catch (err) {
      // اگر API در دسترس نبود، فقط AdminUser محلی
      if (u === 'AdminUser' && pw === 'AdminUser') {
        setCurrentUser({
          role: 'admin',
          username: 'AdminUser',
          full_name: 'مدیر سیستم',
          can_see_all_companies: true,
        })
        applyPermissions({ is_full_admin: true, tabs: [], actions: [] })
        try { sessionStorage.setItem('dejban_auth', '1') } catch {}
        setIsLoggedIn(true)
        return
      }
      setLoginError('خطا در ارتباط با سرور — بک‌اند را بررسی کنید')
    }
  }

  useEffect(() => {
    if (!showUserMenu) return
    const onDoc = (ev) => {
      // اگر کلیک داخل منوی کاربر بود، نبند (دکمه خروج باید کار کند)
      const menu = document.getElementById('user-account-menu')
      if (menu && menu.contains(ev.target)) return
      setShowUserMenu(false)
    }
    const tmr = setTimeout(() => document.addEventListener('click', onDoc), 0)
    return () => {
      clearTimeout(tmr)
      document.removeEventListener('click', onDoc)
    }
  }, [showUserMenu])

  const handleLogout = (e) => {
    if (e) {
      e.preventDefault?.()
      e.stopPropagation?.()
    }
    try { sessionStorage.removeItem('dejban_auth'); sessionStorage.removeItem('dejban_user') } catch {}
    setShowUserMenu(false)
    setLoginUser('')
    setLoginPass('')
    setLoginError('')
    setCardPrintPerson(null)
    setCurrentUser({
      role: 'admin',
      username: '',
      full_name: '',
      can_see_all_companies: true,
    })
    // خروج قطعی → صفحه ورود
    setIsLoggedIn(false)
    setUserPerms({ is_full_admin: false, tabs: [], actions: [] })
    try { sessionStorage.removeItem('dejban_perms') } catch {}
  }

  const applyPermissions = (perms) => {
    const normalized = {
      is_full_admin: !!perms?.is_full_admin,
      tabs: Array.isArray(perms?.tabs) ? perms.tabs.map(String) : [],
      actions: Array.isArray(perms?.actions) ? perms.actions.map(String) : [],
    }
    setUserPerms(normalized)
    try { sessionStorage.setItem('dejban_perms', JSON.stringify(normalized)) } catch {}
    // اگر تب فعلی مجاز نیست، اولین تب مجاز را باز کن
    if (!normalized.is_full_admin) {
      const allowed = TABS.filter((tb) => normalized.tabs.includes(tb.id))
      if (allowed.length) {
        setActiveTab((cur) => (normalized.tabs.includes(cur) ? cur : allowed[0].id))
      }
    }
    return normalized
  }

  const canAccessTab = (tabId) => {
    if (!tabId) return true
    if (userPerms?.is_full_admin) return true
    // AdminUser کامل
    if (currentUser?.username === 'AdminUser') return true
    return (userPerms?.tabs || []).includes(tabId)
  }

  const canAccessAction = (code) => {
    if (!code) return true
    if (userPerms?.is_full_admin) return true
    if (currentUser?.username === 'AdminUser') return true
    // اکشن‌های سیستمی عمومی
    if (String(code).startsWith('SYS_')) return true
    const actions = userPerms?.actions || []
    // اگر برای این تب هیچ اکشنی تعریف نشده ولی خود تب مجاز است، همه اکشن‌های تب را آزاد بگذار
    const meta = ACTION_BY_CODE[code]
    if (meta?.tab && canAccessTab(meta.tab)) {
      const tabActions = actions.filter((c) => ACTION_BY_CODE[c]?.tab === meta.tab)
      if (tabActions.length === 0) return true
      return actions.includes(code)
    }
    return actions.includes(code)
  }

  const filterRibbonGroups = (groups) => {
    if (!groups) return []
    if (userPerms?.is_full_admin || currentUser?.username === 'AdminUser') return groups
    return groups
      .map((g) => {
        const items = (g.items || [])
          .map((item) => {
            if (item.type === 'large') {
              return canAccessAction(item.code) ? item : null
            }
            if (item.type === 'stack') {
              const buttons = (item.buttons || []).filter((b) => canAccessAction(b.code))
              if (!buttons.length) return null
              return { ...item, buttons }
            }
            return item
          })
          .filter(Boolean)
        if (!items.length) return null
        return { ...g, items }
      })
      .filter(Boolean)
  }

  const isFullAdmin = !!(userPerms?.is_full_admin || currentUser?.username === 'AdminUser')

  const visibleTabs = useMemo(
    () => (isFullAdmin ? TABS : TABS.filter((tb) => canAccessTab(tb.id))),
    [isFullAdmin, userPerms, currentUser]
  )

  const ribbonGroups = useMemo(() => {
    const groups = RIBBONS[activeTab] || []
    if (isFullAdmin) return groups
    return filterRibbonGroups(groups)
  }, [activeTab, isFullAdmin, userPerms, currentUser])

  /** بارگذاری کامل پرسنل (با عکس) برای چاپ کارت PVC */
  const openIdCardPrint = async (person) => {
    const base = person || selectedPersonnel
    if (!base) {
      window.alert('ابتدا یک پرسنل را از لیست انتخاب کنید')
      return
    }
    setCardPrintLoading(true)
    try {
      const code = base.company_code
      const id = base.id
      let full = { ...base }
      if (id != null) {
        const q = code != null ? `?company_code=${encodeURIComponent(code)}` : ''
        const res = await fetch(`/api/personnel/${id}${q}`)
        if (res.ok) {
          const data = await res.json()
          full = { ...base, ...data }
        }
      }
      setCardPrintPerson(full)
      setCardPrintSide('both')
    } catch (err) {
      setCardPrintPerson({ ...base })
    } finally {
      setCardPrintLoading(false)
    }
  }

  // همگام‌سازی سایز کارت با CSS هنگام تغییر
  useEffect(() => {
    const s = PVC_CARD_SIZES.find((x) => x.id === cardPrintSizeId) || PVC_CARD_SIZES[0]
    const w = `${Number(s.wMm).toFixed(2)}mm`
    const h = `${Number(s.hMm).toFixed(2)}mm`
    document.documentElement.style.setProperty('--pvc-w', w)
    document.documentElement.style.setProperty('--pvc-h', h)
  }, [cardPrintSizeId])

  const applyPvcCardSize = (size) => {
    const s = size || cardPrintSize || PVC_CARD_SIZES[0]
    const w = `${Number(s.wMm).toFixed(2)}mm`
    const h = `${Number(s.hMm).toFixed(2)}mm`
    const root = document.documentElement
    root.style.setProperty('--pvc-w', w)
    root.style.setProperty('--pvc-h', h)
    // استایل پویا برای @page هنگام چاپ
    let el = document.getElementById('pvc-print-page-style')
    if (!el) {
      el = document.createElement('style')
      el.id = 'pvc-print-page-style'
      document.head.appendChild(el)
    }
    el.textContent = `
      @media print {
        @page { size: ${w} ${h}; margin: 0 !important; padding: 0 !important; }
        html, body {
          width: ${w} !important;
          height: ${h} !important;
        }
        #pvc-print-root {
          width: ${w} !important;
        }
        #pvc-print-root .pvc-card {
          width: ${w} !important;
          height: ${h} !important;
          min-width: ${w} !important;
          min-height: ${h} !important;
          max-width: ${w} !important;
          max-height: ${h} !important;
        }
      }
    `
  }

  const doPrintIdCard = (side) => {
    setCardPrintSide(side)
    applyPvcCardSize(cardPrintSize)
    const prevTitle = document.title
    const s = cardPrintSize || PVC_CARD_SIZES[0]
    document.title = `PVC-${s.id}-${Number(s.wMm).toFixed(2)}x${Number(s.hMm).toFixed(2)}`
    setTimeout(() => {
      try {
        window.print()
      } finally {
        setTimeout(() => { document.title = prevTitle }, 500)
      }
    }, 180)
  }

  const refreshBackupList = () => {
    fetch('/api/admin/backups')
      .then((r) => r.json())
      .then((d) => setBackupList(d.items || []))
      .catch(() => setBackupList([]))
  }

  const loadAccessLevels = () => {
    fetch('/api/admin/access-levels')
      .then((r) => r.json())
      .then((d) => setAccessLevels(d.items || []))
      .catch(() => setAccessLevels([]))
  }

  const loadSysUsers = () => {
    fetch('/api/admin/users')
      .then((r) => r.json())
      .then((d) => setSysUsers(d.items || []))
      .catch(() => setSysUsers([]))
  }

  const resetLevelForm = () => {
    setEditingLevelId(null)
    setLevelForm({ name: '', description: '', is_full_admin: false, is_active: true, tabs: [], actions: [] })
    setShowLevelForm(false)
    setAccessLevelMsg('')
  }

  const openLevelEdit = (lv) => {
    setEditingLevelId(lv.id)
    setLevelForm({
      name: lv.name || '',
      description: lv.description || '',
      is_full_admin: !!lv.is_full_admin,
      is_active: lv.is_active !== false,
      tabs: [...(lv.tabs || [])],
      actions: [...(lv.actions || [])],
    })
    setShowLevelForm(true)
    setAccessLevelMsg('')
  }

  const toggleLevelTab = (tabId) => {
    setLevelForm((prev) => {
      const has = prev.tabs.includes(tabId)
      const tabs = has ? prev.tabs.filter((t) => t !== tabId) : [...prev.tabs, tabId]
      // حذف اکشن‌های تب حذف‌شده
      const actions = has
        ? prev.actions.filter((code) => {
            const meta = ACTION_BY_CODE[code]
            return meta?.tab !== tabId
          })
        : prev.actions
      return { ...prev, tabs, actions }
    })
  }

  const toggleLevelAction = (code) => {
    setLevelForm((prev) => {
      const has = prev.actions.includes(code)
      return {
        ...prev,
        actions: has ? prev.actions.filter((c) => c !== code) : [...prev.actions, code],
      }
    })
  }

  const selectAllActionsForTab = (tabId) => {
    const codes = RIBBON_CATALOG.filter((a) => a.tab === tabId).map((a) => a.code)
    setLevelForm((prev) => {
      const set = new Set(prev.actions)
      codes.forEach((c) => set.add(c))
      const tabs = prev.tabs.includes(tabId) ? prev.tabs : [...prev.tabs, tabId]
      return { ...prev, tabs, actions: [...set] }
    })
  }

  const clearActionsForTab = (tabId) => {
    setLevelForm((prev) => ({
      ...prev,
      actions: prev.actions.filter((code) => ACTION_BY_CODE[code]?.tab !== tabId),
    }))
  }

  const saveAccessLevel = () => {
    if (!levelForm.name.trim()) {
      setAccessLevelMsg('نام سطح دسترسی الزامی است')
      return
    }
    const body = {
      name: levelForm.name.trim(),
      description: levelForm.description || '',
      is_full_admin: !!levelForm.is_full_admin,
      is_active: !!levelForm.is_active,
      tabs: levelForm.is_full_admin ? [] : levelForm.tabs,
      actions: levelForm.is_full_admin ? [] : levelForm.actions,
    }
    const url = editingLevelId
      ? `/api/admin/access-levels/${editingLevelId}`
      : '/api/admin/access-levels'
    const method = editingLevelId ? 'PUT' : 'POST'
    fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(async (r) => {
        const d = await r.json()
        if (!r.ok) throw new Error(d.detail || 'خطا در ذخیره')
        setAccessLevelMsg(editingLevelId ? 'سطح دسترسی به‌روزرسانی شد' : 'سطح دسترسی ایجاد شد')
        loadAccessLevels()
        resetLevelForm()
      })
      .catch((err) => setAccessLevelMsg(err.message || 'خطا'))
  }

  const deleteAccessLevel = (id, name) => {
    if (!window.confirm(`حذف سطح دسترسی «${name}»؟`)) return
    fetch(`/api/admin/access-levels/${id}`, { method: 'DELETE' })
      .then(async (r) => {
        const d = await r.json()
        if (!r.ok) throw new Error(d.detail || 'خطا')
        setAccessLevelMsg('حذف شد')
        loadAccessLevels()
      })
      .catch((err) => setAccessLevelMsg(err.message || 'خطا'))
  }

  const resetUserForm = () => {
    setEditingUserId(null)
    setUserForm({
      username: '', password: '', full_name: '', access_level_id: '', company_code: '100',
      is_active: true, can_see_all_companies: false,
    })
    setShowUserForm(false)
    setSysUserMsg('')
  }

  const openUserEdit = (u) => {
    setEditingUserId(u.id)
    setUserForm({
      username: u.username || '',
      password: '',
      full_name: u.full_name || '',
      access_level_id: u.access_level_id != null ? String(u.access_level_id) : '',
      company_code: u.company_code != null ? String(u.company_code) : '100',
      is_active: u.is_active !== false,
      can_see_all_companies: !!u.can_see_all_companies,
    })
    setShowUserForm(true)
    setSysUserMsg('')
  }

  const saveSysUser = () => {
    if (!userForm.username.trim()) {
      setSysUserMsg('نام کاربری الزامی است')
      return
    }
    const body = {
      username: userForm.username.trim(),
      full_name: userForm.full_name || '',
      company_code: userForm.company_code || '100',
      is_active: !!userForm.is_active,
      can_see_all_companies: !!userForm.can_see_all_companies,
    }
    if (userForm.password) body.password = userForm.password
    if (userForm.access_level_id === '' || userForm.access_level_id == null) {
      if (editingUserId) body.clear_access_level = true
      else body.access_level_id = null
    } else {
      body.access_level_id = parseInt(userForm.access_level_id, 10)
    }
    const url = editingUserId ? `/api/admin/users/${editingUserId}` : '/api/admin/users'
    const method = editingUserId ? 'PUT' : 'POST'
    if (!editingUserId && !userForm.password) {
      body.password = '1234'
    }
    fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(async (r) => {
        const d = await r.json()
        if (!r.ok) throw new Error(d.detail || 'خطا در ذخیره')
        setSysUserMsg(editingUserId ? 'کاربر به‌روزرسانی شد' : 'کاربر ایجاد شد')
        loadSysUsers()
        resetUserForm()
      })
      .catch((err) => setSysUserMsg(err.message || 'خطا'))
  }

  const deleteSysUser = (id, username) => {
    if (!window.confirm(`حذف کاربر «${username}»؟`)) return
    fetch(`/api/admin/users/${id}`, { method: 'DELETE' })
      .then(async (r) => {
        const d = await r.json()
        if (!r.ok) throw new Error(d.detail || 'خطا')
        setSysUserMsg('حذف شد')
        loadSysUsers()
      })
      .catch((err) => setSysUserMsg(err.message || 'خطا'))
  }

  useEffect(() => {
    if (activeTab === 'modiriat' && (workflowSubView === 'backup' || true)) {
      // when on system tab, allow refresh when opening backup views via ribbon
    }
  }, [activeTab])

  const loadReport = async (key) => {
    if (!key) return
    setReportLoading(true)
    try {
      const res = await fetch(`/api/reports/${key}`)
      const data = await res.json()
      setReportData(data)
    } catch (e) {
      setReportData({ title: 'خطا', columns: ['پیام'], rows: [{ پیام: String(e) }], count: 0 })
    } finally {
      setReportLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'gozaresh' && reportKey) loadReport(reportKey)
  }, [activeTab, reportKey])


  const handleSearch = () => {
    setPersonnelPage(1)
    setSearchQuery(searchInput.trim())
  }

  const changePersonnelPageSize = (value) => {
    const next = value === 'all' ? 'all' : Number(value)
    setPersonnelPage(1)
    setPersonnelPageSize(next)
  }

  const goPersonnelPage = (page) => {
    const max = personnelPageCount
    const p = Math.min(Math.max(1, page), max)
    setPersonnelPage(p)
  }

  const renderPersonnelPagination = (placement = 'bottom') => (
    <div
      className={`personnel-pagination personnel-pagination-${placement}`}
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 10,
        marginTop: placement === 'bottom' ? 12 : 0,
        marginBottom: placement === 'top' ? 12 : 0,
        paddingTop: placement === 'bottom' ? 10 : 0,
        paddingBottom: placement === 'top' ? 10 : 0,
        borderTop: placement === 'bottom' ? '1px solid #e2e8f0' : undefined,
        borderBottom: placement === 'top' ? '1px solid #e2e8f0' : undefined,
        fontSize: 13,
      }}
    >
      <div style={{ color: '#4a5568' }}>
        {personnelLoading
          ? 'در حال بارگذاری...'
          : personnelTotal === 0
            ? 'موردی نیست'
            : personnelPageSize === 'all'
              ? `نمایش همه ${personnelTotal.toLocaleString('fa-IR')} نفر`
              : `نمایش ${(((personnelPage - 1) * Number(personnelPageSize)) + 1).toLocaleString('fa-IR')} تا ${Math.min(personnelPage * Number(personnelPageSize), personnelTotal).toLocaleString('fa-IR')} از ${personnelTotal.toLocaleString('fa-IR')} نفر`}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#4a5568' }}>
          در هر صفحه:
          <select
            value={String(personnelPageSize)}
            onChange={(e) => changePersonnelPageSize(e.target.value)}
            style={{
              padding: '4px 8px',
              borderRadius: 6,
              border: '1px solid #cbd5e0',
              fontFamily: 'inherit',
              fontSize: 13,
            }}
          >
            {PAGE_SIZE_OPTIONS.map((opt) => (
              <option key={String(opt)} value={String(opt)}>
                {opt === 'all' ? 'همه' : opt}
              </option>
            ))}
          </select>
        </label>
        {personnelPageSize !== 'all' && (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <button
              type="button"
              className="refresh-btn"
              disabled={personnelPage <= 1 || personnelLoading}
              onClick={() => goPersonnelPage(1)}
              title="اولین صفحه"
            >
              «
            </button>
            <button
              type="button"
              className="refresh-btn"
              disabled={personnelPage <= 1 || personnelLoading}
              onClick={() => goPersonnelPage(personnelPage - 1)}
              title="صفحه قبل"
            >
              ‹ قبلی
            </button>
            <span style={{ padding: '0 6px', color: '#2d3748' }}>
              صفحه {personnelPage.toLocaleString('fa-IR')} از {personnelPageCount.toLocaleString('fa-IR')}
            </span>
            <button
              type="button"
              className="refresh-btn"
              disabled={personnelPage >= personnelPageCount || personnelLoading}
              onClick={() => goPersonnelPage(personnelPage + 1)}
              title="صفحه بعد"
            >
              بعدی ›
            </button>
            <button
              type="button"
              className="refresh-btn"
              disabled={personnelPage >= personnelPageCount || personnelLoading}
              onClick={() => goPersonnelPage(personnelPageCount)}
              title="آخرین صفحه"
            >
              »
            </button>
          </div>
        )}
      </div>
    </div>
  )

  const handleRegister = (e) => {
    e.preventDefault()
    setFormMsg('')
    // شرکت/مرکز/واحد از «تخصیص شرکت به پرسنل» تنظیم می‌شوند؛ در ثبت الزامی نیستند
    const code = formData.company_code || selectedPersonnel?.company_code || ''
    const isEdit = Boolean(editingId)
    const url = isEdit
      ? `/api/personnel/${editingId}?company_code=${encodeURIComponent(code || '0')}`
      : `/api/personnel${code ? `?company_code=${encodeURIComponent(code)}` : ''}`
    const payload = { ...formData }
    delete payload.company_code
    // عکس/امضای خالی در ویرایش = پاک‌سازی عمدی
    if (isEdit) {
      if (!payload.photo) payload.photo = '__clear__'
      if (!payload.signature) payload.signature = '__clear__'
    } else {
      if (!payload.photo) delete payload.photo
      if (!payload.signature) delete payload.signature
    }
    fetch(url, {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (r) => {
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || (isEdit ? 'خطا در ویرایش' : 'خطا در ثبت'))
        return data
      })
      .then(() => {
        setFormMsg(isEdit ? 'مشخصات پرسنل با موفقیت ویرایش شد' : 'پرسنل با موفقیت ثبت شد')
        setEditingId(null)
        setFormData({ ...emptyForm, company_code: code })
        loadPersonnel(searchQuery)
        setTimeout(() => {
          setShowRegisterForm(false)
          setFormMsg('')
        }, 1200)
      })
      .catch((err) => setFormMsg(err.message || (isEdit ? 'خطا در ویرایش' : 'خطا در ثبت')))
  }

  const personKey = (p) => {
    if (!p) return ''
    return `${p.company_code ?? ''}-${p.id}`
  }

  const isPersonSelected = (p) =>
    (selectedPersonnelList || []).some((x) => personKey(x) === personKey(p))

  const isPrimarySelected = (p) =>
    selectedPersonnel && personKey(selectedPersonnel) === personKey(p)

  const clearPersonnelSelection = () => {
    setSelectedPersonnel(null)
    setSelectedPersonnelList([])
  }

  const selectPersonnel = (p) => {
    if (!p) {
      clearPersonnelSelection()
      return
    }
    setSelectedPersonnelList((prev) => {
      const key = personKey(p)
      const exists = (prev || []).some((x) => personKey(x) === key)
      let next
      if (exists) {
        next = (prev || []).filter((x) => personKey(x) !== key)
      } else {
        next = [...(prev || []), p]
      }
      // برای عملیات تک‌نفره: آخرین انتخاب‌شده به‌عنوان primary
      setSelectedPersonnel(next.length ? next[next.length - 1] : null)
      return next
    })
  }

  const selectAllFilteredPersonnel = (checked) => {
    if (!checked) {
      clearPersonnelSelection()
      return
    }
    const list = filteredPersonnel || []
    setSelectedPersonnelList(list)
    setSelectedPersonnel(list.length ? list[list.length - 1] : null)
  }

  const requireSelectedPersonnel = (actionLabel = 'این عملیات') => {
    if (selectedPersonnel) return selectedPersonnel
    window.alert(`برای «${actionLabel}» ابتدا یک پرسنل را از لیست انتخاب کنید.`)
    return null
  }

  const openPhotoModal = (p) => {
    const person = p || selectedPersonnel
    if (!person) return
    setSelectedPersonnel(person)
    setPhotoModalMsg('')
    setPhotoPreview(person.photo || '')
    setDocsPhotoCandidates([])
    setShowPhotoModal(true)
    // لیست تصاویر موجود در فولدر مدارک
    const code = person.company_code || ''
    fetch(
      `/api/personnel/${person.id}/photo/docs-candidates?company_code=${encodeURIComponent(code)}`
    )
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data.items)) setDocsPhotoCandidates(data.items)
      })
      .catch(() => setDocsPhotoCandidates([]))
  }

  const applyPhotoToSelection = (photoUrl, personnelRow) => {
    setPhotoPreview(photoUrl || '')
    setSelectedPersonnel((prev) => {
      const base = personnelRow || prev
      if (!base) return prev
      return { ...base, photo: photoUrl }
    })
    // به‌روز کردن ردیف در لیست
    setPersonnel((list) =>
      (list || []).map((row) => {
        if (personKey(row) === personKey(personnelRow || selectedPersonnel)) {
          return { ...row, photo: photoUrl }
        }
        return row
      })
    )
    if (editingId && selectedPersonnel && editingId === selectedPersonnel.id) {
      setFormData((prev) => ({ ...prev, photo: photoUrl }))
    }
  }

  const uploadPhotoFromComputer = async (fileList) => {
    const p = selectedPersonnel
    if (!p || !fileList || !fileList.length) return
    const file = fileList[0]
    const name = (file.name || '').toLowerCase()
    if (!name.endsWith('.jpg') && !name.endsWith('.jpeg') && !name.endsWith('.png')) {
      setPhotoModalMsg('فقط فایل‌های JPG و PNG مجاز هستند')
      return
    }
    setPhotoModalBusy(true)
    setPhotoModalMsg('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const code = p.company_code || ''
      const res = await fetch(
        `/api/personnel/${p.id}/photo?company_code=${encodeURIComponent(code)}`,
        { method: 'POST', body: fd }
      )
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'خطا در آپلود عکس')
      applyPhotoToSelection(data.photo, data.personnel || p)
      setPhotoModalMsg(data.message || 'عکس ذخیره شد')
    } catch (err) {
      setPhotoModalMsg(err.message || 'خطا در آپلود')
    } finally {
      setPhotoModalBusy(false)
      if (photoFileRef.current) photoFileRef.current.value = ''
    }
  }

  const loadAttachDestBrowser = (relPath = '', searchQ) => {
    setAttachDestLoading(true)
    const q =
      searchQ !== undefined && searchQ !== null ? searchQ : attachDestSearch
    const params = new URLSearchParams()
    if (relPath) params.set('path', relPath)
    if (q) params.set('q', q)
    fetch(`/api/docs/list?${params}`)
      .then(async (r) => {
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || 'خطا در بارگذاری مسیر')
        setAttachDestPath(data.path || relPath || '')
        setAttachDestRoot(data.root || '')
        setAttachDestItems(Array.isArray(data.items) ? data.items.filter((x) => x.is_dir) : [])
      })
      .catch((err) => setAttachMsg(err.message || 'خطا'))
      .finally(() => setAttachDestLoading(false))
  }

  const openAttachModal = async (p) => {
    const person = p || selectedPersonnel
    if (!person) {
      window.alert('ابتدا یک پرسنل را از لیست انتخاب کنید.')
      return
    }
    setSelectedPersonnel(person)
    setAttachMode(null)
    setAttachMsg('')
    setAttachSourceInfo('')
    setAttachDestSearch('')
    setShowAttachModal(true)
    // مسیر فولدر پرسنل برای حالت انتقال فایل
    try {
      const code = person.company_code || ''
      const res = await fetch(
        `/api/personnel/${person.id}/docs-folder?company_code=${encodeURIComponent(code)}`
      )
      const data = await res.json().catch(() => ({}))
      if (res.ok && data.relative_path != null) {
        setAttachPersonFolder(data.relative_path)
        setAttachDestPath(data.relative_path)
      } else {
        setAttachPersonFolder('')
      }
    } catch {
      setAttachPersonFolder('')
    }
    loadAttachDestBrowser('', '')
  }

  const uploadAttachFolderTree = async (fileList) => {
    if (!fileList || !fileList.length) return
    const files = Array.from(fileList)
    const relPaths = files.map((f) => f.webkitRelativePath || f.name)
    // نام ریشه فولدر انتخاب‌شده
    const top = (relPaths[0] || '').split('/')[0] || 'folder'
    setAttachSourceInfo(`${files.length} فایل از فولدر «${top}»`)
    setAttachBusy(true)
    setAttachMsg('در حال انتقال فولدر...')
    try {
      const fd = new FormData()
      fd.append('path', attachDestPath || '')
      fd.append('relative_paths', JSON.stringify(relPaths))
      files.forEach((f) => fd.append('files', f))
      const res = await fetch('/api/docs/upload-tree', { method: 'POST', body: fd })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'خطا در انتقال فولدر')
      setAttachMsg(data.message || 'انتقال فولدر انجام شد')
      loadAttachDestBrowser(attachDestPath, attachDestSearch)
    } catch (err) {
      setAttachMsg(err.message || 'خطا')
    } finally {
      setAttachBusy(false)
      if (attachFolderRef.current) attachFolderRef.current.value = ''
    }
  }

  const uploadAttachFilesToPerson = async (fileList) => {
    if (!fileList || !fileList.length) return
    const dest = attachPersonFolder
    if (!dest) {
      setAttachMsg('مسیر فولدر پرسنل مشخص نیست')
      return
    }
    setAttachBusy(true)
    setAttachMsg('در حال انتقال فایل‌ها...')
    try {
      const fd = new FormData()
      fd.append('path', dest)
      Array.from(fileList).forEach((f) => fd.append('files', f))
      const res = await fetch('/api/docs/upload', { method: 'POST', body: fd })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'خطا در آپلود فایل')
      setAttachMsg(data.message || 'فایل‌ها منتقل شدند')
      setAttachSourceInfo(`${fileList.length} فایل → ${dest}`)
    } catch (err) {
      setAttachMsg(err.message || 'خطا')
    } finally {
      setAttachBusy(false)
      if (attachFilesRef.current) attachFilesRef.current.value = ''
    }
  }

  const transferPhotoFromDocs = async () => {
    const p = selectedPersonnel
    if (!p) return
    setPhotoModalBusy(true)
    setPhotoModalMsg('')
    try {
      const code = p.company_code || ''
      const res = await fetch(
        `/api/personnel/${p.id}/photo/from-docs?company_code=${encodeURIComponent(code)}`,
        { method: 'POST' }
      )
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'خطا در انتقال از فولدر مدارک')
      applyPhotoToSelection(data.photo, data.personnel || p)
      setPhotoModalMsg(data.message || 'عکس از فولدر مدارک منتقل شد')
      // بروزرسانی لیست کاندیدها
      if (data.source_file) {
        setDocsPhotoCandidates((prev) => {
          const exists = prev.some((x) => x.name === data.source_file)
          return exists ? prev : [{ name: data.source_file, size: null }, ...prev]
        })
      }
    } catch (err) {
      setPhotoModalMsg(err.message || 'خطا')
    } finally {
      setPhotoModalBusy(false)
    }
  }

  const fillFormFromPerson = (p) => {
    const next = { ...emptyForm }
    Object.keys(emptyForm).forEach((k) => {
      if (p[k] !== undefined && p[k] !== null && p[k] !== '') next[k] = p[k]
    })
    next.company_code = p.company_code || next.company_code || ''
    next.active_status = p.active_status || 'فعال'
    next.is_retired = p.is_retired || 'خیر'
    next.is_native = p.is_native || 'خیر'
    next.banned_entry = p.banned_entry || 'خیر'
    next.banned_security = p.banned_security || 'خیر'
    next.settlement_done = p.settlement_done || 'خیر'
    next.show_on_internet = p.show_on_internet || 'خیر'
    next.photo = p.photo || ''
    next.signature = p.signature || ''
    setFormData(next)
  }

  const startEditPersonnel = async (p) => {
    if (!p) return
    setSelectedPersonnel(p)
    setEditingId(p.id)
    setFormMsg('')
    setShowRegisterForm(true)
    setShowDependents(false)
    setShowCards(false)
    // اول با داده لیست پر می‌کنیم، بعد رکورد کامل (با عکس) را می‌گیریم
    fillFormFromPerson(p)
    try {
      const code = p.company_code || ''
      const r = await fetch(`/api/personnel/${p.id}?company_code=${encodeURIComponent(code)}`)
      if (r.ok) {
        const full = await r.json()
        fillFormFromPerson(full)
        setSelectedPersonnel({ ...p, ...full })
      }
    } catch (_) { /* نگه داشتن داده لیست */ }
  }

  /** آپلود فوری عکس/امضا وقتی پرسنل از قبل ذخیره شده */
  const persistMediaNow = async (field, dataUrl) => {
    if (!editingId || !dataUrl || !dataUrl.startsWith('data:image')) return
    const code = formData.company_code || selectedPersonnel?.company_code || ''
    try {
      // از endpoint فایل استفاده می‌کنیم اگر blob ساختیم؛ در غیر این صورت با PUT ذخیره می‌شود
      await fetch(`/api/personnel/${editingId}?company_code=${encodeURIComponent(code)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: dataUrl }),
      })
    } catch (_) { /* ذخیره نهایی فرم هم انجام می‌شود */ }
  }


  const cancelPersonnelForm = () => {
    setEditingId(null)
    setFormData(emptyForm)
    setFormMsg('')
    setShowRegisterForm(false)
    setShowDependents(false)
    setShowCards(false)
  }

  const handleDeletePersonnel = async (p) => {
    if (!window.confirm(`حذف ${p.first_name || ''} ${p.last_name || ''}؟`)) return
    const code = p.company_code || ''
    const url = `/api/personnel/${p.id}?company_code=${encodeURIComponent(code)}`
    try {
      const r = await fetch(url, { method: 'DELETE' })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(data.detail || 'خطا در حذف')
      if (isPersonSelected(p)) clearPersonnelSelection()
      loadPersonnel(searchQuery)
    } catch (err) {
      window.alert(err.message || 'خطا در حذف')
    }
  }

  const handleCompanyRegister = (e) => {
    e.preventDefault()
    if (!isAdmin) {
      setCompanyMsg('فقط مدیر سیستم مجاز به ثبت/ویرایش شرکت است')
      return
    }
    setCompanyMsg('')
    const isEdit = Boolean(editingCompanyCode)
    const url = isEdit ? `/api/companies/${editingCompanyCode}` : '/api/companies'
    const method = isEdit ? 'PUT' : 'POST'
    const body = {
      ...companyForm,
      parent_code: companyForm.parent_code === '' || companyForm.parent_code == null
        ? null
        : parseInt(companyForm.parent_code, 10),
    }
    if (isEdit) body.is_active = true
    fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(async (r) => {
        const data = await r.json()
        if (!r.ok) throw new Error(data.detail || (isEdit ? 'خطا در ویرایش شرکت' : 'خطا در ثبت شرکت'))
        return data
      })
      .then((data) => {
        setCompanyMsg(
          data.message ||
            (isEdit
              ? 'اطلاعات شرکت به‌روز شد'
              : `شرکت ثبت شد — کد: ${data.code} — دیتابیس: co_db.db`)
        )
        setCompanyForm({ name: '', short_name: '', description: '', parent_code: '', logo: '' })
        setEditingCompanyCode(null)
        loadCompanies(true)
        setTimeout(() => {
          setShowCompanyForm(false)
          setCompanyMsg('')
        }, 2000)
      })
      .catch((err) => setCompanyMsg(err.message || 'خطا'))
  }

  const startEditCompany = (c) => {
    if (!isAdmin) {
      window.alert('فقط مدیر سیستم مجاز به ویرایش شرکت است')
      return
    }
    setEditingCompanyCode(c.code)
    setCompanyForm({
      name: c.name || '',
      short_name: c.short_name || '',
      description: c.description || '',
      parent_code: c.parent_code != null ? String(c.parent_code) : '',
      logo: c.logo || '',
    })
    setCompanyMsg('')
    setShowCompanyForm(true)
  }

  const toggleCompanyActive = async (c) => {
    if (!isAdmin) {
      window.alert('فقط مدیر سیستم مجاز به فعال/غیرفعال کردن شرکت است')
      return
    }
    const next = !c.is_active
    const label = next ? 'فعال' : 'غیرفعال'
    if (!window.confirm(`شرکت «${c.name}» ${label} شود؟`)) return
    try {
      const res = await fetch(
        `/api/companies/${c.code}/active?is_active=${next ? 'true' : 'false'}`,
        { method: 'PATCH' }
      )
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'خطا در تغییر وضعیت')
      loadCompanies()
      window.alert(data.message || `شرکت ${label} شد`)
    } catch (err) {
      window.alert(err.message || 'خطا')
    }
  }


  const persistQatIds = (ids) => {
    setQatIds(ids)
    try {
      localStorage.setItem(QAT_STORAGE_KEY, JSON.stringify(ids))
    } catch {
      /* ignore */
    }
  }

  const isInQat = (id) => qatIds.includes(id)

  const toggleQatItem = (id) => {
    if (isInQat(id)) {
      persistQatIds(qatIds.filter((x) => x !== id))
    } else {
      persistQatIds([...qatIds, id])
    }
  }

  const addToQat = (id) => {
    if (!isInQat(id)) persistQatIds([...qatIds, id])
  }

  const removeFromQat = (id) => {
    persistQatIds(qatIds.filter((x) => x !== id))
  }

  const resetQat = () => persistQatIds([...DEFAULT_QAT_IDS])

  const qatItems = qatIds
    .map((id) => ACTION_BY_CODE[id] || QAT_CATALOG.find((c) => c.id === id || c.code === id))
    .filter(Boolean)

  const findActionByCode = (code) => ACTION_BY_CODE[code] || null

  const findCatalogByLabel = (label, tabId = activeTab) => {
    // فقط برای سازگاری منوی راست‌کلیک؛ اولویت با code است
    const flat = String(label || '').replace(/\n/g, ' ').trim()
    const inTab = QAT_CATALOG.find(
      (c) => c.kind === 'ribbon' && c.tab === tabId && c.label === flat
    )
    if (inTab) return inTab
    const all = QAT_CATALOG.filter((c) => c.kind === 'ribbon' && c.label === flat)
    if (all.length === 1) return all[0]
    return null
  }

  const handleQatClick = (item) => {
    if (!item) return
    const code = item.code || item.id
    // مسیر‌یابی فقط با code — بدون وابستگی به متن برچسب
    const run = () => onAction(code)
    if (item.tab && item.tab !== activeTab) {
      setActiveTab(item.tab)
      setTimeout(run, 40)
    } else {
      run()
    }
  }

  const openRibbonContextMenu = (e, actionOrLabel, maybeCode) => {
    e.preventDefault()
    e.stopPropagation()
    let action = null
    if (maybeCode) action = findActionByCode(maybeCode)
    if (!action && actionOrLabel && actionOrLabel.code) action = findActionByCode(actionOrLabel.code)
    if (!action && typeof actionOrLabel === 'string') action = findCatalogByLabel(actionOrLabel)
    if (!action) return
    setQatMenu({ x: e.clientX, y: e.clientY, action })
  }

  /**
   * مسیریابی مرکزی بر اساس code یکتا (نه متن label).
   * codeها فقط داخلی‌اند و در UI نمایش داده نمی‌شوند.
   */
  /** گزینه‌هایی که بک‌اند/UI واقعی دارند — بقیه «به زودی فعال می‌شود» */


  const loadBaseClientCompanies = () => {
    fetch('/api/baseinfo/client_companies')
      .then((r) => r.json())
      .then((d) => {
        const items = Array.isArray(d) ? d : (d.items || d.rows || [])
        setBaseClientCompanies(items)
      })
      .catch(() => setBaseClientCompanies([]))
  }

  /** آیا دکمه ریبون مربوط به زیربرگهٔ فعلی است؟ */
  const isRibbonActionActive = (code) => {
    if (activeTab === 'peymankar') {
      if (code === 'PYM_REPORT' || code === 'PYM_REPORT_CSV') return peymankarSubView === 'report'
      const map = { PYM_CO_REG: 'companies', PYM_CONTRACT: 'contracts', PYM_STAFF: 'personnel', PYM_VEHICLE: 'vehicles', PYM_DRIVER: 'drivers' }
      return map[code] === peymankarSubView
    }
    if (activeTab === 'companies') {
      if (code === 'CO_ORG_UNITS' || code === 'CO_ORG_SITES') return companySubView === 'units'
      if (code === 'CO_REG_NEW') return showCompanyForm && !editingCompanyCode
      if (code === 'CO_REG_EDIT') return showCompanyForm && !!editingCompanyCode
      if (code === 'CO_REG_SEARCH' || code === 'CO_RPT_ACTIVE') return companySubView === 'list' && !showCompanyForm
    }
    if (activeTab === 'personnel') {
      if (code === 'PER_ASSIGN_ORG') return showAssignOrg
      if (code === 'PER_CARD_ISSUE') return showCards
      if (code === 'PER_REG_NEW') return showRegisterForm && !editingId
    }
    if (activeTab === 'mojaz') {
      const map = {
        MJZ_PERSON: 'person', MJZ_VEHICLE: 'vehicle', MJZ_GOODS: 'goods',
        MJZ_LIST: 'list', MJZ_VIEW: 'list', MJZ_RPT: 'report', RPT_MJZ: 'report',
        TRD_TRAIN: 'trd_train', TRD_SHIP: 'trd_ship', TRD_FOREIGN: 'trd_foreign',
        TRD_WATER: 'trd_water', TRD_SEC: 'trd_sec',
      }
      return map[code] === mojazSubView
    }
    return false
  }

  const parseApiJson = async (res) => {
    const ct = (res.headers.get('content-type') || '').toLowerCase()
    const textBody = await res.text()
    if (!textBody) return {}
    // اگر HTML برگشت (بک‌اند قطع / پروکسی اشتباه) — پیام فارسی واضح
    if (ct.includes('text/html') || textBody.trimStart().startsWith('<!DOCTYPE') || textBody.trimStart().startsWith('<html')) {
      throw new Error('پاسخ API به‌جای JSON، HTML است — بک‌اند را روی پورت ۹۵۵۵ اجرا کنید (uvicorn main:app --port 9555)')
    }
    try {
      return JSON.parse(textBody)
    } catch {
      throw new Error('پاسخ سرور JSON معتبر نیست — وضعیت سرویس API را بررسی کنید')
    }
  }

  const loadMjzPermits = async (opts = {}) => {
    setMjzLoading(true)
    if (!opts.keepMsg) setMjzMsg('')
    const qs = new URLSearchParams()
    if (opts.permit_type) qs.set('permit_type', opts.permit_type)
    if (opts.status) qs.set('status', opts.status)
    if (opts.q) qs.set('q', opts.q)
    try {
      let res = await fetch(`/api/mjz/permits?${qs.toString()}`)
      let data = await parseApiJson(res)
      if (!res.ok) {
        const detail = typeof data.detail === 'string' ? data.detail : ''
        throw new Error(detail || `خطا در بارگذاری مجوزها (کد ${res.status})`)
      }
      let items = data.items || []
      if (!items.length && !opts.q && !opts.permit_type && !opts.status && !opts.skipSeed) {
        try {
          const seedRes = await fetch('/api/mjz/seed-samples', { method: 'POST' })
          await parseApiJson(seedRes).catch(() => ({}))
          res = await fetch(`/api/mjz/permits?${qs.toString()}`)
          data = await parseApiJson(res)
          if (res.ok) items = data.items || []
        } catch (_) { /* seed اختیاری */ }
      }
      setMjzList(items)
      if (!items.length && opts.q) setMjzMsg('مجوزی با این مشخصات یافت نشد')
    } catch (e) {
      setMjzList([])
      setMjzMsg(e?.message || 'خطا در بارگذاری مجوزها — بک‌اند (پورت ۹۵۵۵) را بررسی کنید')
    } finally {
      setMjzLoading(false)
    }
  }

  const exportMjzCsv = (opts = {}) => {
    const qs = new URLSearchParams()
    if (opts.permit_type) qs.set('permit_type', opts.permit_type)
    if (opts.status) qs.set('status', opts.status)
    if (opts.q) qs.set('q', opts.q)
    else if ((mjzSearchNo || '').trim()) qs.set('q', (mjzSearchNo || '').trim())
    const url = `/api/mjz/permits/export.csv?${qs.toString()}`
    const a = document.createElement('a')
    a.href = url
    a.download = 'mjz_permits_report.csv'
    document.body.appendChild(a)
    a.click()
    a.remove()
    setMjzMsg('فایل CSV در حال دریافت است…')
  }

  const resetMjzForm = (ptype = 'person') => {
    setMjzForm({
      permit_type: ptype, holder_name: '', national_id: '', personnel_code: '',
      company_name: '', unit_name: '', vehicle_plate: '', vehicle_type: '', driver_name: '',
      goods_desc: '', goods_count: '', purpose: '', destination: '', gate_name: '',
      valid_from: '', valid_to: '',
      allowed_entry_date: '', allowed_entry_time: '', allowed_exit_date: '', allowed_exit_time: '',
      notes: '',
      issued_by: currentUser?.full_name || currentUser?.username || '',
    })
    setMjzMsg('')
  }

  const saveMjzPermit = async () => {
    if (mjzForm.permit_type === 'vehicle') {
      if (!mjzForm.vehicle_plate) { setMjzMsg('شماره پلاک خودرو الزامی است'); return }
    } else if (mjzForm.permit_type === 'goods') {
      if (!mjzForm.goods_desc) { setMjzMsg('شرح کالا الزامی است'); return }
      if (!mjzForm.holder_name && !mjzForm.driver_name) { setMjzMsg('نام تحویل‌گیرنده/راننده الزامی است'); return }
    } else {
      if (!mjzForm.holder_name) { setMjzMsg('نام دارنده مجوز الزامی است'); return }
    }
    try {
      const res = await fetch('/api/mjz/permits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...mjzForm,
          issued_by: currentUser?.full_name || currentUser?.username || mjzForm.issued_by || 'سیستم',
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'خطا در ثبت')
      setMjzMsg(`مجوز ${data.permit_no} با موفقیت صادر شد`)
      resetMjzForm(mjzForm.permit_type)
      loadMjzPermits()
    } catch (e) {
      setMjzMsg(e.message || 'خطا')
    }
  }

  const searchMjzByNo = async () => {
    const no = (mjzSearchNo || '').trim()
    setMjzMsg('')
    setMojazSubView('list')
    // ابتدا لیست فیلترشده را نشان بده
    loadMjzPermits({ q: no || undefined })
    if (!no) {
      setMjzViewItem(null)
      return
    }
    // اگر شماره دقیق بود، کارت جزئیات را هم باز کن
    setMjzLoading(true)
    try {
      const res = await fetch(`/api/mjz/permits/by-no/${encodeURIComponent(no)}`)
      const data = await res.json()
      if (res.ok && data && data.id) {
        setMjzViewItem(data)
      } else {
        setMjzViewItem(null)
        // لیست فیلترشده کافی است؛ پیام فقط اگر هیچ نتیجه‌ای نباشد بعداً از جدول مشخص می‌شود
      }
    } catch (e) {
      setMjzViewItem(null)
    } finally {
      setMjzLoading(false)
    }
  }

  const confirmMjzEntry = async () => {
    if (!mjzViewItem?.id) return
    try {
      const res = await fetch(`/api/mjz/permits/${mjzViewItem.id}/confirm-entry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guard_name: mjzGuardName || currentUser?.full_name || currentUser?.username || 'نگهبان',
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'خطا')
      setMjzViewItem(data)
      setMjzMsg(`ورود در ${toPersianDigits(data.entry_at || '')} ثبت شد` + (data.entry_delay && data.entry_delay !== '—' ? ` — ${data.entry_delay}` : ''))
      loadMjzPermits()
    } catch (e) {
      setMjzMsg(e.message || 'خطا')
    }
  }

  const confirmMjzExit = async () => {
    if (!mjzViewItem?.id) return
    try {
      const res = await fetch(`/api/mjz/permits/${mjzViewItem.id}/confirm-exit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guard_name: mjzGuardName || currentUser?.full_name || currentUser?.username || 'نگهبان',
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'خطا')
      setMjzViewItem(data)
      setMjzMsg(`خروج در ${toPersianDigits(data.exit_at || '')} ثبت شد` + (data.exit_delay && data.exit_delay !== '—' ? ` — ${data.exit_delay}` : ''))
      loadMjzPermits()
    } catch (e) {
      setMjzMsg(e.message || 'خطا')
    }
  }

  const MJZ_TYPE_LABEL = { person: 'تردد نفر', vehicle: 'تردد خودرو', goods: 'خروج کالا' }
  const MJZ_STATUS_LABEL = {
    issued: 'صادر شده', entered: 'ورود ثبت‌شده', exited: 'خروج ثبت‌شده', cancelled: 'لغو شده',
  }

  const IMPLEMENTED_ACTIONS = new Set([
    'MJZ_PERSON', 'MJZ_VEHICLE', 'MJZ_GOODS', 'MJZ_LIST', 'MJZ_VIEW', 'MJZ_RPT', 'RPT_MJZ',
    'TRD_TRAIN', 'TRD_SHIP', 'TRD_FOREIGN', 'TRD_WATER', 'TRD_SEC',
    'SYS_SAVE', 'SYS_PRINT', 'SYS_BACK', 'SYS_SEARCH',
    'PER_REG_NEW', 'PER_REG_EDIT', 'PER_REG_SEARCH', 'PER_REG_ARCHIVE',
    'PER_DOC_PHOTO', 'PER_DOC_ID', 'PER_DOC_ATTACH',
    'PER_REL_REG', 'PER_CARD_ISSUE', 'PER_ASSIGN_ORG',
    'BI_UNITS', 'BI_CENTER', 'BI_EDU', 'BI_RESP', 'BI_EMP',
    'BI_DOORS', 'BI_GOODS_DEST', 'BI_SERVICES', 'BI_CLIENTS', 'BI_ENTRY_EXIT', 'BI_DOOR_ACCESS',
    'BI_VEH_TYPE', 'BI_VEHICLES', 'BI_CARGO_VEH', 'BI_CARGO_REASON',
    'BI_GOODS_IO', 'BI_GOODS_PROD',
    'RPT_GUEST', 'RPT_PERS_TR', 'RPT_VEH_TR', 'RPT_MISC',
    'RPT_GOODS_IO', 'RPT_GOODS_REP', 'RPT_CARGO', 'RPT_CTR_GOODS',
    'RPT_PERS', 'RPT_CTR_PERS', 'RPT_BOARD', 'RPT_REPLACE',
    'RPT_TR_REQ', 'RPT_GUEST_RSV', 'RPT_PERS_HIST', 'RPT_GOODS_RSV', 'RPT_LOG',
    'ENT_GROUP', 'ENT_PROT_CENTER', 'ENT_PROT_PLACE', 'ENT_SHIFT_HOURS',
    'ENT_SHIFT_LEAD', 'ENT_WORK_SHIFT', 'ENT_STAFF_STATUS', 'ENT_EQUIPMENT',
    'ENT_GUARD_BOARD', 'ENT_SHIFT_EVENTS', 'ENT_SHIFT_SCHED', 'ENT_ELEC',
    'ENT_REPLACE', 'ENT_PERMIT', 'ENT_MON_EVT', 'ENT_MON_STAFF',
    'ENT_G_RPT', 'ENT_G_REF', 'ENT_NEWS', 'ENT_ROLL',
    'ENT_BOARD_SUM', 'ENT_G_EVT', 'ENT_DEPLOY', 'ENT_OFF_EVT',
    'CARD_PERS_PRINT', 'CARD_CTR_PRINT', 'CARD_ISSUED_RPT',
    'CARD_VEH_PERS', 'CARD_VEH_CTR', 'CARD_VEH_RPT',
    'PYM_CO_REG', 'PYM_CONTRACT', 'PYM_STAFF', 'PYM_VEHICLE', 'PYM_DRIVER', 'PYM_REPORT', 'PYM_REPORT_CSV',
    'PAT_DEVICES', 'PAT_EVENTS', 'PAT_CHECKPOINTS', 'PAT_GUARDS',
    'PAT_ROUTE_CFG', 'PAT_ROUTES', 'PAT_SHIFT_TIMES',
    'HR_EVAL_OPTS', 'HR_EVAL_TITLES', 'HR_EVAL_PERIOD', 'HR_EVAL_MONTHLY',
    'HR_AREAS', 'HR_HOUSES', 'HR_HOUSE_DELIVERY',
    'HR_VIOL_PERS', 'HR_VIOL_VEH', 'HR_INCIDENT', 'HR_DRUG', 'HR_REWARD',
    'HR_FOREIGN', 'HR_COUNTRIES', 'HR_ARCHIVE',
    'HR_TRAVEL_OUT', 'HR_TRAVEL_PERS', 'HR_EXIT_ADMIN', 'HR_EXIT_SCI',
    'TND_COMPANIES', 'TND_TENDERS', 'TND_AUCTIONS', 'TND_CONTRACTS',
    'KRT_OUTGOING', 'KRT_INBOX', 'KRT_MANAGE', 'KRT_FOLDERS',
    'BSK_WEIGH', 'BSK_TURN', 'BSK_BAN', 'BSK_CO', 'BSK_TON', 'BSK_SET', 'BSK_RPT',
    'PLK_PROCESS', 'PLK_TRAFFIC', 'PLK_MON', 'PLK_PARK', 'PLK_RPT', 'PLK_FULL_RPT', 'PLK_ACCESS', 'PLK_INSIDE', 'PLK_CAM', 'PLK_ONLINE',
    'AC_TRAFFIC', 'AC_ACCESS', 'AC_GUEST', 'AC_GCARD', 'AC_GZONE', 'AC_GDEL', 'AC_GRPT', 'AC_ASSIGN', 'AC_TERM', 'AC_TSTAT', 'AC_SYNC', 'AC_RPT',
    'WF_TYPES', 'WF_APPROVERS', 'WF_DELEGATE', 'WF_PARKING', 'ADM_BACKUP', 'ADM_RESTORE',
    'CO_REG_NEW', 'CO_REG_EDIT', 'CO_REG_SEARCH', 'CO_REG_ARCHIVE', 'CO_ORG_UNITS', 'CO_ORG_SITES', 'CO_RPT_ACTIVE',
    'ADM_SETTINGS', 'ADM_DOCS', 'ADM_ROLES', 'ADM_USERS', 'ADM_USER_CO',
    'PER_BUILD_FOLDERS',
  ])

  const cleanActionLabel = (raw) => String(raw || '').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim()

  const notifyComingSoon = (name) => {
    const t = cleanActionLabel(name) || 'این قابلیت'
    window.alert(`«${t}» به زودی فعال می‌شود.`)
  }

  const onAction = (code) => {
    const action = findActionByCode(code)
    const label = cleanActionLabel(action?.label || code)

    // اعمال سطح دسترسی
    if (action?.tab && !canAccessTab(action.tab)) {
      window.alert(`مجوز دسترسی به برگه «${action.tabLabel || action.tab}» را ندارید`)
      return
    }
    if (!canAccessAction(code)) {
      window.alert(`مجوز اجرای «${label}» را ندارید`)
      return
    }

    switch (code) {
      // —— سیستم / نوار سریع ——
      case 'SYS_SAVE': {
        const form = document.querySelector('.workspace form')
        if (form) form.requestSubmit?.()
        return
      }
      case 'SYS_PRINT':
        window.print()
        return
      case 'SYS_BACK':
        window.history.back()
        return
      case 'SYS_SEARCH':
        setActiveTab('personnel')
        setTimeout(() => document.getElementById('personnel-search-input')?.focus(), 40)
        return

      // —— حراست: آرشیوها ——
      case 'HR_VIOL_ARCHIVE':
        setActiveTab('herasat')
        notifyComingSoon('آرشیو تخلفات')
        return
      case 'HR_INC_ARCHIVE':
        setActiveTab('herasat')
        notifyComingSoon('آرشیو حوادث')
        return

      // —— پرسنل ——
      case 'PER_REG_NEW':
        setActiveTab('personnel')
        setEditingId(null)
        setFormData(emptyForm)
        setFormMsg('')
        setShowDependents(false)
        setShowCards(false)
        setPersonnelRecordKind(null)
        setShowRegisterForm(true)
        return
      case 'PER_REG_EDIT': {
        setActiveTab('personnel')
        const p = requireSelectedPersonnel('ویرایش اطلاعات')
        if (!p) return
        startEditPersonnel(p)
        return
      }
      case 'PER_REG_SEARCH':
        setActiveTab('personnel')
        setTimeout(() => document.getElementById('personnel-search-input')?.focus(), 40)
        return
      case 'PER_REG_ARCHIVE':
        setActiveTab('personnel')
        cancelPersonnelForm()
        openArchive('')
        return
      case 'PER_DOC_PHOTO': {
        setActiveTab('personnel')
        const p = requireSelectedPersonnel('عکس پرسنلی')
        if (!p) return
        openPhotoModal(p)
        return
      }
      case 'PER_DOC_ID': {
        setActiveTab('personnel')
        const p = requireSelectedPersonnel('مدارک شناسایی')
        if (!p) return
        cancelPersonnelForm()
        openPersonnelDocs(p)
        return
      }
      case 'PER_DOC_ATTACH': {
        setActiveTab('personnel')
        const p = requireSelectedPersonnel('پیوست فایل')
        if (!p) return
        openAttachModal(p)
        return
      }
      case 'PER_LIST':
        setActiveTab('personnel')
        setShowRegisterForm(false)
        setShowDependents(false)
        setShowCards(false)
        setPersonnelRecordKind(null)
        setEditingId(null)
        loadPersonnel()
        return
      case 'PER_DOC_PRINT':
      case 'PER_CARD_BLOCK':
      case 'PER_CARD_RENEW': {
        setActiveTab('personnel')
        notifyComingSoon(label)
        return
      }
      case 'PER_REL_SERVICE':
        setActiveTab('personnel')
        openPersonnelRecords('service', 'سوابق خدماتی')
        return
      case 'PER_REL_TRAVEL':
        setActiveTab('personnel')
        openPersonnelRecords('travel', 'سفر خارجی')
        return
      case 'PER_REL_MEDICAL':
        setActiveTab('personnel')
        openPersonnelRecords('medical', 'سوابق پزشکی')
        return
      case 'PER_REL_REG': {
        setActiveTab('personnel')
        const p = requireSelectedPersonnel('ثبت وابستگان')
        if (!p) return
        setShowRegisterForm(false)
        setShowCards(false)
        setPersonnelRecordKind(null)
        setShowDependents(true)
        setEditingDepId(null)
        setDepForm({ first_name: '', last_name: '', national_id: '', relation: '', birth_date: '', gender: '', phone: '', description: '' })
        setDepMsg('')
        loadDependents(p)
        return
      }
      case 'PER_ASSIGN_ORG': {
        setActiveTab('personnel')
        setShowRegisterForm(false)
        setShowDependents(false)
        setShowCards(false)
        setPersonnelRecordKind(null)
        setShowAssignOrg(true)
        setAssignOrgMsg('')
        loadUnits()
        loadCompanies()
        if (selectedPersonnel) {
          setAssignOrgForm({
            company_code: selectedPersonnel.company_code != null ? String(selectedPersonnel.company_code) : '',
            center: selectedPersonnel.center || '',
            department: selectedPersonnel.department || '',
          })
        } else {
          setAssignOrgForm({ company_code: '', center: '', department: '' })
        }
        return
      }
      case 'PER_CARD_ISSUE': {
        setActiveTab('personnel')
        const p = requireSelectedPersonnel('صدور کارت شناسایی')
        if (!p) return
        if (!p.company_code) {
          window.alert('ابتدا از «تخصیص شرکت به پرسنل» شرکت تابعه را به این پرسنل تخصیص دهید؛ سپس صدور کارت فعال می‌شود.')
          setShowAssignOrg(true)
          setShowCards(false)
          setShowRegisterForm(false)
          setAssignOrgForm({
            company_code: '',
            center: p.center || '',
            department: p.department || '',
          })
          return
        }
        setShowRegisterForm(false)
        setShowDependents(false)
        setShowAssignOrg(false)
        setShowCards(true)
        setEditingCardId(null)
        setCardForm({ card_number: '', card_type: 'شناسایی', issue_date: '', expiry_date: '', status: 'فعال', printed: false, description: '' })
        setCardMsg('')
        loadCards(p)
        openIdCardPrint(p)
        return
      }
      // —— اطلاعات پایه ——
      case 'BI_UNITS':
      case 'BI_CENTER':
        setActiveTab('companies')
        setShowCompanyForm(false)
        setCompanySubView('units')
        loadUnits()
        loadCompanies()
        return
      case 'BI_EDU':
        setActiveTab('baseinfo')
        setBaseSubView('edu')
        return
      case 'BI_RESP':
        setActiveTab('baseinfo')
        setBaseSubView('resp')
        return
      case 'BI_EMP':
        setActiveTab('baseinfo')
        setBaseSubView('emp')
        return
      case 'BI_DOORS':
        setActiveTab('baseinfo')
        setBaseSubView('doors')
        return
      case 'BI_GOODS_DEST':
        setActiveTab('baseinfo')
        setBaseSubView('goods')
        return
      case 'BI_SERVICES':
        setActiveTab('baseinfo')
        setBaseSubView('services')
        return
      case 'BI_CLIENTS':
        setActiveTab('baseinfo')
        setBaseSubView('clients')
        return
      case 'BI_ENTRY_EXIT':
        setActiveTab('baseinfo')
        setBaseSubView('entry_exit')
        return
      case 'BI_DOOR_ACCESS':
        setActiveTab('baseinfo')
        setBaseSubView('door_access')
        return
      case 'BI_VEH_TYPE':
        setActiveTab('baseinfo'); setBaseSubView('veh_types'); return
      case 'BI_VEHICLES':
        setActiveTab('baseinfo'); setBaseSubView('vehicles'); return
      case 'BI_CARGO_VEH':
        setActiveTab('baseinfo'); setBaseSubView('cargo_vehicles'); return
      case 'BI_CARGO_REASON':
        setActiveTab('baseinfo'); setBaseSubView('cargo_reasons'); return
      case 'BI_GOODS_IO':
        setActiveTab('baseinfo'); setBaseSubView('goods_io'); return
      case 'BI_GOODS_PROD':
        setActiveTab('baseinfo'); setBaseSubView('goods_products'); return

      case 'RPT_GUEST': setActiveTab('gozaresh'); setReportKey('guest'); return
      case 'RPT_PERS_TR': setActiveTab('gozaresh'); setReportKey('personnel_traffic'); return
      case 'RPT_VEH_TR': setActiveTab('gozaresh'); setReportKey('vehicle_traffic'); return
      case 'RPT_MISC': setActiveTab('gozaresh'); setReportKey('misc_traffic'); return
      case 'RPT_GOODS_IO': setActiveTab('gozaresh'); setReportKey('goods_io'); return
      case 'RPT_GOODS_REP': setActiveTab('gozaresh'); setReportKey('goods_repair'); return
      case 'RPT_CARGO': setActiveTab('gozaresh'); setReportKey('cargo_vehicle'); return
      case 'RPT_CTR_GOODS': setActiveTab('gozaresh'); setReportKey('contractor_goods'); return
      case 'RPT_PERS': setActiveTab('gozaresh'); setReportKey('personnel'); return
      case 'RPT_CTR_PERS': setActiveTab('gozaresh'); setReportKey('contractor_personnel'); return
      case 'RPT_BOARD': setActiveTab('gozaresh'); setReportKey('guard_board'); return
      case 'RPT_REPLACE': setActiveTab('gozaresh'); setReportKey('replacement'); return
      case 'RPT_TR_REQ': setActiveTab('gozaresh'); setReportKey('traffic_request'); return
      case 'RPT_GUEST_RSV': setActiveTab('gozaresh'); setReportKey('guest_reserve'); return
      case 'RPT_PERS_HIST': setActiveTab('gozaresh'); setReportKey('personnel_history'); return
      case 'RPT_GOODS_RSV': setActiveTab('gozaresh'); setReportKey('goods_reserve'); return
      case 'RPT_LOG': setActiveTab('gozaresh'); setReportKey('system_log'); return
      case 'ENT_GROUP':
        setActiveTab('entezamat'); setEntezamatSubView('groups'); return
      case 'ENT_PROT_CENTER':
        setActiveTab('entezamat'); setEntezamatSubView('prot_centers'); return
      case 'ENT_PROT_PLACE':
        setActiveTab('entezamat'); setEntezamatSubView('prot_places'); return
      case 'ENT_SHIFT_HOURS':
        setActiveTab('entezamat'); setEntezamatSubView('shift_hours'); return
      case 'ENT_SHIFT_LEAD':
        setActiveTab('entezamat'); setEntezamatSubView('shift_leaders'); return
      case 'ENT_WORK_SHIFT':
        setActiveTab('entezamat'); setEntezamatSubView('work_shifts'); return
      case 'ENT_STAFF_STATUS':
        setActiveTab('entezamat'); setEntezamatSubView('staff_status'); return
      case 'ENT_EQUIPMENT':
        setActiveTab('entezamat'); setEntezamatSubView('equipment'); return
      case 'ENT_GUARD_BOARD':
        setActiveTab('entezamat'); setEntezamatSubView('guard_board'); return
      case 'ENT_SHIFT_EVENTS':
        setActiveTab('entezamat'); setEntezamatSubView('shift_events'); return
      case 'ENT_SHIFT_SCHED':
        setActiveTab('entezamat'); setEntezamatSubView('shift_schedule'); return
      case 'ENT_ELEC':
        setActiveTab('entezamat'); setEntezamatSubView('electronics'); return
      case 'ENT_REPLACE':
        setActiveTab('entezamat'); setEntezamatSubView('replacement'); return
      case 'ENT_PERMIT':
        setActiveTab('entezamat'); setEntezamatSubView('permits'); return
      case 'ENT_MON_EVT':
        setActiveTab('entezamat'); setEntezamatSubView('mon_events'); return
      case 'ENT_MON_STAFF':
        setActiveTab('entezamat'); setEntezamatSubView('mon_staff'); return
      case 'ENT_G_RPT':
        setActiveTab('entezamat'); setEntezamatSubView('guard_reports'); return
      case 'ENT_G_REF':
        setActiveTab('entezamat'); setEntezamatSubView('guard_referrals'); return
      case 'ENT_NEWS':
        setActiveTab('herasat'); setHerasatSubView('news'); return
      case 'ENT_ROLL':
        setActiveTab('entezamat'); setEntezamatSubView('roll_call'); return
      case 'ENT_BOARD_SUM':
        setActiveTab('entezamat'); setEntezamatSubView('board_summary'); return
      case 'ENT_G_EVT':
        setActiveTab('entezamat'); setEntezamatSubView('guard_events'); return
      case 'ENT_DEPLOY':
        setActiveTab('entezamat'); setEntezamatSubView('deploy'); return
      case 'ENT_OFF_EVT':
        setActiveTab('entezamat'); setEntezamatSubView('officer_events'); return

      // —— صدور کارت ——
      case 'CARD_PERS_PRINT':
        setActiveTab('sodor_kart'); setCardSubView('personnel_card'); return
      case 'CARD_CTR_PRINT':
        setActiveTab('sodor_kart'); setCardSubView('contractor_card'); return
      case 'CARD_ISSUED_RPT':
        setActiveTab('sodor_kart'); setCardSubView('issued_report'); return
      case 'CARD_VEH_PERS':
        setActiveTab('sodor_kart'); setCardSubView('vehicle_personnel'); return
      case 'CARD_VEH_CTR':
        setActiveTab('sodor_kart'); setCardSubView('vehicle_contractor'); return
      case 'CARD_VEH_RPT':
        setActiveTab('sodor_kart'); setCardSubView('vehicle_report'); return

      // —— پیمانکاران ——
      case 'PYM_CO_REG':
        setActiveTab('peymankar'); setPeymankarSubView('companies'); return
      case 'PYM_CONTRACT':
        setActiveTab('peymankar'); setPeymankarSubView('contracts'); return
      case 'PYM_STAFF':
        setActiveTab('peymankar'); setPeymankarSubView('personnel'); return
      case 'PYM_VEHICLE':
        setActiveTab('peymankar'); setPeymankarSubView('vehicles'); return
      case 'PYM_DRIVER':
        setActiveTab('peymankar'); setPeymankarSubView('drivers'); return
      case 'PYM_REPORT':
        setActiveTab('peymankar')
        setPeymankarSubView('report')
        setPymReportMsg('')
        setTimeout(() => loadPymReport(pymReportKind || 'summary'), 0)
        return
      case 'PYM_REPORT_CSV': {
        setActiveTab('peymankar')
        setPeymankarSubView('report')
        const params = new URLSearchParams({
          kind: pymReportKind || 'summary',
        })
        if (pymReportQ) params.set('q', pymReportQ)
        if (pymReportCompany) params.set('company_name', pymReportCompany)
        downloadUrl(`/api/peymankar/report.csv?${params.toString()}`, `peymankar_${pymReportKind || 'summary'}_report.csv`)
        return
      }

      // —— گشت و پایش ——
      case 'PAT_DEVICES':
        setActiveTab('monitoring'); setPatrolSubView('devices'); return
      case 'PAT_EVENTS':
        setActiveTab('monitoring'); setPatrolSubView('events'); return
      case 'PAT_CHECKPOINTS':
        setActiveTab('monitoring'); setPatrolSubView('checkpoints'); return
      case 'PAT_GUARDS':
        setActiveTab('monitoring'); setPatrolSubView('guards'); return
      case 'PAT_ROUTE_CFG':
        setActiveTab('monitoring'); setPatrolSubView('route_config'); return
      case 'PAT_ROUTES':
        setActiveTab('monitoring'); setPatrolSubView('routes'); return
      case 'PAT_SHIFT_TIMES':
        setActiveTab('monitoring'); setPatrolSubView('shift_times'); return

      // —— حراست ——
      case 'HR_EVAL_OPTS':
        setActiveTab('herasat'); setHerasatSubView('eval_options'); return
      case 'HR_EVAL_TITLES':
        setActiveTab('herasat'); setHerasatSubView('eval_titles'); return
      case 'HR_EVAL_PERIOD':
        setActiveTab('herasat'); setHerasatSubView('eval_periods'); return
      case 'HR_EVAL_MONTHLY':
        setActiveTab('herasat'); setHerasatSubView('eval_monthly'); return
      case 'HR_AREAS':
        setActiveTab('herasat'); setHerasatSubView('areas'); return
      case 'HR_HOUSES':
        setActiveTab('herasat'); setHerasatSubView('houses'); return
      case 'HR_HOUSE_DELIVERY':
        setActiveTab('herasat'); setHerasatSubView('house_delivery'); return
      case 'HR_VIOL_PERS':
        setActiveTab('herasat'); setHerasatSubView('viol_personnel'); return
      case 'HR_VIOL_VEH':
        setActiveTab('herasat'); setHerasatSubView('viol_vehicle'); return
      case 'HR_INCIDENT':
        setActiveTab('herasat'); setHerasatSubView('incidents'); return
      case 'HR_DRUG':
        setActiveTab('herasat'); setHerasatSubView('drug_tests'); return
      case 'HR_REWARD':
        setActiveTab('herasat'); setHerasatSubView('rewards'); return
      case 'HR_FOREIGN':
        setActiveTab('herasat'); setHerasatSubView('foreign_nationals'); return
      case 'HR_COUNTRIES':
        setActiveTab('herasat'); setHerasatSubView('countries'); return
      case 'HR_ARCHIVE':
        setActiveTab('herasat'); setHerasatSubView('doc_archive'); return
      case 'HR_TRAVEL_OUT':
        setActiveTab('herasat'); setHerasatSubView('travel_abroad'); return
      case 'HR_TRAVEL_PERS':
        setActiveTab('herasat'); setHerasatSubView('travel_personal'); return
      case 'HR_EXIT_ADMIN':
        setActiveTab('herasat'); setHerasatSubView('exit_admin'); return
      case 'HR_EXIT_SCI':
        setActiveTab('herasat'); setHerasatSubView('exit_scientific'); return

      // —— مناقصات و مزایدات ——
      case 'TND_COMPANIES':
        setActiveTab('monaghese'); setMonagheseSubView('companies'); return
      case 'TND_TENDERS':
        setActiveTab('monaghese'); setMonagheseSubView('tenders'); return
      case 'TND_AUCTIONS':
        setActiveTab('monaghese'); setMonagheseSubView('auctions'); return
      case 'TND_CONTRACTS':
        setActiveTab('monaghese'); setMonagheseSubView('contracts'); return

      // —— کارتابل ——
      case 'KRT_OUTGOING':
        setActiveTab('kartabl'); setKartablSubView('outgoing'); return
      case 'KRT_INBOX':
        setActiveTab('kartabl'); setKartablSubView('inbox'); return
      case 'KRT_MANAGE':
        setActiveTab('kartabl'); setKartablSubView('management'); return
      case 'KRT_FOLDERS':
        setActiveTab('kartabl'); setKartablSubView('folders'); return

      // —— باسکول ——
      case 'BSK_WEIGH':
        setActiveTab('baskool'); setBaskoolSubView('weighings'); return
      case 'BSK_TURN':
        setActiveTab('baskool'); setBaskoolSubView('turns'); return
      case 'BSK_BAN':
        setActiveTab('baskool'); setBaskoolSubView('traffic_ban'); return
      case 'BSK_CO':
        setActiveTab('baskool'); setBaskoolSubView('companies'); return
      case 'BSK_TON':
        setActiveTab('baskool'); setBaskoolSubView('max_tonnage'); return
      case 'BSK_SET':
        setActiveTab('baskool'); setBaskoolSubView('settings'); return
      case 'BSK_RPT':
        setActiveTab('baskool'); setBaskoolSubView('weigh_reports'); return

      // —— پلاک‌خوان ——
      case 'PLK_PROCESS':
        setActiveTab('pelakhwan'); setPelakhwanSubView('process'); return
      case 'PLK_TRAFFIC':
        setActiveTab('pelakhwan'); setPelakhwanSubView('traffic'); return
      case 'PLK_MON':
        setActiveTab('pelakhwan'); setPelakhwanSubView('monitoring'); return
      case 'PLK_PARK':
        setActiveTab('pelakhwan'); setPelakhwanSubView('parking'); return
      case 'PLK_RPT':
        setActiveTab('pelakhwan'); setPelakhwanSubView('traffic_report'); return
      case 'PLK_FULL_RPT':
        setActiveTab('pelakhwan'); setPelakhwanSubView('full_traffic_report'); return
      case 'PLK_ACCESS':
        setActiveTab('pelakhwan'); setPelakhwanSubView('access_level'); return
      case 'PLK_INSIDE':
        setActiveTab('pelakhwan'); setPelakhwanSubView('inside_vehicles'); return
      case 'PLK_CAM':
        setActiveTab('pelakhwan'); setPelakhwanSubView('cameras'); return
      case 'PLK_ONLINE':
        setActiveTab('pelakhwan'); setPelakhwanSubView('online_monitor'); return

      // —— کنترل دسترسی ——
      case 'AC_TRAFFIC':
        setActiveTab('access'); setAccessSubView('traffic'); return
      case 'AC_ACCESS':
        setActiveTab('access'); setAccessSubView('access_def'); return
      case 'AC_GUEST':
        setActiveTab('access'); setAccessSubView('guests'); return
      case 'AC_GCARD':
        setActiveTab('access'); setAccessSubView('guest_cards'); return
      case 'AC_GZONE':
        setActiveTab('access'); setAccessSubView('guest_zone'); return
      case 'AC_GDEL':
        setActiveTab('access'); setAccessSubView('guest_delivered'); return
      case 'AC_GRPT':
        setActiveTab('access'); setAccessSubView('guest_report'); return
      case 'AC_ASSIGN':
        setActiveTab('access'); setAccessSubView('assign'); return
      case 'AC_TERM':
        setActiveTab('access'); setAccessSubView('terminals'); return
      case 'AC_TSTAT':
        setActiveTab('access'); setAccessSubView('terminal_status'); return
      case 'AC_SYNC':
        setActiveTab('access'); setAccessSubView('user_sync'); return
      case 'AC_RPT':
        setActiveTab('access'); setAccessSubView('general_report'); return

      // —— جریان کار ——
      case 'WF_TYPES':
        setActiveTab('workflow'); setWorkflowSubView('request_types'); return
      case 'WF_APPROVERS':
        setActiveTab('workflow'); setWorkflowSubView('approvers'); return
      case 'WF_DELEGATE':
        setActiveTab('workflow'); setWorkflowSubView('delegation'); return
      case 'WF_PARKING':
        setActiveTab('workflow'); setWorkflowSubView('parking_docs'); return
      case 'ADM_BACKUP':
        setActiveTab('modiriat'); setWorkflowSubView('backup'); setBackupMsg(''); refreshBackupList(); return
      case 'ADM_RESTORE':
        setActiveTab('modiriat'); setWorkflowSubView('restore'); setBackupMsg(''); refreshBackupList(); return













      // —— شرکت‌ها ——
      case 'CO_REG_NEW':
        setActiveTab('companies')
        if (!isAdmin) {
          window.alert('فقط مدیر سیستم مجاز به ثبت شرکت است')
          return
        }
        setEditingCompanyCode(null)
        setCompanyForm({ name: '', short_name: '', description: '', parent_code: '', logo: '' })
        setCompanyMsg('')
        setShowCompanyForm(true)
        setCompanySubView('form')
        return
      case 'CO_REG_EDIT':
        setActiveTab('companies')
        if (!isAdmin) {
          window.alert('فقط مدیر سیستم مجاز به ویرایش شرکت است')
          return
        }
        window.alert('برای ویرایش، از ستون عملیات در لیست شرکت‌ها استفاده کنید.')
        return
      case 'CO_REG_SEARCH':
        setActiveTab('companies')
        setShowCompanyForm(false)
        setCompanySubView('list')
        setEditingCompanyCode(null)
        setCompanySearch('')
        setCompanyStatusFilter('all')
        loadCompanies()
        focusCompanySearch()
        return
      case 'CO_REG_ARCHIVE':
        setActiveTab('companies')
        setShowCompanyForm(false)
        setEditingCompanyCode(null)
        setCompanyStatusFilter('inactive')
        setCompanySearch('')
        loadCompanies()
        return
      case 'CO_RPT_ACTIVE':
        setActiveTab('companies')
        setShowCompanyForm(false)
        setEditingCompanyCode(null)
        setCompanyStatusFilter('active')
        setCompanySearch('')
        loadCompanies()
        return
      case 'CO_ORG_UNITS':
      case 'CO_ORG_SITES':
        setActiveTab('companies')
        setShowCompanyForm(false)
        setCompanySubView('units')
        loadUnits()
        loadCompanies()
        return

      // —— مدیریت ——
      case 'ADM_ROLES':
        setActiveTab('modiriat'); setWorkflowSubView('access_levels'); setAccessLevelMsg(''); loadAccessLevels(); return
      case 'ADM_USERS':
        setActiveTab('modiriat'); setWorkflowSubView('sys_users'); setSysUserMsg(''); loadAccessLevels(); loadSysUsers(); return
      case 'ADM_USER_CO':
        setActiveTab('modiriat'); setWorkflowSubView('sys_users'); setSysUserMsg(''); loadAccessLevels(); loadSysUsers(); return
      case 'ADM_SETTINGS':
        loadSettings()
        setSettingsMsg('')
        setShowSettings(true)
        return
      case 'ADM_DOCS':
        setShowArchDocs(true)
        return
      case 'ADM_EARCHIVE':
        setActiveTab('modiriat')
        notifyComingSoon('آرشیو الکترونیکی')
        return

      case 'MJZ_PERSON':
        setActiveTab('mojaz'); setMojazSubView('person'); resetMjzForm('person');
        fetch('/api/mjz/seed-samples', { method: 'POST' }).catch(() => {});
        if (typeof loadBaseClientCompanies === 'function') loadBaseClientCompanies();
        loadCompanies();
        return
      case 'MJZ_VEHICLE':
        setActiveTab('mojaz'); setMojazSubView('vehicle'); resetMjzForm('vehicle');
        fetch('/api/mjz/seed-samples', { method: 'POST' }).catch(() => {});
        if (typeof loadBaseClientCompanies === 'function') loadBaseClientCompanies();
        loadCompanies();
        return
      case 'MJZ_GOODS':
        setActiveTab('mojaz'); setMojazSubView('goods'); resetMjzForm('goods');
        fetch('/api/mjz/seed-samples', { method: 'POST' }).catch(() => {});
        if (typeof loadBaseClientCompanies === 'function') loadBaseClientCompanies();
        loadCompanies();
        return
      case 'MJZ_PASS':
        setActiveTab('mojaz'); setMojazSubView('person'); resetMjzForm('person'); return
      case 'MJZ_LIST':
        setActiveTab('mojaz')
        setMojazSubView('list')
        setMjzViewItem(null)
        setMjzSearchNo('')
        setMjzMsg('')
        loadMjzPermits({ skipSeed: false })
        return
      case 'MJZ_VIEW':
        setActiveTab('mojaz'); setMojazSubView('list'); setMjzViewItem(null); setMjzSearchNo(''); setMjzMsg(''); return
      case 'MJZ_RPT':
      case 'RPT_MJZ':
        setActiveTab('mojaz'); setMojazSubView('report'); setMjzViewItem(null); setMjzMsg('');
        loadMjzPermits({ q: (mjzSearchNo || '').trim() || undefined });
        return
      case 'TRD_TRAIN':
        setActiveTab('mojaz'); setMojazSubView('trd_train'); setMjzMsg(''); return
      case 'TRD_SHIP':
        setActiveTab('mojaz'); setMojazSubView('trd_ship'); setMjzMsg(''); return
      case 'TRD_FOREIGN':
        setActiveTab('mojaz'); setMojazSubView('trd_foreign'); setMjzMsg(''); return
      case 'TRD_WATER':
        setActiveTab('mojaz'); setMojazSubView('trd_water'); setMjzMsg(''); return
      case 'TRD_SEC':
        setActiveTab('mojaz'); setMojazSubView('trd_sec'); setMjzMsg(''); return

      default: {
        // ساخت فولدر و سایر
        if (code === 'PER_BUILD_FOLDERS' || String(label).includes('ساخت فولدر')) {
          fetch('/api/docs/create-all-folders', { method: 'POST' })
            .then(async (res) => {
              const data = await res.json()
              if (!res.ok) throw new Error(data.detail || 'خطا در ساخت فولدرها')
              alert(data.message || 'فولدرهای پرسنل با موفقیت ایجاد شدند.')
            })
            .catch((err) => alert('خطا در ایجاد فولدرها: ' + err.message))
          return
        }
        if (action?.tab) setActiveTab(action.tab)
        notifyComingSoon(label)
        return
      }
    }
  }

  // سازگاری: فراخوانی قدیمی با label — در صورت امکان از code رزولو می‌شود
  const onRibbonClick = (labelOrCode, forcedTab = null, explicitCode = null) => {
    if (explicitCode) {
      onAction(explicitCode)
      return
    }
    // اگر خود code پاس داده شده
    if (ACTION_BY_CODE[labelOrCode]) {
      onAction(labelOrCode)
      return
    }
    const flat = String(labelOrCode || '').replace(/\n/g, ' ').trim()
    const tab = forcedTab || activeTab
    const hit =
      QAT_CATALOG.find((c) => c.kind === 'ribbon' && c.tab === tab && c.label === flat) ||
      (QAT_CATALOG.filter((c) => c.kind === 'ribbon' && c.label === flat).length === 1
        ? QAT_CATALOG.find((c) => c.kind === 'ribbon' && c.label === flat)
        : null)
    if (hit?.code) {
      onAction(hit.code)
      return
    }
    notifyComingSoon(flat || labelOrCode)
  }


  if (!isLoggedIn) {
    return (
      <div className="login-screen">
        <form className="login-card" onSubmit={handleLogin}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 20 }}>
            <OilFundLogo size={96} />
            <IoecLogoSvg size={96} />
            <div style={{ marginTop: 14, fontSize: 17, fontWeight: 800, color: '#1e4a9a', lineHeight: 1.45 }}>
              تأسیسات دریایی ایران
            </div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#1e3a8a', marginTop: 10 }}>
              سیستم جامع حراست
            </div>
          </div>
          {loginError && <div className="login-error">{loginError}</div>}
          <div style={{ marginBottom: 14, textAlign: 'right' }}>
            <label>نام کاربری</label>
            <input
              autoFocus
              value={loginUser}
              onChange={(e) => setLoginUser(e.target.value)}
              placeholder="AdminUser"
              autoComplete="username"
            />
          </div>
          <div style={{ marginBottom: 18, textAlign: 'right' }}>
            <label>رمز عبور</label>
            <input
              type="password"
              value={loginPass}
              onChange={(e) => setLoginPass(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="btn-primary" style={{ width: '100%', padding: '12px', fontSize: 15 }}>
            ورود به سامانه
          </button>
        </form>
      </div>
    )
  }

  return (
    <>
      {/* Title Bar */}
      <div className="title-bar">
        <div className="logo">
          <OilFundLogo size={36} />
          <span>سیستم جامع حراست — تأسیسات دریایی ایران</span>
        </div>
      </div>

      {/* Quick Access — سبک Microsoft Word */}
      <div className="quick-access">
        <div className="qat-left">
          {qatItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className="qa-btn"
              title={`${item.label}${item.tabLabel ? ` (${item.tabLabel})` : ''}\nراست‌کلیک برای حذف از نوار سریع`}
              onClick={() => handleQatClick(item)}
              onContextMenu={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setQatMenu({ x: e.clientX, y: e.clientY, action: item })
              }}
            >
              <span className="qa-icon">
                {item.label.includes('صدور کارت')
                  ? renderRibbonIcon(item.icon, item.label, true)
                  : item.icon}
              </span>
              <span className="qa-label">{item.label}</span>
            </button>
          ))}
          <div className="qa-separator" />
          <div className="qat-customize-wrap">
            <button
              type="button"
              className="qa-btn qa-customize-btn"
              title="سفارشی‌سازی نوار دسترسی سریع"
              onClick={(e) => {
                e.stopPropagation()
                setShowQatCustomize((v) => !v)
                setQatMenu(null)
              }}
            >
              ▾
            </button>
            {showQatCustomize && (
              <div className="qat-dropdown" onClick={(e) => e.stopPropagation()}>
                <div className="qat-dropdown-header">
                  <strong>سفارشی‌سازی نوار سریع</strong>
                  <span style={{ fontSize: 11, color: '#718096' }}>
                    مانند ورد — افزودن/حذف دستورات ریبون
                  </span>
                </div>
                <input
                  type="text"
                  className="qat-filter"
                  placeholder="جستجوی دستور..."
                  value={qatFilter}
                  onChange={(e) => setQatFilter(e.target.value)}
                />
                <div className="qat-dropdown-list">
                  {BUILTIN_QAT.map((item) => (
                    <label key={item.id} className="qat-check-row">
                      <input
                        type="checkbox"
                        checked={isInQat(item.id)}
                        onChange={() => toggleQatItem(item.id)}
                      />
                      <span className="qat-check-icon">{item.icon}</span>
                      <span>{item.label}</span>
                      <span className="qat-check-tab">سیستم</span>
                    </label>
                  ))}
                  <div className="qat-dropdown-sep" />
                  {RIBBON_CATALOG.filter((item) => {
                    const q = qatFilter.trim()
                    if (!q) return true
                    const hay = `${item.label} ${item.tabLabel || ''} ${item.group || ''}`
                    return hay.includes(q)
                  }).map((item) => (
                    <label key={item.id} className="qat-check-row">
                      <input
                        type="checkbox"
                        checked={isInQat(item.id)}
                        onChange={() => toggleQatItem(item.id)}
                      />
                      <span className="qat-check-icon">
                        {item.label.includes('صدور کارت')
                          ? renderRibbonIcon(item.icon, item.label, true)
                          : item.icon}
                      </span>
                      <span>{item.label}</span>
                      <span className="qat-check-tab">{item.tabLabel}</span>
                    </label>
                  ))}
                </div>
                <div className="qat-dropdown-footer">
                  <button type="button" className="btn-secondary" onClick={resetQat}>
                    بازنشانی پیش‌فرض
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => setShowQatCustomize(false)}
                  >
                    بستن
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ position: 'relative' }} className="no-print">
          <button
            type="button"
            className="qa-btn"
            onClick={() => setShowUserMenu((v) => !v)}
            title="منوی کاربر"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            👤 کاربر: {currentUser?.full_name || currentUser?.username || 'مدیر سیستم'}
            <span style={{ fontSize: 10, opacity: 0.7 }}>▼</span>
          </button>
          {showUserMenu && (
            <div
              id="user-account-menu"
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: 4,
                minWidth: 200,
                background: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: 8,
                boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                zIndex: 5000,
                padding: 6,
                direction: 'rtl',
              }}
              onClick={(e) => e.stopPropagation()}
              onMouseDown={(e) => e.stopPropagation()}
            >
              <div style={{ padding: '8px 12px', fontSize: 12, color: '#64748b', borderBottom: '1px solid #edf2f7' }}>
                {currentUser?.username || 'AdminUser'}
              </div>
              <button
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  handleLogout(e)
                }}
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  handleLogout(e)
                }}
                style={{
                  width: '100%',
                  textAlign: 'right',
                  padding: '10px 12px',
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  fontSize: 13,
                  color: '#c53030',
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#fff5f5' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
              >
                🚪 خروج از سیستم
              </button>
            </div>
          )}
        </div>
        <button type="button" className="qa-btn" title="اعلان‌ها">
          🔔
        </button>
      </div>

      {/* منوی راست‌کلیک نوار سریع / ریبون */}
      {qatMenu && (
        <div
          className="qat-context-menu"
          style={{ top: qatMenu.y, left: Math.min(qatMenu.x, window.innerWidth - 220) }}
          onClick={(e) => e.stopPropagation()}
        >
          {isInQat(qatMenu.action.id) ? (
            <button
              type="button"
              onClick={() => {
                removeFromQat(qatMenu.action.id)
                setQatMenu(null)
              }}
            >
              حذف از نوار دسترسی سریع
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                addToQat(qatMenu.action.id)
                setQatMenu(null)
              }}
            >
              افزودن به نوار دسترسی سریع
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              setQatMenu(null)
              setShowQatCustomize(true)
            }}
          >
            سفارشی‌سازی نوار سریع...
          </button>
        </div>
      )}

      {/* Tabs — اسکرول افقی بالای نام برگه‌ها */}
      <div className="tab-bar-wrap">
        <div className="tab-bar-scroll">
          <div className="tab-bar">
            {visibleTabs.map((tab) => (
              <button
                key={tab.id}
                className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => {
                  if (!isFullAdmin && !canAccessTab(tab.id)) {
                    window.alert('شما مجوز دسترسی به این برگه را ندارید')
                    return
                  }
                  // تعویض فوری برگه؛ بارگذاری داده بعد از paint
                  startTransition(() => {
                    setActiveTab(tab.id)
                    if (tab.id === 'mojaz') {
                      setMojazSubView('list')
                      setMjzViewItem(null)
                      setMjzMsg('')
                    }
                  })
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Ribbon */}
      <div className="ribbon">
        {ribbonGroups.map((group, gi) => (
          <div className="ribbon-group" key={gi}>
            <div className="ribbon-group-buttons">
              {group.items.map((item, ii) => {
                if (item.type === 'large') {
                  const flat = String(item.label || '').replace(/\n/g, ' ')
                  const needsSel =
                    activeTab === 'personnel' &&
                    (flat.includes('ویرایش') ||
                      flat.includes('عکس') ||
                      flat.includes('مدارک') ||
                      flat.includes('صدور کارت') ||
                      flat.includes('سطح دسترسی') ||
                      flat.includes('وابستگان') ||
                      flat.includes('سوابق') ||
                      flat.includes('سفر خارجی'))
                  const dimmed = needsSel && !selectedPersonnel
                  return (
                    <button
                      className={`btn-large${isRibbonActionActive(item.code) ? ' active' : ''}`}
                      key={ii}
                      onClick={() => onAction(item.code)}
                      onContextMenu={(e) => openRibbonContextMenu(e, item.label, item.code)}
                      title={
                        dimmed
                          ? 'ابتدا یک پرسنل را از لیست انتخاب کنید'
                          : selectedPersonnel && needsSel
                            ? `${flat} — ${selectedPersonnel.first_name || ''} ${selectedPersonnel.last_name || ''}`
                            : `${flat} — راست‌کلیک: افزودن به نوار سریع`
                      }
                      style={dimmed ? { opacity: 0.45 } : undefined}
                    >
                      <div className="icon">{renderRibbonIcon(item.icon, item.label)}</div>
                      <div className="label">
                        {item.label.split('\n').map((line, li) => (
                          <React.Fragment key={li}>
                            {line}
                            {li < item.label.split('\n').length - 1 && <br />}
                          </React.Fragment>
                        ))}
                      </div>
                    </button>
                  )
                }
                if (item.type === 'stack') {
                  return (
                    <div className="btn-stack" key={ii}>
                      {item.buttons.map((btn, bi) => {
                        const flat = String(btn.label || '').replace(/\n/g, ' ')
                        const needsSel =
                          activeTab === 'personnel' &&
                          (flat.includes('پیوست') ||
                            flat.includes('چاپ پرونده') ||
                            flat.includes('تمدید') ||
                            flat.includes('مسدود'))
                        const dimmed = needsSel && !selectedPersonnel
                        return (
                          <button
                            className="btn-small"
                            key={bi}
                            onClick={() => onAction(btn.code)}
                            onContextMenu={(e) => openRibbonContextMenu(e, btn.label, btn.code)}
                            title={
                              dimmed
                                ? 'ابتدا یک پرسنل را از لیست انتخاب کنید'
                                : `${flat} — راست‌کلیک: افزودن به نوار سریع`
                            }
                            style={dimmed ? { opacity: 0.45 } : undefined}
                          >
                            <span className="icon">{renderRibbonIcon(btn.icon, btn.label, true)}</span>
                            {btn.label}
                          </button>
                        )
                      })}
                    </div>
                  )
                }
                return null
              })}
            </div>
            <div className="ribbon-group-title">{group.title}</div>
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div
          className={`sidebar${sidebarPinned ? ' sidebar-open' : ''}`}
          title={sidebarPinned ? 'منو سنجاق شده — برای بستن کلیک کنید' : 'برای نمایش منو ماوس را اینجا نگه دارید'}
        >
          <button
            type="button"
            className="sidebar-pin-btn"
            title={sidebarPinned ? 'برداشتن سنجاق' : 'سنجاق کردن منو'}
            onClick={(e) => { e.stopPropagation(); setSidebarPinned((v) => !v) }}
          >{sidebarPinned ? '📌' : '📍'}</button>
          {activeTab === 'personnel' ? (
            <>
              <h3>منوی سریع پرسنل</h3>
              <div
                className={`sidebar-item ${!showRegisterForm && !showDependents && !showCards && !personnelRecordKind && !showAssignOrg ? 'active' : ''}`}
                onClick={() => { cancelPersonnelForm(); setShowDependents(false); setShowCards(false); setPersonnelRecordKind(null); setShowAssignOrg(false) }}
              >
                📋 لیست پرسنل
              </div>
              <div
                className={`sidebar-item ${showRegisterForm ? 'active' : ''}`}
                onClick={() => {
                  setEditingId(null)
                  setFormData(emptyForm)
                  setFormMsg('')
                  setShowRegisterForm(true)
                  setShowDependents(false)
                  setShowCards(false)
                  setShowAssignOrg(false)
                  setPersonnelRecordKind(null)
                }}
              >
                ➕ ثبت مشخصات پرسنل
              </div>
              <div
                className={`sidebar-item ${showAssignOrg ? 'active' : ''}`}
                onClick={() => {
                  setShowAssignOrg(true)
                  setShowRegisterForm(false)
                  setShowDependents(false)
                  setShowCards(false)
                  setPersonnelRecordKind(null)
                  setAssignOrgMsg('')
                  loadUnits()
                  loadCompanies()
                  const p = selectedPersonnel
                  setAssignOrgForm({
                    company_code: p?.company_code != null ? String(p.company_code) : '',
                    center: p?.center || '',
                    department: p?.department || '',
                  })
                }}
              >
                🏢 تخصیص شرکت مرکز و واحد
              </div>
              <div className="sidebar-item" onClick={() => document.getElementById('personnel-search-input')?.focus()}>
                🔍 جستجوی پرسنل
              </div>
              <div
                className={`sidebar-item ${showCards ? 'active' : ''}`}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                onClick={() => {
                  const p = selectedPersonnel || requireSelectedPersonnel('صدور کارت')
                  if (!p) return
                  if (!p.company_code) {
                    window.alert('ابتدا از «تخصیص شرکت به پرسنل» شرکت تابعه را تخصیص دهید.')
                    setShowAssignOrg(true)
                    setShowCards(false)
                    setShowRegisterForm(false)
                    setAssignOrgForm({
                      company_code: '',
                      center: p.center || '',
                      department: p.department || '',
                    })
                    return
                  }
                  setShowRegisterForm(false)
                  setShowDependents(false)
                  setShowAssignOrg(false)
                  setShowCards(true)
                  setEditingCardId(null)
                  setCardMsg('')
                  loadCards(p)
                }}
              >
                <IconIdCard size={16} color="#4a5568" />
                صدور کارت
              </div>
              <div
                className={`sidebar-item ${showDependents ? 'active' : ''}`}
                onClick={() => {
                  const p = selectedPersonnel || requireSelectedPersonnel('وابستگان')
                  if (!p) return
                  setShowRegisterForm(false)
                  setShowCards(false)
                  setPersonnelRecordKind(null)
                  setShowDependents(true)
                  setEditingDepId(null)
                  setDepMsg('')
                  loadDependents(p)
                }}
              >
                👨👦 وابستگان
              </div>
              <div className={`sidebar-item ${personnelRecordKind === 'service' ? 'active' : ''}`} onClick={() => openPersonnelRecords('service', 'سوابق خدماتی')}>📋 سوابق خدماتی</div>
              <div className={`sidebar-item ${personnelRecordKind === 'travel' ? 'active' : ''}`} onClick={() => openPersonnelRecords('travel', 'سفر خارجی')}>✈️ سفر خارجی</div>
              <div className={`sidebar-item ${personnelRecordKind === 'medical' ? 'active' : ''}`} onClick={() => openPersonnelRecords('medical', 'سوابق پزشکی')}>🏥 سوابق پزشکی</div>
            </>
          ) : activeTab === 'baseinfo' ? (
            <>
              <h3>اطلاعات پایه</h3>
              <div className={`sidebar-item ${baseSubView === 'edu' ? 'active' : ''}`} onClick={() => setBaseSubView('edu')}>🎓 رشته تحصیلی</div>
              <div className={`sidebar-item ${baseSubView === 'resp' ? 'active' : ''}`} onClick={() => setBaseSubView('resp')}>💼 گروه مسئولیت</div>
              <div className={`sidebar-item ${baseSubView === 'emp' ? 'active' : ''}`} onClick={() => setBaseSubView('emp')}>📋 انواع استخدام</div>
              <div className={`sidebar-item ${baseSubView === 'doors' ? 'active' : ''}`} onClick={() => setBaseSubView('doors')}>🚪 تعریف درب‌های تردد</div>
              <div className={`sidebar-item ${baseSubView === 'goods' ? 'active' : ''}`} onClick={() => setBaseSubView('goods')}>📦 تعریف مقصد کالا</div>
              <div className={`sidebar-item ${baseSubView === 'services' ? 'active' : ''}`} onClick={() => setBaseSubView('services')}>🚌 تعریف سرویس</div>
              <div className={`sidebar-item ${baseSubView === 'clients' ? 'active' : ''}`} onClick={() => setBaseSubView('clients')}>🏢 تعریف شرکت/مشتری</div>
              <div className={`sidebar-item ${baseSubView === 'entry_exit' ? 'active' : ''}`} onClick={() => setBaseSubView('entry_exit')}>↔️ تعریف نوع ورود و خروج</div>
              <div className={`sidebar-item ${baseSubView === 'door_access' ? 'active' : ''}`} onClick={() => setBaseSubView('door_access')}>🔑 دسترسی درب</div>
              <div className={`sidebar-item ${baseSubView === 'veh_types' ? 'active' : ''}`} onClick={() => setBaseSubView('veh_types')}>🚘 تعریف نوع خودروها</div>
              <div className={`sidebar-item ${baseSubView === 'vehicles' ? 'active' : ''}`} onClick={() => setBaseSubView('vehicles')}>🚗 تعریف خودروها</div>
              <div className={`sidebar-item ${baseSubView === 'cargo_vehicles' ? 'active' : ''}`} onClick={() => setBaseSubView('cargo_vehicles')}>🚛 تعریف خودروهای باری</div>
              <div className={`sidebar-item ${baseSubView === 'cargo_reasons' ? 'active' : ''}`} onClick={() => setBaseSubView('cargo_reasons')}>📝 علت تردد خودروهای باری</div>
              <div className={`sidebar-item ${baseSubView === 'goods_io' ? 'active' : ''}`} onClick={() => setBaseSubView('goods_io')}>📥 انواع ورود و خروج کالا</div>
              <div className={`sidebar-item ${baseSubView === 'goods_products' ? 'active' : ''}`} onClick={() => setBaseSubView('goods_products')}>📦 تعریف کالا و محصولات</div>
            </>
          ) : activeTab === 'gozaresh' ? (
            <>
              <h3>گزارشات</h3>
              {[
                ['guest', '🧑 گزارشات میهمان'],
                ['personnel_traffic', '🚶 تردد پرسنل و پیمانکاران'],
                ['vehicle_traffic', '🚗 تردد خودرو پرسنل/پیمانکار'],
                ['goods_io', '📦 ورود و خروج کالا'],
                ['goods_repair', '🔧 کالای تعمیری و خدمات'],
                ['personnel', '👥 گزارش پرسنل'],
                ['contractor_personnel', '👷 پرسنل پیمانکار'],
                ['cargo_vehicle', '🚛 تردد خودروهای باری'],
                ['guard_board', '📋 لوح نگهبانی'],
                ['replacement', '🔁 درخواست جایگزینی'],
                ['misc_traffic', '👤 تردد افراد متفرقه'],
                ['system_log', '🧾 گزارش لاگ'],
                ['contractor_goods', '🏢 کالای پیمانکار'],
                ['traffic_request', '📝 درخواست تردد'],
                ['guest_reserve', '🗓️ رزرو میهمان'],
                ['personnel_history', '📜 تاریخچه پرسنل'],
                ['goods_reserve', '📥 رزرو کالا'],
              ].map(([k, label]) => (
                <div key={k} className={`sidebar-item ${reportKey === k ? 'active' : ''}`} onClick={() => setReportKey(k)}>{label}</div>
              ))}
            </>
          ) : activeTab === 'entezamat' ? (

            <>
              <h3>انتظامات</h3>
              <div className={`sidebar-item ${entezamatSubView === 'guard_board' ? 'active' : ''}`} onClick={() => setEntezamatSubView('guard_board')}>📋 لوح نگهبانی</div>
              <div className={`sidebar-item ${entezamatSubView === 'shift_events' ? 'active' : ''}`} onClick={() => setEntezamatSubView('shift_events')}>📝 ثبت وقایع شیفت</div>
              <div className={`sidebar-item ${entezamatSubView === 'shift_schedule' ? 'active' : ''}`} onClick={() => setEntezamatSubView('shift_schedule')}>📅 برنامه نوبتکاری</div>
              <div className={`sidebar-item ${entezamatSubView === 'electronics' ? 'active' : ''}`} onClick={() => setEntezamatSubView('electronics')}>📻 تجهیزات الکترونیک پرسنل</div>
              <div className={`sidebar-item ${entezamatSubView === 'replacement' ? 'active' : ''}`} onClick={() => setEntezamatSubView('replacement')}>🔁 درخواست جایگزینی</div>
              <div className={`sidebar-item ${entezamatSubView === 'permits' ? 'active' : ''}`} onClick={() => setEntezamatSubView('permits')}>📄 صدور مجوز</div>
              <div className={`sidebar-item ${entezamatSubView === 'mon_events' ? 'active' : ''}`} onClick={() => setEntezamatSubView('mon_events')}>🖥️ وقایع اتاق مانیتورینگ</div>
              <div className={`sidebar-item ${entezamatSubView === 'mon_staff' ? 'active' : ''}`} onClick={() => setEntezamatSubView('mon_staff')}>👤 مسئولین مانیتورینگ</div>
              <div className={`sidebar-item ${entezamatSubView === 'guard_reports' ? 'active' : ''}`} onClick={() => setEntezamatSubView('guard_reports')}>📊 گزارش نگهبانی</div>
              <div className={`sidebar-item ${entezamatSubView === 'guard_referrals' ? 'active' : ''}`} onClick={() => setEntezamatSubView('guard_referrals')}>↪️ گزارش ارجاع نگهبانی</div>
              <div className={`sidebar-item ${entezamatSubView === 'roll_call' ? 'active' : ''}`} onClick={() => setEntezamatSubView('roll_call')}>✅ رول‌کال</div>
              <div className={`sidebar-item ${entezamatSubView === 'board_summary' ? 'active' : ''}`} onClick={() => setEntezamatSubView('board_summary')}>📌 لوح نگهبانی اجمالی</div>
              <div className={`sidebar-item ${entezamatSubView === 'guard_events' ? 'active' : ''}`} onClick={() => setEntezamatSubView('guard_events')}>📓 ثبت وقایع نگهبانی</div>
              <div className={`sidebar-item ${entezamatSubView === 'deploy' ? 'active' : ''}`} onClick={() => setEntezamatSubView('deploy')}>📍 محل استقرار</div>
              <div className={`sidebar-item ${entezamatSubView === 'officer_events' ? 'active' : ''}`} onClick={() => setEntezamatSubView('officer_events')}>🛡️ وقایع افسر نگهبانی</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>تعاریف پایه</div>
              <div className={`sidebar-item ${entezamatSubView === 'groups' ? 'active' : ''}`} onClick={() => setEntezamatSubView('groups')}>👥 تعریف گروه</div>
              <div className={`sidebar-item ${entezamatSubView === 'prot_centers' ? 'active' : ''}`} onClick={() => setEntezamatSubView('prot_centers')}>🏛️ مراکز حفاظتی</div>
              <div className={`sidebar-item ${entezamatSubView === 'prot_places' ? 'active' : ''}`} onClick={() => setEntezamatSubView('prot_places')}>📍 اماکن حفاظتی</div>
              <div className={`sidebar-item ${entezamatSubView === 'shift_hours' ? 'active' : ''}`} onClick={() => setEntezamatSubView('shift_hours')}>⏰ ساعت‌های شیفت</div>
              <div className={`sidebar-item ${entezamatSubView === 'shift_leaders' ? 'active' : ''}`} onClick={() => setEntezamatSubView('shift_leaders')}>🧑‍💼 مسئول شیفت</div>
              <div className={`sidebar-item ${entezamatSubView === 'work_shifts' ? 'active' : ''}`} onClick={() => setEntezamatSubView('work_shifts')}>🔄 نوبت کار</div>
              <div className={`sidebar-item ${entezamatSubView === 'staff_status' ? 'active' : ''}`} onClick={() => setEntezamatSubView('staff_status')}>📋 وضعیت پرسنل</div>
              <div className={`sidebar-item ${entezamatSubView === 'equipment' ? 'active' : ''}`} onClick={() => setEntezamatSubView('equipment')}>🛡️ تجهیزات نگهبانی</div>
            </>
          ) : activeTab === 'sodor_kart' ? (
            <>
              <h3>صدور کارت</h3>
              <details className="sidebar-group" open>
                <summary>کارت پرسنل و پیمانکار</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${cardSubView === 'personnel_card' ? 'active' : ''}`} onClick={() => setCardSubView('personnel_card')}>🪪 چاپ کارت پرسنل</div>
                  <div className={`sidebar-item ${cardSubView === 'contractor_card' ? 'active' : ''}`} onClick={() => setCardSubView('contractor_card')}>🪪 چاپ کارت پیمانکاران</div>
                  <div className={`sidebar-item ${cardSubView === 'issued_report' ? 'active' : ''}`} onClick={() => setCardSubView('issued_report')}>📊 گزارش کارت‌های صادر شده</div>
                </div>
              </details>
              <details className="sidebar-group" open>
                <summary>کارت خودرو</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${cardSubView === 'vehicle_personnel' ? 'active' : ''}`} onClick={() => setCardSubView('vehicle_personnel')}>🚗 چاپ کارت خودروی پرسنل</div>
                  <div className={`sidebar-item ${cardSubView === 'vehicle_contractor' ? 'active' : ''}`} onClick={() => setCardSubView('vehicle_contractor')}>🚛 چاپ کارت خودروی پیمانکاران</div>
                  <div className={`sidebar-item ${cardSubView === 'vehicle_report' ? 'active' : ''}`} onClick={() => setCardSubView('vehicle_report')}>📋 گزارش کارت‌های خودروی صادر شده</div>
                </div>
              </details>
            </>
          ) : activeTab === 'mojaz' ? (
            <>
              <h3>صدور مجوز تردد</h3>
              <details className="sidebar-group" open>
                <summary>صدور انواع مجوز</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${mojazSubView === 'person' ? 'active' : ''}`} onClick={() => { setMojazSubView('person'); resetMjzForm('person') }}>👤 مجوز تردد نفر</div>
                  <div className={`sidebar-item ${mojazSubView === 'vehicle' ? 'active' : ''}`} onClick={() => { setMojazSubView('vehicle'); resetMjzForm('vehicle') }}>🚗 مجوز تردد خودرو</div>
                  <div className={`sidebar-item ${mojazSubView === 'goods' ? 'active' : ''}`} onClick={() => { setMojazSubView('goods'); resetMjzForm('goods') }}>📦 مجوز خروج کالا</div>
                </div>
              </details>
              <details className="sidebar-group" open>
                <summary>نگهبانی و پیگیری</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${mojazSubView === 'list' ? 'active' : ''}`} onClick={() => { setMojazSubView('list'); setMjzViewItem(null); loadMjzPermits({ q: mjzSearchNo || undefined }) }}>📋 لیست و تأیید مجوزها</div>
                  <div className={`sidebar-item ${mojazSubView === 'report' ? 'active' : ''}`} onClick={() => { setMojazSubView('report'); loadMjzPermits() }}>📊 گزارش مجوزها (CSV)</div>
                </div>
              </details>
              <details className="sidebar-group" open>
                <summary>ترددهای خاص</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${mojazSubView === 'trd_train' ? 'active' : ''}`} onClick={() => setMojazSubView('trd_train')}>🚂 قطار و واگن باری</div>
                  <div className={`sidebar-item ${mojazSubView === 'trd_ship' ? 'active' : ''}`} onClick={() => setMojazSubView('trd_ship')}>🚢 تردد کشتی در اسکله</div>
                  <div className={`sidebar-item ${mojazSubView === 'trd_foreign' ? 'active' : ''}`} onClick={() => setMojazSubView('trd_foreign')}>👤 اتباع خارج‌شده از کشتی</div>
                  <div className={`sidebar-item ${mojazSubView === 'trd_water' ? 'active' : ''}`} onClick={() => setMojazSubView('trd_water')}>💧 آبگیری شناورها</div>
                  <div className={`sidebar-item ${mojazSubView === 'trd_sec' ? 'active' : ''}`} onClick={() => setMojazSubView('trd_sec')}>🔒 اطلاعات امنیتی کشتی</div>
                </div>
              </details>
            </>
          ) : activeTab === 'peymankar' ? (
            <>
              <h3>پیمانکاران</h3>
              <details className="sidebar-group" open>
                <summary>شرکت و قرارداد</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${peymankarSubView === 'companies' ? 'active' : ''}`} onClick={() => setPeymankarSubView('companies')}>🏢 شرکت‌های پیمانکار</div>
                  <div className={`sidebar-item ${peymankarSubView === 'contracts' ? 'active' : ''}`} onClick={() => setPeymankarSubView('contracts')}>📄 قرارداد شرکت‌های پیمانکار</div>
                </div>
              </details>
              <details className="sidebar-group" open>
                <summary>پرسنل و ناوگان</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${peymankarSubView === 'personnel' ? 'active' : ''}`} onClick={() => setPeymankarSubView('personnel')}>👷 پرسنل شرکت‌های پیمانکار</div>
                  <div className={`sidebar-item ${peymankarSubView === 'vehicles' ? 'active' : ''}`} onClick={() => setPeymankarSubView('vehicles')}>🚛 ثبت خودروهای پیمانکاران</div>
                  <div className={`sidebar-item ${peymankarSubView === 'drivers' ? 'active' : ''}`} onClick={() => setPeymankarSubView('drivers')}>🪪 ثبت راننده‌های پیمانکاران</div>
                  <div className={`sidebar-item ${peymankarSubView === 'report' ? 'active' : ''}`} onClick={() => { setPeymankarSubView('report'); loadPymReport(pymReportKind || 'summary') }}>📊 گزارش‌گیری پیمانکاران</div>
                </div>
              </details>
            </>
          ) : activeTab === 'monitoring' ? (
            <>
              <h3>گشت و پایش</h3>
              <div style={{ margin: '4px 0', fontSize: 11, color: '#718096' }}>تنظیمات</div>
              <div className={`sidebar-item ${patrolSubView === 'devices' ? 'active' : ''}`} onClick={() => setPatrolSubView('devices')}>📟 لیست دستگاه‌ها</div>
              <div className={`sidebar-item ${patrolSubView === 'events' ? 'active' : ''}`} onClick={() => setPatrolSubView('events')}>📋 لیست رخدادها</div>
              <div className={`sidebar-item ${patrolSubView === 'checkpoints' ? 'active' : ''}`} onClick={() => setPatrolSubView('checkpoints')}>📍 لیست نقاط بازدید</div>
              <div className={`sidebar-item ${patrolSubView === 'guards' ? 'active' : ''}`} onClick={() => setPatrolSubView('guards')}>🛡️ لیست نگهبانان</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>پیکربندی عملیاتی</div>
              <div className={`sidebar-item ${patrolSubView === 'route_config' ? 'active' : ''}`} onClick={() => setPatrolSubView('route_config')}>🗺️ پیکربندی مسیر</div>
              <div className={`sidebar-item ${patrolSubView === 'routes' ? 'active' : ''}`} onClick={() => setPatrolSubView('routes')}>🛤️ مسیرها و ساعات شروع</div>
              <div className={`sidebar-item ${patrolSubView === 'shift_times' ? 'active' : ''}`} onClick={() => setPatrolSubView('shift_times')}>⏰ تعیین ساعت شروع و پایان</div>
            </>

          ) : activeTab === 'herasat' ? (
            <>
              <h3>حراست</h3>
              <details className="sidebar-group" open>
                <summary>ارزشیابی پرسنل</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${herasatSubView === 'eval_options' ? 'active' : ''}`} onClick={() => setHerasatSubView('eval_options')}>📊 گزینه‌های ارزشیابی</div>
                  <div className={`sidebar-item ${herasatSubView === 'eval_titles' ? 'active' : ''}`} onClick={() => setHerasatSubView('eval_titles')}>📝 عناوین ارزشیابی</div>
                  <div className={`sidebar-item ${herasatSubView === 'eval_periods' ? 'active' : ''}`} onClick={() => setHerasatSubView('eval_periods')}>📅 تعریف دوره ارزشیابی</div>
                  <div className={`sidebar-item ${herasatSubView === 'eval_monthly' ? 'active' : ''}`} onClick={() => setHerasatSubView('eval_monthly')}>👤 ارزشیابی ماهانه پرسنل</div>
                </div>
              </details>
              <details className="sidebar-group">
                <summary>منازل و اماکن</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${herasatSubView === 'areas' ? 'active' : ''}`} onClick={() => setHerasatSubView('areas')}>🗺️ تعریف نواحی</div>
                  <div className={`sidebar-item ${herasatSubView === 'houses' ? 'active' : ''}`} onClick={() => setHerasatSubView('houses')}>🏠 تعریف منازل</div>
                  <div className={`sidebar-item ${herasatSubView === 'house_delivery' ? 'active' : ''}`} onClick={() => setHerasatSubView('house_delivery')}>🔑 تحویل منازل و اماکن</div>
                </div>
              </details>
              <details className="sidebar-group" open>
                <summary>کنترل حراست</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${herasatSubView === 'violations_personnel' ? 'active' : ''}`} onClick={() => setHerasatSubView('violations_personnel')}>⚠️ تخلفات پرسنل و پیمانکار</div>
                  <div className={`sidebar-item ${herasatSubView === 'violations_vehicle' ? 'active' : ''}`} onClick={() => setHerasatSubView('violations_vehicle')}>🚗 تخلفات خودرویی</div>
                  <div className={`sidebar-item ${herasatSubView === 'incidents' ? 'active' : ''}`} onClick={() => setHerasatSubView('incidents')}>📋 صورتجلسه حوادث</div>
                  <div className={`sidebar-item ${herasatSubView === 'drug_tests' ? 'active' : ''}`} onClick={() => setHerasatSubView('drug_tests')}>🧪 مصرف مواد مخدر</div>
                  <div className={`sidebar-item ${herasatSubView === 'rewards' ? 'active' : ''}`} onClick={() => setHerasatSubView('rewards')}>🏆 تقدیر و تشویق</div>
                </div>
              </details>
              <details className="sidebar-group">
                <summary>اتباع و مدارک</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${herasatSubView === 'foreign_nationals' ? 'active' : ''}`} onClick={() => setHerasatSubView('foreign_nationals')}>🌍 اتباع خارجی</div>
                  <div className={`sidebar-item ${herasatSubView === 'countries' ? 'active' : ''}`} onClick={() => setHerasatSubView('countries')}>🏳️ مشخصات کشورها</div>
                  <div className={`sidebar-item ${herasatSubView === 'doc_archive' ? 'active' : ''}`} onClick={() => setHerasatSubView('doc_archive')}>📁 بایگانی مدارک</div>
                </div>
              </details>
              <details className="sidebar-group">
                <summary>سفر و خروج</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${herasatSubView === 'travel_abroad' ? 'active' : ''}`} onClick={() => setHerasatSubView('travel_abroad')}>✈️ اعزام به خارج</div>
                  <div className={`sidebar-item ${herasatSubView === 'travel_personal' ? 'active' : ''}`} onClick={() => setHerasatSubView('travel_personal')}>🧳 سفرهای شخصی</div>
                  <div className={`sidebar-item ${herasatSubView === 'exit_admin' ? 'active' : ''}`} onClick={() => setHerasatSubView('exit_admin')}>📄 خروج مدارک اداری</div>
                  <div className={`sidebar-item ${herasatSubView === 'exit_scientific' ? 'active' : ''}`} onClick={() => setHerasatSubView('exit_scientific')}>📚 خروج مدارک علمی</div>
                </div>
              </details>
              <details className="sidebar-group" open>
                <summary>گزارش‌ها</summary>
                <div className="sidebar-group-body">
                  <div className={`sidebar-item ${herasatSubView === 'news' ? 'active' : ''}`} onClick={() => setHerasatSubView('news')}>📢 گزارش خبر</div>
                </div>
              </details>
            </>
          ) : activeTab === 'monaghese' ? (
            <>
              <h3>مناقصات و مزایدات</h3>
              <div className={`sidebar-item ${monagheseSubView === 'companies' ? 'active' : ''}`} onClick={() => setMonagheseSubView('companies')}>🏢 شرکت‌های حاضر در مناقصه/مزایده</div>
              <div className={`sidebar-item ${monagheseSubView === 'tenders' ? 'active' : ''}`} onClick={() => setMonagheseSubView('tenders')}>📢 مناقصات</div>
              <div className={`sidebar-item ${monagheseSubView === 'auctions' ? 'active' : ''}`} onClick={() => setMonagheseSubView('auctions')}>🔨 مزایده</div>
              <div className={`sidebar-item ${monagheseSubView === 'contracts' ? 'active' : ''}`} onClick={() => setMonagheseSubView('contracts')}>📄 قراردادها</div>
            </>
          ) : activeTab === 'kartabl' ? (
            <>
              <h3>کارتابل</h3>
              <div className={`sidebar-item ${kartablSubView === 'outgoing' ? 'active' : ''}`} onClick={() => setKartablSubView('outgoing')}>📤 نامه‌های صادره</div>
              <div className={`sidebar-item ${kartablSubView === 'inbox' ? 'active' : ''}`} onClick={() => setKartablSubView('inbox')}>📥 نامه‌های وارده</div>
              <div className={`sidebar-item ${kartablSubView === 'management' ? 'active' : ''}`} onClick={() => setKartablSubView('management')}>📬 مدیریت کارتابل</div>
              <div className={`sidebar-item ${kartablSubView === 'folders' ? 'active' : ''}`} onClick={() => setKartablSubView('folders')}>📁 پوشه‌های بایگانی</div>
            </>
          ) : activeTab === 'baskool' ? (
            <>
              <h3>باسکول</h3>
              <div className={`sidebar-item ${baskoolSubView === 'weighings' ? 'active' : ''}`} onClick={() => setBaskoolSubView('weighings')}>⚖️ ثبت توزین</div>
              <div className={`sidebar-item ${baskoolSubView === 'turns' ? 'active' : ''}`} onClick={() => setBaskoolSubView('turns')}>🎫 سیستم ثبت نوبت</div>
              <div className={`sidebar-item ${baskoolSubView === 'traffic_ban' ? 'active' : ''}`} onClick={() => setBaskoolSubView('traffic_ban')}>🚫 ممنوعیت تردد</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>اطلاعات پایه</div>
              <div className={`sidebar-item ${baskoolSubView === 'companies' ? 'active' : ''}`} onClick={() => setBaskoolSubView('companies')}>🏢 تعریف شرکت‌ها</div>
              <div className={`sidebar-item ${baskoolSubView === 'max_tonnage' ? 'active' : ''}`} onClick={() => setBaskoolSubView('max_tonnage')}>📦 حداکثر تناژ</div>
              <div className={`sidebar-item ${baskoolSubView === 'settings' ? 'active' : ''}`} onClick={() => setBaskoolSubView('settings')}>⚙️ تنظیمات باسکول</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>گزارشات</div>
              <div className={`sidebar-item ${baskoolSubView === 'weigh_reports' ? 'active' : ''}`} onClick={() => setBaskoolSubView('weigh_reports')}>📊 گزارش توزین</div>
            </>
          ) : activeTab === 'pelakhwan' ? (
            <>
              <h3>پلاک‌خوان</h3>
              <div className={`sidebar-item ${pelakhwanSubView === 'process' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('process')}>🔍 فرم پردازش پلاک‌خوان</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'traffic' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('traffic')}>🚗 تردد پلاک‌خوان</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'monitoring' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('monitoring')}>📡 مانیتورینگ پلاک‌خوان</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'parking' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('parking')}>🅿️ فرم پارکینگ</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>گزارشات</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'traffic_report' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('traffic_report')}>📊 گزارش تردد</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'full_traffic_report' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('full_traffic_report')}>📋 گزارش تردد کامل</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'access_level' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('access_level')}>🔐 سطح دسترسی خودروها</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'inside_vehicles' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('inside_vehicles')}>🏢 خودروهای داخل سازمان</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>تنظیمات</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'cameras' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('cameras')}>📷 تعریف دوربین‌ها</div>
              <div className={`sidebar-item ${pelakhwanSubView === 'online_monitor' ? 'active' : ''}`} onClick={() => setPelakhwanSubView('online_monitor')}>📺 مانیتورینگ آنلاین</div>
            </>
          ) : activeTab === 'access' ? (
            <>
              <h3>کنترل دسترسی</h3>
              <div className={`sidebar-item ${accessSubView === 'traffic' ? 'active' : ''}`} onClick={() => setAccessSubView('traffic')}>🚶 فرم تردد RFID</div>
              <div className={`sidebar-item ${accessSubView === 'access_def' ? 'active' : ''}`} onClick={() => setAccessSubView('access_def')}>🔑 تعریف دسترسی</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>مهمان</div>
              <div className={`sidebar-item ${accessSubView === 'guests' ? 'active' : ''}`} onClick={() => setAccessSubView('guests')}>👤 مهمان</div>
              <div className={`sidebar-item ${accessSubView === 'guest_cards' ? 'active' : ''}`} onClick={() => setAccessSubView('guest_cards')}>💳 کارت مهمان‌ها</div>
              <div className={`sidebar-item ${accessSubView === 'guest_zone' ? 'active' : ''}`} onClick={() => setAccessSubView('guest_zone')}>🗺️ محدوده تردد مهمان</div>
              <div className={`sidebar-item ${accessSubView === 'guest_delivered' ? 'active' : ''}`} onClick={() => setAccessSubView('guest_delivered')}>📤 کارت‌های تحویل‌شده</div>
              <div className={`sidebar-item ${accessSubView === 'guest_report' ? 'active' : ''}`} onClick={() => setAccessSubView('guest_report')}>📊 گزارش تردد مهمانان</div>
              <div style={{ margin: '8px 0 4px', fontSize: 11, color: '#718096' }}>تخصیص و دستگاه</div>
              <div className={`sidebar-item ${accessSubView === 'assign' ? 'active' : ''}`} onClick={() => setAccessSubView('assign')}>✅ فرم تخصیص</div>
              <div className={`sidebar-item ${accessSubView === 'terminals' ? 'active' : ''}`} onClick={() => setAccessSubView('terminals')}>🖥️ ترمینال‌ها</div>
              <div className={`sidebar-item ${accessSubView === 'terminal_status' ? 'active' : ''}`} onClick={() => setAccessSubView('terminal_status')}>📡 وضعیت ترمینال‌ها</div>
              <div className={`sidebar-item ${accessSubView === 'user_sync' ? 'active' : ''}`} onClick={() => setAccessSubView('user_sync')}>🔄 همسان‌سازی کاربران</div>
              <div className={`sidebar-item ${accessSubView === 'general_report' ? 'active' : ''}`} onClick={() => setAccessSubView('general_report')}>📋 گزارشات کلی</div>
            </>
          ) : activeTab === 'workflow' ? (
            <>
              <h3>جریان کار</h3>
              <div className={`sidebar-item ${workflowSubView === 'request_types' ? 'active' : ''}`} onClick={() => setWorkflowSubView('request_types')}>📋 انواع درخواست</div>
              <div className={`sidebar-item ${workflowSubView === 'approvers' ? 'active' : ''}`} onClick={() => setWorkflowSubView('approvers')}>✅ تاییدکننده درخواست</div>
              <div className={`sidebar-item ${workflowSubView === 'delegation' ? 'active' : ''}`} onClick={() => setWorkflowSubView('delegation')}>🔀 تفویض اختیار</div>
              <div className={`sidebar-item ${workflowSubView === 'parking_docs' ? 'active' : ''}`} onClick={() => setWorkflowSubView('parking_docs')}>🅿️ تاییدات پارکینگ و مدارک</div>
            </>
          ) : activeTab === 'modiriat' ? (
            <>
              <h3>مدیریت سیستم</h3>
              <div className={`sidebar-item ${workflowSubView === 'access_levels' ? 'active' : ''}`} onClick={() => { setWorkflowSubView('access_levels'); loadAccessLevels(); setAccessLevelMsg('') }}>🔒 تعریف سطح دسترسی</div>
              <div className={`sidebar-item ${workflowSubView === 'sys_users' ? 'active' : ''}`} onClick={() => { setWorkflowSubView('sys_users'); loadSysUsers(); loadAccessLevels(); setSysUserMsg('') }}>👥 تعریف کاربران</div>
              <div className={`sidebar-item ${workflowSubView === 'backup' ? 'active' : ''}`} onClick={() => { setWorkflowSubView('backup'); refreshBackupList() }}>💾 گرفتن نسخه پشتیبان</div>
              <div className={`sidebar-item ${workflowSubView === 'restore' ? 'active' : ''}`} onClick={() => { setWorkflowSubView('restore'); refreshBackupList() }}>♻️ بازیابی نسخه پشتیبان</div>
              <div className={`sidebar-item ${workflowSubView === 'settings' ? 'active' : ''}`} onClick={() => setWorkflowSubView('settings')}>⚙️ تنظیمات سیستم</div>
            </>
          ) : activeTab === 'companies' ? (
            <>
              <h3>منوی شرکت‌های تابعه</h3>
              <div
                className={`sidebar-item ${companySubView === 'list' && !showCompanyForm ? 'active' : ''}`}
                onClick={() => {
                  setShowCompanyForm(false)
                  setCompanySubView('list')
                  setEditingCompanyCode(null)
                  setCompanyMsg('')
                }}
              >
                📋 لیست شرکت‌ها
              </div>
              {isAdmin && (
                <div
                  className={`sidebar-item ${showCompanyForm || companySubView === 'form' ? 'active' : ''}`}
                  onClick={() => {
                    setEditingCompanyCode(null)
                    setCompanyForm({ name: '', short_name: '', description: '', parent_code: '', logo: '' })
                    setCompanyMsg('')
                    setShowCompanyForm(true)
                    setCompanySubView('form')
                  }}
                >
                  ➕ ثبت شرکت تابعه
                </div>
              )}
              <div
                className={`sidebar-item ${companySubView === 'units' ? 'active' : ''}`}
                onClick={() => {
                  setShowCompanyForm(false)
                  setCompanySubView('units')
                  setEditingCompanyCode(null)
                  loadUnits()
                  loadCompanies()
                }}
              >
                🏛️ تعریف واحد و مرکز
              </div>
              <div
                className="sidebar-item"
                onClick={() => {
                  setShowCompanyForm(false)
                  setCompanySubView('list')
                  setEditingCompanyCode(null)
                  loadCompanies()
                }}
              >
                🔄 به‌روزرسانی لیست
              </div>
            </>
          ) : (
            <>
              <h3>منوی سریع حراست</h3>
              <div className="sidebar-item active">📋 لیست تخلفات امروز</div>
              <div className="sidebar-item">🚨 حوادث باز</div>
              <div className="sidebar-item">🧪 آزمایش‌های در انتظار</div>
              <div className="sidebar-item">✈️ سفرهای ثبت‌شده</div>
              <div className="sidebar-item">🔍 بازدیدهای اخیر</div>
              <div className="sidebar-item">🚫 ممنوع‌الخروج‌ها</div>
              <div style={{ marginTop: 20 }} />
              <h3>اعلان‌های مهم</h3>
              <div className="sidebar-item" style={{ color: '#718096', fontSize: 12 }}>
                فعلاً اعلانی وجود ندارد
              </div>
            </>
          )}
        </div>

        <div className="workspace">
          {activeTab === 'companies' ? (
            <>
              <div className="workspace-header">
                <h2>
                  {companySubView === 'units'
                    ? 'تعریف واحد و مرکز (شرکت‌های تابعه)'
                    : showCompanyForm
                    ? (editingCompanyCode ? `ویرایش شرکت — کد ${editingCompanyCode}` : 'ثبت شرکت تابعه')
                    : `لیست شرکت‌های تابعه — ${filteredCompanies.length}${companySearch || companyStatusFilter !== 'all' ? ` از ${companies.length}` : ''} شرکت`}
                </h2>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  {!showCompanyForm && (
                    <input
                      type="text"
                      value={companySearch}
                      onChange={(e) => setCompanySearch(e.target.value)}
                      onFocus={focusCompanySearch}
                      placeholder="جستجوی سریع شرکت..."
                      style={{
                        padding: '6px 12px', border: '1px solid #cbd5e0', borderRadius: 6,
                        fontFamily: 'inherit', fontSize: 13, width: 220,
                      }}
                    />
                  )}
                  {isAdmin && (
                    <button
                      className="refresh-btn"
                      onClick={() => {
                        if (showCompanyForm) {
                          setShowCompanyForm(false)
                          setEditingCompanyCode(null)
                          setCompanyForm({ name: '', short_name: '', description: '', parent_code: '', logo: '' })
                          setCompanyMsg('')
                        } else {
                          setEditingCompanyCode(null)
                          setCompanyForm({ name: '', short_name: '', description: '', parent_code: '', logo: '' })
                          setCompanyMsg('')
                          setShowCompanyForm(true)
                        }
                      }}
                    >
                      {showCompanyForm ? '📋 بازگشت به لیست' : '➕ ثبت شرکت جدید'}
                    </button>
                  )}
                  {companySubView !== 'units' && !showCompanyForm && (
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => {
                        setCompanySubView('units')
                        setShowCompanyForm(false)
                        loadUnits()
                        loadCompanies()
                      }}
                    >
                      🏛️ تعریف واحد و مرکز
                    </button>
                  )}
                  {companySubView === 'units' && (
                    <button
                      type="button"
                      className="refresh-btn"
                      onClick={() => {
                        setCompanySubView('list')
                        setEditingUnitId(null)
                      }}
                    >
                      📋 بازگشت به لیست شرکت‌ها
                    </button>
                  )}

                </div>
              </div>

              {companySubView === 'units' ? (
                <div className="card">
                  {unitMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: unitMsg.includes('موفق') || unitMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                      color: unitMsg.includes('موفق') || unitMsg.includes('شد') ? '#276749' : '#c53030',
                    }}>{unitMsg}</div>
                  )}
                  <div style={{ marginBottom: 12, padding: '10px 12px', background: '#ebf8ff', borderRadius: 8, fontSize: 13, color: '#2c5282', border: '1px solid #90cdf4' }}>
                    <b>منبع تعریف مرکز و واحد:</b> زیرمجموعه شرکت‌های تابعه. نام مرکز و نام واحد اینجا ثبت می‌شود.
                    در برگه پرسنل از گزینه «تخصیص شرکت به پرسنل» برای اتصال پرسنل به این مقادیر استفاده کنید.
                    فیلد «شرکت» هر واحد را به یک شرکت تابعه وصل می‌کند.
                  </div>
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const isEdit = Boolean(editingUnitId)
                    const url = isEdit ? `/api/units/${editingUnitId}` : '/api/units'
                    const body = {
                      ...unitForm,
                      show_on_guard_board: unitForm.show_on_guard_board ? 1 : 0,
                      show_on_internet: unitForm.show_on_internet ? 1 : 0,
                    }
                    fetch(url, {
                      method: isEdit ? 'PUT' : 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(body),
                    })
                      .then(async (r) => {
                        const d = await r.json().catch(() => ({}))
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setUnitMsg(isEdit ? 'واحد ویرایش شد' : 'واحد با موفقیت ثبت شد')
                        setUnitForm({ code: '', name: '', parent_name: '', center_name: '', company_code: '', show_on_guard_board: true, show_on_internet: false, image_path: '', symbol_path: '' })
                        setEditingUnitId(null)
                        loadUnits()
                      })
                      .catch((err) => setUnitMsg(err.message || 'خطا'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {[
                        ['center_name', 'نام مرکز *'], ['name', 'نام واحد *'], ['parent_name', 'واحد والد'], ['code', 'کد واحد'],
                      ].map(([k, lab]) => (
                        <div key={k}>
                          <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>{lab}</label>
                          <input required={lab.includes('*')} value={unitForm[k] || ''} onChange={(e) => setUnitForm({ ...unitForm, [k]: e.target.value })}
                            style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                        </div>
                      ))}
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>شرکت تابعه</label>
                        <select value={unitForm.company_code || ''} onChange={(e) => setUnitForm({ ...unitForm, company_code: e.target.value })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="">— انتخاب شرکت —</option>
                          {companies.map((c) => (
                            <option key={c.code} value={c.code}>{c.code} — {c.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>نمایش در لوح نگهبانی</label>
                        <select value={unitForm.show_on_guard_board ? '1' : '0'} onChange={(e) => setUnitForm({ ...unitForm, show_on_guard_board: e.target.value === '1' })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="1">بلی</option><option value="0">خیر</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>نمایش در اینترنت</label>
                        <select value={unitForm.show_on_internet ? '1' : '0'} onChange={(e) => setUnitForm({ ...unitForm, show_on_internet: e.target.value === '1' })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="0">خیر</option><option value="1">بلی</option>
                        </select>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">{editingUnitId ? '💾 ذخیره ویرایش' : '💾 ثبت واحد'}</button>
                      <button type="button" className="refresh-btn" onClick={() => {
                        setUnitForm({ code: '', name: '', parent_name: '', center_name: '', company_code: '', show_on_guard_board: true, show_on_internet: false, image_path: '', symbol_path: '' })
                        setEditingUnitId(null)
                        setUnitMsg('')
                      }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={loadUnits}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead><tr><th>ردیف</th><th>کد</th><th>نام مرکز</th><th>نام واحد</th><th>شرکت</th><th>واحد والد</th><th>لوح نگهبانی</th><th>عملیات</th></tr></thead>
                      <tbody>
                        {units.length === 0 ? (
                          <tr><td colSpan={8} style={{ textAlign: 'center', color: '#718096' }}>واحدی ثبت نشده</td></tr>
                        ) : units.map((u, i) => (
                          <tr key={u.id || i}>
                            <td>{i + 1}</td>
                            <td>{u.code || '—'}</td>
                            <td>{u.center_name || '—'}</td>
                            <td>{u.name || '—'}</td>
                            <td>{(() => {
                              const co = companies.find((c) => String(c.code) === String(u.company_code))
                              return co ? `${co.code} — ${co.name}` : (u.company_code || '—')
                            })()}</td>
                            <td>{u.parent_name || '—'}</td>
                            <td>{u.show_on_guard_board ? '✓' : '—'}</td>
                            <td style={{ whiteSpace: 'nowrap' }}>
                              <button type="button" className="refresh-btn" style={{ marginLeft: 4 }} onClick={() => {
                                setUnitForm({
                                  code: u.code || '', name: u.name || '', parent_name: u.parent_name || '',
                                  center_name: u.center_name || '', company_code: u.company_code != null ? String(u.company_code) : '',
                                  show_on_guard_board: !!u.show_on_guard_board, show_on_internet: !!u.show_on_internet,
                                  image_path: u.image_path || '', symbol_path: u.symbol_path || '',
                                })
                                setEditingUnitId(u.id)
                                setUnitMsg('')
                              }}>ویرایش</button>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف واحد؟')) return
                                fetch(`/api/units/${u.id}`, { method: 'DELETE' }).then(() => loadUnits())
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : showCompanyForm && isAdmin ? (

                <div className="card">
                  <h3>{editingCompanyCode ? `ویرایش شرکت — کد ${editingCompanyCode}` : 'فرم ثبت شرکت تابعه'}</h3>
                  <p style={{ fontSize: 12, color: '#718096', marginBottom: 12 }}>
                    {editingCompanyCode
                      ? 'نام و مشخصات شرکت را ویرایش کنید. کد شرکت و دیتابیس تغییر نمی‌کند.'
                      : 'با ثبت شرکت، یک کد سه‌رقمی (از ۱۰۰) و دیتابیس جداگانه co_XXX ساخته می‌شود.'}
                  </p>
                  {companyMsg && (
                    <div
                      style={{
                        marginBottom: 12,
                        padding: '8px 12px',
                        borderRadius: 6,
                        background:
                          companyMsg.includes('ثبت شد') || companyMsg.includes('به‌روز')
                            ? '#c6f6d5'
                            : '#fed7d7',
                        color:
                          companyMsg.includes('ثبت شد') || companyMsg.includes('به‌روز')
                            ? '#276749'
                            : '#c53030',
                        fontSize: 13,
                      }}
                    >
                      {companyMsg}
                    </div>
                  )}
                  <form onSubmit={handleCompanyRegister}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>
                          نام شرکت * (از اطلاعات پایه یا دستی)
                        </label>
                        <input
                          required
                          list="base-client-companies"
                          value={companyForm.name}
                          onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '8px 10px',
                            border: '1px solid #e2e8f0',
                            borderRadius: 6,
                            fontFamily: 'inherit',
                            fontSize: 13,
                          }}
                        />
                        <datalist id="base-client-companies">
                          {(baseClientCompanies || []).map((c) => (
                            <option key={c.id || c.code || c.name} value={c.name}>{c.code ? `کد ${c.code}` : ''}</option>
                          ))}
                        </datalist>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>
                          شرکت سطح بالاتر (ساختار درختی)
                        </label>
                        <select
                          value={companyForm.parent_code || ''}
                          onChange={(e) => setCompanyForm({ ...companyForm, parent_code: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '8px 10px',
                            border: '1px solid #e2e8f0',
                            borderRadius: 6,
                            fontFamily: 'inherit',
                            fontSize: 13,
                          }}
                        >
                          <option value="">— بدون والد (ریشه) —</option>
                          {(companies || []).filter((c) => !editingCompanyCode || String(c.code) !== String(editingCompanyCode)).map((c) => (
                            <option key={c.code} value={c.code}>{c.code} — {c.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>
                          نام کوتاه
                        </label>
                        <input
                          value={companyForm.short_name}
                          onChange={(e) => setCompanyForm({ ...companyForm, short_name: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '8px 10px',
                            border: '1px solid #e2e8f0',
                            borderRadius: 6,
                            fontFamily: 'inherit',
                            fontSize: 13,
                          }}
                        />
                      </div>
                                            <div style={{ gridColumn: '1 / -1' }}>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>
                          لوگوی شرکت (برای کارت شناسایی)
                        </label>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                          {companyForm.logo ? (
                            <>
                              <img src={companyForm.logo} alt="لوگو" style={{ width: 64, height: 64, objectFit: 'contain', border: '1px solid #e2e8f0', borderRadius: 8, background: '#fff' }} />
                              <button type="button" className="refresh-btn" onClick={() => setCompanyForm({ ...companyForm, logo: '' })}>حذف لوگو</button>
                            </>
                          ) : (
                            <span style={{ fontSize: 12, color: '#a0aec0' }}>لوگویی انتخاب نشده</span>
                          )}
                          <input type="file" accept="image/*" onChange={(e) => {
                            const file = e.target.files?.[0]
                            e.target.value = ''
                            if (!file) return
                            if (file.size > 2 * 1024 * 1024) {
                              setCompanyMsg('حجم لوگو حداکثر ۲ مگابایت')
                              return
                            }
                            const reader = new FileReader()
                            reader.onload = () => setCompanyForm({ ...companyForm, logo: String(reader.result || '') })
                            reader.readAsDataURL(file)
                          }} style={{ fontSize: 12 }} />
                        </div>
                      </div>
<div style={{ gridColumn: '1 / -1' }}>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>
                          توضیحات
                        </label>
                        <input
                          value={companyForm.description}
                          onChange={(e) => setCompanyForm({ ...companyForm, description: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '8px 10px',
                            border: '1px solid #e2e8f0',
                            borderRadius: 6,
                            fontFamily: 'inherit',
                            fontSize: 13,
                          }}
                        />
                      </div>
                    </div>
                    <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                      <button
                        type="submit"
                        style={{
                          padding: '8px 20px',
                          background: '#2b6cb0',
                          color: 'white',
                          border: 'none',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontFamily: 'inherit',
                          fontSize: 13,
                        }}
                      >
                        {editingCompanyCode ? '💾 ذخیره تغییرات' : '💾 ذخیره و صدور کد'}
                      </button>
                      <button
                        type="button"
                        className="refresh-btn"
                        onClick={() => {
                          setShowCompanyForm(false)
                          setEditingCompanyCode(null)
                          setCompanyForm({ name: '', short_name: '', description: '', parent_code: '', logo: '' })
                          setCompanyMsg('')
                        }}
                      >
                        انصراف
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <div className="card">
                  <h3>شرکت‌های ثبت‌شده در سیستم</h3>
                  {!isAdmin && (
                    <p style={{ fontSize: 12, color: '#718096', marginBottom: 8 }}>
                      ویرایش و غیرفعال‌سازی فقط برای مدیر سیستم فعال است.
                    </p>
                  )}
                  <div style={{
                    display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center',
                    marginBottom: 14, padding: '10px 12px', background: '#f7fafc',
                    border: '1px solid #e2e8f0', borderRadius: 8,
                  }}>
                    <span style={{ fontSize: 13, color: '#2d3748', fontWeight: 600 }}>🔍 جستجوی شرکت</span>
                    <input
                      id="company-search-input"
                      type="text"
                      value={companySearch}
                      onChange={(e) => setCompanySearch(e.target.value)}
                      placeholder="کد، نام، نام کوتاه، شرکت والد..."
                      style={{
                        flex: 1, minWidth: 200, maxWidth: 360, padding: '8px 12px',
                        border: '1px solid #cbd5e0', borderRadius: 6,
                        fontFamily: 'inherit', fontSize: 13,
                      }}
                    />
                    <select
                      value={companyStatusFilter}
                      onChange={(e) => setCompanyStatusFilter(e.target.value)}
                      style={{ padding: '8px 10px', border: '1px solid #cbd5e0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                    >
                      <option value="all">همه وضعیت‌ها</option>
                      <option value="active">فقط فعال</option>
                      <option value="inactive">فقط غیرفعال</option>
                    </select>
                    <button type="button" className="refresh-btn" onClick={() => { setCompanySearch(''); setCompanyStatusFilter('all') }}>
                      ✕ پاک کردن
                    </button>
                    <button type="button" className="refresh-btn" onClick={loadCompanies}>به‌روزرسانی</button>
                    <span style={{ fontSize: 12, color: '#718096' }}>
                      نتیجه: {toPersianDigits(filteredCompanies.length)} از {toPersianDigits(companies.length)}
                    </span>
                  </div>
                  <table>
                    <thead>
                      <tr>
                        <th>کد</th>
                        <th>نام شرکت</th>
                        <th>نام کوتاه</th>
                        <th>شرکت والد</th>
                        <th>دیتابیس</th>
                        <th>تعداد پرسنل</th>
                        <th>وضعیت</th>
                        {isAdmin && <th>عملیات</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {companies.length === 0 ? (
                        <tr>
                          <td colSpan={isAdmin ? 8 : 7} style={{ textAlign: 'center', color: '#718096' }}>
                            {apiStatus === 'offline'
                              ? 'اتصال به سرور برقرار نیست'
                              : 'شرکتی ثبت نشده است'}
                          </td>
                        </tr>
                      ) : filteredCompanies.length === 0 ? (
                        <tr>
                          <td colSpan={isAdmin ? 8 : 7} style={{ textAlign: 'center', color: '#a0aec0' }}>
                            نتیجه‌ای برای جستجو یافت نشد
                          </td>
                        </tr>
                      ) : (
                        filteredCompanies.map((c) => (
                          <tr key={c.code} style={{ opacity: c.is_active ? 1 : 0.65 }}>
                            <td>
                              <strong>{c.code}</strong>
                            </td>
                            <td>{c.name}</td>
                            <td>{c.short_name || '—'}</td>
                            <td>{c.parent_code != null ? (() => { const p = (companies || []).find((x) => String(x.code) === String(c.parent_code)); return p ? `${c.parent_code} — ${p.short_name || p.name}` : String(c.parent_code); })() : '—'}</td>
                            <td>
                              <span className="badge badge-blue">{c.db_name || 'co_db'}</span>
                            </td>
                            <td>{c.personnel_count ?? 0}</td>
                            <td>
                              <span
                                className={`badge ${c.is_active ? 'badge-green' : 'badge-red'}`}
                              >
                                {c.is_active ? 'فعال' : 'غیرفعال'}
                              </span>
                            </td>
                            {isAdmin && (
                              <td style={{ whiteSpace: 'nowrap' }}>
                                <button
                                  type="button"
                                  className="refresh-btn"
                                  style={{ marginLeft: 4, fontSize: 12 }}
                                  onClick={() => startEditCompany(c)}
                                >
                                  ویرایش
                                </button>
                                <button
                                  type="button"
                                  className="refresh-btn"
                                  style={{
                                    fontSize: 12,
                                    color: c.is_active ? '#c53030' : '#276749',
                                  }}
                                  onClick={() => toggleCompanyActive(c)}
                                >
                                  {c.is_active ? 'غیرفعال' : 'فعال‌سازی'}
                                </button>
                              </td>
                            )}
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : activeTab === 'personnel' ? (
            <>
              <div className="workspace-header">
                <div>
                  <h2>
                    {showDependents
                      ? `وابستگان — ${selectedPersonnel ? ((selectedPersonnel.first_name || '') + ' ' + (selectedPersonnel.last_name || '')) : ''}`
                      : personnelRecordKind
                        ? `${PERSONNEL_RECORD_META[personnelRecordKind]?.title || 'سوابق'} — ${selectedPersonnel ? ((selectedPersonnel.first_name || '') + ' ' + (selectedPersonnel.last_name || '')) : ''}`
                      : showAssignOrg
                        ? `تخصیص شرکت به پرسنل — ${selectedPersonnel ? ((selectedPersonnel.first_name || '') + ' ' + (selectedPersonnel.last_name || '')) : ''}`
                      : showCards
                        ? `صدور کارت — ${selectedPersonnel ? ((selectedPersonnel.first_name || '') + ' ' + (selectedPersonnel.last_name || '')) : ''}`
                        : showRegisterForm
                          ? (editingId ? 'ویرایش مشخصات پرسنل' : 'ثبت مشخصات پرسنل')
                          : `لیست پرسنل — ${personnelTotal} نفر`}
                  </h2>
                  {!showRegisterForm && !showDependents && !showCards && !personnelRecordKind && (
                    <small style={{ display: 'block', color: '#64748b', marginTop: 2 }}>
                      نمایش تجمیعی همه شرکت‌ها (هر شرکت از دیتابیس خودش)
                      {personnelScopeNote ? ` — ${personnelScopeNote}` : ''}
                    </small>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  {!showRegisterForm && !personnelRecordKind && (
                    <>
                      <input
                        id="personnel-search-input"
                        type="text"
                        placeholder="جستجو: نام، کد ملی، تلفن، شرکت..."
                        value={searchInput}
                        onChange={(e) => setSearchInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        style={{
                          padding: '6px 12px',
                          border: '1px solid #cbd5e0',
                          borderRadius: 6,
                          fontFamily: 'inherit',
                          fontSize: 13,
                          width: 260,
                        }}
                      />
                      <button className="refresh-btn" onClick={handleSearch}>
                        🔍 جستجو
                      </button>
                      <button
                        className="refresh-btn"
                        onClick={() => {
                          setSearchInput('')
                          setPersonnelPage(1)
                          setSearchQuery('')
                        }}
                      >
                        ✕ پاک
                      </button>
                    </>
                  )}
                  <button
                    className="refresh-btn"
                    onClick={() => {
                      if (showRegisterForm) cancelPersonnelForm()
                      else {
                        setEditingId(null)
                        setFormData(emptyForm)
                        setFormMsg('')
                        setShowRegisterForm(true)
                      }
                    }}
                  >
                    {showRegisterForm ? '📋 بازگشت به لیست' : '➕ ثبت جدید'}
                  </button>
                  {!showRegisterForm && !showDependents && !showCards && (
                    <>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl('/api/personnel/template.csv', 'personnel_template.csv')}>
                        📥 قالب CSV پرسنل
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) importPersonnelCsvFile(f) }} />
                      </label>
                    </>
                  )}
                </div>
              </div>

                            {personnelRecordKind ? (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                    <h3 style={{ margin: 0 }}>{PERSONNEL_RECORD_META[personnelRecordKind]?.title}</h3>
                    <button type="button" className="refresh-btn" onClick={() => { setPersonnelRecordKind(null); setEditingRecId(null); setRecForm({}); setRecMsg('') }}>📋 بازگشت به لیست</button>
                  </div>
                  {selectedPersonnel && (
                    <div style={{ marginBottom: 12, padding: '8px 12px', background: '#ebf8ff', borderRadius: 6, fontSize: 13 }}>
                      پرسنل: <strong>{selectedPersonnel.first_name} {selectedPersonnel.last_name}</strong>
                      {' — '}کدملی: {selectedPersonnel.national_id || '—'}
                      {' — '}{selectedPersonnel.company || selectedPersonnel.center || ''}
                    </div>
                  )}
                  {recMsg && (
                    <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13, background: recMsg.includes('خطا') ? '#fed7d7' : '#c6f6d5', color: recMsg.includes('خطا') ? '#c53030' : '#276749' }}>{recMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    if (!selectedPersonnel) return
                    const code = selectedPersonnel.company_code
                    const body = { ...recForm, personnel_id: selectedPersonnel.id }
                    const url = editingRecId
                      ? `/api/personnel-records/${personnelRecordKind}/${editingRecId}?company_code=${encodeURIComponent(code)}`
                      : `/api/personnel-records/${personnelRecordKind}?company_code=${encodeURIComponent(code)}`
                    fetch(url, {
                      method: editingRecId ? 'PUT' : 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(body),
                    })
                      .then(async (r) => {
                        const d = await r.json().catch(() => ({}))
                        if (!r.ok) throw new Error(d.detail || 'خطا در ذخیره')
                        setRecMsg(editingRecId ? 'ویرایش شد' : 'ثبت شد')
                        setEditingRecId(null)
                        setRecForm({})
                        loadPersonnelRecords(selectedPersonnel, personnelRecordKind)
                      })
                      .catch((err) => setRecMsg('خطا: ' + (err.message || '')))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {(PERSONNEL_RECORD_META[personnelRecordKind]?.fields || []).map((f) => (
                        <div key={f.key}>
                          <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>{f.label}</label>
                          {f.type === 'date' || isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput value={recForm[f.key] || ''} onChange={(v) => setRecForm({ ...recForm, [f.key]: v })} />
                          ) : (
                            <input value={recForm[f.key] || ''} onChange={(e) => setRecForm({ ...recForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                      <button type="submit" className="btn-primary">{editingRecId ? '💾 ذخیره ویرایش' : '💾 ثبت'}</button>
                      {editingRecId && (
                        <button type="button" className="refresh-btn" onClick={() => { setEditingRecId(null); setRecForm({}) }}>انصراف</button>
                      )}
                    </div>
                  </form>
                  <table>
                    <thead>
                      <tr>
                        <th>ردیف</th>
                        {(PERSONNEL_RECORD_META[personnelRecordKind]?.columns || []).map((c) => {
                          const f = (PERSONNEL_RECORD_META[personnelRecordKind]?.fields || []).find((x) => x.key === c)
                          return <th key={c}>{f?.label || c}</th>
                        })}
                        <th>عملیات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {personnelRecords.length === 0 ? (
                        <tr><td colSpan={10} style={{ textAlign: 'center', color: '#a0aec0' }}>سابقه‌ای ثبت نشده است</td></tr>
                      ) : personnelRecords.map((row, i) => (
                        <tr key={row.id}>
                          <td>{toPersianDigits(i + 1)}</td>
                          {(PERSONNEL_RECORD_META[personnelRecordKind]?.columns || []).map((c) => (
                            <td key={c}>{row[c] ? toPersianDigits(row[c]) : '—'}</td>
                          ))}
                          <td>
                            <button type="button" className="refresh-btn" onClick={() => {
                              setEditingRecId(row.id)
                              const next = {}
                              ;(PERSONNEL_RECORD_META[personnelRecordKind]?.fields || []).forEach((f) => { next[f.key] = row[f.key] || '' })
                              setRecForm(next)
                            }}>ویرایش</button>{' '}
                            <button type="button" className="refresh-btn" onClick={() => {
                              if (!window.confirm('حذف این سابقه؟')) return
                              const code = selectedPersonnel.company_code
                              fetch(`/api/personnel-records/${personnelRecordKind}/${row.id}?company_code=${encodeURIComponent(code)}`, { method: 'DELETE' })
                                .then((r) => { if (!r.ok) throw new Error('خطا'); loadPersonnelRecords(selectedPersonnel, personnelRecordKind) })
                                .catch((e) => setRecMsg('خطا: ' + e.message))
                            }}>حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : showDependents ? (

                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <h3 style={{ margin: 0 }}>ثبت وابستگان</h3>
                    <button type="button" className="refresh-btn" onClick={() => { setShowDependents(false); setEditingDepId(null) }}>📋 بازگشت به لیست</button>
                  </div>
                  {selectedPersonnel && (
                    <div style={{ marginBottom: 12, padding: '8px 12px', background: '#ebf8ff', borderRadius: 6, fontSize: 13 }}>
                      پرسنل: <strong>{selectedPersonnel.first_name} {selectedPersonnel.last_name}</strong> — کدملی: {selectedPersonnel.national_id || '—'} — {selectedPersonnel.company || ''}
                    </div>
                  )}
                  {depMsg && (
                    <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 6, background: depMsg.includes('موفق') ? '#c6f6d5' : '#fed7d7', color: depMsg.includes('موفق') ? '#276749' : '#c53030', fontSize: 13 }}>{depMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    if (!selectedPersonnel) return
                    const code = selectedPersonnel.company_code
                    const payload = { ...depForm, personnel_id: selectedPersonnel.id }
                    const isEdit = Boolean(editingDepId)
                    const url = isEdit
                      ? `/api/dependents/${editingDepId}?company_code=${encodeURIComponent(code)}`
                      : `/api/dependents?company_code=${encodeURIComponent(code)}`
                    fetch(url, { method: isEdit ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
                      .then(async (r) => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || 'خطا'); return d })
                      .then(() => {
                        setDepMsg(isEdit ? 'وابسته با موفقیت ویرایش شد' : 'وابسته با موفقیت ثبت شد')
                        setEditingDepId(null)
                        setDepForm({ first_name: '', last_name: '', national_id: '', relation: '', birth_date: '', gender: '', phone: '', description: '' })
                        loadDependents(selectedPersonnel)
                        setTimeout(() => setDepMsg(''), 1500)
                      })
                      .catch((err) => setDepMsg(err.message || 'خطا'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 10, marginBottom: 12 }}>
                      {[
                        ['first_name', 'نام'], ['last_name', 'نام خانوادگی'], ['national_id', 'کد ملی'],
                        ['relation', 'نسبت'], ['birth_date', 'تاریخ تولد'], ['phone', 'تلفن'],
                      ].map(([k, lab]) => (
                        <div key={k}>
                          <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>{lab}</label>
                          {isDateFieldKey(k, null, lab) ? (
                            <JalaliDateInput value={depForm[k] || ''} onChange={(v) => setDepForm({ ...depForm, [k]: v })} />
                          ) : (
                            <input value={depForm[k] || ''} onChange={(e) => setDepForm({ ...depForm, [k]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>جنسیت</label>
                        <select value={depForm.gender || ''} onChange={(e) => setDepForm({ ...depForm, gender: e.target.value })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="">—</option><option value="مرد">مرد</option><option value="زن">زن</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>توضیحات</label>
                        <input value={depForm.description || ''} onChange={(e) => setDepForm({ ...depForm, description: e.target.value })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                      <button type="submit" style={{ padding: '8px 20px', background: '#2b6cb0', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}>
                        {editingDepId ? '💾 ذخیره ویرایش' : '💾 ثبت وابسته'}
                      </button>
                      {editingDepId && (
                        <button type="button" className="refresh-btn" onClick={() => { setEditingDepId(null); setDepForm({ first_name: '', last_name: '', national_id: '', relation: '', birth_date: '', gender: '', phone: '', description: '' }) }}>انصراف</button>
                      )}
                    </div>
                  </form>
                  <table>
                    <thead><tr><th>ردیف</th><th>نام</th><th>نام خانوادگی</th><th>کد ملی</th><th>نسبت</th><th>جنسیت</th><th>تلفن</th><th>عملیات</th></tr></thead>
                    <tbody>
                      {dependents.length === 0 ? (
                        <tr><td colSpan={8} style={{ textAlign: 'center', color: '#718096' }}>وابسته‌ای ثبت نشده</td></tr>
                      ) : dependents.map((d, i) => (
                        <tr key={d.id}>
                          <td>{i + 1}</td>
                          <td>{d.first_name}</td>
                          <td>{d.last_name}</td>
                          <td>{d.national_id}</td>
                          <td>{d.relation}</td>
                          <td>{d.gender}</td>
                          <td>{d.phone}</td>
                          <td style={{ whiteSpace: 'nowrap' }}>
                            <button type="button" className="refresh-btn" onClick={() => {
                              setEditingDepId(d.id)
                              setDepForm({ first_name: d.first_name || '', last_name: d.last_name || '', national_id: d.national_id || '', relation: d.relation || '', birth_date: d.birth_date || '', gender: d.gender || '', phone: d.phone || '', description: d.description || '' })
                            }}>ویرایش</button>{' '}
                            <button type="button" className="refresh-btn" onClick={() => {
                              if (!window.confirm('حذف این وابسته؟')) return
                              const code = selectedPersonnel.company_code
                              fetch(`/api/dependents/${d.id}?company_code=${encodeURIComponent(code)}`, { method: 'DELETE' })
                                .then((r) => { if (!r.ok) throw new Error('خطا'); loadDependents(selectedPersonnel) })
                                .catch((e) => setDepMsg(e.message))
                            }}>حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : showAssignOrg ? (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                    <h3 style={{ margin: 0 }}>تخصیص گروهی شرکت / مرکز / واحد</h3>
                    <button type="button" className="refresh-btn" onClick={() => { setShowAssignOrg(false); setAssignOrgMsg('') }}>📋 بازگشت به لیست</button>
                  </div>
                  <div style={{
                    marginBottom: 14, padding: '12px 14px', borderRadius: 8, border: '1px solid #c6f6d5',
                    background: '#f0fff4', display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center',
                  }}>
                    <span style={{ fontSize: 13, color: '#276749', fontWeight: 600 }}>تخصیص از فایل CSV</span>
                    <button
                      type="button"
                      className="refresh-btn"
                      style={{ fontSize: 12 }}
                      onClick={() => downloadUrl('/api/personnel/assign-org-template.csv', 'assign_org_template.csv')}
                    >
                      📥 دانلود قالب CSV نمونه
                    </button>
                    <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                      📤 ورود تخصیص از CSV
                      <input
                        type="file"
                        accept=".csv,text/csv"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                          const f = e.target.files?.[0]
                          e.target.value = ''
                          if (f) importAssignOrgCsvFile(f)
                        }}
                      />
                    </label>
                    <span style={{ fontSize: 12, color: '#4a5568' }}>
                      ستون‌ها: کد ملی (یا کد پرسنلی) + کد/نام شرکت + مرکز + واحد
                    </span>
                  </div>
                  <div style={{ marginBottom: 14, padding: '10px 12px', background: '#ebf8ff', borderRadius: 8, fontSize: 13, border: '1px solid #90cdf4' }}>
                    <div style={{ marginBottom: 8, fontWeight: 600, color: '#2c5282' }}>
                      {(selectedPersonnelList || []).length
                        ? `${(selectedPersonnelList || []).length} نفر انتخاب شده‌اند`
                        : 'هنوز پرسنلی انتخاب نشده — از لیست زیر تیک بزنید یا به لیست برگردید'}
                    </div>
                    {(selectedPersonnelList || []).length > 0 && (
                      <div style={{ maxHeight: 140, overflow: 'auto', border: '1px solid #bee3f8', borderRadius: 6, background: '#fff' }}>
                        <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ background: '#edf2f7' }}>
                              <th style={{ padding: 6, textAlign: 'right' }}>نام</th>
                              <th style={{ padding: 6, textAlign: 'right' }}>کد ملی</th>
                              <th style={{ padding: 6, textAlign: 'right' }}>شرکت فعلی</th>
                              <th style={{ padding: 6, textAlign: 'right' }}>مرکز / واحد</th>
                              <th style={{ width: 40 }}></th>
                            </tr>
                          </thead>
                          <tbody>
                            {(selectedPersonnelList || []).map((p) => (
                              <tr key={personKey(p)}>
                                <td style={{ padding: 6 }}>{(p.first_name || '') + ' ' + (p.last_name || '')}</td>
                                <td style={{ padding: 6 }}>{p.national_id || '—'}</td>
                                <td style={{ padding: 6 }}>{p.company || 'تخصیص‌نشده'}</td>
                                <td style={{ padding: 6 }}>{(p.center || '—') + ' / ' + (p.department || '—')}</td>
                                <td style={{ padding: 6 }}>
                                  <button type="button" className="refresh-btn" style={{ fontSize: 11, padding: '2px 6px' }}
                                    onClick={() => selectPersonnel(p)} title="حذف از انتخاب">✕</button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                    {(selectedPersonnelList || []).length === 0 && (
                      <div style={{ marginTop: 8 }}>
                        <label style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>یا انتخاب سریع از لیست پرسنل (چندتایی با Ctrl/کلیک مکرر در لیست اصلی بهتر است)</label>
                        <select
                          multiple
                          size={6}
                          value={(selectedPersonnelList || []).map((p) => `${p.company_code || ''}::${p.id}`)}
                          onChange={(e) => {
                            const opts = Array.from(e.target.selectedOptions).map((o) => o.value)
                            const next = []
                            opts.forEach((v) => {
                              const [cc, id] = v.split('::')
                              const p = (personnel || []).find((x) => String(x.id) === String(id) && String(x.company_code || '') === String(cc || ''))
                                || (personnel || []).find((x) => String(x.id) === String(id))
                              if (p) next.push(p)
                            })
                            setSelectedPersonnelList(next)
                            setSelectedPersonnel(next.length ? next[next.length - 1] : null)
                          }}
                          style={{ width: '100%', maxWidth: 520, padding: 6, border: '1px solid #90cdf4', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                        >
                          {(personnel || []).map((p) => (
                            <option key={`${p.company_code}-${p.id}`} value={`${p.company_code || ''}::${p.id}`}>
                              {(p.first_name || '') + ' ' + (p.last_name || '')} — {p.national_id || '—'} — {p.company || 'تخصیص‌نشده'}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                  {assignOrgMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: assignOrgMsg.includes('موفق') || assignOrgMsg.includes('نفر') ? '#c6f6d5' : '#fed7d7',
                      color: assignOrgMsg.includes('موفق') || assignOrgMsg.includes('نفر') ? '#276749' : '#c53030',
                    }}>{assignOrgMsg}</div>
                  )}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12, marginBottom: 14 }}>
                    <div>
                      <label style={{ fontSize: 12, color: '#c53030', display: 'block', marginBottom: 4 }}>شرکت تابعه *</label>
                      <select
                        value={assignOrgForm.company_code}
                        onChange={(e) => setAssignOrgForm({ ...assignOrgForm, company_code: e.target.value, center: '', department: '' })}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      >
                        <option value="">— انتخاب شرکت —</option>
                        {(companies || []).filter((c) => c.is_active !== false).map((c) => (
                          <option key={c.code} value={c.code}>{c.code} — {c.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: 12, color: '#c53030', display: 'block', marginBottom: 4 }}>مرکز *</label>
                      <select
                        value={assignOrgForm.center}
                        onChange={(e) => setAssignOrgForm({ ...assignOrgForm, center: e.target.value, department: '' })}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      >
                        <option value="">— از تعریف واحد و مرکز —</option>
                        {[...new Set(
                          (units || [])
                            .filter((u) => !assignOrgForm.company_code || String(u.company_code) === String(assignOrgForm.company_code))
                            .map((u) => u.center_name || u.parent_name)
                            .filter(Boolean)
                        )].map((name) => (
                          <option key={name} value={name}>{name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: 12, color: '#c53030', display: 'block', marginBottom: 4 }}>واحد *</label>
                      <select
                        value={assignOrgForm.department}
                        onChange={(e) => setAssignOrgForm({ ...assignOrgForm, department: e.target.value })}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      >
                        <option value="">— از تعریف واحد و مرکز —</option>
                        {(units || [])
                          .filter((u) => {
                            if (assignOrgForm.company_code && String(u.company_code) !== String(assignOrgForm.company_code)) return false
                            const cn = u.center_name || u.parent_name || ''
                            if (assignOrgForm.center && cn !== assignOrgForm.center) return false
                            return true
                          })
                          .map((u) => (
                            <option key={u.id} value={u.name}>{u.name}</option>
                          ))}
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={!(selectedPersonnelList || []).length}
                      onClick={async () => {
                        const list = selectedPersonnelList || []
                        if (!list.length) {
                          setAssignOrgMsg('حداقل یک پرسنل را انتخاب کنید')
                          return
                        }
                        if (!assignOrgForm.company_code || !assignOrgForm.center || !assignOrgForm.department) {
                          setAssignOrgMsg('شرکت، مرکز و واحد الزامی است')
                          return
                        }
                        const co = (companies || []).find((c) => String(c.code) === String(assignOrgForm.company_code))
                        let ok = 0
                        let fail = 0
                        const errors = []
                        for (const p of list) {
                          const prevCode = p.company_code || '0'
                          try {
                            const r = await fetch(
                              `/api/personnel/${p.id}?company_code=${encodeURIComponent(prevCode)}`,
                              {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                  company_code: assignOrgForm.company_code,
                                  company: co ? co.name : '',
                                  center: assignOrgForm.center,
                                  department: assignOrgForm.department,
                                }),
                              }
                            )
                            const d = await r.json().catch(() => ({}))
                            if (!r.ok) throw new Error(d.detail || 'خطا')
                            ok += 1
                          } catch (err) {
                            fail += 1
                            errors.push(`${p.first_name || ''} ${p.last_name || ''}: ${err.message || 'خطا'}`)
                          }
                        }
                        if (ok && !fail) {
                          setAssignOrgMsg(`تخصیص گروهی با موفقیت برای ${ok} نفر ذخیره شد`)
                        } else if (ok && fail) {
                          setAssignOrgMsg(`برای ${ok} نفر موفق و برای ${fail} نفر ناموفق. ${errors.slice(0, 3).join(' | ')}`)
                        } else {
                          setAssignOrgMsg(errors[0] || 'خطا در تخصیص گروهی')
                        }
                        const updated = list.map((p) => ({
                          ...p,
                          company_code: assignOrgForm.company_code,
                          company: co ? co.name : p.company,
                          center: assignOrgForm.center,
                          department: assignOrgForm.department,
                        }))
                        setSelectedPersonnelList(updated)
                        setSelectedPersonnel(updated.length ? updated[updated.length - 1] : null)
                        loadPersonnel(searchQuery, personnelPage, personnelPageSize)
                      }}
                    >
                      💾 تخصیص گروهی به {(selectedPersonnelList || []).length || 0} نفر
                    </button>
                    <button type="button" className="refresh-btn" onClick={() => { loadUnits(); loadCompanies() }}>
                      🔄 به‌روزرسانی لیست‌ها
                    </button>
                    <button type="button" className="refresh-btn" onClick={() => clearPersonnelSelection()}>
                      ✕ پاک کردن انتخاب
                    </button>
                  </div>
                  <p style={{ fontSize: 12, color: '#718096', marginTop: 12 }}>
                    شرکت از «شرکت‌های تابعه» و مرکز/واحد از «تعریف واحد و مرکز» خوانده می‌شود. تخصیص روی همه افراد تیک‌خورده اعمال می‌شود.
                  </p>
                </div>
              ) : showCards ? (

                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <h3 style={{ margin: 0 }}>صدور کارت شناسایی</h3>
                    <button type="button" className="refresh-btn" onClick={() => { setShowCards(false); setEditingCardId(null) }}>📋 بازگشت به لیست</button>
                  </div>
                  {selectedPersonnel && (
                    <div style={{ marginBottom: 12, padding: '8px 12px', background: '#ebf8ff', borderRadius: 6, fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                      <span>پرسنل: <strong>{selectedPersonnel.first_name} {selectedPersonnel.last_name}</strong> — کدملی: {selectedPersonnel.national_id || '—'} — {selectedPersonnel.company || ''}</span>
                      <button type="button" className="btn-primary" disabled={cardPrintLoading} onClick={() => openIdCardPrint(selectedPersonnel)}>
                        {cardPrintLoading ? '…' : '🪪 پیش‌نمایش و چاپ کارت PVC'}
                      </button>
                    </div>
                  )}
                  {cardPrintPerson && (
                    <div className="card" style={{ marginBottom: 16, background: '#f7fafc', border: '1px solid #e2e8f0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                        <h3 style={{ margin: 0, fontSize: 15 }}>کارت شناسایی PVC (استاندارد CR80 — ۸۵٫۶×۵۴ میلی‌متر)</h3>
                        <button type="button" className="refresh-btn" onClick={() => setCardPrintPerson(null)}>بستن پیش‌نمایش</button>
                      </div>
                      <p style={{ fontSize: 12, color: '#64748b', marginTop: 0 }}>
                        مناسب چاپ با پرینترهای کارت PVC مانند Fargo. می‌توانید فقط رو، فقط پشت، یا هر دو طرف را جداگانه چاپ کنید.
                      </p>
                      <div className="pvc-print-area no-print">
                        <div>
                          <div style={{ textAlign: 'center', fontSize: 12, fontWeight: 700, marginBottom: 6, color: '#1e3a8a' }}>روی کارت</div>
                          <IdCardFront person={cardPrintPerson} companyName={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).name || cardPrintPerson.company || ORG_SHORT} logoUrl={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).logo || ''} />
                        </div>
                        <div>
                          <div style={{ textAlign: 'center', fontSize: 12, fontWeight: 700, marginBottom: 6, color: '#1e3a8a' }}>پشت کارت</div>
                          <IdCardBack person={cardPrintPerson} companyName={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).name || cardPrintPerson.company || ORG_SHORT} logoUrl={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).logo || ''} />
                        </div>
                      </div>
                      <div className="no-print" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', marginTop: 14 }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#2d3748' }}>
                          <span style={{ fontWeight: 700 }}>سایز کارت PVC:</span>
                          <select
                            value={cardPrintSizeId}
                            onChange={(e) => {
                              const id = e.target.value
                              setCardPrintSizeId(id)
                              const s = PVC_CARD_SIZES.find((x) => x.id === id) || PVC_CARD_SIZES[0]
                              applyPvcCardSize(s)
                            }}
                            style={{
                              padding: '6px 10px',
                              border: '1px solid #cbd5e0',
                              borderRadius: 6,
                              fontFamily: 'inherit',
                              fontSize: 13,
                              minWidth: 260,
                              background: '#fff',
                            }}
                          >
                            {PVC_CARD_SIZES.map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.label} — {Number(s.wMm).toFixed(2)}×{Number(s.hMm).toFixed(2)} mm
                              </option>
                            ))}
                          </select>
                        </label>
                        <button type="button" className="btn-primary" onClick={() => doPrintIdCard('front')}>🖨️ چاپ روی کارت</button>
                        <button type="button" className="btn-primary" onClick={() => doPrintIdCard('back')}>🖨️ چاپ پشت کارت</button>
                        <button type="button" className="btn-secondary" onClick={() => doPrintIdCard('both')}>🖨️ چاپ پشت و رو (دو صفحه)</button>
                        <div className="pvc-print-hint no-print" style={{ flexBasis: '100%' }}>
                          <b>سایز انتخاب‌شده:</b>{' '}
                          {cardPrintSize.label} —{' '}
                          <b>{Number(cardPrintSize.wMm).toFixed(2)} × {Number(cardPrintSize.hMm).toFixed(2)} mm</b>
                          {cardPrintSize.note ? ` (${cardPrintSize.note})` : ''}
                          <br />
                          <b>تنظیمات پرینتر:</b> اندازه کاغذ/کارت = همین ابعاد —
                          حاشیه = <b>۰</b> —
                          مقیاس = <b>۱۰۰٪ / Actual size</b> —
                          جهت = <b>Landscape</b> —
                          رنگ پس‌زمینه فعال —
                          حاشیه امن محتوا: <b>۲ mm</b> (خط‌چین آبی فقط در پیش‌نمایش).
                          <div style={{ marginTop: 6, fontSize: 11, color: '#718096' }}>
                            سایزهای پشتیبانی‌شده:
                            {' '}CR80 (ID-1)، CR79، CR100، CR90، ID-2، Badge —
                            پیش‌فرض پیشنهادی برای اکثر پرینترهای PVC: <b>CR80</b>.
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  {cardMsg && (
                    <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 6, background: cardMsg.includes('موفق') ? '#c6f6d5' : '#fed7d7', color: cardMsg.includes('موفق') ? '#276749' : '#c53030', fontSize: 13 }}>{cardMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    if (!selectedPersonnel) return
                    const code = selectedPersonnel.company_code
                    const payload = { ...cardForm, personnel_id: selectedPersonnel.id }
                    const isEdit = Boolean(editingCardId)
                    const url = isEdit
                      ? `/api/cards/${editingCardId}?company_code=${encodeURIComponent(code)}`
                      : `/api/cards?company_code=${encodeURIComponent(code)}`
                    fetch(url, { method: isEdit ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
                      .then(async (r) => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || 'خطا'); return d })
                      .then(() => {
                        setCardMsg(isEdit ? 'کارت با موفقیت ویرایش شد' : 'کارت با موفقیت صادر شد')
                        setEditingCardId(null)
                        setCardForm({ card_number: '', card_type: 'شناسایی', issue_date: '', expiry_date: '', status: 'فعال', printed: false, description: '' })
                        loadCards(selectedPersonnel)
                        loadPersonnel(searchQuery)
                        setTimeout(() => setCardMsg(''), 1500)
                      })
                      .catch((err) => setCardMsg(err.message || 'خطا'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 10, marginBottom: 12 }}>
                      {[
                        ['card_number', 'شماره کارت *'], ['issue_date', 'تاریخ صدور'], ['expiry_date', 'تاریخ پایان اعتبار'],
                      ].map(([k, lab]) => (
                        <div key={k}>
                          <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>{lab}</label>
                          <input required={lab.includes('*')} value={cardForm[k] || ''} onChange={(e) => setCardForm({ ...cardForm, [k]: e.target.value })}
                            style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                        </div>
                      ))}
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>نوع کارت</label>
                        <select value={cardForm.card_type || 'شناسایی'} onChange={(e) => setCardForm({ ...cardForm, card_type: e.target.value })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="شناسایی">شناسایی</option>
                          <option value="تردد">تردد</option>
                          <option value="مهمان">مهمان</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>وضعیت</label>
                        <select value={cardForm.status || 'فعال'} onChange={(e) => setCardForm({ ...cardForm, status: e.target.value })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="فعال">فعال</option>
                          <option value="مسدود">مسدود</option>
                          <option value="منقضی">منقضی</option>
                          <option value="باطل">باطل</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>توضیحات</label>
                        <input value={cardForm.description || ''} onChange={(e) => setCardForm({ ...cardForm, description: e.target.value })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                      <button type="submit" style={{ padding: '8px 20px', background: '#2b6cb0', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}>
                        {editingCardId ? '💾 ذخیره ویرایش' : '🪪 صدور کارت'}
                      </button>
                      {editingCardId && (
                        <button type="button" className="refresh-btn" onClick={() => { setEditingCardId(null); setCardForm({ card_number: '', card_type: 'شناسایی', issue_date: '', expiry_date: '', status: 'فعال', printed: false, description: '' }) }}>انصراف</button>
                      )}
                    </div>
                  </form>
                  <table>
                    <thead><tr><th>ردیف</th><th>شماره کارت</th><th>نوع</th><th>تاریخ صدور</th><th>پایان اعتبار</th><th>وضعیت</th><th>عملیات</th></tr></thead>
                    <tbody>
                      {cards.length === 0 ? (
                        <tr><td colSpan={7} style={{ textAlign: 'center', color: '#718096' }}>کارتی صادر نشده</td></tr>
                      ) : cards.map((c, i) => (
                        <tr key={c.id}>
                          <td>{i + 1}</td>
                          <td>{c.card_number}</td>
                          <td>{c.card_type}</td>
                          <td>{c.issue_date}</td>
                          <td>{c.expiry_date}</td>
                          <td><span className={`badge ${c.status === 'فعال' ? 'badge-green' : 'badge-red'}`}>{c.status}</span></td>
                          <td style={{ whiteSpace: 'nowrap' }}>
                            <button type="button" className="refresh-btn" onClick={() => {
                              setEditingCardId(c.id)
                              setCardForm({ card_number: c.card_number || '', card_type: c.card_type || 'شناسایی', issue_date: c.issue_date || '', expiry_date: c.expiry_date || '', status: c.status || 'فعال', printed: !!c.printed, description: c.description || '' })
                            }}>ویرایش</button>{' '}
                            <button type="button" className="refresh-btn" onClick={() => {
                              if (!window.confirm('حذف این کارت؟')) return
                              const code = selectedPersonnel.company_code
                              fetch(`/api/cards/${c.id}?company_code=${encodeURIComponent(code)}`, { method: 'DELETE' })
                                .then((r) => { if (!r.ok) throw new Error('خطا'); loadCards(selectedPersonnel) })
                                .catch((e) => setCardMsg(e.message))
                            }}>حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : showRegisterForm ? (
                <div className="card" style={{ padding: 12 }}>
                  <div style={{
                    textAlign: 'center', marginBottom: 10, padding: '6px 0',
                    background: 'linear-gradient(90deg,#4a5568,#2d3748)', color: '#fff',
                    borderRadius: 6, fontWeight: 700, fontSize: 14, letterSpacing: 0.5,
                  }}>تعریف پرسنل</div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی از فایل:</span>
                    <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                      onClick={() => downloadUrl('/api/personnel/template.csv', 'personnel_template.csv')}>
                      📥 دانلود قالب CSV
                    </button>
                    <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                      📤 ورود از CSV
                      <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) importPersonnelCsvFile(f) }} />
                    </label>
                    <span style={{ fontSize: 11, color: '#718096' }}>قالب را پر کنید و برای ثبت دسته‌ای بارگذاری کنید</span>
                  </div>
                  {formMsg && (
                    <div style={{
                      marginBottom: 10, padding: '6px 10px', borderRadius: 6, fontSize: 12,
                      background: (formMsg.includes('موفق') || formMsg.includes('ورود CSV')) ? '#c6f6d5' : '#fed7d7',
                      color: (formMsg.includes('موفق') || formMsg.includes('ورود CSV')) ? '#276749' : '#c53030',
                    }}>{formMsg}</div>
                  )}
                  <form onSubmit={handleRegister}>
                    <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr 1fr 1fr', gap: 8, alignItems: 'start' }}>
                      {/* —— ستون عکس و امضا —— */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
                        <div style={{ fontSize: 11, color: '#4a5568', alignSelf: 'stretch' }}>عکس پرسنلی:</div>
                        <div style={{
                          width: 90, height: 110, border: '1px solid #cbd5e0', borderRadius: 4,
                          overflow: 'hidden', background: '#edf2f7', display: 'flex',
                          alignItems: 'center', justifyContent: 'center',
                        }}>
                          {formData.photo
                            ? <img src={formData.photo} alt="عکس" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            : <span style={{ fontSize: 28, color: '#a0aec0' }}>👤</span>}
                        </div>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <label style={{
                            width: 28, height: 28, borderRadius: 4, background: '#e53e3e', color: '#fff',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 14,
                          }} title="حذف عکس" onClick={() => {
                            setFormData((prev) => ({ ...prev, photo: '' }))
                            if (editingId) {
                              const code = formData.company_code || selectedPersonnel?.company_code || ''
                              fetch(`/api/personnel/${editingId}?company_code=${encodeURIComponent(code)}`, {
                                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ photo: '__clear__' }),
                              }).catch(() => {})
                            }
                          }}>✕</label>
                          <label style={{
                            width: 28, height: 28, borderRadius: 4, background: '#3182ce', color: '#fff',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 12,
                          }} title="آپلود عکس">
                            ⬆
                            <input type="file" accept="image/*" style={{ display: 'none' }}
                              onChange={(e) => {
                                const file = e.target.files?.[0]
                                if (!file) return
                                const reader = new FileReader()
                                reader.onload = () => {
                                  const dataUrl = reader.result
                                  setFormData((prev) => ({ ...prev, photo: dataUrl }))
                                  persistMediaNow('photo', dataUrl)
                                }
                                reader.readAsDataURL(file)
                              }} />
                          </label>
                        </div>
                        <div style={{ fontSize: 11, color: '#4a5568', alignSelf: 'stretch', marginTop: 6 }}>امضای پرسنل:</div>
                        <div style={{
                          width: 90, height: 50, border: '1px solid #cbd5e0', borderRadius: 4,
                          overflow: 'hidden', background: '#edf2f7', display: 'flex',
                          alignItems: 'center', justifyContent: 'center',
                        }}>
                          {formData.signature
                            ? <img src={formData.signature} alt="امضا" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                            : <span style={{ fontSize: 11, color: '#a0aec0' }}>—</span>}
                        </div>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <label style={{
                            width: 28, height: 28, borderRadius: 4, background: '#e53e3e', color: '#fff',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 14,
                          }} onClick={() => setFormData((prev) => ({ ...prev, signature: '' }))}>✕</label>
                          <label style={{
                            width: 28, height: 28, borderRadius: 4, background: '#3182ce', color: '#fff',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 12,
                          }}>
                            ⬆
                            <input type="file" accept="image/*" style={{ display: 'none' }}
                              onChange={(e) => {
                                const file = e.target.files?.[0]
                                if (!file) return
                                const reader = new FileReader()
                                reader.onload = () => {
                                  const dataUrl = reader.result
                                  setFormData((prev) => ({ ...prev, signature: dataUrl }))
                                  persistMediaNow('signature', dataUrl)
                                }
                                reader.readAsDataURL(file)
                              }} />
                          </label>
                        </div>
                      </div>

                      {/* —— سه ستون فیلدها —— */}
                      {(() => {
                        const inp = (key, label, opts = {}) => (
                          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 4, minHeight: 28 }}>
                            <label style={{
                              fontSize: 11, color: opts.req ? '#c53030' : '#4a5568',
                              whiteSpace: 'nowrap', minWidth: opts.lw || 88, textAlign: 'left',
                            }}>{label}{opts.req ? ' *' : ''}:</label>
                            {opts.type === 'select' ? (
                              <select
                                required={!!opts.req}
                                value={formData[key] || ''}
                                onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
                                style={{ flex: 1, padding: '3px 6px', border: '1px solid #cbd5e0', borderRadius: 3, fontFamily: 'inherit', fontSize: 12, height: 26 }}
                              >
                                {(opts.options || []).map((o) => (
                                  <option key={o.v} value={o.v}>{o.l}</option>
                                ))}
                              </select>
                            ) : opts.type === 'radio' ? (
                              <div style={{ display: 'flex', gap: 10, fontSize: 12 }}>
                                {(opts.options || [{ v: 'خیر', l: 'خیر' }, { v: 'بلی', l: 'بلی' }]).map((o) => (
                                  <label key={o.v} style={{ display: 'flex', alignItems: 'center', gap: 3, cursor: 'pointer' }}>
                                    <input type="radio" name={key} checked={(formData[key] || 'خیر') === o.v}
                                      onChange={() => setFormData({ ...formData, [key]: o.v })} />
                                    {o.l}
                                  </label>
                                ))}
                              </div>
                            ) : isDateFieldKey(key, opts.type, label) ? (
                              <div style={{ flex: 1 }}>
                                <JalaliDateInput
                                  required={!!opts.req}
                                  value={formData[key] || ''}
                                  onChange={(v) => setFormData({ ...formData, [key]: v })}
                                />
                              </div>
                            ) : isTimeFieldKey(key, opts.type) ? (
                              <div style={{ flex: 1 }}>
                                <JalaliTimeInput
                                  required={!!opts.req}
                                  value={formData[key] || ''}
                                  onChange={(v) => setFormData({ ...formData, [key]: v })}
                                />
                              </div>
                            ) : (
                              <input
                                required={!!opts.req}
                                type={opts.inputType || 'text'}
                                value={formData[key] || ''}
                                onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
                                style={{ flex: 1, padding: '3px 6px', border: '1px solid #cbd5e0', borderRadius: 3, fontFamily: 'inherit', fontSize: 12, height: 26 }}
                              />
                            )}
                          </div>
                        )

                        return (
                          <>
                            {/* ستون راست */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                              {inp('indicator_num', 'کد پرسنلی', { req: true })}
                              {inp('first_name', 'نام', { req: true })}
                              {inp('last_name', 'نام خانوادگی', { req: true })}
                              {inp('license_type', 'نوع گواهینامه')}
                              {inp('position', 'سمت')}
                              {inp('gender', 'جنسیت', { req: true, type: 'select', options: [
                                { v: '', l: '—' }, { v: 'مرد', l: 'مرد' }, { v: 'زن', l: 'زن' },
                              ]})}
                              {inp('phone', 'تلفن همراه')}
                              {inp('return_code', 'کد/متن عودت')}
                              {inp('national_id', 'کد ملی', { req: true })}
                              {inp('birth_date', 'تاریخ تولد')}
                              {inp('birth_place', 'محل تولد')}
                              {inp('military_status', 'نظام وظیفه', { req: true, type: 'select', options: [
                                { v: '', l: '—' }, { v: 'نامشخص', l: 'نامشخص' }, { v: 'پایان خدمت', l: 'پایان خدمت' },
                                { v: 'معاف', l: 'معاف' }, { v: 'در حال خدمت', l: 'در حال خدمت' }, { v: 'مشمول', l: 'مشمول' },
                              ]})}
                              {inp('religion', 'دین', { req: true, type: 'select', options: [
                                { v: '', l: '—' }, { v: 'نامشخص', l: 'نامشخص' }, { v: 'اسلام', l: 'اسلام' },
                                { v: 'مسیحی', l: 'مسیحی' }, { v: 'کلیمی', l: 'کلیمی' }, { v: 'زرتشتی', l: 'زرتشتی' }, { v: 'سایر', l: 'سایر' },
                              ]})}
                              {inp('responsibility_group', 'گروه مسئولیت', {
                                type: 'select',
                                options: [
                                  { v: '', l: '— از اطلاعات پایه —' },
                                  ...respGroups.map((x) => ({ v: x.name, l: x.name })),
                                ],
                              })}
                              {inp('validity_end', 'پایان اعتبار')}
                              {inp('military_exemption_type', 'نوع معافیت نظام وظیفه', { lw: 110 })}
                              {inp('is_native', 'بومی', { type: 'radio' })}
                              {inp('time_card_code', 'کد کارت ساعت')}
                              {inp('card_status', 'وضعیت کارت', { type: 'select', options: [
                                { v: '', l: '—' }, { v: 'فعال', l: 'فعال' }, { v: 'مسدود', l: 'مسدود' },
                                { v: 'منقضی', l: 'منقضی' }, { v: 'باطل', l: 'باطل' },
                              ]})}
                            </div>

                            {/* ستون وسط */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 4, minHeight: 28, opacity: 0.85 }}>
                                <label style={{ fontSize: 11, color: '#718096', whiteSpace: 'nowrap', minWidth: 88, textAlign: 'left' }}>مرکز:</label>
                                <span style={{ flex: 1, fontSize: 12, color: '#4a5568' }}>{formData.center || '— از تخصیص شرکت به پرسنل —'}</span>
                              </div>
                              {inp('room_floor', 'اتاق/طبقه')}
                              {inp('previous_last_name', 'نام خانوادگی سابق', { lw: 100 })}
                              {inp('nickname', 'نام نانبر')}
                              {inp('nickname_family', 'نام خانوادگی نانبر', { lw: 100 })}
                              {inp('blood_type', 'گروه خونی', { type: 'select', options: [
                                { v: '', l: '—' },
                                ...['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((b) => ({ v: b, l: b })),
                              ]})}
                              {inp('father_name', 'نام پدر', { req: true })}
                              {inp('card_return_date', 'تاریخ عودت کارت')}
                              {inp('education_degree', 'مدرک تحصیلی')}
                              {inp('education_field', 'رشته تحصیلی', {
                                type: 'select',
                                options: [
                                  { v: '', l: '— از اطلاعات پایه —' },
                                  ...eduFields.map((x) => ({ v: x.name, l: x.name })),
                                ],
                              })}
                              {inp('landline', 'تلفن ثابت')}
                              {inp('postal_code', 'کد پستی')}
                              {inp('denomination', 'مذهب', { type: 'select', options: [
                                { v: '', l: '—' }, { v: 'نامشخص', l: 'نامشخص' }, { v: 'شیعه', l: 'شیعه' }, { v: 'سنی', l: 'سنی' },
                              ]})}
                              {inp('nationality', 'تابعیت', { req: true, type: 'select', options: [
                                { v: '', l: '—' }, { v: 'نامشخص', l: 'نامشخص' }, { v: 'ایرانی', l: 'ایرانی' }, { v: 'غیر ایرانی', l: 'غیر ایرانی' },
                              ]})}
                              {inp('email', 'ایمیل')}
                              {/* نام مرکز از اطلاعات پایه در فیلد مرکز بالا */}
                              {inp('is_retired', 'بازنشسته', { type: 'radio' })}
                              {inp('address', 'آدرس منزل')}
                              {inp('show_on_internet', 'نمایش در اینترنت', { type: 'radio', lw: 100 })}
                              {inp('description', 'توضیحات')}
                            </div>

                            {/* ستون چپ */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 4, minHeight: 28, opacity: 0.85 }}>
                                <label style={{ fontSize: 11, color: '#718096', whiteSpace: 'nowrap', minWidth: 88, textAlign: 'left' }}>واحد:</label>
                                <span style={{ flex: 1, fontSize: 12, color: '#4a5568' }}>{formData.department || '— از تخصیص شرکت به پرسنل —'}</span>
                              </div>
                              {inp('license_number', 'شماره گواهینامه')}
                              {inp('membership_type', 'نوع عضویت')}
                              {inp('employment_type', 'نوع استخدام', {
                                type: 'select',
                                options: [
                                  { v: '', l: '— از اطلاعات پایه —' },
                                  ...empTypes.map((x) => ({ v: x.name, l: x.name })),
                                ],
                              })}
                              {inp('card_number', 'شماره کارت')}
                              {inp('license_issue_place', 'محل صدور گواهینامه', { lw: 100 })}
                              {inp('id_cert_number', 'شماره شناسنامه')}
                              {inp('id_cert_place', 'محل صدور شناسنامه', { lw: 100 })}
                              {inp('internal_phone1', 'داخلی ۱')}
                              {inp('internal_phone2', 'داخلی ۲')}
                              {inp('internal_phone3', 'داخلی ۳')}
                              {inp('rank', 'رتبه')}
                              {inp('workplace', 'محل خدمت')}
                              {inp('hire_date', 'تاریخ استخدام')}
                              {inp('validity_start', 'تاریخ شروع اعتبار')}
                              {inp('marital_status', 'وضعیت تاهل', { type: 'select', options: [
                                { v: '', l: '—' }, { v: 'مجرد', l: 'مجرد' }, { v: 'متاهل', l: 'متاهل' },
                                { v: 'مطلقه', l: 'مطلقه' }, { v: 'همسر فوت‌شده', l: 'همسر فوت‌شده' },
                              ]})}
                              {inp('banned_entry', 'ممنوع الورودها', { type: 'radio' })}
                              {inp('settlement_done', 'تسویه حساب', { type: 'radio' })}
                              {inp('banned_security', 'ممنوع انتظامات', { type: 'radio' })}
                              {inp('print_count', 'دفعات چاپ')}
                            </div>
                          </>
                        )
                      })()}
                    </div>

                    {/* ردیف پایین — مطابق تصویر ۲ */}
                    <div style={{
                      display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8,
                      marginTop: 10, paddingTop: 10, borderTop: '1px solid #e2e8f0',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <label style={{ fontSize: 11, color: '#4a5568', whiteSpace: 'nowrap', minWidth: 100 }}>مجموعه دسترسی:</label>
                        <input value={formData.access_group || ''} onChange={(e) => setFormData({ ...formData, access_group: e.target.value })}
                          style={{ flex: 1, padding: '3px 6px', border: '1px solid #cbd5e0', borderRadius: 3, fontFamily: 'inherit', fontSize: 12, height: 26 }} />
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <label style={{ fontSize: 11, color: '#4a5568', whiteSpace: 'nowrap', minWidth: 100 }}>نام نمایشی آنلاین:</label>
                        <input value={formData.online_display_name || ''} onChange={(e) => setFormData({ ...formData, online_display_name: e.target.value })}
                          style={{ flex: 1, padding: '3px 6px', border: '1px solid #cbd5e0', borderRadius: 3, fontFamily: 'inherit', fontSize: 12, height: 26 }} />
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <label style={{ fontSize: 11, color: '#4a5568', whiteSpace: 'nowrap', minWidth: 70 }}>وضعیت:</label>
                        <select value={formData.active_status || 'فعال'} onChange={(e) => setFormData({ ...formData, active_status: e.target.value })}
                          style={{ flex: 1, padding: '3px 6px', border: '1px solid #cbd5e0', borderRadius: 3, fontFamily: 'inherit', fontSize: 12, height: 26 }}>
                          <option value="فعال">فعال</option>
                          <option value="غیرفعال">غیرفعال</option>
                        </select>
                      </div>
                    </div>

                    <div style={{ marginTop: 12, display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                      <button type="submit" style={{
                        padding: '7px 22px', background: '#2b6cb0', color: 'white', border: 'none',
                        borderRadius: 5, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13, fontWeight: 600,
                      }}>
                        {editingId ? '💾 ذخیره ویرایش' : '💾 ذخیره'}
                      </button>
                      <button type="button" className="refresh-btn" onClick={cancelPersonnelForm}>انصراف</button>
                    </div>
                  </form>
                </div>
              ) : (
                <div className="card">
                  <h3>لیست پرسنل ثبت‌شده</h3>
                  {renderPersonnelPagination('top')}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: 6, marginBottom: 10 }}>
                    {[
                      ['indicator_num', 'کد پرسنلی'],
                      ['first_name', 'نام'],
                      ['last_name', 'نام خانوادگی'],
                      ['national_id', 'کد ملی'],
                      ['company', 'شرکت'],
                      ['department', 'واحد'],
                      ['position', 'سمت'],
                      ['active_status', 'وضعیت'],
                    ].map(([key, label]) => (
                      <input
                        key={key}
                        placeholder={label}
                        value={columnFilters[key] || ''}
                        onChange={(e) => setColumnFilters({ ...columnFilters, [key]: e.target.value })}
                        style={{ padding: '6px 8px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 12 }}
                      />
                    ))}
                  </div>
                  {selectedPersonnel && (
                    <div
                      style={{
                        marginBottom: 10,
                        padding: '8px 12px',
                        background: '#ebf8ff',
                        border: '1px solid #90cdf4',
                        borderRadius: 6,
                        fontSize: 13,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: 12,
                        flexWrap: 'wrap',
                      }}
                    >
                      <span>
                        <strong>انتخاب‌شده:</strong>{' '}
                        {(selectedPersonnelList || []).length > 1
                          ? `${(selectedPersonnelList || []).length} نفر`
                          : `${selectedPersonnel.first_name || ''} ${selectedPersonnel.last_name || ''} — کدملی: ${selectedPersonnel.national_id || '—'} — ${selectedPersonnel.company || selectedPersonnel.company_code || ''}`}
                        {(selectedPersonnelList || []).length > 1 && (
                          <span style={{ color: '#4a5568', marginRight: 8 }}>
                            ({(selectedPersonnelList || []).slice(0, 3).map((x) => `${x.first_name || ''} ${x.last_name || ''}`).join('، ')}
                            {(selectedPersonnelList || []).length > 3 ? '…' : ''})
                          </span>
                        )}
                      </span>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          className="btn-primary"
                          style={{ fontSize: 12 }}
                          onClick={() => {
                            setShowAssignOrg(true)
                            setShowRegisterForm(false)
                            setShowDependents(false)
                            setShowCards(false)
                            setPersonnelRecordKind(null)
                            setAssignOrgMsg('')
                            loadUnits()
                            loadCompanies()
                            const p = selectedPersonnel
                            setAssignOrgForm({
                              company_code: p?.company_code != null ? String(p.company_code) : '',
                              center: p?.center || '',
                              department: p?.department || '',
                            })
                          }}
                        >
                          🏢 تخصیص گروهی شرکت / مرکز / واحد
                        </button>
                        <button
                          type="button"
                          className="refresh-btn"
                          style={{ fontSize: 12 }}
                          onClick={() => clearPersonnelSelection()}
                        >
                          ✕ لغو انتخاب
                        </button>
                      </div>
                    </div>
                  )}
                  <table>
                    <thead>
                      <tr>
                        <th style={{ width: 48 }}>
                          <input
                            type="checkbox"
                            title="انتخاب همه در این صفحه"
                            checked={(filteredPersonnel || []).length > 0 && (filteredPersonnel || []).every((p) => isPersonSelected(p))}
                            onChange={(e) => selectAllFilteredPersonnel(e.target.checked)}
                          />
                        </th>
                        <th>ردیف</th>
                        <th>مرکز</th>
                        <th>کد پرسنلی</th>
                        <th>واحد</th>
                        <th>نام</th>
                        <th>نام خانوادگی</th>
                        <th>نام خانوادگی سابق</th>
                        <th>سمت</th>
                        <th>جنسیت</th>
                        <th>کد ملی</th>
                        <th>تلفن همراه</th>
                        <th>وضعیت</th>
                        <th>عملیات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {personnel.length === 0 ? (
                        <tr>
                          <td colSpan={14} style={{ textAlign: 'center', color: '#718096' }}>
                            {apiStatus === 'offline'
                              ? 'اتصال به سرور برقرار نیست — بک‌اند را روی پورت 8100 اجرا کنید'
                              : 'پرسنلی یافت نشد'}
                          </td>
                        </tr>
                      ) : filteredPersonnel.length === 0 ? (
                        <tr>
                          <td colSpan={14} style={{ textAlign: 'center', color: '#718096' }}>
                            موردی با این فیلتر یافت نشد
                          </td>
                        </tr>
                      ) : (
                        filteredPersonnel.map((p) => {
                          const selected = isPersonSelected(p)
                          return (
                            <tr
                              key={personKey(p)}
                              onClick={() => selectPersonnel(p)}
                              style={{
                                cursor: 'pointer',
                                background: selected ? '#ebf8ff' : undefined,
                                outline: selected ? '2px solid #3182ce' : undefined,
                                outlineOffset: -2,
                              }}
                            >
                              <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                                <input
                                  type="checkbox"
                                  checked={!!selected}
                                  onChange={() => selectPersonnel(p)}
                                  title="انتخاب پرسنل (می‌توانید چند نفر را همزمان انتخاب کنید)"
                                />
                              </td>
                              <td>{p.row_num || p.id}</td>
                              <td>{p.company || p.center || '—'}</td>
                              <td>{p.indicator_num || '—'}</td>
                              <td>{p.department || '—'}</td>
                              <td>{p.first_name}</td>
                              <td>{p.last_name}</td>
                              <td>{p.previous_last_name || '—'}</td>
                              <td>{p.position || '—'}</td>
                              <td>{p.gender || '—'}</td>
                              <td>{p.national_id}</td>
                              <td>{p.phone || '—'}</td>
                              <td>
                                <span
                                  className={`badge ${
                                    p.active_status === 'فعال' ? 'badge-green' : 'badge-red'
                                  }`}
                                >
                                  {p.active_status || '—'}
                                </span>
                              </td>
                              <td style={{ whiteSpace: 'nowrap' }} onClick={(e) => e.stopPropagation()}>
                                <button
                                  type="button"
                                  className="refresh-btn"
                                  onClick={() => startEditPersonnel(p)}
                                >
                                  ویرایش
                                </button>
                                {' '}
                                <button
                                  type="button"
                                  className="refresh-btn"
                                  onClick={() => handleDeletePersonnel(p)}
                                >
                                  حذف
                                </button>
                              </td>
                            </tr>
                          )
                        })
                      )}
                    </tbody>
                  </table>
                  {renderPersonnelPagination('bottom')}
                </div>
              )}
            </>
          ) : activeTab === 'gozaresh' ? (
            <div style={{ padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h2 style={{ margin: 0, fontSize: 18, color: '#2b6cb0' }}>
                  {reportData?.title || 'گزارشات'}
                </h2>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ fontSize: 12, color: '#718096' }}>
                    {reportLoading ? 'در حال بارگذاری…' : `${reportData?.count ?? 0} ردیف`}
                  </span>
                  <button type="button" onClick={() => loadReport(reportKey)}
                    style={{ padding: '6px 12px', background: '#2b6cb0', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 12 }}>
                    🔄 بروزرسانی
                  </button>
                </div>
              </div>
              <div style={{ overflowX: 'auto', background: '#fff', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ردیف</th>
                      {(reportData?.columns || []).map((c) => <th key={c}>{c}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {(reportData?.rows || []).length === 0 ? (
                      <tr><td colSpan={(reportData?.columns?.length || 0) + 1} style={{ textAlign: 'center', color: '#a0aec0' }}>
                        {reportLoading ? '…' : 'داده‌ای یافت نشد'}
                      </td></tr>
                    ) : (reportData.rows.map((row, i) => (
                      <tr key={i}>
                        <td>{i + 1}</td>
                        {(reportData.columns || []).map((c) => <td key={c}>{row[c] ?? ''}</td>)}
                      </tr>
                    )))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : activeTab === 'baseinfo' ? (

            <>
              <div className="workspace-header">
                <h2>
                  {baseSubView === 'units' ? 'تعریف واحدها' :
                   baseSubView === 'edu' ? 'رشته تحصیلی' :
                   baseSubView === 'resp' ? 'گروه مسئولیت' :
                   baseSubView === 'emp' ? 'انواع استخدام' :
                   (ENTITY_VIEW_MAP[baseSubView]?.title || LOOKUP_VIEW_MAP[baseSubView]?.title || 'اطلاعات پایه')}
                </h2>
              </div>

              {false && baseSubView === 'units' && (
                <div className="card">
                  <div style={{ marginBottom: 12, padding: '8px 12px', background: '#ebf8ff', border: '1px solid #90cdf4', borderRadius: 6, fontSize: 12, lineHeight: 1.7 }}>
                    <b>منبع تعریف مرکز و واحد:</b> نام مرکز و نام واحد اینجا ثبت می‌شود.
                    در فرم پرسنل و سایر برگه‌ها، فیلدهای <b>مرکز</b> و <b>واحد</b> فقط از این لیست خوانده می‌شوند.
                    برای اتصال به دیتابیس شرکت، فیلد «شرکت» را روی واحد تنظیم کنید.
                  </div>
                  {unitMsg && (
                    <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 6, background: unitMsg.includes('موفق') || unitMsg.includes('شد') ? '#c6f6d5' : '#fed7d7', color: unitMsg.includes('موفق') || unitMsg.includes('شد') ? '#276749' : '#c53030', fontSize: 13 }}>{unitMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = {
                      ...unitForm,
                      company_code: unitForm.company_code ? Number(unitForm.company_code) : null,
                    }
                    const isEdit = Boolean(editingUnitId)
                    const url = isEdit ? `/api/units/${editingUnitId}` : '/api/units'
                    fetch(url, { method: isEdit ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
                      .then(async (r) => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || 'خطا'); return d })
                      .then(() => {
                        setUnitMsg(isEdit ? 'واحد ویرایش شد' : 'واحد با موفقیت ثبت شد')
                        setEditingUnitId(null)
                        setUnitForm({ code: '', name: '', parent_name: '', center_name: '', company_code: '', show_on_guard_board: true, show_on_internet: false, image_path: '', symbol_path: '' })
                        loadUnits()
                        setTimeout(() => setUnitMsg(''), 1500)
                      })
                      .catch((err) => setUnitMsg(err.message || 'خطا'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 10, marginBottom: 12 }}>
                      {[
                        ['center_name', 'نام مرکز *'], ['name', 'نام واحد *'], ['parent_name', 'واحد والد'], ['code', 'کد واحد'],
                      ].map(([k, lab]) => (
                        <div key={k}>
                          <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>{lab}</label>
                          <input required={lab.includes('*')} value={unitForm[k] || ''} onChange={(e) => setUnitForm({ ...unitForm, [k]: e.target.value })}
                            style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                        </div>
                      ))}
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>شرکت</label>
                        <select value={unitForm.company_code || ''} onChange={(e) => setUnitForm({ ...unitForm, company_code: e.target.value })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="">— همه / مشترک —</option>
                          {companies.map((c) => (
                            <option key={c.code} value={c.code}>{c.code} — {c.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>نمایش در لوح نگهبانی</label>
                        <select value={unitForm.show_on_guard_board ? '1' : '0'} onChange={(e) => setUnitForm({ ...unitForm, show_on_guard_board: e.target.value === '1' })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="1">بلی</option><option value="0">خیر</option>
                        </select>
                      </div>
                      <div>
                        <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>نمایش در اینترنت</label>
                        <select value={unitForm.show_on_internet ? '1' : '0'} onChange={(e) => setUnitForm({ ...unitForm, show_on_internet: e.target.value === '1' })}
                          style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                          <option value="0">خیر</option><option value="1">بلی</option>
                        </select>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                      <button type="submit" style={{ padding: '8px 20px', background: '#2b6cb0', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}>
                        {editingUnitId ? '💾 ذخیره ویرایش' : '💾 ثبت واحد'}
                      </button>
                      {editingUnitId && (
                        <button type="button" className="refresh-btn" onClick={() => { setEditingUnitId(null); setUnitForm({ code: '', name: '', parent_name: '', center_name: '', company_code: '', show_on_guard_board: true, show_on_internet: false, image_path: '', symbol_path: '' }) }}>انصراف</button>
                      )}
                    </div>
                  </form>
                  <table>
                    <thead><tr><th>ردیف</th><th>کد</th><th>نام مرکز</th><th>نام واحد</th><th>واحد والد</th><th>لوح نگهبانی</th><th>عملیات</th></tr></thead>
                    <tbody>
                      {units.length === 0 ? (
                        <tr><td colSpan={7} style={{ textAlign: 'center', color: '#718096' }}>واحدی ثبت نشده</td></tr>
                      ) : units.map((u, i) => (
                        <tr key={u.id}>
                          <td>{i + 1}</td>
                          <td>{u.code}</td>
                          <td>{u.center_name}</td>
                          <td>{u.name}</td>
                          <td>{u.parent_name}</td>
                          <td>{u.show_on_guard_board ? '✓' : '—'}</td>
                          <td style={{ whiteSpace: 'nowrap' }}>
                            <button type="button" className="refresh-btn" onClick={() => {
                              setEditingUnitId(u.id)
                              setUnitForm({ code: u.code || '', name: u.name || '', parent_name: u.parent_name || '', center_name: u.center_name || '', company_code: u.company_code || '', show_on_guard_board: !!u.show_on_guard_board, show_on_internet: !!u.show_on_internet })
                            }}>ویرایش</button>{' '}
                            <button type="button" className="refresh-btn" onClick={() => {
                              if (!window.confirm('حذف واحد؟')) return
                              fetch(`/api/units/${u.id}`, { method: 'DELETE' }).then(() => loadUnits())
                            }}>حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {(baseSubView === 'edu' || baseSubView === 'resp' || baseSubView === 'emp') && (
                <div className="card">
                  {namedMsg && (
                    <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 6, background: namedMsg.includes('موفق') || namedMsg.includes('شد') ? '#c6f6d5' : '#fed7d7', color: namedMsg.includes('موفق') || namedMsg.includes('شد') ? '#276749' : '#c53030', fontSize: 13 }}>{namedMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const name = baseSubView === 'edu' ? eduName : baseSubView === 'resp' ? respName : empName
                    const endpoint = baseSubView === 'edu' ? '/api/education-fields' : baseSubView === 'resp' ? '/api/responsibility-groups' : '/api/employment-types'
                    fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
                      .then(async (r) => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || 'خطا'); return d })
                      .then(() => {
                        setNamedMsg('با موفقیت ثبت شد')
                        if (baseSubView === 'edu') { setEduName(''); loadEduFields() }
                        else if (baseSubView === 'resp') { setRespName(''); loadRespGroups() }
                        else { setEmpName(''); loadEmpTypes() }
                        setTimeout(() => setNamedMsg(''), 1500)
                      })
                      .catch((err) => setNamedMsg(err.message || 'خطا'))
                  }} style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>
                        {baseSubView === 'edu' ? 'رشته تحصیلی' : baseSubView === 'resp' ? 'گروه مسئولیت' : 'نوع استخدام'}
                      </label>
                      <input required
                        value={baseSubView === 'edu' ? eduName : baseSubView === 'resp' ? respName : empName}
                        onChange={(e) => {
                          if (baseSubView === 'edu') setEduName(e.target.value)
                          else if (baseSubView === 'resp') setRespName(e.target.value)
                          else setEmpName(e.target.value)
                        }}
                        style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                    </div>
                    <button type="submit" style={{ padding: '8px 20px', background: '#2b6cb0', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}>➕ افزودن</button>
                  </form>
                  <table>
                    <thead><tr><th>ردیف</th><th>نام</th><th>عملیات</th></tr></thead>
                    <tbody>
                      {(baseSubView === 'edu' ? eduFields : baseSubView === 'resp' ? respGroups : empTypes).length === 0 ? (
                        <tr><td colSpan={3} style={{ textAlign: 'center', color: '#718096' }}>موردی ثبت نشده</td></tr>
                      ) : (baseSubView === 'edu' ? eduFields : baseSubView === 'resp' ? respGroups : empTypes).map((item, i) => (
                        <tr key={item.id}>
                          <td>{i + 1}</td>
                          <td>{item.name}</td>
                          <td>
                            <button type="button" className="refresh-btn" onClick={() => {
                              if (!window.confirm('حذف؟')) return
                              const endpoint = baseSubView === 'edu' ? `/api/education-fields/${item.id}` : baseSubView === 'resp' ? `/api/responsibility-groups/${item.id}` : `/api/employment-types/${item.id}`
                              fetch(endpoint, { method: 'DELETE' }).then(() => {
                                if (baseSubView === 'edu') loadEduFields()
                                else if (baseSubView === 'resp') loadRespGroups()
                                else loadEmpTypes()
                              })
                            }}>حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {LOOKUP_VIEW_MAP[baseSubView] && (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const meta = LOOKUP_VIEW_MAP[baseSubView]
                    if (!meta || !lookupName.trim()) return
                    fetch(`/api/lookups/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ name: lookupName.trim(), description: lookupDesc.trim() }),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setLookupName('')
                        setLookupDesc('')
                        loadLookup(baseSubView)
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }} style={{ display: 'flex', gap: 10, alignItems: 'flex-end', marginBottom: 14, flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: 180 }}>
                      <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>نام</label>
                      <input required value={lookupName} onChange={(e) => setLookupName(e.target.value)}
                        style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                    </div>
                    <div style={{ flex: 1, minWidth: 180 }}>
                      <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 3 }}>توضیحات</label>
                      <input value={lookupDesc} onChange={(e) => setLookupDesc(e.target.value)}
                        style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                    </div>
                    <button type="submit" style={{
                      padding: '8px 16px', background: '#2b6cb0', color: '#fff', border: 'none',
                      borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13,
                    }}>💾 ثبت</button>
                  </form>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ردیف</th>
                        <th>نام</th>
                        <th>توضیحات</th>
                        <th>عملیات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lookupItems.length === 0 ? (
                        <tr><td colSpan={4} style={{ textAlign: 'center', color: '#718096' }}>موردی ثبت نشده</td></tr>
                      ) : lookupItems.map((item, i) => (
                        <tr key={item.id}>
                          <td>{i + 1}</td>
                          <td>{item.name}</td>
                          <td>{item.description || '—'}</td>
                          <td>
                            <button type="button" className="refresh-btn" onClick={() => {
                              if (!window.confirm('حذف شود؟')) return
                              const meta = LOOKUP_VIEW_MAP[baseSubView]
                              fetch(`/api/lookups/${meta.table}/${item.id}`, { method: 'DELETE' })
                                .then((r) => {
                                  if (!r.ok) throw new Error('خطا')
                                  loadLookup(baseSubView)
                                  setLookupMsg('حذف شد')
                                })
                                .catch((err) => setLookupMsg(err.message || 'خطا'))
                            }}>حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {ENTITY_VIEW_MAP[baseSubView] && (() => {
                const meta = ENTITY_VIEW_MAP[baseSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {meta?.table && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی:</span>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl(`/api/baseinfo/${meta.table}/template.csv`, `${meta.table}_template.csv`)}>
                        📥 دانلود قالب CSV
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود از CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => {
                            const f = e.target.files?.[0]
                            e.target.value = ''
                            if (!f) return
                            importBaseinfoCsvFile(meta.table, f, (msg) => {
                              setLookupMsg(msg)
                              loadLookup(peymankarSubView || baseSubView || cardSubView, activeTab === 'peymankar' ? 'peymankar' : activeTab === 'baseinfo' ? 'baseinfo' : undefined)
                            })
                          }} />
                      </label>
                      <span style={{ fontSize: 11, color: '#718096' }}>ستون‌های قالب مطابق فیلدهای همین فرم است</span>
                    </div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(baseSubView)
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : (optionsForField(f.key) !== null) ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => {
                              const val = e.target.value
                              const next = { ...entityForm, [f.key]: val }
                              setEntityForm(next)
                            }}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                              required={!!f.required}>
                              <option value="">— انتخاب از اطلاعات پایه —</option>
                              {optionsForField(f.key).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : f.type === 'image' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                              {entityForm[f.key] ? (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                  <img src={entityForm[f.key]} alt="لوگو" style={{ width: 56, height: 56, objectFit: 'contain', border: '1px solid #e2e8f0', borderRadius: 6, background: '#fff' }} />
                                  <button type="button" className="refresh-btn" style={{ fontSize: 12 }} onClick={() => setEntityForm({ ...entityForm, [f.key]: '' })}>حذف لوگو</button>
                                </div>
                              ) : null}
                              <input type="file" accept="image/*" onChange={(e) => {
                                const file = e.target.files?.[0]
                                e.target.value = ''
                                if (!file) return
                                if (file.size > 2 * 1024 * 1024) {
                                  setLookupMsg('حجم لوگو حداکثر ۲ مگابایت باشد')
                                  return
                                }
                                const reader = new FileReader()
                                reader.onload = () => setEntityForm({ ...entityForm, [f.key]: String(reader.result || '') })
                                reader.readAsDataURL(file)
                              }} style={{ fontSize: 12 }} />
                              <span style={{ fontSize: 11, color: '#718096' }}>PNG/JPG — حداکثر ۲MB</span>
                            </div>
                          ) : f.type === 'bool' ? (
                            <div style={{ display: 'flex', gap: 12, fontSize: 13, paddingTop: 6 }}>
                              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                                <input type="radio" checked={!!entityForm[f.key]} onChange={() => setEntityForm({ ...entityForm, [f.key]: true })} /> بلی
                              </label>
                              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                                <input type="radio" checked={!entityForm[f.key]} onChange={() => setEntityForm({ ...entityForm, [f.key]: false })} /> خیر
                              </label>
                            </div>
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13, direction: f.key === 'plate_number' ? 'ltr' : undefined, textAlign: f.key === 'plate_number' ? 'left' : undefined }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <button type="submit" style={{ padding: '8px 16px', background: '#2b6cb0', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13, marginBottom: 12 }}>💾 ثبت</button>
                  </form>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => (
                              <td key={c}>
                                {c === 'logo' && item[c] ? (
                                  <img src={item[c]} alt="" style={{ width: 36, height: 36, objectFit: 'contain', borderRadius: 4, border: '1px solid #e2e8f0' }} />
                                ) : c === 'is_active' || c === 'is_entry' || c === 'is_exit' ? (item[c] ? '✓' : '—') : (
                                  (typeof item[c] === 'string' && item[c].startsWith('data:image') ? '🖼 لوگو' : (item[c] || '—'))
                                )}
                              </td>
                            ))}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(baseSubView); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}

            </>
          ) : activeTab === 'entezamat' ? (
            <>
              <div className="workspace-header">
                <h2>{ENTEZAMAT_VIEW_MAP[entezamatSubView]?.title || 'انتظامات'}</h2>
              </div>
              {ENTEZAMAT_VIEW_MAP[entezamatSubView] && (() => {
                const meta = ENTEZAMAT_VIEW_MAP[entezamatSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {meta?.table && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی:</span>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl(`/api/baseinfo/${meta.table}/template.csv`, `${meta.table}_template.csv`)}>
                        📥 دانلود قالب CSV
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود از CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => {
                            const f = e.target.files?.[0]
                            e.target.value = ''
                            if (!f) return
                            importBaseinfoCsvFile(meta.table, f, (msg) => {
                              setLookupMsg(msg)
                              loadLookup(peymankarSubView || baseSubView || cardSubView, activeTab === 'peymankar' ? 'peymankar' : activeTab === 'baseinfo' ? 'baseinfo' : undefined)
                            })
                          }} />
                      </label>
                      <span style={{ fontSize: 11, color: '#718096' }}>ستون‌های قالب مطابق فیلدهای همین فرم است</span>
                    </div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(entezamatSubView, 'entezamat')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : (optionsForField(f.key) !== null) ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                              required={!!f.required}>
                              <option value="">— انتخاب از اطلاعات پایه —</option>
                              {optionsForField(f.key).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13, direction: f.key === 'plate_number' ? 'ltr' : undefined, textAlign: f.key === 'plate_number' ? 'left' : undefined }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <button type="submit" style={{ padding: '8px 16px', background: '#2b6cb0', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13, marginBottom: 12 }}>💾 ثبت</button>
                  </form>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] || '—'}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(entezamatSubView, 'entezamat'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'sodor_kart' ? (
            <>
              <div className="workspace-header">
                <h2>{CARD_VIEW_MAP[cardSubView]?.title || 'صدور کارت'}</h2>
              </div>
              {CARD_VIEW_MAP[cardSubView] && (() => {
                const meta = CARD_VIEW_MAP[cardSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                const isReadOnly = !!meta.readOnly
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {!isReadOnly && (
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(cardSubView, 'card')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : f.type === 'bool' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                              <input type="checkbox" checked={!!entityForm[f.key]}
                                onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.checked ? 1 : 0 })} />
                              بله
                            </label>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت / صدور کارت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(cardSubView, 'card')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  )}
                  {isReadOnly && (
                    <div style={{ marginBottom: 12 }}>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(cardSubView, 'card')}>🔄 به‌روزرسانی گزارش</button>
                    </div>
                  )}
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          {!isReadOnly && <th>عملیات</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] === 0 || item[c] === 1 ? (item[c] ? '✓' : '✗') : (item[c] ?? '—')}</td>)}
                            {!isReadOnly && (
                              <td>
                                <button type="button" className="refresh-btn" onClick={() => {
                                  if (!window.confirm('حذف شود؟')) return
                                  fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                    .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(cardSubView, 'card'); setLookupMsg('حذف شد') })
                                    .catch((err) => setLookupMsg(err.message || 'خطا'))
                                }}>حذف</button>
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'mojaz' ? (
            <>
              <div className="workspace-header">
                <h2>
                  {mojazSubView === 'person' && 'مجوز تردد نفر'}
                  {mojazSubView === 'vehicle' && 'مجوز تردد خودرو'}
                  {mojazSubView === 'goods' && 'مجوز خروج کالا'}
                  {mojazSubView === 'list' && 'لیست و تأیید مجوزهای صادر شده'}
                  {mojazSubView === 'report' && 'گزارش‌گیری مجوزهای تردد — خروجی CSV'}
                  {mojazSubView === 'trd_train' && 'قطار و واگن باری'}
                  {mojazSubView === 'trd_ship' && 'تردد کشتی در اسکله'}
                  {mojazSubView === 'trd_foreign' && 'اتباع خارج‌شده از کشتی'}
                  {mojazSubView === 'trd_water' && 'آبگیری شناورها'}
                  {mojazSubView === 'trd_sec' && 'اطلاعات امنیتی کشتی'}
                </h2>
                <button type="button" className="refresh-btn" onClick={() => { setMjzMsg(''); loadMjzPermits() }}>🔄 به‌روزرسانی</button>
              </div>
              {mjzMsg && (
                <div style={{ margin: '8px 0', padding: '10px 14px', borderRadius: 8, background: (mjzMsg.includes('خطا') || mjzMsg.includes('الزامی')) ? '#fff5f5' : '#f0fff4', color: (mjzMsg.includes('خطا') || mjzMsg.includes('الزامی')) ? '#c53030' : '#276749', fontSize: 13 }}>
                  {mjzMsg}
                </div>
              )}
              {(mojazSubView === 'person' || mojazSubView === 'vehicle' || mojazSubView === 'goods') && (
                <div className="card" style={{ maxWidth: 960, padding: 20 }}>
                  <div style={{ marginBottom: 14, paddingBottom: 10, borderBottom: '1px solid #edf2f7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#1a365d' }}>
                        {mojazSubView === 'person' && '📋 فرم مجوز تردد نفر'}
                        {mojazSubView === 'vehicle' && '🚗 فرم مجوز تردد خودرو'}
                        {mojazSubView === 'goods' && '📦 فرم مجوز خروج کالا'}
                      </div>
                      <div style={{ fontSize: 12, color: '#718096', marginTop: 4 }}>
                        فیلدهای ستاره‌دار الزامی هستند · تاریخ‌ها به صورت جلالی (مثال: 1405/07/20)
                      </div>
                    </div>
                    <span className="badge-blue" style={{ fontSize: 12, padding: '4px 10px' }}>
                      {mojazSubView === 'person' && 'نوع: تردد نفر'}
                      {mojazSubView === 'vehicle' && 'نوع: تردد خودرو'}
                      {mojazSubView === 'goods' && 'نوع: خروج کالا'}
                    </span>
                  </div>

                  {/* بخش مشخصات فرد */}
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#2d3748', marginBottom: 10, padding: '6px 10px', background: '#f7fafc', borderRadius: 6, borderRight: '3px solid #2b6cb0' }}>
                      مشخصات متقاضی
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 16px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>نام دارنده / متقاضی <span style={{ color: '#c53030' }}>*</span></label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.holder_name} onChange={(e) => setMjzForm({ ...mjzForm, holder_name: e.target.value })} placeholder="نام و نام خانوادگی" />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>کد ملی</label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.national_id} onChange={(e) => setMjzForm({ ...mjzForm, national_id: e.target.value })} placeholder="0012345678" maxLength={10} />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>کد پرسنلی</label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.personnel_code} onChange={(e) => setMjzForm({ ...mjzForm, personnel_code: e.target.value })} placeholder="اختیاری" />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>شرکت / پیمانکار</label>
                        <input list="mjz-client-companies" style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.company_name} onChange={(e) => setMjzForm({ ...mjzForm, company_name: e.target.value })} placeholder="از لیست یا دستی" />
                        <datalist id="mjz-client-companies">
                          {(baseClientCompanies || []).map((c) => (
                            <option key={c.id || c.name} value={c.name} />
                          ))}
                          {(companies || []).map((c) => (
                            <option key={`co-${c.code}`} value={c.name} />
                          ))}
                        </datalist>
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>واحد سازمانی</label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.unit_name} onChange={(e) => setMjzForm({ ...mjzForm, unit_name: e.target.value })} placeholder="نام واحد" />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>دروازه / محل ورود</label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.gate_name} onChange={(e) => setMjzForm({ ...mjzForm, gate_name: e.target.value })} placeholder="مثلاً دروازه اصلی" />
                      </div>
                    </div>
                  </div>

                  {/* بخش خودرو — فقط vehicle و goods */}
                  {(mojazSubView === 'vehicle' || mojazSubView === 'goods') && (
                    <div style={{ marginBottom: 16 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#2d3748', marginBottom: 10, padding: '6px 10px', background: '#f7fafc', borderRadius: 6, borderRight: '3px solid #dd6b20' }}>
                        مشخصات خودرو
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 16px' }}>
                        <div>
                          <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>شماره پلاک {mojazSubView === 'vehicle' && <span style={{ color: '#c53030' }}>*</span>}</label>
                          <IranPlateInput
                            required={mojazSubView === 'vehicle'}
                            value={mjzForm.vehicle_plate}
                            onChange={(v) => setMjzForm({ ...mjzForm, vehicle_plate: v })}
                          />
                        </div>
                        <div>
                          <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>نوع خودرو</label>
                          <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.vehicle_type} onChange={(e) => setMjzForm({ ...mjzForm, vehicle_type: e.target.value })} placeholder="سواری / وانت / باری" />
                        </div>
                        <div>
                          <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>نام راننده</label>
                          <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.driver_name} onChange={(e) => setMjzForm({ ...mjzForm, driver_name: e.target.value })} placeholder="نام راننده" />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* بخش کالا — فقط goods */}
                  {mojazSubView === 'goods' && (
                    <div style={{ marginBottom: 16 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#2d3748', marginBottom: 10, padding: '6px 10px', background: '#f7fafc', borderRadius: 6, borderRight: '3px solid #38a169' }}>
                        مشخصات کالا
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 16px' }}>
                        <div>
                          <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>شرح کالا <span style={{ color: '#c53030' }}>*</span></label>
                          <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.goods_desc} onChange={(e) => setMjzForm({ ...mjzForm, goods_desc: e.target.value })} placeholder="شرح کالا / محموله" />
                        </div>
                        <div>
                          <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>تعداد / مقدار</label>
                          <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.goods_count} onChange={(e) => setMjzForm({ ...mjzForm, goods_count: e.target.value })} placeholder="مثلاً ۱۲ بسته" />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* بخش اعتبار و زمان مجاز */}
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#2d3748', marginBottom: 10, padding: '6px 10px', background: '#f7fafc', borderRadius: 6, borderRight: '3px solid #805ad5' }}>
                      اعتبار و زمان مجاز ورود / خروج (جلالی)
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 16px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>از تاریخ اعتبار</label>
                        <JalaliDateInput value={mjzForm.valid_from} onChange={(v) => setMjzForm({ ...mjzForm, valid_from: v })} />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>تا تاریخ اعتبار</label>
                        <JalaliDateInput value={mjzForm.valid_to} onChange={(v) => setMjzForm({ ...mjzForm, valid_to: v })} />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>تاریخ مجاز ورود</label>
                        <JalaliDateInput value={mjzForm.allowed_entry_date} onChange={(v) => setMjzForm({ ...mjzForm, allowed_entry_date: v })} />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>ساعت مجاز ورود</label>
                        <JalaliTimeInput value={mjzForm.allowed_entry_time} onChange={(v) => setMjzForm({ ...mjzForm, allowed_entry_time: v })} />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>تاریخ مجاز خروج</label>
                        <JalaliDateInput value={mjzForm.allowed_exit_date} onChange={(v) => setMjzForm({ ...mjzForm, allowed_exit_date: v })} />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>ساعت مجاز خروج</label>
                        <JalaliTimeInput value={mjzForm.allowed_exit_time} onChange={(v) => setMjzForm({ ...mjzForm, allowed_exit_time: v })} />
                      </div>
                    </div>
                  </div>

                  {/* بخش مقصد و توضیحات */}
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#2d3748', marginBottom: 10, padding: '6px 10px', background: '#f7fafc', borderRadius: 6, borderRight: '3px solid #3182ce' }}>
                      مقصد و توضیحات
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px 16px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>مقصد</label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.destination} onChange={(e) => setMjzForm({ ...mjzForm, destination: e.target.value })} placeholder="محل مقصد" />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>هدف / علت تردد</label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.purpose} onChange={(e) => setMjzForm({ ...mjzForm, purpose: e.target.value })} placeholder="علت درخواست مجوز" />
                      </div>
                      <div style={{ gridColumn: '1 / -1' }}>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>توضیحات</label>
                        <input style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} value={mjzForm.notes} onChange={(e) => setMjzForm({ ...mjzForm, notes: e.target.value })} placeholder="توضیحات تکمیلی" />
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', borderTop: '1px solid #edf2f7', paddingTop: 14 }}>
                    <button type="button" className="btn-secondary" onClick={() => resetMjzForm(mojazSubView === 'goods' ? 'goods' : mojazSubView === 'vehicle' ? 'vehicle' : 'person')}>پاک کردن</button>
                    <button type="button" className="btn-primary" onClick={saveMjzPermit}>💾 صدور مجوز</button>
                  </div>
                </div>
              )}



              {['trd_train','trd_ship','trd_foreign','trd_water','trd_sec'].includes(mojazSubView) && (
                <div className="card" style={{ padding: 20, maxWidth: 900 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#1a365d', marginBottom: 12 }}>
                    {mojazSubView === 'trd_train' && '🚂 ثبت تردد قطار و واگن باری'}
                    {mojazSubView === 'trd_ship' && '🚢 ثبت تردد کشتی در اسکله'}
                    {mojazSubView === 'trd_foreign' && '👤 ثبت اتباع خارج‌شده از کشتی'}
                    {mojazSubView === 'trd_water' && '💧 ثبت آبگیری شناورها'}
                    {mojazSubView === 'trd_sec' && '🔒 ثبت اطلاعات امنیتی کشتی'}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 12 }}>
                    {(mojazSubView === 'trd_train' ? ['شماره قطار/واگن','مبدأ','مقصد','تاریخ حرکت','ساعت','شرح بار','شرکت حمل','توضیحات']
                      : mojazSubView === 'trd_ship' ? ['نام کشتی','پرچم','اسکله','تاریخ ورود','ساعت ورود','تاریخ خروج','ساعت خروج','نماینده','توضیحات']
                      : mojazSubView === 'trd_foreign' ? ['نام','ملیت','شماره گذرنامه','نام کشتی','تاریخ خروج','ساعت','مقصد','توضیحات']
                      : mojazSubView === 'trd_water' ? ['نام شناور','اسکله','حجم آب (م³)','تاریخ','ساعت','مسئول','توضیحات']
                      : ['نام کشتی','سطح امنیتی','تاریخ بازرسی','ساعت','نتیجه','بازرس','توضیحات']
                    ).map((lab) => (
                      <div key={lab}>
                        <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>{lab}</label>
                        {lab.includes('تاریخ') ? (
                          <JalaliDateInput value={entityForm[lab] || ''} onChange={(v) => setEntityForm({ ...entityForm, [lab]: v })} />
                        ) : lab.includes('ساعت') ? (
                          <JalaliTimeInput value={entityForm[lab] || ''} onChange={(v) => setEntityForm({ ...entityForm, [lab]: v })} />
                        ) : (
                          <input value={entityForm[lab] || ''} onChange={(e) => setEntityForm({ ...entityForm, [lab]: e.target.value })}
                            style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                        )}
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                    <button type="button" className="btn-primary" onClick={() => { setMjzMsg('ثبت شد'); setEntityForm({}) }}>💾 ثبت</button>
                    <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setMojazSubView('list') }}>بازگشت</button>
                  </div>
                  {mjzMsg && <div style={{ marginTop: 10, fontSize: 13, color: '#276749' }}>{mjzMsg}</div>}
                </div>
              )}

              {mojazSubView === 'report' && (
                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 20 }}>
                  <h3 style={{ marginTop: 0, color: '#1a365d' }}>گزارش‌گیری مجوزهای تردد</h3>
                  <p style={{ color: '#4a5568', fontSize: 13, lineHeight: 1.7 }}>
                    فیلترها را تنظیم کنید و خروجی CSV را دریافت کنید. فیلدهای گزارش: شماره مجوز، نوع، وضعیت، مشخصات فرد/خودرو/کالا، زمان‌های مجاز و واقعی ورود/خروج، تأخیرها و صادرکننده.
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 16 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>نوع مجوز</label>
                      <select id="mjzRptType" defaultValue="" style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                        <option value="">همه انواع</option>
                        <option value="person">تردد نفر</option>
                        <option value="vehicle">تردد خودرو</option>
                        <option value="goods">خروج کالا</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>وضعیت</label>
                      <select id="mjzRptStatus" defaultValue="" style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                        <option value="">همه وضعیت‌ها</option>
                        <option value="issued">صادر شده</option>
                        <option value="entered">ورود ثبت‌شده</option>
                        <option value="exited">خروج ثبت‌شده</option>
                        <option value="cancelled">لغو شده</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>جستجو متنی</label>
                      <input value={mjzSearchNo} onChange={(e) => setMjzSearchNo(e.target.value)}
                        placeholder="نام، پلاک، شماره..." style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0' }} />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
                    <button type="button" className="btn-primary" onClick={() => loadMjzPermits({
                      q: (mjzSearchNo || '').trim() || undefined,
                      permit_type: document.getElementById('mjzRptType')?.value || undefined,
                      status: document.getElementById('mjzRptStatus')?.value || undefined,
                    })}>پیش‌نمایش</button>
                    <button type="button" className="btn-primary" style={{ background: '#276749' }} onClick={() => exportMjzCsv({
                      permit_type: document.getElementById('mjzRptType')?.value || undefined,
                      status: document.getElementById('mjzRptStatus')?.value || undefined,
                      q: (mjzSearchNo || '').trim() || undefined,
                    })}>📥 دریافت فایل CSV</button>
                  </div>
                  <div style={{ fontSize: 13, color: '#2b6cb0', marginBottom: 8 }}>تعداد رکورد: {toPersianDigits(mjzList.length)}</div>
                  <div style={{ overflowX: 'auto', maxHeight: 360, border: '1px solid #e2e8f0', borderRadius: 8 }}>
                    <table className="data-table">
                      <thead>
                        <tr><th>شماره</th><th>نوع</th><th>نام</th><th>وضعیت</th><th>ورود</th><th>خروج</th><th>صادرکننده</th></tr>
                      </thead>
                      <tbody>
                        {mjzList.length === 0 ? (
                          <tr><td colSpan={7} style={{ textAlign: 'center', color: '#a0aec0' }}>موردی نیست</td></tr>
                        ) : mjzList.slice(0, 100).map((row) => (
                          <tr key={row.id}>
                            <td style={{ fontFamily: 'monospace' }}>{toPersianDigits(row.permit_no)}</td>
                            <td>{MJZ_TYPE_LABEL[row.permit_type] || row.permit_type}</td>
                            <td>{row.holder_name || '—'}</td>
                            <td>{MJZ_STATUS_LABEL[row.status] || row.status}</td>
                            <td style={{ fontSize: 11 }}>{row.entry_at ? toPersianDigits(row.entry_at) : '—'}</td>
                            <td style={{ fontSize: 11 }}>{row.exit_at ? toPersianDigits(row.exit_at) : '—'}</td>
                            <td style={{ fontSize: 11 }}>{row.issued_by || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {mojazSubView === 'list' && (
                <div>
                  {/* نوار جستجوی استاندارد */}
                  <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 14, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: 14 }}>
                    <div style={{ flex: 1, minWidth: 220 }}>
                      <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>جستجو (شماره، نام، کد ملی، پلاک، شرکت)</label>
                      <input
                        value={mjzSearchNo}
                        onChange={(e) => {
                          const v = e.target.value
                          setMjzSearchNo(v)
                        }}
                        onKeyDown={(e) => { if (e.key === 'Enter') searchMjzByNo() }}
                        placeholder="مثال: 14050720_100001 یا نام یا پلاک"
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      />
                    </div>
                    <div style={{ minWidth: 160 }}>
                      <label style={{ display: 'block', fontSize: 12, color: '#4a5568', marginBottom: 4 }}>نام نگهبان</label>
                      <input
                        value={mjzGuardName}
                        onChange={(e) => setMjzGuardName(e.target.value)}
                        placeholder={currentUser?.full_name || currentUser?.username || 'نگهبان'}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      />
                    </div>
                    <button type="button" className="btn-primary" onClick={searchMjzByNo} disabled={mjzLoading}>🔍 جستجو</button>
                    <button type="button" className="btn-primary" style={{ background: '#276749' }} onClick={() => exportMjzCsv()} title="خروجی CSV">📥 CSV</button>
                    <button type="button" className="refresh-btn" onClick={() => { setMjzSearchNo(''); setMjzViewItem(null); loadMjzPermits() }}>پاک کردن فیلتر</button>
                  </div>

                  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 10, fontSize: 12 }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={{ width: 12, height: 12, borderRadius: 3, background: '#fff', border: '1px solid #e2e8f0' }} /> صادر شده</span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={{ width: 12, height: 12, borderRadius: 3, background: '#fefcbf' }} /> ورود ثبت‌شده</span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><span style={{ width: 12, height: 12, borderRadius: 3, background: '#c6f6d5' }} /> خروج ثبت‌شده</span>
                  </div>

                  <div style={{ overflowX: 'auto', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10 }}>
                    {mjzLoading ? <div style={{ padding: 16 }}>در حال بارگذاری...</div> : (
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>شماره</th><th>نوع</th><th>نام</th><th>پلاک</th><th>وضعیت</th><th>صادرکننده</th><th>ورود</th><th>تأخیر ورود</th><th>خروج</th><th>تأخیر خروج</th><th>عملیات</th>
                          </tr>
                        </thead>
                        <tbody>
                          {mjzList.length === 0 ? (
                            <tr><td colSpan={11} style={{ textAlign: 'center', color: '#a0aec0' }}>مجوزی ثبت نشده است</td></tr>
                          ) : mjzList.map((row) => {
                            const hasEntry = !!row.entry_at
                            const hasExit = !!row.exit_at
                            const rowBg = hasExit ? '#f0fff4' : hasEntry ? '#fffff0' : undefined
                            const selected = mjzViewItem && mjzViewItem.id === row.id
                            return (
                              <tr
                                key={row.id}
                                style={{
                                  background: selected ? '#ebf8ff' : rowBg,
                                  cursor: 'pointer',
                                  outline: selected ? '2px solid #3182ce' : undefined,
                                }}
                                onClick={() => { setMjzViewItem(row); setMjzSearchNo(row.permit_no || ''); setMjzMsg('') }}
                              >
                                <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{toPersianDigits(row.permit_no)}</td>
                                <td>{MJZ_TYPE_LABEL[row.permit_type] || row.permit_type}</td>
                                <td>{row.holder_name || '—'}</td>
                                <td dir="ltr">{row.vehicle_plate ? toPersianDigits(row.vehicle_plate) : '—'}</td>
                                <td>
                                  <span className={hasExit ? 'badge-green' : hasEntry ? 'badge-blue' : ''} style={!hasExit && !hasEntry ? { color: '#718096' } : undefined}>
                                    {MJZ_STATUS_LABEL[row.status] || row.status}
                                  </span>
                                </td>
                                <td style={{ fontSize: 11 }}>{row.issued_by || '—'}</td>
                                <td style={{ fontSize: 11 }}>{row.entry_at ? toPersianDigits(row.entry_at) : '—'}</td>
                                <td style={{ fontSize: 11, color: row.entry_delay_minutes > 0 ? '#c53030' : '#4a5568' }}>{row.entry_delay || '—'}</td>
                                <td style={{ fontSize: 11 }}>{row.exit_at ? toPersianDigits(row.exit_at) : '—'}</td>
                                <td style={{ fontSize: 11, color: row.exit_delay_minutes > 0 ? '#c53030' : '#4a5568' }}>{row.exit_delay || '—'}</td>
                                <td>
                                  <button type="button" className="refresh-btn" style={{ fontSize: 11 }} onClick={(e) => { e.stopPropagation(); setMjzViewItem(row); setMjzSearchNo(row.permit_no || ''); setMjzMsg('') }}>نمایش / تأیید</button>
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>

                  {/* کارت جزئیات و تأیید ورود/خروج زیر لیست */}
                  {mjzViewItem && (
                    <div style={{ marginTop: 16, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 20, maxWidth: 800 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderBottom: '1px solid #edf2f7', paddingBottom: 12 }}>
                        <div>
                          <div style={{ fontSize: 12, color: '#718096' }}>شماره مجوز</div>
                          <div style={{ fontSize: 20, fontWeight: 800, letterSpacing: 1, fontFamily: 'monospace' }}>{toPersianDigits(mjzViewItem.permit_no)}</div>
                        </div>
                        <div style={{ textAlign: 'left' }}>
                          <span className="badge-green" style={{ fontSize: 13, padding: '6px 12px' }}>{MJZ_STATUS_LABEL[mjzViewItem.status] || mjzViewItem.status}</span>
                          <div style={{ fontSize: 12, color: '#64748b', marginTop: 6 }}>نوع: {MJZ_TYPE_LABEL[mjzViewItem.permit_type] || mjzViewItem.permit_type}</div>
                          <div style={{ fontSize: 12, color: '#2b6cb0', marginTop: 4, fontWeight: 600 }}>صادرکننده: {mjzViewItem.issued_by || '—'}</div>
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 20px', fontSize: 13 }}>
                        <div><span style={{ color: '#718096' }}>نام:</span> <b>{mjzViewItem.holder_name || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>کد ملی:</span> <b>{mjzViewItem.national_id ? toPersianDigits(mjzViewItem.national_id) : '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>کد پرسنلی:</span> <b>{mjzViewItem.personnel_code || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>شرکت:</span> <b>{mjzViewItem.company_name || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>پلاک:</span> <b dir="ltr" style={{ display: 'inline-block' }}>{mjzViewItem.vehicle_plate ? toPersianDigits(mjzViewItem.vehicle_plate) : '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>راننده:</span> <b>{mjzViewItem.driver_name || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>کالا:</span> <b>{mjzViewItem.goods_desc || '—'}</b>{mjzViewItem.goods_count ? ` — ${mjzViewItem.goods_count}` : ''}</div>
                        <div><span style={{ color: '#718096' }}>دروازه:</span> <b>{mjzViewItem.gate_name || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>مقصد:</span> <b>{mjzViewItem.destination || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>هدف:</span> <b>{mjzViewItem.purpose || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>مجاز ورود:</span> <b>{(mjzViewItem.allowed_entry_date || '') + (mjzViewItem.allowed_entry_time ? ' — ' + mjzViewItem.allowed_entry_time : '') || '—'}</b></div>
                        <div><span style={{ color: '#718096' }}>مجاز خروج:</span> <b>{(mjzViewItem.allowed_exit_date || '') + (mjzViewItem.allowed_exit_time ? ' — ' + mjzViewItem.allowed_exit_time : '') || '—'}</b></div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16, padding: 12, background: '#f7fafc', borderRadius: 8 }}>
                        <div>
                          <div style={{ fontSize: 12, color: '#718096' }}>زمان ورود</div>
                          <div style={{ fontWeight: 700, color: mjzViewItem.entry_at ? '#276749' : '#a0aec0' }}>{mjzViewItem.entry_at ? toPersianDigits(mjzViewItem.entry_at) : 'هنوز ثبت نشده'}</div>
                          {mjzViewItem.entry_by && <div style={{ fontSize: 11, color: '#64748b' }}>توسط: {mjzViewItem.entry_by}</div>}
                          {mjzViewItem.entry_delay && mjzViewItem.entry_delay !== '—' && (
                            <div style={{ fontSize: 12, marginTop: 4, fontWeight: 700, color: (mjzViewItem.entry_delay_minutes > 0) ? '#c53030' : (mjzViewItem.entry_delay_minutes < 0) ? '#2b6cb0' : '#276749' }}>
                              {mjzViewItem.entry_delay}
                            </div>
                          )}
                        </div>
                        <div>
                          <div style={{ fontSize: 12, color: '#718096' }}>زمان خروج</div>
                          <div style={{ fontWeight: 700, color: mjzViewItem.exit_at ? '#276749' : '#a0aec0' }}>{mjzViewItem.exit_at ? toPersianDigits(mjzViewItem.exit_at) : 'هنوز ثبت نشده'}</div>
                          {mjzViewItem.exit_by && <div style={{ fontSize: 11, color: '#64748b' }}>توسط: {mjzViewItem.exit_by}</div>}
                          {mjzViewItem.exit_delay && mjzViewItem.exit_delay !== '—' && (
                            <div style={{ fontSize: 12, marginTop: 4, fontWeight: 700, color: (mjzViewItem.exit_delay_minutes > 0) ? '#c53030' : (mjzViewItem.exit_delay_minutes < 0) ? '#2b6cb0' : '#276749' }}>
                              {mjzViewItem.exit_delay}
                            </div>
                          )}
                        </div>
                      </div>
                      <div style={{ marginTop: 18, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                        <button type="button" className="refresh-btn" onClick={() => setMjzViewItem(null)}>بستن</button>
                        <button type="button" className="btn-primary" style={{ background: mjzViewItem.entry_at ? '#a0aec0' : '#2b6cb0', minWidth: 140 }} disabled={!!mjzViewItem.entry_at} onClick={confirmMjzEntry}>✅ تأیید ورود</button>
                        <button type="button" className="btn-primary" style={{ background: (!mjzViewItem.entry_at || mjzViewItem.exit_at) ? '#a0aec0' : '#c53030', minWidth: 140 }} disabled={!mjzViewItem.entry_at || !!mjzViewItem.exit_at} onClick={confirmMjzExit}>🚪 تأیید خروج</button>
                      </div>
                    </div>
                  )}
                </div>
              )}

            </>

          ) : activeTab === 'peymankar' ? (
            <>
              <div className="workspace-header">
                <h2>
                  {peymankarSubView === 'report'
                    ? (pymReportData?.title || 'گزارش‌گیری پیمانکاران')
                    : (PEYMANKAR_VIEW_MAP[peymankarSubView]?.title || 'پیمانکاران')}
                </h2>
                {peymankarSubView === 'report' && (
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button type="button" className="btn-primary" disabled={pymReportLoading}
                      onClick={() => loadPymReport(pymReportKind, pymReportQ, pymReportCompany)}>
                      {pymReportLoading ? '…' : '🔄 اجرای گزارش'}
                    </button>
                    <button type="button" className="refresh-btn" onClick={() => {
                      const params = new URLSearchParams({ kind: pymReportKind || 'summary' })
                      if (pymReportQ) params.set('q', pymReportQ)
                      if (pymReportCompany) params.set('company_name', pymReportCompany)
                      downloadUrl(`/api/peymankar/report.csv?${params.toString()}`, `peymankar_${pymReportKind || 'summary'}_report.csv`)
                    }}>📥 خروجی CSV</button>
                    <button type="button" className="refresh-btn" onClick={() => window.print()}>🖨️ چاپ</button>
                  </div>
                )}
              </div>
              {peymankarSubView === 'report' ? (
                <div className="card">
                  <div style={{ marginBottom: 12, padding: '10px 12px', background: '#ebf8ff', border: '1px solid #90cdf4', borderRadius: 8, fontSize: 13, color: '#2c5282' }}>
                    گزارش‌گیری یکپارچه از همه آیتم‌های ریبون پیمانکاران: شرکت‌ها، قراردادها، پرسنل، خودروها و راننده‌ها.
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10, marginBottom: 14 }}>
                    <div>
                      <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>نوع گزارش</label>
                      <select
                        value={pymReportKind}
                        onChange={(e) => {
                          const k = e.target.value
                          setPymReportKind(k)
                          loadPymReport(k, pymReportQ, pymReportCompany)
                        }}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      >
                        <option value="summary">خلاصه وضعیت (همه بخش‌ها)</option>
                        <option value="companies">شرکت‌های پیمانکار</option>
                        <option value="contracts">قرارداد شرکت‌های پیمانکار</option>
                        <option value="personnel">پرسنل شرکت‌های پیمانکار</option>
                        <option value="vehicles">خودروهای پیمانکاران</option>
                        <option value="drivers">راننده‌های پیمانکاران</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>فیلتر نام شرکت</label>
                      <input
                        value={pymReportCompany}
                        onChange={(e) => setPymReportCompany(e.target.value)}
                        placeholder="مثال: پیمانکار نمونه"
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: 12, color: '#4a5568', display: 'block', marginBottom: 4 }}>جستجوی متنی</label>
                      <input
                        value={pymReportQ}
                        onChange={(e) => setPymReportQ(e.target.value)}
                        placeholder="کد، نام، پلاک، کدملی…"
                        onKeyDown={(e) => e.key === 'Enter' && loadPymReport(pymReportKind, pymReportQ, pymReportCompany)}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}
                      />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12, alignItems: 'center' }}>
                    <button type="button" className="btn-primary" disabled={pymReportLoading}
                      onClick={() => loadPymReport(pymReportKind, pymReportQ, pymReportCompany)}>
                      📊 نمایش گزارش
                    </button>
                    <button type="button" className="refresh-btn" onClick={() => {
                      setPymReportQ('')
                      setPymReportCompany('')
                      loadPymReport(pymReportKind, '', '')
                    }}>✕ پاک کردن فیلتر</button>
                    {pymReportMsg && <span style={{ fontSize: 13, color: '#4a5568' }}>{pymReportMsg}</span>}
                  </div>
                  {pymReportLoading && <div style={{ padding: 16, color: '#718096' }}>در حال آماده‌سازی گزارش…</div>}
                  {!pymReportLoading && pymReportData && (
                    <>
                      <div style={{ marginBottom: 8, fontSize: 14, fontWeight: 700, color: '#1a365d' }}>
                        {pymReportData.title} — {pymReportData.count ?? 0} ردیف
                      </div>
                      <div style={{ overflow: 'auto', maxHeight: '60vh', border: '1px solid #e2e8f0', borderRadius: 8 }}>
                        <table>
                          <thead>
                            <tr>
                              <th>ردیف</th>
                              {(pymReportData.columns || []).map((c) => (
                                <th key={c}>{c}</th>
                              ))}
                              {pymReportKind === 'summary' && <th>عملیات</th>}
                            </tr>
                          </thead>
                          <tbody>
                            {(pymReportData.rows || []).length === 0 ? (
                              <tr><td colSpan={(pymReportData.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>ردیفی یافت نشد</td></tr>
                            ) : (
                              (pymReportData.rows || []).map((row, i) => (
                                <tr key={i}>
                                  <td>{i + 1}</td>
                                  {(pymReportData.columns || []).map((c) => (
                                    <td key={c}>{row[c] != null && row[c] !== '' ? String(row[c]) : '—'}</td>
                                  ))}
                                  {pymReportKind === 'summary' && (
                                    <td>
                                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                                        onClick={() => {
                                          const k = row['کلید'] || row.key
                                          if (!k) return
                                          setPymReportKind(k)
                                          loadPymReport(k, pymReportQ, pymReportCompany)
                                        }}>
                                        جزئیات
                                      </button>
                                    </td>
                                  )}
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              ) : PEYMANKAR_VIEW_MAP[peymankarSubView] && (() => {
                const meta = PEYMANKAR_VIEW_MAP[peymankarSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {meta?.table && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی:</span>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl(`/api/baseinfo/${meta.table}/template.csv`, `${meta.table}_template.csv`)}>
                        📥 دانلود قالب CSV
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود از CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => {
                            const f = e.target.files?.[0]
                            e.target.value = ''
                            if (!f) return
                            importBaseinfoCsvFile(meta.table, f, (msg) => {
                              setLookupMsg(msg)
                              loadLookup(peymankarSubView || baseSubView || cardSubView, activeTab === 'peymankar' ? 'peymankar' : activeTab === 'baseinfo' ? 'baseinfo' : undefined)
                            })
                          }} />
                      </label>
                      <span style={{ fontSize: 11, color: '#718096' }}>ستون‌های قالب مطابق فیلدهای همین فرم است</span>
                    </div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    const isEdit = !!editingEntityId
                    const url = isEdit
                      ? `/api/baseinfo/${meta.table}/${editingEntityId}`
                      : `/api/baseinfo/${meta.table}`
                    fetch(url, {
                      method: isEdit ? 'PUT' : 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json().catch(() => ({}))
                        if (!r.ok) throw new Error(d.detail || (isEdit ? 'خطا در ویرایش' : 'خطا در ثبت'))
                        setLookupMsg(isEdit ? 'با موفقیت ویرایش شد' : 'با موفقیت ثبت شد')
                        setEntityForm({})
                        setEditingEntityId(null)
                        loadLookup(peymankarSubView, 'peymankar')
                        if (peymankarSubView === 'companies') loadCtrCompanies()
                      })
                      .catch((err) => setLookupMsg(err.message || (isEdit ? 'خطا در ویرایش' : 'خطا در ثبت')))
                  }}>
                    {editingEntityId && (
                      <div style={{
                        marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                        background: '#ebf8ff', color: '#2b6cb0', border: '1px solid #90cdf4',
                      }}>
                        در حال ویرایش رکورد #{editingEntityId} — پس از تغییر، «ذخیره ویرایش» را بزنید
                        <button type="button" className="refresh-btn" style={{ marginRight: 10, fontSize: 12 }}
                          onClick={() => { setEditingEntityId(null); setEntityForm({}); setLookupMsg('') }}>
                          انصراف از ویرایش
                        </button>
                      </div>
                    )}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : f.type === 'bool' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                              <input type="checkbox" checked={!!entityForm[f.key]}
                                onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.checked ? 1 : 0 })} />
                              بله
                            </label>
                          ) : f.type === 'select' ? (
                            <select required={!!f.required} value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">— انتخاب کنید —</option>
                              {(f.options || optionsForField(f.key) || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">
                        {editingEntityId ? '💾 ذخیره ویرایش' : '💾 ثبت'}
                      </button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setEditingEntityId(null); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(peymankarSubView, 'peymankar')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i} style={editingEntityId === item.id ? { background: '#ebf8ff' } : undefined}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] === 0 || item[c] === 1 ? (item[c] ? '✓' : '✗') : (item[c] ?? '—')}</td>)}
                            <td style={{ whiteSpace: 'nowrap' }}>
                              <button type="button" className="refresh-btn" style={{ marginLeft: 4 }} onClick={() => {
                                const formData = {}
                                ;(meta.fields || []).forEach((f) => {
                                  if (item[f.key] !== undefined && item[f.key] !== null) formData[f.key] = item[f.key]
                                })
                                setEntityForm(formData)
                                setEditingEntityId(item.id)
                                setLookupMsg('')
                                window.scrollTo({ top: 0, behavior: 'smooth' })
                              }}>ویرایش</button>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => {
                                    if (!r.ok) throw new Error('خطا')
                                    if (editingEntityId === item.id) {
                                      setEditingEntityId(null)
                                      setEntityForm({})
                                    }
                                    loadLookup(peymankarSubView, 'peymankar')
                                    setLookupMsg('حذف شد')
                                    if (peymankarSubView === 'companies') loadCtrCompanies()
                                  })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'monitoring' ? (
            <>
              <div className="workspace-header">
                <h2>{PATROL_VIEW_MAP[patrolSubView]?.title || 'گشت و پایش'}</h2>
              </div>
              {PATROL_VIEW_MAP[patrolSubView] && (() => {
                const meta = PATROL_VIEW_MAP[patrolSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {meta?.table && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی:</span>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl(`/api/baseinfo/${meta.table}/template.csv`, `${meta.table}_template.csv`)}>
                        📥 دانلود قالب CSV
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود از CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => {
                            const f = e.target.files?.[0]
                            e.target.value = ''
                            if (!f) return
                            importBaseinfoCsvFile(meta.table, f, (msg) => {
                              setLookupMsg(msg)
                              loadLookup(peymankarSubView || baseSubView || cardSubView, activeTab === 'peymankar' ? 'peymankar' : activeTab === 'baseinfo' ? 'baseinfo' : undefined)
                            })
                          }} />
                      </label>
                      <span style={{ fontSize: 11, color: '#718096' }}>ستون‌های قالب مطابق فیلدهای همین فرم است</span>
                    </div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(patrolSubView, 'patrol')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : f.type === 'bool' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                              <input type="checkbox" checked={!!entityForm[f.key]}
                                onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.checked ? 1 : 0 })} />
                              بله
                            </label>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(patrolSubView, 'patrol')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] === 0 || item[c] === 1 ? (item[c] ? '✓' : '✗') : (item[c] ?? '—')}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(patrolSubView, 'patrol'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'herasat' ? (
            <>
              <div className="workspace-header">
                <h2>{HERASAT_VIEW_MAP[herasatSubView]?.title || 'حراست'}</h2>
              </div>
              {HERASAT_VIEW_MAP[herasatSubView] && (() => {
                const meta = HERASAT_VIEW_MAP[herasatSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {meta?.table && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی:</span>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl(`/api/baseinfo/${meta.table}/template.csv`, `${meta.table}_template.csv`)}>
                        📥 دانلود قالب CSV
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود از CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => {
                            const f = e.target.files?.[0]
                            e.target.value = ''
                            if (!f) return
                            importBaseinfoCsvFile(meta.table, f, (msg) => {
                              setLookupMsg(msg)
                              loadLookup(peymankarSubView || baseSubView || cardSubView, activeTab === 'peymankar' ? 'peymankar' : activeTab === 'baseinfo' ? 'baseinfo' : undefined)
                            })
                          }} />
                      </label>
                      <span style={{ fontSize: 11, color: '#718096' }}>ستون‌های قالب مطابق فیلدهای همین فرم است</span>
                    </div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(herasatSubView, 'herasat')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput
                              required={!!f.required}
                              value={entityForm[f.key] || ''}
                              onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })}
                            />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : f.type === 'bool' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                              <input type="checkbox" checked={!!entityForm[f.key]}
                                onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.checked ? 1 : 0 })} />
                              بله
                            </label>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(herasatSubView, 'herasat')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] === 0 || item[c] === 1 ? (item[c] ? '✓' : '✗') : (item[c] ?? '—')}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(herasatSubView, 'herasat'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'monaghese' ? (
            <>
              <div className="workspace-header">
                <h2>{MONAGHESE_VIEW_MAP[monagheseSubView]?.title || 'مناقصات و مزایدات'}</h2>
              </div>
              {MONAGHESE_VIEW_MAP[monagheseSubView] && (() => {
                const meta = MONAGHESE_VIEW_MAP[monagheseSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {meta?.table && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی:</span>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl(`/api/baseinfo/${meta.table}/template.csv`, `${meta.table}_template.csv`)}>
                        📥 دانلود قالب CSV
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود از CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => {
                            const f = e.target.files?.[0]
                            e.target.value = ''
                            if (!f) return
                            importBaseinfoCsvFile(meta.table, f, (msg) => {
                              setLookupMsg(msg)
                              loadLookup(peymankarSubView || baseSubView || cardSubView, activeTab === 'peymankar' ? 'peymankar' : activeTab === 'baseinfo' ? 'baseinfo' : undefined)
                            })
                          }} />
                      </label>
                      <span style={{ fontSize: 11, color: '#718096' }}>ستون‌های قالب مطابق فیلدهای همین فرم است</span>
                    </div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(monagheseSubView, 'monaghese')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(monagheseSubView, 'monaghese')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] ?? '—'}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(monagheseSubView, 'monaghese'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'kartabl' ? (
            <>
              <div className="workspace-header">
                <h2>{KARTABL_VIEW_MAP[kartablSubView]?.title || 'کارتابل'}</h2>
              </div>
              {KARTABL_VIEW_MAP[kartablSubView] && (() => {
                const meta = KARTABL_VIEW_MAP[kartablSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') || lookupMsg.includes('ورود CSV') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  {meta?.table && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12, padding: '8px 10px', background: '#f7fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: 12, color: '#4a5568' }}>ورود گروهی:</span>
                      <button type="button" className="refresh-btn" style={{ fontSize: 12 }}
                        onClick={() => downloadUrl(`/api/baseinfo/${meta.table}/template.csv`, `${meta.table}_template.csv`)}>
                        📥 دانلود قالب CSV
                      </button>
                      <label className="btn-primary" style={{ fontSize: 12, padding: '6px 12px', cursor: 'pointer', margin: 0 }}>
                        📤 ورود از CSV
                        <input type="file" accept=".csv,text/csv" style={{ display: 'none' }}
                          onChange={(e) => {
                            const f = e.target.files?.[0]
                            e.target.value = ''
                            if (!f) return
                            importBaseinfoCsvFile(meta.table, f, (msg) => {
                              setLookupMsg(msg)
                              loadLookup(peymankarSubView || baseSubView || cardSubView, activeTab === 'peymankar' ? 'peymankar' : activeTab === 'baseinfo' ? 'baseinfo' : undefined)
                            })
                          }} />
                      </label>
                      <span style={{ fontSize: 11, color: '#718096' }}>ستون‌های قالب مطابق فیلدهای همین فرم است</span>
                    </div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    const payload = { ...entityForm }
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(kartablSubView, 'kartabl')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={f.key === 'letter_body' ? { gridColumn: '1 / -1' } : undefined}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : f.key === 'letter_body' ? (
                            <textarea value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              rows={4} style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          ) : (
                            <input required={!!f.required} placeholder={f.placeholder || ''} value={entityForm[f.key] || ''}
                              onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(kartablSubView, 'kartabl')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] ?? '—'}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(kartablSubView, 'kartabl'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'baskool' ? (
            <>
              <div className="workspace-header">
                <h2>{BASKOOL_VIEW_MAP[baskoolSubView]?.title || 'باسکول'}</h2>
              </div>
              {BASKOOL_VIEW_MAP[baskoolSubView] && (() => {
                const meta = BASKOOL_VIEW_MAP[baskoolSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ ...entityForm }),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(baskoolSubView, 'baskool')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : f.type === 'bool' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                              <input type="checkbox" checked={!!entityForm[f.key]} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.checked ? 1 : 0 })} /> بله
                            </label>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(baskoolSubView, 'baskool')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] === 0 || item[c] === 1 ? (item[c] ? '✓' : '✗') : (item[c] ?? '—')}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(baskoolSubView, 'baskool'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'pelakhwan' ? (
            <>
              <div className="workspace-header">
                <h2>{PELAKHWAN_VIEW_MAP[pelakhwanSubView]?.title || 'پلاک‌خوان'}</h2>
              </div>
              {PELAKHWAN_VIEW_MAP[pelakhwanSubView] && (() => {
                const meta = PELAKHWAN_VIEW_MAP[pelakhwanSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ ...entityForm }),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(pelakhwanSubView, 'pelakhwan')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : undefined}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : f.type === 'bool' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                              <input type="checkbox" checked={!!entityForm[f.key]} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.checked ? 1 : 0 })} /> بله
                            </label>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(pelakhwanSubView, 'pelakhwan')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] === 0 || item[c] === 1 ? (item[c] ? '✓' : '✗') : (item[c] ?? '—')}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(pelakhwanSubView, 'pelakhwan'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'access' ? (
            <>
              <div className="workspace-header">
                <h2>{ACCESS_VIEW_MAP[accessSubView]?.title || 'کنترل دسترسی'}</h2>
              </div>
              {ACCESS_VIEW_MAP[accessSubView] && (() => {
                const meta = ACCESS_VIEW_MAP[accessSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ ...entityForm }),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(accessSubView, 'access')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key} style={(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? { gridColumn: '1 / -1' } : (isDateFieldKey(f.key, f.type, f.label) ? { minWidth: 130, maxWidth: 160 } : undefined)}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {(f.type === 'iran_plate' || f.key === 'plate_number' || f.key === 'vehicle_plate' || f.key === 'last_read_plate' || f.key === 'live_plate') ? (
                            <IranPlateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isDateFieldKey(f.key, f.type, f.label) ? (
                            <JalaliDateInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : isTimeFieldKey(f.key, f.type) ? (
                            <JalaliTimeInput required={!!f.required} value={entityForm[f.key] || ''} onChange={(v) => setEntityForm({ ...entityForm, [f.key]: v })} />
                          ) : f.type === 'bool' ? (
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                              <input type="checkbox" checked={!!entityForm[f.key]} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.checked ? 1 : 0 })} /> بله
                            </label>
                          ) : f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(accessSubView, 'access')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] === 0 || item[c] === 1 ? (item[c] ? '✓' : '✗') : (item[c] ?? '—')}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(accessSubView, 'access'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'workflow' ? (
            <>
              <div className="workspace-header">
                <h2>{WORKFLOW_VIEW_MAP[workflowSubView]?.title || 'جریان کار'}</h2>
              </div>
              {WORKFLOW_VIEW_MAP[workflowSubView] && (() => {
                const meta = WORKFLOW_VIEW_MAP[workflowSubView]
                const labelOf = (key) => (meta.fields.find((f) => f.key === key)?.label || key)
                return (
                <div className="card">
                  {lookupMsg && (
                    <div style={{
                      marginBottom: 10, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                      background: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                      color: lookupMsg.includes('موفق') || lookupMsg.includes('شد') ? '#276749' : '#c53030',
                    }}>{lookupMsg}</div>
                  )}
                  <form onSubmit={(e) => {
                    e.preventDefault()
                    fetch(`/api/baseinfo/${meta.table}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ ...entityForm }),
                    })
                      .then(async (r) => {
                        const d = await r.json()
                        if (!r.ok) throw new Error(d.detail || 'خطا')
                        setLookupMsg('با موفقیت ثبت شد')
                        setEntityForm({})
                        loadLookup(workflowSubView, 'workflow')
                      })
                      .catch((err) => setLookupMsg(err.message || 'خطا در ثبت'))
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 12 }}>
                      {meta.fields.map((f) => (
                        <div key={f.key}>
                          <label style={{ fontSize: 12, color: f.required ? '#c53030' : '#4a5568', display: 'block', marginBottom: 3 }}>
                            {f.label}{f.required ? ' *' : ''}
                          </label>
                          {f.type === 'select' ? (
                            <select value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }}>
                              <option value="">—</option>
                              {(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                            </select>
                          ) : (
                            <input required={!!f.required} value={entityForm[f.key] || ''} onChange={(e) => setEntityForm({ ...entityForm, [f.key]: e.target.value })}
                              style={{ width: '100%', padding: '7px 9px', border: '1px solid #e2e8f0', borderRadius: 6, fontFamily: 'inherit', fontSize: 13 }} />
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="submit" className="btn-primary">💾 ثبت</button>
                      <button type="button" className="refresh-btn" onClick={() => { setEntityForm({}); setLookupMsg('') }}>پاک کردن</button>
                      <button type="button" className="refresh-btn" onClick={() => loadLookup(workflowSubView, 'workflow')}>🔄 به‌روزرسانی</button>
                    </div>
                  </form>
                  <div style={{ marginTop: 16, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ردیف</th>
                          {(meta.columns || []).map((c) => <th key={c}>{labelOf(c)}</th>)}
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lookupItems.length === 0 ? (
                          <tr><td colSpan={(meta.columns || []).length + 2} style={{ textAlign: 'center', color: '#718096' }}>نتیجه‌ای یافت نشد</td></tr>
                        ) : lookupItems.map((item, i) => (
                          <tr key={item.id || i}>
                            <td>{i + 1}</td>
                            {(meta.columns || []).map((c) => <td key={c}>{item[c] ?? '—'}</td>)}
                            <td>
                              <button type="button" className="refresh-btn" onClick={() => {
                                if (!window.confirm('حذف شود؟')) return
                                fetch(`/api/baseinfo/${meta.table}/${item.id}`, { method: 'DELETE' })
                                  .then((r) => { if (!r.ok) throw new Error('خطا'); loadLookup(workflowSubView, 'workflow'); setLookupMsg('حذف شد') })
                                  .catch((err) => setLookupMsg(err.message || 'خطا'))
                              }}>حذف</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                )
              })()}
            </>
          ) : activeTab === 'modiriat' && workflowSubView === 'access_levels' ? (
            <>
              <div className="workspace-header">
                <h2>تعریف سطح دسترسی</h2>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" className="btn-primary" onClick={() => {
                    resetLevelForm()
                    setShowLevelForm(true)
                  }}>+ سطح دسترسی جدید</button>
                  <button type="button" className="refresh-btn" onClick={loadAccessLevels}>🔄 به‌روزرسانی</button>
                </div>
              </div>
              {accessLevelMsg && (
                <div style={{
                  marginBottom: 12, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                  background: accessLevelMsg.includes('خطا') || accessLevelMsg.includes('الزامی') || accessLevelMsg.includes('تکراری') || accessLevelMsg.includes('نیست') ? '#fed7d7' : '#c6f6d5',
                  color: accessLevelMsg.includes('خطا') || accessLevelMsg.includes('الزامی') || accessLevelMsg.includes('تکراری') || accessLevelMsg.includes('نیست') ? '#c53030' : '#276749',
                }}>{accessLevelMsg}</div>
              )}
              {showLevelForm && (
                <div className="card" style={{ marginBottom: 16 }}>
                  <h3 style={{ marginTop: 0 }}>{editingLevelId ? 'ویرایش سطح دسترسی' : 'سطح دسترسی جدید'}</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                      نام سطح دسترسی *
                      <input value={levelForm.name} onChange={(e) => setLevelForm({ ...levelForm, name: e.target.value })} placeholder="مثال: اپراتور حراست" />
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                      توضیحات
                      <input value={levelForm.description} onChange={(e) => setLevelForm({ ...levelForm, description: e.target.value })} placeholder="توضیح اختیاری" />
                    </label>
                  </div>
                  <div style={{ display: 'flex', gap: 20, marginBottom: 14, flexWrap: 'wrap' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
                      <input type="checkbox" checked={!!levelForm.is_full_admin} onChange={(e) => setLevelForm({ ...levelForm, is_full_admin: e.target.checked })} />
                      دسترسی کامل (مدیر سیستم — همه برگه‌ها و گزینه‌ها)
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
                      <input type="checkbox" checked={!!levelForm.is_active} onChange={(e) => setLevelForm({ ...levelForm, is_active: e.target.checked })} />
                      فعال
                    </label>
                  </div>
                  {!levelForm.is_full_admin && (
                    <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 12, background: '#f7fafc' }}>
                      <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 13 }}>برگه‌ها و گزینه‌های ریبون مجاز</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 420, overflowY: 'auto' }}>
                        {TABS.map((tab) => {
                          const tabOn = levelForm.tabs.includes(tab.id)
                          const tabActions = RIBBON_CATALOG.filter((a) => a.tab === tab.id)
                          return (
                            <div key={tab.id} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6, padding: 10 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, fontSize: 13, cursor: 'pointer' }}>
                                  <input type="checkbox" checked={tabOn} onChange={() => toggleLevelTab(tab.id)} />
                                  {tab.label}
                                </label>
                                {tabOn && tabActions.length > 0 && (
                                  <>
                                    <button type="button" className="refresh-btn" style={{ fontSize: 11, padding: '2px 8px' }} onClick={() => selectAllActionsForTab(tab.id)}>همه گزینه‌ها</button>
                                    <button type="button" className="refresh-btn" style={{ fontSize: 11, padding: '2px 8px' }} onClick={() => clearActionsForTab(tab.id)}>پاک کردن گزینه‌ها</button>
                                    <span style={{ fontSize: 11, color: '#718096' }}>
                                      {levelForm.actions.filter((c) => ACTION_BY_CODE[c]?.tab === tab.id).length} / {tabActions.length} گزینه
                                    </span>
                                  </>
                                )}
                              </div>
                              {tabOn && tabActions.length > 0 && (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 6, marginTop: 8 }}>
                                  {tabActions.map((act) => (
                                    <label key={act.code} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, cursor: 'pointer' }}>
                                      <input
                                        type="checkbox"
                                        checked={levelForm.actions.includes(act.code)}
                                        onChange={() => toggleLevelAction(act.code)}
                                      />
                                      <span>{act.icon ? `${act.icon} ` : ''}{act.label}</span>
                                    </label>
                                  ))}
                                </div>
                              )}
                              {tabOn && tabActions.length === 0 && (
                                <div style={{ fontSize: 12, color: '#a0aec0', marginTop: 6 }}>این برگه گزینه ریبون جداگانه ندارد (خود برگه مجاز است).</div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                    <button type="button" className="btn-primary" onClick={saveAccessLevel}>💾 ذخیره</button>
                    <button type="button" className="refresh-btn" onClick={resetLevelForm}>انصراف</button>
                  </div>
                </div>
              )}
              <div className="card">
                <div style={{ overflowX: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>ردیف</th>
                        <th>نام</th>
                        <th>توضیحات</th>
                        <th>نوع</th>
                        <th>برگه‌ها</th>
                        <th>گزینه‌ها</th>
                        <th>کاربران</th>
                        <th>وضعیت</th>
                        <th>عملیات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accessLevels.length === 0 ? (
                        <tr><td colSpan={9} style={{ textAlign: 'center', color: '#718096' }}>سطحی تعریف نشده</td></tr>
                      ) : accessLevels.map((lv, i) => (
                        <tr key={lv.id}>
                          <td>{i + 1}</td>
                          <td style={{ fontWeight: 600 }}>{lv.name}</td>
                          <td style={{ fontSize: 12, color: '#4a5568' }}>{lv.description || '—'}</td>
                          <td>{lv.is_full_admin ? <span className="badge-blue">مدیر کامل</span> : <span className="badge-green">محدود</span>}</td>
                          <td>{lv.is_full_admin ? 'همه' : (lv.tabs?.length || 0)}</td>
                          <td>{lv.is_full_admin ? 'همه' : (lv.actions?.length || 0)}</td>
                          <td>{lv.user_count ?? 0}</td>
                          <td>{lv.is_active ? 'فعال' : 'غیرفعال'}</td>
                          <td style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            <button type="button" className="refresh-btn" onClick={() => openLevelEdit(lv)}>✏️ ویرایش</button>
                            <button type="button" className="refresh-btn" style={{ color: '#c53030' }} onClick={() => deleteAccessLevel(lv.id, lv.name)}>🗑️ حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : activeTab === 'modiriat' && workflowSubView === 'sys_users' ? (
            <>
              <div className="workspace-header">
                <h2>تعریف کاربران و اختصاص سطح دسترسی</h2>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" className="btn-primary" onClick={() => {
                    resetUserForm()
                    setShowUserForm(true)
                    loadAccessLevels()
                  }}>+ کاربر جدید</button>
                  <button type="button" className="refresh-btn" onClick={() => { loadSysUsers(); loadAccessLevels() }}>🔄 به‌روزرسانی</button>
                </div>
              </div>
              {sysUserMsg && (
                <div style={{
                  marginBottom: 12, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                  background: sysUserMsg.includes('خطا') || sysUserMsg.includes('الزامی') || sysUserMsg.includes('تکراری') || sysUserMsg.includes('نیست') ? '#fed7d7' : '#c6f6d5',
                  color: sysUserMsg.includes('خطا') || sysUserMsg.includes('الزامی') || sysUserMsg.includes('تکراری') || sysUserMsg.includes('نیست') ? '#c53030' : '#276749',
                }}>{sysUserMsg}</div>
              )}
              {showUserForm && (
                <div className="card" style={{ marginBottom: 16 }}>
                  <h3 style={{ marginTop: 0 }}>{editingUserId ? 'ویرایش کاربر' : 'کاربر جدید'}</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                      نام کاربری *
                      <input value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} disabled={userForm.username === 'admin' && !!editingUserId} />
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                      رمز عبور {editingUserId ? '(خالی = بدون تغییر)' : '*'}
                      <input type="password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} placeholder={editingUserId ? '••••••' : ''} />
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                      نام کامل
                      <input value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} />
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                      سطح دسترسی
                      <select value={userForm.access_level_id} onChange={(e) => setUserForm({ ...userForm, access_level_id: e.target.value })}>
                        <option value="">— بدون سطح —</option>
                        {accessLevels.filter((l) => l.is_active !== false).map((l) => (
                          <option key={l.id} value={l.id}>{l.name}{l.is_full_admin ? ' (مدیر کامل)' : ''}</option>
                        ))}
                      </select>
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                      کد شرکت
                      <select value={userForm.company_code} onChange={(e) => setUserForm({ ...userForm, company_code: e.target.value })}>
                        {(companies.length ? companies : [{ code: 100, name: 'ستاد' }]).map((c) => (
                          <option key={c.code} value={String(c.code)}>{c.code} — {c.short_name || c.name}</option>
                        ))}
                      </select>
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, justifyContent: 'flex-end' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
                        <input type="checkbox" checked={!!userForm.is_active} onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })} />
                        فعال
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
                        <input type="checkbox" checked={!!userForm.can_see_all_companies} onChange={(e) => setUserForm({ ...userForm, can_see_all_companies: e.target.checked })} />
                        مشاهده همه شرکت‌ها
                      </label>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button type="button" className="btn-primary" onClick={saveSysUser}>💾 ذخیره</button>
                    <button type="button" className="refresh-btn" onClick={resetUserForm}>انصراف</button>
                  </div>
                </div>
              )}
              <div className="card">
                <div style={{ overflowX: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>ردیف</th>
                        <th>نام کاربری</th>
                        <th>نام کامل</th>
                        <th>سطح دسترسی</th>
                        <th>شرکت</th>
                        <th>همه شرکت‌ها</th>
                        <th>وضعیت</th>
                        <th>عملیات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sysUsers.length === 0 ? (
                        <tr><td colSpan={8} style={{ textAlign: 'center', color: '#718096' }}>کاربری تعریف نشده</td></tr>
                      ) : sysUsers.map((u, i) => (
                        <tr key={u.id}>
                          <td>{i + 1}</td>
                          <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>{u.username}</td>
                          <td>{u.full_name || '—'}</td>
                          <td>
                            {u.access_level_name
                              ? <span>{u.access_level_name}{u.is_full_admin ? ' 🔑' : ''}</span>
                              : <span style={{ color: '#a0aec0' }}>بدون سطح</span>}
                          </td>
                          <td>{u.company_code || '—'}</td>
                          <td>{u.can_see_all_companies ? 'بله' : 'خیر'}</td>
                          <td>{u.is_active ? 'فعال' : 'غیرفعال'}</td>
                          <td style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            <button type="button" className="refresh-btn" onClick={() => openUserEdit(u)}>✏️ ویرایش</button>
                            {u.username !== 'admin' && (
                              <button type="button" className="refresh-btn" style={{ color: '#c53030' }} onClick={() => deleteSysUser(u.id, u.username)}>🗑️ حذف</button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : activeTab === 'modiriat' && (workflowSubView === 'backup' || workflowSubView === 'restore') ? (
            <>
              <div className="workspace-header">
                <h2>{workflowSubView === 'backup' ? 'گرفتن نسخه پشتیبان' : 'بازیابی نسخه پشتیبان'}</h2>
                <button className="refresh-btn" onClick={refreshBackupList}>🔄 به‌روزرسانی لیست</button>
              </div>
              <div className="card">
                {backupMsg && (
                  <div style={{
                    marginBottom: 12, padding: '8px 12px', borderRadius: 6, fontSize: 13,
                    background: backupMsg.includes('موفق') || backupMsg.includes('شد') ? '#c6f6d5' : '#fed7d7',
                    color: backupMsg.includes('موفق') || backupMsg.includes('شد') ? '#276749' : '#c53030',
                  }}>{backupMsg}</div>
                )}
                {workflowSubView === 'backup' && (
                  <div style={{ marginBottom: 16 }}>
                    <p style={{ fontSize: 13, color: '#4a5568', marginBottom: 10 }}>
                      از کل پایگاه‌داده <code>co_db.db</code> یک نسخه پشتیبان در سرور ایجاد می‌شود. می‌توانید آن را دانلود کنید.
                    </p>
                    <button type="button" className="btn-primary" onClick={() => {
                      setBackupMsg('در حال ایجاد...')
                      fetch('/api/admin/backup', { method: 'POST' })
                        .then(async (r) => {
                          const d = await r.json()
                          if (!r.ok) throw new Error(d.detail || 'خطا')
                          setBackupMsg(d.message || 'نسخه پشتیبان ایجاد شد')
                          refreshBackupList()
                        })
                        .catch((err) => setBackupMsg(err.message || 'خطا'))
                    }}>💾 ایجاد نسخه پشتیبان جدید</button>
                  </div>
                )}
                {workflowSubView === 'restore' && (
                  <div style={{ marginBottom: 16 }}>
                    <p style={{ fontSize: 13, color: '#4a5568', marginBottom: 10 }}>
                      بازیابی از فایل موجود در سرور یا آپلود فایل <code>.db</code>. قبل از بازیابی یک نسخه خودکار ذخیره می‌شود.
                    </p>
                    <label className="btn-primary" style={{ display: 'inline-block', cursor: 'pointer' }}>
                      📤 آپلود و بازیابی فایل
                      <input type="file" accept=".db,.sqlite" style={{ display: 'none' }} onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (!f) return
                        if (!window.confirm('دیتابیس فعلی جایگزین می‌شود. ادامه؟')) return
                        const fd = new FormData()
                        fd.append('file', f)
                        setBackupMsg('در حال بازیابی...')
                        fetch('/api/admin/restore-upload', { method: 'POST', body: fd })
                          .then(async (r) => {
                            const d = await r.json()
                            if (!r.ok) throw new Error(d.detail || 'خطا')
                            setBackupMsg(d.message || 'بازیابی انجام شد')
                            refreshBackupList()
                          })
                          .catch((err) => setBackupMsg(err.message || 'خطا'))
                        e.target.value = ''
                      }} />
                    </label>
                  </div>
                )}
                <div style={{ overflowX: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>ردیف</th>
                        <th>نام فایل</th>
                        <th>حجم</th>
                        <th>تاریخ</th>
                        <th>عملیات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {backupList.length === 0 ? (
                        <tr><td colSpan={5} style={{ textAlign: 'center', color: '#718096' }}>نسخه پشتیبانی موجود نیست</td></tr>
                      ) : backupList.map((b, i) => (
                        <tr key={b.name}>
                          <td>{i + 1}</td>
                          <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{b.name}</td>
                          <td>{(b.size / 1024).toFixed(1)} KB</td>
                          <td>{b.modified ? new Date(b.modified * 1000).toLocaleString('fa-IR') : '—'}</td>
                          <td style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            <a className="refresh-btn" href={`/api/admin/backup/download/${encodeURIComponent(b.name)}`} download>⬇️ دانلود</a>
                            {workflowSubView === 'restore' && (
                              <button type="button" className="btn-primary" onClick={() => {
                                if (!window.confirm(`بازیابی از ${b.name}؟`)) return
                                setBackupMsg('در حال بازیابی...')
                                fetch(`/api/admin/restore?name=${encodeURIComponent(b.name)}`, { method: 'POST' })
                                  .then(async (r) => {
                                    const d = await r.json()
                                    if (!r.ok) throw new Error(d.detail || 'خطا')
                                    setBackupMsg(d.message || 'بازیابی انجام شد')
                                    refreshBackupList()
                                  })
                                  .catch((err) => setBackupMsg(err.message || 'خطا'))
                              }}>♻️ بازیابی</button>
                            )}
                            <button type="button" className="refresh-btn" onClick={() => {
                              if (!window.confirm('حذف این نسخه؟')) return
                              fetch(`/api/admin/backup/${encodeURIComponent(b.name)}`, { method: 'DELETE' })
                                .then(async (r) => {
                                  const d = await r.json()
                                  if (!r.ok) throw new Error(d.detail || 'خطا')
                                  setBackupMsg('حذف شد')
                                  refreshBackupList()
                                })
                                .catch((err) => setBackupMsg(err.message || 'خطا'))
                            }}>حذف</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="workspace-header">
                <h2>داشبورد حراست — امروز ۱۴۰۴/۰۷/۰۹</h2>
                <button className="refresh-btn">🔄 به‌روزرسانی</button>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="value" style={{ color: '#e53e3e' }}>
                    {stats.violations_today}
                  </div>
                  <div className="label">تخلف امروز</div>
                </div>
                <div className="stat-card">
                  <div className="value" style={{ color: '#dd6b20' }}>
                    {stats.open_incidents}
                  </div>
                  <div className="label">حادثه باز</div>
                </div>
                <div className="stat-card">
                  <div className="value" style={{ color: '#2b6cb0' }}>
                    {stats.inspections_done}
                  </div>
                  <div className="label">بازدید انجام‌شده</div>
                </div>
                <div className="stat-card">
                  <div className="value" style={{ color: '#38a169' }}>
                    {stats.guest_visits}
                  </div>
                  <div className="label">تردد میهمان</div>
                </div>
              </div>

              <div className="card">
                <h3>آخرین تخلفات ثبت‌شده</h3>
                {violations.length === 0 ? (
                  <div style={{ padding: '24px 8px', textAlign: 'center', color: '#718096', fontSize: 14 }}>
                    فعلاً اطلاعاتی برای نمایش وجود ندارد.
                  </div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>کد</th>
                        <th>نام پرسنل / پیمانکار</th>
                        <th>نوع تخلف</th>
                        <th>تاریخ</th>
                        <th>وضعیت</th>
                        <th>جریمه</th>
                      </tr>
                    </thead>
                    <tbody>
                      {violations.map((v) => (
                        <tr key={v.code}>
                          <td>{v.code}</td>
                          <td>{v.name}</td>
                          <td>{v.type}</td>
                          <td>{v.date}</td>
                          <td>
                            <span
                              className={`badge ${STATUS_COLORS[v.status_color] || 'badge-blue'}`}
                            >
                              {v.status}
                            </span>
                          </td>
                          <td>{v.fine}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* مودال پیوست فایل */}
      {showAttachModal && selectedPersonnel && (
        <div className="modal-overlay" onClick={() => !attachBusy && setShowAttachModal(false)}>
          <div
            className="modal-box"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: 640 }}
          >
            <div className="modal-header">
              <h3>پیوست فایل / انتقال مدارک</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => !attachBusy && setShowAttachModal(false)}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: 12, fontSize: 13, color: '#4a5568' }}>
              پرسنل:{' '}
              <strong>
                {selectedPersonnel.first_name} {selectedPersonnel.last_name}
              </strong>
              {' — '}
              کدملی: {selectedPersonnel.national_id || '—'}
              {selectedPersonnel.company ? ` — ${selectedPersonnel.company}` : ''}
            </div>

            {!attachMode && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <p style={{ fontSize: 13, color: '#4a5568', margin: 0 }}>
                  یکی از گزینه‌ها را انتخاب کنید:
                </p>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ padding: '12px 16px', textAlign: 'right' }}
                  onClick={() => {
                    setAttachMode('folder')
                    setAttachMsg('')
                    loadAttachDestBrowser(attachDestPath || '', '')
                  }}
                >
                  <div style={{ fontWeight: 600 }}>انتقال فولدر مدارک پرسنل</div>
                  <div style={{ fontSize: 11, opacity: 0.9, marginTop: 4 }}>
                    مبدأ: فولدر از کامپیوتر (مثلاً کل فولدرهای یک شرکت) — مقصد: مسیر قابل انتخاب با جستجو
                  </div>
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ padding: '12px 16px', textAlign: 'right' }}
                  onClick={() => {
                    setAttachMode('files')
                    setAttachMsg('')
                  }}
                >
                  <div style={{ fontWeight: 600 }}>انتقال فایل‌های مدارک پرسنل</div>
                  <div style={{ fontSize: 11, opacity: 0.85, marginTop: 4 }}>
                    مقصد: فولدر پرسنل انتخاب‌شده — انتخاب فایل از کامپیوتر
                  </div>
                </button>
              </div>
            )}

            {attachMode === 'folder' && (
              <div>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ fontSize: 12, marginBottom: 10 }}
                  onClick={() => setAttachMode(null)}
                >
                  ← بازگشت به گزینه‌ها
                </button>
                <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 8 }}>
                  <strong>مقصد انتقال:</strong>{' '}
                  <span style={{ direction: 'ltr', display: 'inline-block' }}>
                    {attachDestRoot || '…'}
                    {attachDestPath ? ` / ${attachDestPath}` : ' / (ریشه)'}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                  <input
                    type="text"
                    value={attachDestSearch}
                    onChange={(e) => setAttachDestSearch(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') loadAttachDestBrowser(attachDestPath, attachDestSearch)
                    }}
                    placeholder="جستجوی پوشه مقصد..."
                    style={{
                      flex: '1 1 160px',
                      padding: '6px 10px',
                      border: '1px solid #cbd5e0',
                      borderRadius: 6,
                      fontFamily: 'inherit',
                      fontSize: 12,
                    }}
                  />
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ fontSize: 12 }}
                    onClick={() => loadAttachDestBrowser(attachDestPath, attachDestSearch)}
                  >
                    جستجو
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ fontSize: 12 }}
                    disabled={!attachDestPath}
                    onClick={() => {
                      const parts = attachDestPath.split('/').filter(Boolean)
                      parts.pop()
                      loadAttachDestBrowser(parts.join('/'), '')
                    }}
                  >
                    یک سطح بالاتر
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ fontSize: 12 }}
                    onClick={() => loadAttachDestBrowser('', '')}
                  >
                    ریشه
                  </button>
                </div>
                <div
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: 6,
                    maxHeight: 180,
                    overflow: 'auto',
                    marginBottom: 12,
                    background: '#f7fafc',
                  }}
                >
                  {attachDestLoading ? (
                    <div style={{ padding: 12, fontSize: 12, color: '#718096' }}>در حال بارگذاری...</div>
                  ) : attachDestItems.length === 0 ? (
                    <div style={{ padding: 12, fontSize: 12, color: '#718096' }}>
                      پوشه‌ای در این مسیر نیست — می‌توانید همین مسیر را به‌عنوان مقصد استفاده کنید.
                    </div>
                  ) : (
                    attachDestItems.map((it) => (
                      <button
                        key={it.relative_path}
                        type="button"
                        onClick={() => loadAttachDestBrowser(it.relative_path, '')}
                        style={{
                          display: 'block',
                          width: '100%',
                          textAlign: 'right',
                          padding: '8px 12px',
                          border: 'none',
                          borderBottom: '1px solid #edf2f7',
                          background: 'transparent',
                          cursor: 'pointer',
                          fontFamily: 'inherit',
                          fontSize: 13,
                        }}
                      >
                        📁 {it.name}
                      </button>
                    ))
                  )}
                </div>
                <input
                  ref={attachFolderRef}
                  type="file"
                  // @ts-ignore
                  webkitdirectory=""
                  directory=""
                  multiple
                  style={{ display: 'none' }}
                  onChange={(e) => uploadAttachFolderTree(e.target.files)}
                />
                <button
                  type="button"
                  className="btn-primary"
                  disabled={attachBusy}
                  onClick={() => attachFolderRef.current?.click()}
                  style={{ width: '100%' }}
                >
                  {attachBusy ? 'در حال انتقال...' : 'انتخاب فولدر از کامپیوتر و انتقال به مقصد'}
                </button>
                {attachSourceInfo && (
                  <div style={{ fontSize: 12, color: '#718096', marginTop: 8 }}>{attachSourceInfo}</div>
                )}
              </div>
            )}

            {attachMode === 'files' && (
              <div>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ fontSize: 12, marginBottom: 10 }}
                  onClick={() => setAttachMode(null)}
                >
                  ← بازگشت به گزینه‌ها
                </button>
                <div style={{ fontSize: 13, marginBottom: 10, color: '#2d3748' }}>
                  <strong>مقصد:</strong> فولدر پرسنل انتخاب‌شده
                  <div style={{ direction: 'ltr', fontSize: 12, color: '#4a5568', marginTop: 4 }}>
                    {attachPersonFolder || '(در حال تعیین مسیر...)'}
                  </div>
                </div>
                <input
                  ref={attachFilesRef}
                  type="file"
                  multiple
                  style={{ display: 'none' }}
                  onChange={(e) => uploadAttachFilesToPerson(e.target.files)}
                />
                <button
                  type="button"
                  className="btn-primary"
                  disabled={attachBusy || !attachPersonFolder}
                  onClick={() => attachFilesRef.current?.click()}
                  style={{ width: '100%' }}
                >
                  {attachBusy ? 'در حال انتقال...' : 'انتخاب فایل‌ها از کامپیوتر و انتقال'}
                </button>
                {attachSourceInfo && (
                  <div style={{ fontSize: 12, color: '#718096', marginTop: 8 }}>{attachSourceInfo}</div>
                )}
              </div>
            )}

            {attachMsg && (
              <div
                style={{
                  marginTop: 12,
                  fontSize: 13,
                  color: attachMsg.includes('خطا') ? '#c53030' : '#2f855a',
                }}
              >
                {attachMsg}
              </div>
            )}

            <div style={{ marginTop: 14, display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="btn-primary"
                disabled={attachBusy}
                onClick={() => setShowAttachModal(false)}
              >
                بستن
              </button>
            </div>
          </div>
        </div>
      )}

      {/* مودال عکس پرسنلی */}
      {showPhotoModal && selectedPersonnel && (
        <div className="modal-overlay" onClick={() => setShowPhotoModal(false)}>
          <div
            className="modal-box"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: 520 }}
          >
            <div className="modal-header">
              <h3>عکس پرسنلی</h3>
              <button type="button" className="modal-close" onClick={() => setShowPhotoModal(false)}>×</button>
            </div>
            <div style={{ marginBottom: 14, fontSize: 13, color: '#4a5568' }}>
              <strong>
                {selectedPersonnel.first_name} {selectedPersonnel.last_name}
              </strong>
              {' — '}
              کدملی: {selectedPersonnel.national_id || '—'}
              {selectedPersonnel.company ? ` — ${selectedPersonnel.company}` : ''}
            </div>

            <div
              style={{
                display: 'flex',
                gap: 16,
                alignItems: 'flex-start',
                marginBottom: 16,
                flexWrap: 'wrap',
              }}
            >
              <div
                style={{
                  width: 120,
                  height: 150,
                  border: '1px solid #e2e8f0',
                  borderRadius: 8,
                  overflow: 'hidden',
                  background: '#f7fafc',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {photoPreview ? (
                  <img
                    src={photoPreview}
                    alt="عکس پرسنلی"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <span style={{ color: '#a0aec0', fontSize: 13 }}>بدون عکس</span>
                )}
              </div>
              <div style={{ flex: 1, minWidth: 200 }}>
                <p style={{ fontSize: 13, margin: '0 0 12px', color: '#4a5568' }}>
                  یکی از روش‌های زیر را انتخاب کنید:
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={photoModalBusy}
                    onClick={() => photoFileRef.current?.click()}
                    style={{ textAlign: 'center' }}
                  >
                    انتقال عکس از کامپیوتر
                  </button>
                  <input
                    ref={photoFileRef}
                    type="file"
                    accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                    style={{ display: 'none' }}
                    onChange={(e) => uploadPhotoFromComputer(e.target.files)}
                  />
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={photoModalBusy}
                    onClick={transferPhotoFromDocs}
                    style={{ textAlign: 'center' }}
                  >
                    انتقال عکس از فولدر مدارک پرسنل
                  </button>
                </div>
                <p style={{ fontSize: 11, color: '#718096', marginTop: 10 }}>
                  در فولدر مدارک، هر فایل با فرمت JPG یا PNG (با هر نامی) به‌عنوان عکس پرسنلی قابل انتقال است.
                </p>
                {docsPhotoCandidates.length > 0 && (
                  <div style={{ fontSize: 12, color: '#2d3748', marginTop: 6 }}>
                    تصاویر موجود در فولدر: {docsPhotoCandidates.map((x) => x.name).join('، ')}
                  </div>
                )}
              </div>
            </div>

            {photoModalMsg && (
              <div
                style={{
                  marginBottom: 12,
                  fontSize: 13,
                  color: photoModalMsg.includes('خطا') || photoModalMsg.includes('یافت نشد')
                    ? '#c53030'
                    : '#2f855a',
                }}
              >
                {photoModalMsg}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="btn-primary" onClick={() => setShowPhotoModal(false)}>
                بستن
              </button>
            </div>
          </div>
        </div>
      )}

      {/* مودال تنظیمات سیستم — مسیر ریشه مدارک پرسنل */}
      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 560 }}>
            <div className="modal-header">
              <h3>⚙️ تنظیمات سیستم</h3>
              <button type="button" className="modal-close" onClick={() => setShowSettings(false)}>×</button>
            </div>
            <form onSubmit={saveSettings}>
              <div className="form-group" style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600 }}>
                  مسیر ریشه فولدرهای پرسنل
                </label>
                <p style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                  ساختار فولدرها: <strong>ریشه / نام شرکت تابعه / کدملی</strong>.
                  با ثبت هر شرکت، فولدر آن شرکت در ریشه ساخته می‌شود و مدارک و عکس هر پرسنل
                  داخل فولدر کدملی زیر شرکت مربوطه ذخیره می‌گردد.
                </p>
                <input
                  type="text"
                  value={docsRootInput}
                  onChange={(e) => setDocsRootInput(e.target.value)}
                  placeholder="مثال: C:\DejbanDocs یا /home/data/personnel_docs"
                  style={{ width: '100%', padding: '8px 10px', direction: 'ltr', textAlign: 'left' }}
                  dir="ltr"
                />
              </div>
              {settingsMsg && (
                <div style={{ marginBottom: 12, color: settingsMsg.includes('خطا') ? '#c53030' : '#2f855a' }}>
                  {settingsMsg}
                </div>
              )}
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowSettings(false)}>
                  بستن
                </button>
                <button type="submit" className="btn-primary" disabled={settingsSaving}>
                  {settingsSaving ? 'در حال ذخیره...' : 'ذخیره مسیر'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* مودال مستندات معماری پروژه */}
      {showArchDocs && (
        <div className="modal-overlay" onClick={() => setShowArchDocs(false)}>
          <div
            className="modal-box"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: 720, maxHeight: '85vh', overflow: 'auto' }}
          >
            <div className="modal-header">
              <h3>📘 مستندات معماری — سیاست اطلاعات پایه</h3>
              <button type="button" className="modal-close" onClick={() => setShowArchDocs(false)}>×</button>
            </div>
            <div style={{ fontSize: 13, lineHeight: 1.8, color: '#2d3748', padding: '4px 4px 12px' }}>
              <div style={{
                background: '#ebf8ff', border: '1px solid #90cdf4', borderRadius: 8,
                padding: '10px 12px', marginBottom: 14,
              }}>
                <strong>اصل محوری (الزامی):</strong> برگه <b>اطلاعات پایه</b> منبع حقیقت (Source of Truth)
                برای داده‌های مرجع است.
                <br />
                <b>هر فیلدی در سایر برگه‌ها</b> (مثل پرسنل، کارت، مجوز، تردد و …) که معادلش در اطلاعات پایه
                وجود دارد — مانند <b>رشته تحصیلی، واحد، گروه مسئولیت، نوع استخدام، درب، مقصد کالا</b> —
                <u>باید حتماً مقدارش از اطلاعات پایه خوانده شود</u> (لیست کشویی متصل به API)، نه به‌صورت متن آزاد یا hard-code.
              </div>

              <h4 style={{ margin: '12px 0 6px', color: '#2b6cb0' }}>چرا این سیاست؟</h4>
              <ul style={{ margin: 0, paddingRight: 18 }}>
                <li>یکپارچگی: تغییر نام واحد یا رشته در یک جا اعمال می‌شود</li>
                <li>گسترش‌پذیری: افزودن گزینه بدون تغییر کد فرم‌ها</li>
                <li>چندشرکتی: یک دیتابیس متمرکز (<code>co_db.db</code>) با فیلتر <code>company_code</code></li>
                <li>هم‌خوانی با الگوی سیستم جامع حراست</li>
              </ul>

              <h4 style={{ margin: '14px 0 6px', color: '#2b6cb0' }}>نقشه وابستگی فیلدها</h4>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table" style={{ fontSize: 12 }}>
                  <thead>
                    <tr>
                      <th>فیلد در فرم‌ها</th>
                      <th>منبع اطلاعات پایه</th>
                      <th>API</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['مرکز (center)', 'تعریف واحدها → نام مرکز', '/api/units'],
                      ['واحد (department)', 'تعریف واحدها → نام واحد', '/api/units'],
                      ['رشته تحصیلی', 'رشته تحصیلی', '/api/education-fields'],
                      ['گروه مسئولیت', 'گروه مسئولیت', '/api/responsibility-groups'],
                      ['نوع استخدام', 'انواع استخدام', '/api/employment-types'],
                      ['درب‌های تردد', 'تعریف درب‌های تردد', '/api/lookups/access_doors'],
                      ['مقصد کالا', 'تعریف مقصد کالا', '/api/lookups/goods_destinations'],
                      ['سرویس', 'تعریف سرویس', '/api/lookups/services'],
                      ['شرکت/مشتری', 'تعریف شرکت/مشتری', '/api/lookups/client_companies'],
                      ['نوع ورود و خروج', 'نوع ورود و خروج', '/api/lookups/entry_exit_types'],
                      ['دسترسی درب', 'دسترسی درب', '/api/baseinfo/door_user_access'],
                      ['نوع خودرو', 'تعریف نوع خودروها', '/api/baseinfo/vehicle_types'],
                      ['نوع ورود/خروج کالا', 'انواع ورود و خروج کالا', '/api/baseinfo/goods_entry_exit_types'],
                      ['کالا / محصول', 'تعریف کالا و محصولات', '/api/baseinfo/goods_products'],
                    ].map((row) => (
                      <tr key={row[0]}>
                        <td>{row[0]}</td>
                        <td>{row[1]}</td>
                        <td style={{ direction: 'ltr', textAlign: 'left', fontFamily: 'monospace', fontSize: 11 }}>{row[2]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <h4 style={{ margin: '14px 0 6px', color: '#2b6cb0' }}>قانون توسعه</h4>
              <ol style={{ margin: 0, paddingRight: 18 }}>
                <li><b>الزام:</b> اگر فیلدی در اطلاعات پایه تعریف شده، در همهٔ برگه‌ها فقط از همان منبع (select از API) پر شود — مثال: رشته تحصیلی</li>
                <li>گزینهٔ لیست‌شدنی جدید → اول در اطلاعات پایه تعریف شود، بعد در فرم مصرف شود</li>
                <li>فیلد پرسنل جدید → فقط به <code>PERSONAL_FIELDS</code> در <code>database.py</code> اضافه شود</li>
                <li><b>hard-code</b> و ورودی متن آزاد برای مقادیر مرجع ممنوع است</li>
                <li>جزئیات کامل: فایل <code>docs/ARCHITECTURE.md</code></li>
              </ol>

              <h4 style={{ margin: '14px 0 6px', color: '#2b6cb0' }}>محل ذخیره‌سازی</h4>
              <ul style={{ margin: 0, paddingRight: 18 }}>
                <li>همه جداول در دیتابیس متمرکز <code>data/co_db.db</code></li>
                <li>شرکت‌ها: جدول <code>companies</code> — پرسنل با ستون <code>company_code</code></li>
                <li>اطلاعات پایه / انتظامات / خودرو / کالا: جداول مرجع در همان فایل</li>
              </ul>
              <h4 style={{ margin: '14px 0 6px', color: '#2b6cb0' }}>ماژول‌های مرجع فعلی</h4>
              <ul style={{ margin: 0, paddingRight: 18 }}>
                <li>اطلاعات پایه: واحد، رشته، استخدام، درب، کالا، سرویس، مشتری، <b>کالاها</b>، <b>خودروها</b></li>
                <li>انتظامات: گروه، مراکز/اماکن حفاظتی، شیفت، مسئول، نوبت، وضعیت، تجهیزات</li>
                <li>پرسنل (تب مستقل): مشخصات، وابستگان، کارت — پلاک ایران با فیلد ترکیبی</li>
              </ul>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 8 }}>
              <button type="button" className="btn-primary" onClick={() => setShowArchDocs(false)}>بستن</button>
            </div>
          </div>
        </div>
      )}

      {/* مودال آرشیو پرسنل — آپلود / حذف / افزودن / ویرایش / جستجو */}
      {showArchive && (
        <div className="modal-overlay" onClick={() => setShowArchive(false)}>
          <div
            className="modal-box"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: 820, maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}
          >
            <div className="modal-header">
              <h3>📂 آرشیو پرسنل</h3>
              <button type="button" className="modal-close" onClick={() => setShowArchive(false)}>×</button>
            </div>

            <div style={{ marginBottom: 8, fontSize: 13, color: '#555' }}>
              <div>
                <strong>ریشه:</strong>{' '}
                <code dir="ltr" style={{ fontSize: 12 }}>{archiveRoot || '—'}</code>
              </div>
              <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <strong>مسیر جاری:</strong>
                <code dir="ltr" style={{ fontSize: 12 }}>
                  {archivePath ? ` / ${archivePath}` : ' / (ریشه)'}
                </code>
                {archivePath ? (
                  <button type="button" className="btn-secondary" style={{ padding: '2px 10px', fontSize: 12 }} onClick={archiveGoUp}>
                    ⬆ یک سطح بالاتر
                  </button>
                ) : null}
              </div>
            </div>

            {/* نوار ابزار و جستجو */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10, alignItems: 'center' }}>
              <input
                type="text"
                value={archiveSearch}
                onChange={(e) => setArchiveSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') loadArchive(archivePath, archiveSearch)
                }}
                placeholder="جستجوی پوشه/فایل (فارسی و عربی)..."
                style={{ flex: '1 1 180px', minWidth: 160, padding: '6px 10px', border: '1px solid #cbd5e0', borderRadius: 6 }}
              />
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: 12 }}
                onClick={() => loadArchive(archivePath, archiveSearch)}
              >
                🔍 جستجو
              </button>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: 12 }}
                disabled={archiveBusy}
                onClick={archiveCreateFolder}
              >
                ➕ پوشه جدید
              </button>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: 12 }}
                disabled={archiveBusy}
                onClick={() => archiveFileRef.current?.click()}
              >
                ⬆️ آپلود فایل
              </button>
              <input
                ref={archiveFileRef}
                type="file"
                multiple
                style={{ display: 'none' }}
                onChange={(e) => archiveUploadFiles(e.target.files)}
              />
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: 12 }}
                disabled={archiveBusy}
                title="همگام‌سازی فولدر شرکت‌ها و پرسنل (فقط موارد جدید؛ موجودها رد می‌شوند)"
                onClick={() => {
                  setArchiveBusy(true)
                  setArchiveMsg('در حال بروزرسانی فولدرها...')
                  fetch('/api/docs/sync-folders?rebuild=true', { method: 'POST' })
                    .then(async (r) => {
                      const d = await r.json()
                      if (!r.ok) throw new Error(d.detail || 'خطا در بروزرسانی')
                      setArchiveMsg(d.message || 'بروزرسانی انجام شد')
                      loadArchive(archivePath, archiveSearch)
                    })
                    .catch((err) => setArchiveMsg(err.message || 'خطا'))
                    .finally(() => setArchiveBusy(false))
                }}
              >
                🔄 بروزرسانی
              </button>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: 12 }}
                disabled={archiveBusy}
                title="همان همگام‌سازی فولدر شرکت‌ها و کدملی"
                onClick={() => {
                  setArchiveBusy(true)
                  setArchiveMsg('در حال ساخت/همگام‌سازی فولدرها...')
                  fetch('/api/docs/create-all-folders?rebuild=true', { method: 'POST' })
                    .then(async (r) => {
                      const d = await r.json()
                      if (!r.ok) throw new Error(d.detail || 'خطا')
                      setArchiveMsg(d.message)
                      loadArchive(archivePath, archiveSearch)
                    })
                    .catch((err) => setArchiveMsg(err.message))
                    .finally(() => setArchiveBusy(false))
                }}
              >
                📁 ساخت فولدر شرکت‌ها و کدملی
              </button>
            </div>

            {archiveMsg && (
              <div style={{ marginBottom: 8, fontSize: 12, color: archiveMsg.includes('خطا') ? '#c53030' : '#2f855a' }}>
                {archiveMsg}
              </div>
            )}

            <div style={{ flex: 1, overflow: 'auto', border: '1px solid #e2e8f0', borderRadius: 6, minHeight: 220 }}>
              {archiveLoading ? (
                <div style={{ padding: 24, textAlign: 'center', color: '#718096' }}>در حال بارگذاری...</div>
              ) : archiveError ? (
                <div style={{ padding: 24, textAlign: 'center', color: '#c53030' }}>{archiveError}</div>
              ) : archiveItems.length === 0 ? (
                <div style={{ padding: 24, textAlign: 'center', color: '#718096' }}>
                  {archiveSearch
                    ? 'موردی با این جستجو یافت نشد.'
                    : 'این پوشه خالی است. می‌توانید پوشه بسازید یا فایل آپلود کنید.'}
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f7fafc', textAlign: 'right' }}>
                      <th style={{ padding: '8px 12px' }}>نام</th>
                      <th style={{ padding: '8px 12px' }}>نوع</th>
                      <th style={{ padding: '8px 12px' }}>حجم</th>
                      <th style={{ padding: '8px 12px', width: 140 }}>عملیات</th>
                    </tr>
                  </thead>
                  <tbody>
                    {archiveItems.map((it) => (
                      <tr
                        key={it.relative_path}
                        style={{ borderTop: '1px solid #edf2f7' }}
                        onDoubleClick={() => {
                          if (it.is_dir) loadArchive(it.relative_path, '')
                        }}
                      >
                        <td style={{ padding: '8px 12px' }}>
                          {it.is_dir ? (
                            <button
                              type="button"
                              onClick={() => {
                                setArchiveSearch('')
                                loadArchive(it.relative_path, '')
                              }}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#2b6cb0',
                                cursor: 'pointer',
                                padding: 0,
                                font: 'inherit',
                              }}
                            >
                              📁 {it.name}
                            </button>
                          ) : (
                            <a
                              href={`/api/docs/file?path=${encodeURIComponent(it.relative_path)}&inline=true`}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#2d3748', textDecoration: 'none' }}
                            >
                              📄 {it.name}
                            </a>
                          )}
                        </td>
                        <td style={{ padding: '8px 12px' }}>{it.is_dir ? 'پوشه' : 'فایل'}</td>
                        <td style={{ padding: '8px 12px', direction: 'ltr' }}>
                          {it.is_dir ? '—' : formatFileSize(it.size)}
                        </td>
                        <td style={{ padding: '6px 8px', whiteSpace: 'nowrap' }}>
                          {!it.is_dir && (
                            <a
                              href={`/api/docs/file?path=${encodeURIComponent(it.relative_path)}&inline=false`}
                              className="btn-secondary"
                              style={{
                                padding: '4px 8px',
                                marginLeft: 4,
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 4,
                                verticalAlign: 'middle',
                                textDecoration: 'none',
                                fontSize: 11,
                                color: '#276749',
                              }}
                              title="دانلود فایل"
                              download
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#276749" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                <polyline points="7 10 12 15 17 10" />
                                <line x1="12" y1="15" x2="12" y2="3" />
                              </svg>
                              دانلود
                            </a>
                          )}
                          <button
                            type="button"
                            className="btn-secondary"
                            style={{
                              padding: '4px 8px',
                              marginLeft: 4,
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 4,
                              verticalAlign: 'middle',
                            }}
                            disabled={archiveBusy}
                            title="ویرایش نام"
                            onClick={() => archiveRenameItem(it)}
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2b6cb0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                              <path d="M12 20h9" />
                              <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                            </svg>
                            <span style={{ fontSize: 11, color: '#2b6cb0' }}>ویرایش</span>
                          </button>
                          <button
                            type="button"
                            className="btn-secondary"
                            style={{
                              padding: '4px 8px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 4,
                              verticalAlign: 'middle',
                            }}
                            disabled={archiveBusy}
                            title="حذف"
                            onClick={() => archiveDeleteItem(it)}
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#c53030" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                              <polyline points="3 6 5 6 21 6" />
                              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                              <path d="M10 11v6" />
                              <path d="M14 11v6" />
                              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
                            </svg>
                            <span style={{ fontSize: 11, color: '#c53030' }}>حذف</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div style={{ marginTop: 12, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button type="button" className="btn-primary" onClick={() => setShowArchive(false)}>
                بستن
              </button>
            </div>
          </div>
        </div>
      )}


      {/* ریشه چاپ کارت PVC */}
      <div
        id="pvc-print-root"
        aria-hidden="true"
        style={{
          position: 'fixed',
          left: '-10000px',
          top: 0,
          width: 'var(--pvc-w)',
          margin: 0,
          padding: 0,
          background: '#fff',
        }}
      >
        {cardPrintPerson && (cardPrintSide === 'front' || cardPrintSide === 'both') && (
          <IdCardFront person={cardPrintPerson} companyName={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).name || cardPrintPerson.company || ORG_SHORT} logoUrl={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).logo || ''} />
        )}
        {cardPrintPerson && (cardPrintSide === 'back' || cardPrintSide === 'both') && (
          <IdCardBack person={cardPrintPerson} companyName={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).name || cardPrintPerson.company || ORG_SHORT} logoUrl={(companies.find((c) => String(c.code) === String(cardPrintPerson.company_code)) || {}).logo || ''} />
        )}
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-left">
          <span>{apiStatus === 'online' ? '🟢' : '🔴'} سیستم {apiStatus === 'online' ? 'آنلاین' : 'آفلاین'}</span>
          <span>کاربر: {currentUser?.full_name || currentUser?.username || 'AdminUser'}</span>
          <button type="button" className="refresh-btn" style={{ marginRight: 8, fontSize: 11, padding: '2px 10px', color: '#c53030', borderColor: '#feb2b2' }} onClick={handleLogout} title="خروج از سیستم و بازگشت به صفحه ورود">🚪 خروج</button>
          <span>🏢 شرکت: ۱۰۰ — تأسیسات دریایی ایران</span>
          <span>DB: co_db</span>
          <span>نسخه: ۱.۰.۱۱۲</span>
        </div>
        <div className="status-right">
          <span>دسترسی: فقط پرسنل شرکت خود</span>
          <span>۱۴۰۴/۰۷/۰۹ — ۰۸:۳۰</span>
        </div>
      </div>
    </>
  )
}

export default App
