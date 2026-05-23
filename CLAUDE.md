# Family Kitchen Dashboard — CLAUDE.md

> **למשתמש החדש של Claude:** קרא את הקובץ הזה במלואו לפני שתתחיל לעבוד.

> **עדכון אחרון:** 23/05/2026 — סשן v13: Google Calendar, תכנון שבועי, עיצוב מסכי ילדים, אירועים קרובים 7 ימים, Briefing עשיר.

---

## 1. תיאור הפרויקט

דשבורד אינטראקטיבי על iPad במטבח משפחת Ginzburg:
- שעה ותאריך עברי+לועזי, מזג אוויר, זמני שבת
- מערכת שעות + שיעורי בית + אירועי שיעור (Webtop)
- Google Calendar משפחתי (דרך הסקרייפר — ללא CORS)
- "היום במשפחה" — חוגים + קלנדר + ייחודי (ללא כפילות שיעורים)
- "אירועים קרובים 7 ימים" — קלנדר + חוגים + ימי הולדת + חגים
- מסכים אישיים לרון/יובל/יהב עם מערכת שעות + לחיצה לפירוט תכנון
- AI Briefing עשיר: ברכה + חוגים + מבחנים + אירועים + מזג אוויר
- צ'אט קולי עם Claude AI

**Stack:** HTML+JS+React (Babel CDN) → GitHub Pages. סקרייפר Python מקומי.

---

## 2. פרטי המשפחה

- **ניר גינזבורג** | שוהם (lat 31.9956, lon 34.9544)
- **רון** — כיתה ו', Webtop: `5000965` / `Ron071214` | יומהולדת: **07.12.2014**
- **יובל** — כיתה ב', Webtop: `6384174` / `714235` | יומהולדת: **05.01.2017**
- **יהב** — בן 5, גן | יומהולדת: **18.02.2021**
- **ניר (אבא)** — 12.09.1984 | **רותי (אמא)** — 09.05.1985
- **סבים:** חיה 29.10 | שרגא 22.12 | זאב 02.06 | אווה 27.05
- **iPad:** מטבח, landscape, 1180×820

---

## 3. ארכיטקטורה

```
webtop_scraper.py → webtop_data.json → index.html (GitHub Pages)
                    (כולל calendar_events)
```

**Repo:** `github.com/Ginzburgnir/family-dashboard`
**URL:** `https://ginzburgnir.github.io/family-dashboard/`
**מקומי:** `python -m http.server 8080` ← `http://localhost:8080`

---

## 4. הסקרייפר — webtop_scraper.py (~833 שורות)

```bash
python webtop_scraper.py --u1 6384174 --p1 714235 --n1 יובל --u2 5000965 --p2 Ron071214 --n2 רון
```

**מה שולף:**
- Webtop: weekly_plan + weekly_schedule + lesson_events + homework + messages + notifications
- **Google Calendar:** `fetch_calendar()` — iCal סודי ב-Python (ללא CORS)

**Google Calendar URL (סודי):**
```
https://calendar.google.com/calendar/ical/61ddedeb...@group.calendar.google.com/private-054cd130400f4006319a75af38891c9b/basic.ics
```
(מוגדר כ-`GCAL_ICS_URL` בראש הקובץ)

**פלט calendar_events:**
```json
{ "summary":"...", "location":"...", "all_day":true, "start_iso":"2026-05-25T00:00:00",
  "days_away":2, "date_heb":"25 במאי", "time":"" }
```

**חשוב מאוד:** `days_away` מחושב ב-Python — לא ב-JS. מונע בעיית timezone.

**פלט תקין:**
```
[google calendar] -> X events in next 90 days
📅 Google Calendar: X אירועים
```

**הערות טכניות:**
- תיקון weekday: `(dt.weekday() + 1) % 7`
- API typos: `WeeklyScedule`, `Scheduale`

---

## 5. הדשבורד — index.html (~5992 שורות, v13)

### מסכים (7 טאבים)
1. **בית** — Hero + יובל/רון (מערכת מחר) + מרכז + ויג'טים
2. **לו"ז** — יומן חודשי + שבוע דינמי
3. **רון** — KidScreen
4. **יובל** — KidScreen
5. **יהב** — חוגים בלבד
6. **פתקים**
7. **גלריה**

### מסך הבית
- Grid: `1fr 1.6fr 1fr`
- Hero: שעון 108px, compact
- עמודות ילדים: `overflow-y: scroll; -webkit-overflow-scrolling: touch`
- AI Briefing: `flex-shrink: 0` — חייב!
- "היום במשפחה": ללא שיעורי בית ספר (tag!=='school')
- "אירועים קרובים": 7 ימים, ציר מחר→+7

