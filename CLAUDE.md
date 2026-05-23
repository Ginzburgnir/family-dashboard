# Family Kitchen Dashboard — CLAUDE.md

> **למשתמש החדש של Claude:** קרא את הקובץ הזה במלואו לפני שתתחיל לעבוד. הוא מכיל את כל ההקשר של הפרויקט, מצבו הנוכחי, ומה נשאר לעשות.

> **עדכון אחרון:** 23/05/2026 — סשן שכלל מערכת חוגים מלאה, מחר במשפחה, תיקוני סנכרון, היום בהיסטוריה.

---

## 1. תיאור הפרויקט

דשבורד אינטראקטיבי המוצג על iPad במטבח של משפחת Ginzburg. מציג בזמן אמת:
- שעה ותאריך עברי+לועזי
- מזג אוויר עם המלצת לבוש
- זמני שבת וכניסת/יציאת שבת
- מערכת שעות + שיעורי בית של שני הילדים (יובל ורון)
- הודעות והתראות מ-Webtop (מערכת בית הספר)
- צ'אט קולי רציף עם Claude AI
- "היום בהיסטוריה" — Wikipedia עברית / Claude Haiku / 20 עובדות סטטיות
- חופשות וחגים קרובים
- ימי הולדת משפחתיים עם ספירה לאחור
- מסכים אישיים לרון, יובל, ויהב עם מערכת חוגים
- **היום במשפחה** — ציר זמן יומי לכל ילד + משפחה
- **מחר במשפחה** — שיעורים, חוגים, מבחנים ואירועים של מחר

**Stack:** HTML+JS+React (Babel CDN) → GitHub Pages. סקרייפר Python שרץ במחשב המקומי.

---

## 2. פרטי המשפחה

- **שם:** ניר גינזבורג
- **מיקום:** שוהם, ישראל (lat 31.9956, lon 34.9544)
- **ילדים:**
  - **רון** — כיתה ו', יוזר Webtop: `5000965`, סיסמה: `Ron071214`. יום הולדת: **07.12.2014**
  - **יובל** — כיתה ב', יוזר Webtop: `6384174`, סיסמה: `714235`. יום הולדת: **05.01.2017**
  - **יהב** — בן 5, אין Webtop (גן). יום הולדת: **18.02.2021**
- **הורים:**
  - **אבא (ניר)** — יום הולדת: **12.09.1984**
  - **אמא (רותי)** — יום הולדת: **09.05.1985** ✅ עודכן 23/05/2026
- **סבים וסבתות** (ללא גיל):
  - **סבתא חיה** — **29.10** | **סבא שרגא** — **22.12**
  - **סבא זאב** — **02.06** | **סבתא אווה** — **27.05**
- **iPad:** במטבח, landscape, 1180×820. עדיין בשימוש לניסויים — קיוסק לסוף.
- **רמת טכנית:** משתמש לא-טכני. הוראות שלב-אחר-שלב.

---

## 3. ארכיטקטורה

```
מחשב מקומי (Windows)          GitHub Pages              iPad / Safari
─────────────────────          ────────────────          ─────────────
webtop_scraper.py  ──push──>  webtop_data.json  ─fetch─> index.html
                               index.html
```

**Repo:** `github.com/Ginzburgnir/family-dashboard`
**URL פעיל:** `https://ginzburgnir.github.io/family-dashboard/`

**הרצה מקומית לבדיקות:**
```
cd C:\Users\user\Desktop\FAMILY\
python -m http.server 8080
```
דפדפן: `http://localhost:8080` | iPad (אותה רשת): `http://<IP>:8080`

---

## 4. הסקרייפר — `webtop_scraper.py` (~747 שורות)

```
python webtop_scraper.py --u1 6384174 --p1 714235 --n1 יובל --u2 5000965 --p2 Ron071214 --n2 רון
```

**endpoints:** SSO → `weekly_plan` (GetEvents) → `weekly_schedule` (GetPupilScheduale) → `lesson_events` → `homework` → `messages` + body

**הערות טכניות חשובות:**
- ✅ **תוקן: באג ימי השבוע** — `(dt.weekday() + 1) % 7` (לא `dt.weekday()`)
- API typos שחייבים לשמור: `WeeklyScedule`, `Scheduale`
- שדה סיסמה ב-edu.gov.il: `readonly` מוסר ב-`focus`

---

## 5. הדשבורד — `index.html` (~5761 שורות, v12)

### מסכים (7 טאבים)
1. **בית** — Hero + "היום במשפחה" + "מחר במשפחה" + ימי הולדת/חופשות + שבת/היסטוריה
2. **לו"ז** — יומן חודשי + DayViewOverlay
3. **רון** — KidScreen עם מערכת שעות + חוגים
4. **יובל** — KidScreen עם מערכת שעות + חוגים
5. **יהב** — KidScreen עם חוגים בלבד
6. **פתקים** — קיר הודעות משפחתי
7. **גלריה** — מצגת תמונות

### מערכת חוגים — v2 (נוסף 23/05/2026)

**localStorage keys:**
- `fd_activities_v2` — `{ ron: [...], yuval: [...], yahav: [...] }`
- `fd_exceptions_v2` — חריגים שבועיים

**מבנה activity:**
```js
{ id, name, days: number[], time: 'HH:MM', timeTo: 'HH:MM',
  place, dayTimes: { 0:'16:00', 2:'17:00' }, paused: bool }
```

**מבנה exception:**
```js
{ actId, weekKey:'YYYY-MM-DD'(ראשון בשבוע), origDay,
  cancelled?: true | overrideDay?: number | overrideTime?: 'HH:MM' }
```

