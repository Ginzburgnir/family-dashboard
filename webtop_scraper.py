import asyncio, json, argparse, sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("pip install playwright && python -m playwright install chromium")

BASE        = "https://webtop.smartschool.co.il"
OUTPUT_FILE = Path(__file__).parent / "webtop_data.json"

DAYS = {0:"ראשון",1:"שני",2:"שלישי",3:"רביעי",4:"חמישי",5:"שישי",6:"שבת"}

async def wait_angular(page, timeout=15000):
    try:
        await page.wait_for_selector("mat-spinner,.mat-spinner", state="hidden", timeout=timeout)
    except Exception:
        pass
    await page.wait_for_timeout(1500)

async def login(page, username, password):
    await page.goto(BASE + "/account/login", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # אשר cookies (מאפשר את הכפתורים)
    try:
        await page.click('button:has-text("אשר cookies")', timeout=6000)
        await page.wait_for_timeout(2000)
        print("    cookies accepted")
    except Exception:
        # נסה JS לאשר
        try:
            await page.evaluate("""
                () => {
                    const btns = [...document.querySelectorAll('button')];
                    const cb = btns.find(b => b.textContent.includes('אשר') || b.textContent.includes('cookie'));
                    if (cb) { cb.click(); return true; }
                    return false;
                }
            """)
            await page.wait_for_timeout(2000)
        except Exception:
            pass

    # הסר disabled מכל הכפתורים
    await page.evaluate("""
        () => document.querySelectorAll('button[disabled],button.mat-button-disabled').forEach(b => {
            b.removeAttribute('disabled');
            b.classList.remove('mat-button-disabled');
        })
    """)
    await page.wait_for_timeout(500)

    # לחץ הזדהות משרד החינוך — force=True מתעלם מ-disabled
    try:
        await page.click('button:has-text("הזדהות משרד החינוך")', force=True, timeout=8000)
        print("    edu btn: force click OK")
    except Exception as e:
        print(f"    edu btn force failed: {e}")
        await page.evaluate("""
            () => {
                const edu = [...document.querySelectorAll('button')].find(b => b.textContent.includes('משרד החינוך'));
                if (edu) edu.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
            }
        """)
        print("    edu btn: dispatchEvent fallback")
    # שמור screenshot לפני ניווט
    await page.screenshot(path="/tmp/before_edu.png")

    # המתן לניווט לדף edu.gov
    try:
        await page.wait_for_url(lambda u: "edu.gov" in u or "lgn" in u, timeout=12000)
        print(f"    navigated to: {page.url}")
    except Exception:
        print(f"    no navigation yet, URL: {page.url}")
        # נסה dispatchEvent — טריגר Angular
        await page.evaluate("""
            () => {
                const edu = [...document.querySelectorAll('button')].find(
                    b => b.textContent.includes('משרד החינוך'));
                if (edu) {
                    ['mousedown','mouseup','click'].forEach(ev =>
                        edu.dispatchEvent(new MouseEvent(ev, {bubbles:true, cancelable:true})));
                }
            }
        """)
        try:
            await page.wait_for_url(lambda u: "edu.gov" in u or "lgn" in u, timeout=10000)
            print(f"    navigated (2nd try): {page.url}")
        except Exception:
            print(f"    still on: {page.url}")
            # נסה ניווט ישיר לURL שנמצא בכפתור
            href = await page.evaluate("""
                () => {
                    const a = document.querySelector('a[href*="edu.gov"], a[href*="lgn"]');
                    return a ? a.href : null;
                }
            """)
            if href:
                print(f"    direct nav to: {href}")
                await page.goto(href, wait_until="domcontentloaded", timeout=15000)
            else:
                await page.wait_for_timeout(3000)

    await page.screenshot(path="/tmp/edu_page.png")
    print(f"    edu page URL: {page.url}")

    # מלא פרטים
    try:
        await page.wait_for_selector("#userName", state="attached", timeout=20000)
    except Exception:
        # נסה סלקטורים חלופיים
        for sel in ['input[type="text"]', 'input[name*="user"]', 'input[id*="user"]']:
            try:
                await page.wait_for_selector(sel, state="visible", timeout=3000)
                break
            except Exception:
                continue

    print(f"    filling form...")
    # מלא username
    try:
        await page.fill("#userName", username)
    except Exception:
        await page.fill('input[type="text"]:visible', username)

    # מלא password — click קודם להסרת readonly
    try:
        await page.click("#password")
        await page.wait_for_timeout(400)
        await page.type("#password", password)
    except Exception:
        pwd = await page.query_selector('input[type="password"]:visible')
        if pwd:
            await pwd.click()
            await page.wait_for_timeout(400)
            await pwd.type(password)

    # שלח
    try:
        await page.click('button[type="submit"]', timeout=8000)
    except Exception:
        await page.evaluate("document.querySelector('form') && document.querySelector('form').submit()")

    await page.wait_for_timeout(6000)
    await page.screenshot(path="/tmp/after_login.png")
    ok = BASE in page.url and "login" not in page.url
    print(f"  login {'OK' if ok else 'FAIL'}: {page.url}")
    return ok

async def intercept_nav(page, goto_url, keywords, extra_wait=5):
    captured = {}
    async def on_response(response):
        url = response.url
        if any(k.lower() in url.lower() for k in keywords):
            try:
                body = await response.json()
                key = url.split("/")[-1].split("?")[0][:50]
                captured[key] = body
            except Exception:
                pass
    page.on("response", on_response)
    try:
        await page.goto(goto_url, wait_until="networkidle", timeout=20000)
        await wait_angular(page, 15000)
        await page.wait_for_timeout(extra_wait * 1000)
    except Exception as e:
        print(f"    nav err: {e}")
    finally:
        page.remove_listener("response", on_response)
    return captured

async def get_cdk_rows(page):
    return await page.evaluate("""
        () => {
            const rowSels = ['[role="row"]','.cdk-row','.mat-row','tr'];
            const cellSels = ['[role="cell"],[role="gridcell"]','.cdk-cell','.mat-cell','td'];
            let rows = [];
            for (const rs of rowSels) {
                rows = [...document.querySelectorAll(rs)];
                if (rows.length > 2) break;
            }
            return rows.map(row => {
                for (const cs of cellSels) {
                    const cells = [...row.querySelectorAll(cs)];
                    if (cells.length > 0) return cells.map(c => c.innerText.trim());
                }
                return [row.innerText.trim()];
            }).filter(r => r.join('').length > 0);
        }
    """)

# ── PARSERS ────────────────────────────────────────────────────
def parse_weekly(captured):
    """GetEvents.data.data.events[] -> title, description, startTime, date, student_F/L_Name"""
    weekly = {}
    raw = captured.get("GetEvents", {})
    events = raw.get("data", {}).get("data", {}).get("events", [])
    for e in events:
        if not isinstance(e, dict): continue
        date_str = e.get("date", "")[:10]  # YYYY-MM-DD
        try:
            dt = datetime.fromisoformat(date_str)
            day = DAYS.get(dt.weekday(), date_str)
        except Exception:
            day = date_str
        period   = str(e.get("startTime", ""))
        subject  = str(e.get("title", ""))
        teacher  = f"{e.get('student_F_Name','')} {e.get('student_L_Name','')}".strip()
        topic    = str(e.get("description", "")).replace("\r\n", " ").replace("\n", " ").strip()
        if day not in weekly:
            weekly[day] = []
        weekly[day].append({
            "period": period, "subject": subject,
            "teacher": teacher, "topic": topic,
            "date": date_str,
        })
    return weekly

def parse_events(captured, cdk_fallback=None):
    """GetPupilDiciplineEvents.data.diciplineEvents[] -> eventType, eventDate, hourNum, subjectName"""
    SKIP = ["סוג האירוע","תאריך","שעה","קבוצת לימוד"]
    events = []
    raw = captured.get("GetPupilDiciplineEvents", {})
    items = raw.get("data", {}).get("diciplineEvents", [])
    for e in items:
        if not isinstance(e, dict): continue
        date_str = e.get("eventDate","")[:10]
        events.append({
            "type":    str(e.get("eventType", "")),
            "date":    date_str,
            "period":  str(e.get("hourNum", "")),
            "subject": str(e.get("subjectName", "")),
            "teacher": str(e.get("teacherName", "")),
            "note":    str(e.get("remark", "") or ""),
        })
    if not events and cdk_fallback:
        for row in cdk_fallback:
            if any(k in " ".join(row) for k in SKIP): continue
            if len(row) >= 2 and any(row):
                events.append({"type":row[0],"date":row[1] if len(row)>1 else "",
                               "period":row[2] if len(row)>2 else "",
                               "subject":row[3] if len(row)>3 else "","teacher":"","note":""})
    return events

def parse_homework(captured):
    """GetPupilLessonsAndHomework.data[].hoursData[].scheduale[] -> subject_name, descClass, homeWork"""
    homework = []
    raw = captured.get("GetPupilLessonsAndHomework", {})
    days = raw.get("data", [])
    if not isinstance(days, list): return homework
    for day in days:
        if not isinstance(day, dict): continue
        date_str = day.get("date","")[:10]
        day_idx  = day.get("dayIndex", 0)
        day_name = DAYS.get(day_idx, str(day_idx))
        for hour_data in day.get("hoursData", []):
            hour_num = hour_data.get("hour", "")
            for lesson in hour_data.get("scheduale", []):
                if not isinstance(lesson, dict): continue
                topic = str(lesson.get("descClass", "") or "").strip()
                hw    = str(lesson.get("homeWork", "") or "").strip()
                if topic or hw:
                    homework.append({
                        "date":    date_str,
                        "day":     day_name,
                        "period":  str(hour_num),
                        "subject": str(lesson.get("subject_name", "")),
                        "teacher": str(lesson.get("teacher", "")),
                        "topic":   topic,
                        "hw":      hw,
                    })
    return homework

def parse_messages(captured):
    """GetMessagesInbox.data[] -> subject, sendingDate, student_F/L_name"""
    msgs = []
    raw = captured.get("GetMessagesInbox", {})
    items = raw.get("data", [])
    if not isinstance(items, list): return msgs
    for item in items[:12]:
        if not isinstance(item, dict): continue
        sender = f"{item.get('student_F_name','')} {item.get('student_L_name','')}".strip()
        date   = str(item.get("sendingDate",""))[:10]
        subj   = str(item.get("subject",""))
        msgs.append({"sender": sender, "date": date, "subject": subj})
    return msgs

# ── SCRAPE ─────────────────────────────────────────────────────
async def scrape_student(browser, username, password, name):
    print(f"\n{'='*40}\n{name}\n{'='*40}")
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    page = await context.new_page()
    data = {"name":name,"weekly_plan":{},"lesson_events":[],"homework":[],"messages":[],
            "last_updated":datetime.now().isoformat(),"error":None}
    try:
        if not await login(page, username, password):
            return {**data,"error":"login_failed"}

        # Weekly plan
        print("  [weekly plan]")
        cap = await intercept_nav(page, BASE+"/Weekly_Plan",
            keywords=["WeeklyScedule","WeeklySchedule","GetEvents","GetInitData"], extra_wait=5)
        data["weekly_plan"] = parse_weekly(cap)
        cnt = sum(len(v) for v in data["weekly_plan"].values())
        print(f"  -> {cnt} lessons in {len(data['weekly_plan'])} days")

        # Lesson events
        print("  [lesson events]")
        cap = await intercept_nav(page, BASE+"/Student_Card/4",
            keywords=["PupilCard","Discipline","DiciplineEvents","GetPupil"], extra_wait=5)
        rows = await get_cdk_rows(page)
        data["lesson_events"] = parse_events(cap, cdk_fallback=rows)
        print(f"  -> {len(data['lesson_events'])} events")

        # Homework
        print("  [homework]")
        await page.goto(BASE+"/Student_Card/5", wait_until="networkidle", timeout=15000)
        await wait_angular(page)
        hw_cap = {}
        async def on_hw(response):
            if "LessonsAndHomework" in response.url or "PupilLessons" in response.url:
                try:
                    body = await response.json()
                    hw_cap["GetPupilLessonsAndHomework"] = body
                except Exception:
                    pass
        page.on("response", on_hw)
        for txt in ["נושאי שיעור", "שיעורי בית", "נושאי שיעור ושיעורי-בית"]:
            try:
                el = await page.query_selector(f'text="{txt}"')
                if not el: el = await page.query_selector(f"text={txt}")
                if el:
                    await el.click()
                    await wait_angular(page, 8000)
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                pass
        page.remove_listener("response", on_hw)
        data["homework"] = parse_homework(hw_cap)
        print(f"  -> {len(data['homework'])} hw items")

        # Messages
        print("  [messages]")
        cap = await intercept_nav(page, BASE+"/Messages",
            keywords=["GetMessagesInbox","MessagesInbox","Inbox"], extra_wait=4)
        data["messages"] = parse_messages(cap)
        print(f"  -> {len(data['messages'])} messages")

    except Exception as e:
        import traceback
        print(f"ERROR: {e}"); data["error"] = str(e)
    finally:
        await context.close()
    return data

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--u1", required=True)
    parser.add_argument("--p1", required=True)
    parser.add_argument("--n1", default="יובל")
    parser.add_argument("--u2", default=None)
    parser.add_argument("--p2", default=None)
    parser.add_argument("--n2", default="רון")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    result = {"students":[],"generated_at":datetime.now().isoformat(),"status":"ok"}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=args.headless,
            args=["--disable-blink-features=AutomationControlled"])
        s1 = await scrape_student(browser, args.u1, args.p1, args.n1)
        result["students"].append(s1)
        if args.u2 and args.p2:
            s2 = await scrape_student(browser, args.u2, args.p2, args.n2)
            result["students"].append(s2)
        await browser.close()
    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {OUTPUT_FILE}")
    for s in result["students"]:
        print(f"  {s['name']}: {len(s['weekly_plan'])} days | "
              f"{len(s['lesson_events'])} events | "
              f"{len(s['homework'])} hw | {len(s['messages'])} msgs")

if __name__ == "__main__":
    asyncio.run(main())