### מסך ילדים (KidScreen)
- **עמודה 1:** שיעורי בית + מבחן קומפקטי
- **עמודה 2:** אירועי שיעור
- **עמודה 3:** חוגים מלא
- **תכנון שיעור:** לחיצה על שיעור עם 📖 → selectedLesson → פירוט מלא (pre-wrap)
- `selectedLesson` state — מתאפס בהחלפת יום

### מערכת חוגים v2
- localStorage: `fd_activities_v2` + `fd_exceptions_v2`
- `{ id, name, days:[], time, timeTo, place, dayTimes:{}, paused }`
- exception: `{ actId, weekKey, origDay, cancelled?/overrideDay?/overrideTime? }`
- `getWeekKey(date)` → YYYY-MM-DD של ראשון
- רענון: `dispatchEvent('activitiesUpdated')` → `actTick` → HomeScreen

### Google Calendar בדשבורד
- קורא מ-`webtop?.calendar_events` (לא fetch ישיר)
- `days_away` = `e.days_away` מהסקרייפר (לא מחושב מחדש!)
- `kind:'custom'`, CSS class: `ev-tag.calendar` (כחול `#7ab3f8`)

### AI Briefing
- ברכה לפי שעה (בוקר/צהריים/ערב)
- יום הולדת / אירוע קלנדר היום
- שבת שלום / שישי קצר
- שיעורי בית + מבחנים ≤3 ימים
- חוגים היום (מ-localStorage)
- אירוע מחר/מחרתיים
- טיפ לבוש

### היסטוריה — 3 שכבות
1. Wikipedia עברית (filter: לא "הוא היום ה-X")
2. Claude Haiku (`ai_anthropic_key_v1` מ-localStorage)
3. 20 עובדות סטטיות (`(month*31+day) % 20`)

---

## 6. גרסאות

- v9-v11: todayEvents, ימי הולדת, מסכי ילדים, weekly_schedule, weekday fix
- v12: חוגים v2, מחר במשפחה, actTick, היסטוריה 3 שכבות
- **v13 (23/05/2026):**
  - ✅ Google Calendar דרך סקרייפר Python (iCal parser)
  - ✅ תיקון timezone: days_away מ-Python
  - ✅ "היום במשפחה" ללא שיעורים + "7 ימים" במקום "מחר"
  - ✅ לחיצה על 📖 פותח פירוט תכנון שיעור מלא
  - ✅ AI Briefing עשיר + flex-shrink:0
  - ✅ Layout מסכי ילדים: מבחן לעמודה 1, חוגים לעמודה 3
  - ✅ Hero קומפקטי + עמודות שוות
  - ✅ iOS scroll fix
  - ✅ vacation widget null safety
  - ✅ weeklyPlan initial `{}` (לא `[]`)
  - ✅ לוח השבוע תאריך דינמי

---

## 7. TODO — הבא

### 🔴 בתור:
1. **תכנון שבועי מ-Webtop** — endpoint נוסף שמחזיר נתונים עשירים יותר מ-GetEvents. צריך: Webtop → תכנון שבועי → F12 → Network → מצוא endpoint → הוסף לסקרייפר
2. **Telegram Bot** — עדכון מרחוק + תזכורות (Node.js/Python, Render חינמי)
3. **גלריה** — Google Photos / Apple Photos

### 🔵 בסוף:
4. **קיוסק/מסך מלא** — PWA / Guided Access
5. **אוטומציה** — Task Scheduler / Pi

---

## 8. בעיות נפוצות

| בעיה | פתרון |
|------|-------|
| דשבורד שחור | F12 → Console → Babel error |
| vacation widget קורס | אין חגים ב-data.events |
| אין מערכת שעות | הרץ סקרייפר + העלה JSON |
| Briefing לא נראה | flex-shrink:0 על .briefing |
| קלנדר לא מציג | Console: `window.FAMILY.calendarStatus` |
| תאריך קלנדר שגוי | days_away חייב מהסקרייפר (Python) |
| חוגים לא מתעדכנים | dispatchEvent('activitiesUpdated') |

---

## 9. קבצים

```
C:\Users\user\Desktop\FAMILY\
├── webtop_scraper.py   ~833 שורות
├── webtop_data.json    פלט (כולל calendar_events)
├── index.html          ~5992 שורות
└── CLAUDE.md           המסמך הזה
```

---

## 10. עצות

1. **בתחילת שיחה** — בקש index.html + webtop_scraper.py + webtop_data.json
2. **בעיות קלנדר** — `window.FAMILY.calendarStatus` ב-Console
3. **אל תמציא Webtop endpoints** — DevTools → Network
4. **Hard refresh** לפני כל בדיקה

---

*עודכן 23/05/2026 — סוף סשן v13.*
*הפסקנו אחרי: פירוט תכנון שבועי בלחיצה על 📖 במסך ילדים.*
*הצעד הבא: endpoint "תכנון שבועי" מ-Webtop + Telegram Bot.*