**רענון אוטומטי למסך הבית:** `window.dispatchEvent(new CustomEvent('activitiesUpdated'))` → `actTick` → `liveActivityEvents` מחשב מחדש

**getWeekKey(date):** מחזיר YYYY-MM-DD של ראשון בשבוע

### תכונות מרכזיות

**מסך הבית — "היום במשפחה":**
- 3 קבוצות: רון / יובל / המשפחה
- `mergedToday` = school events + live activity events מ-localStorage

**מסך הבית — "מחר במשפחה":** (חדש v12)
- מציג שיעורים, חוגים, מבחנים, אירועים של מחר
- `mergedTmr` = `tomorrowEvents` (static school) + live tomorrow activities

**היום בהיסטוריה — 3 שכבות:**
1. Wikipedia עברית (עם filter לסינון תיאורי תאריך)
2. Claude Haiku (אם `ai_anthropic_key_v1` שמור)
3. 20 עובדות היסטוריות סטטיות בעברית (תמיד עובד)

**ימי הולדת:** מחשב גיל אוטומטי, מוצג 14 יום מראש, ב"היום במשפחה"

### מבני נתונים

`window.FAMILY`:
```js
{
  date, weather, shabbat,
  ron: { name, initial, grade, en, now, next, nextDayLabel, homework, test,
         lessonEvents, messages, notifications, weeklyPlan, weeklyTopics },
  yuval: { ...same },
  events: [{ id, kind, name, date, daysAway, icon, _d, bdayKind?, age? }],
  todayEvents: [{ who, time, text, tag, state, _min }],
  tomorrowEvents: [{ who, time, text, tag, _min }],
  history: { year, text },
  briefing: [...], week: [...], holiday: {...}
}
```

---

## 6. תהליך עדכון נתונים

1. הרץ סקריפט → יוצר `webtop_data.json`
2. **אופציה A:** העלה ל-GitHub → GitHub Pages → iPad מרענן
3. **אופציה B:** `python -m http.server 8080` → iPad מסתכל ב-LAN

**אוטומציה:** GitHub Actions חסום (CloudFront 403). Task Scheduler מקומי — אפשרי.

---

## 7. הוראות עבודה למפתח

1. **המשתמש לא טכני** — פקודות מלאות להעתקה, שלב-אחר-שלב
2. **שמור על מה שעובד** — תמיד `str_replace` לשינויים נקודתיים
3. **בעברית** — כל הממשק. RTL בכל מקום
4. **iOS Safari quirks** — speech priming, fixed positioning, CORS
5. **תמיד וודא syntax** אחרי שינוי

### בעיות נפוצות:
- **"דשבורד שחור":** Babel syntax; חסר createRoot; FAMILY חסר field
- **"חוגים לא מתעדכנים":** וודא `dispatchEvent('activitiesUpdated')` נקרא
- **"שיעור של מחר מוצג כהיום":** `isSchoolDayLocal && inSchoolTime` — תוקן
- **"יום שבוע שגוי בסקרייפר":** `(dt.weekday() + 1) % 7` — תוקן
- **"היסטוריה לא מציגה":** בדוק שכבות — Wikipedia → Claude key → static facts

---

## 8. גרסאות

- v1–v7: בנייה ראשונית, AI voice
- v8: body הודעות, continuous mode
- v9: todayEvents, ימי הולדת, יומן clickable
- v10: הגדלת פונטים, 3 קבוצות, "המערכת של מחר"
- v11: מסכים אישיים, weekly_schedule, תיקון weekday bug
- **v12 (23/05/2026):**
  - ✅ מערכת חוגים מלאה (מחזורי + חריגים שבועיים + השהיה)
  - ✅ ActionsModal — ניהול חוג בלחיצה אחת
  - ✅ "מחר במשפחה" במסך הבית
  - ✅ עדכון מסך בית בזמן אמת (actTick + CustomEvent)
  - ✅ תיקון סנכרון בין מסכי ילדים (key={kidKey})
  - ✅ שנת לידה רותי 1985
  - ✅ היסטוריה — 3 שכבות fallback בעברית
  - ✅ ActivityModal — ימים מרובים, שעת סיום, שעות שונות לפי יום

---

## 9. TODO — ספרינט הבא

### 🔴 בתור:
1. **Google Calendar** — ייבוא אירועי משפחה אוטומטי (OAuth2)
2. **גלריה** — חיבור לאלבומים אמיתיים (Apple Photos / Google Photos)
3. **Telegram Bot** — עדכון מרחוק + תזכורות (Node.js, Render/Railway חינמי)

### 🔵 בסוף:
4. **קיוסק/מסך מלא** — PWA או Guided Access על האייפד
5. **אוטומציה מלאה לסקרייפר** — Task Scheduler / Raspberry Pi

### 💡 פיצ'רים גדולים יותר (לאחר מכן):
- Apple Photos — "לפני X שנים ביום הזה"
- התראות push לטלפון
- Google Calendar משפחתי
- רשימת קניות שיתופית

---

## 10. עצות לשיחות עתידיות

1. **בקש 3 קבצים בתחילת שיחה:** `index.html`, `webtop_scraper.py`, `webtop_data.json`
2. **בקש פלט סקרייפר** לאבחון בעיות
3. **אל תמציא Webtop endpoints** — DevTools (F12) → Network → העתק cURL
4. **Safari cache:** אם משהו לא נראה — "האם עשית hard refresh?"
5. **תמיד עדכן CLAUDE.md** בסוף סשן משמעותי

---

*עודכן 23/05/2026 — סוף סשן v12. הצעד הבא: Google Calendar + גלריה.*
