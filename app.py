"""AI Doctor — Streamlit app.
Run locally:  streamlit run app.py
Deploy free:   push this folder to GitHub -> share.streamlit.io -> New app
"""
import streamlit as st

import database as db
from medical_kb import (
    CONDITIONS, DISCLAIMER, INDIA_HELPLINES, ALL_SYMPTOM_OPTIONS,
    ai_reply, symptom_checker, _find_conditions,
)
import report_parser as rp

try:
    from openai import OpenAI
    HAS_OPENAI = True
except Exception:  # noqa: BLE001
    HAS_OPENAI = False

# ------------------------------------------------------------ setup
st.set_page_config(page_title="AI Doctor", page_icon="🩺", layout="wide",
                   initial_sidebar_state="expanded")
db.init_db()

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "openai_key" not in st.session_state:
    st.session_state.openai_key = ""

# ------------------------------------------------------------ styling
st.markdown("""
<style>
  .main-header {background: linear-gradient(135deg,#0d9488,#0e7490); padding:1.6rem 2rem;
    border-radius:16px; color:white; margin-bottom:1.2rem;}
  .main-header h1 {margin:0; font-size:1.9rem;}
  .main-header p {margin:.3rem 0 0; opacity:.92;}
  .card {background:#f0fdfa; border:1px solid #ccfbf1; border-radius:14px; padding:1rem 1.2rem; margin-bottom:.8rem;}
  .stat {background:white; border:1px solid #e5e7eb; border-radius:14px; padding:1rem; text-align:center;}
  .stat h2 {margin:0; color:#0d9488;}
  .stat p {margin:.2rem 0 0; color:#6b7280; font-size:.85rem;}
  .emg {background:#fef2f2; border:1px solid #fecaca; border-radius:14px; padding:1rem 1.2rem;}
  section[data-testid="stSidebar"] {background:#f0fdfa;}
  div.stButton > button {border-radius:10px;}
</style>
""", unsafe_allow_html=True)


def header(title, subtitle=""):
    st.markdown(f'<div class="main-header"><h1>{title}</h1><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


def go(page):
    st.session_state.page = page
    st.rerun()


# ------------------------------------------------------------ auth
def auth_page():
    header("🩺 AI Doctor", "Your personal AI health assistant — log in to continue")
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        tab_login, tab_reg = st.tabs(["🔑 Login", "📝 Register"])
        with tab_login:
            with st.form("login"):
                email = st.text_input("Email")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True, type="primary"):
                    user, err = db.login_user(email, pw)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['name']}!")
                        st.rerun()
        with tab_reg:
            with st.form("register"):
                name = st.text_input("Full name")
                email = st.text_input("Email")
                pw = st.text_input("Password (min 6 chars)", type="password")
                pw2 = st.text_input("Confirm password", type="password")
                if st.form_submit_button("Create account", use_container_width=True, type="primary"):
                    if not name or not email or not pw:
                        st.error("Please fill all fields.")
                    elif len(pw) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif pw != pw2:
                        st.error("Passwords don't match.")
                    else:
                        uid, err = db.register_user(name, email, pw)
                        if err:
                            st.error(err)
                        else:
                            user, _ = db.login_user(email, pw)
                            st.session_state.user = user
                            st.success("Account created — welcome aboard! 🎉")
                            st.rerun()
        st.info("🔒 Your data is stored securely with hashed passwords. " + DISCLAIMER)


# ------------------------------------------------------------ sidebar
def sidebar():
    u = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👋 {u['name']}")
        st.caption(u["email"])
        pages = ["Dashboard", "💬 AI Chat", "🩸 Report Analyzer", "🔍 Symptom Checker",
                 "💊 Medicine Lookup", "❤️ Vitals Tracker", "⏰ Reminders", "👤 Health Profile"]
        for p in pages:
            label = p.replace("💬 ", "").replace("🩸 ", "").replace("🔍 ", "").replace("💊 ", "") \
                     .replace("❤️ ", "").replace("⏰ ", "").replace("👤 ", "")
            if st.button(("➤ " if st.session_state.page in (p, label) else "") + p,
                         use_container_width=True,
                         key=f"nav_{p}"):
                go(label if label != p else p)
        st.divider()
        with st.expander("🤖 AI mode (optional)"):
            st.caption("Add an OpenAI API key for GPT-powered replies. Otherwise the built-in medical brain is used.")
            key = st.text_input("OpenAI API key", type="password",
                                value=st.session_state.openai_key)
            if key != st.session_state.openai_key:
                st.session_state.openai_key = key
                st.rerun()
            if st.session_state.openai_key and not HAS_OPENAI:
                st.warning("`openai` package not installed — using built-in brain.")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "Dashboard"
            st.rerun()


# ------------------------------------------------------------ dashboard
def page_dashboard():
    u = st.session_state.user
    prof = db.get_profile(u["id"])
    header("🩺 AI Doctor", f"Welcome back, {u['name']}! How are you feeling today?")
    c1, c2, c3, c4 = st.columns(4)
    chats = db.get_chats(u["id"])
    reports = db.get_reports(u["id"])
    vitals = db.get_vitals(u["id"])
    rems = db.get_reminders(u["id"])
    with c1:
        st.markdown(f'<div class="stat"><h2>{len(chats)//2}</h2><p>AI chats</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat"><h2>{len(reports)}</h2><p>Reports analyzed</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat"><h2>{len(vitals)}</h2><p>Vitals logged</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat"><h2>{len(rems)}</h2><p>Active reminders</p></div>', unsafe_allow_html=True)

    st.subheader("⚡ Quick actions")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("💬 Chat with AI Doctor", use_container_width=True): go("AI Chat")
    with q2:
        if st.button("🩸 Analyze blood report", use_container_width=True): go("Report Analyzer")
    with q3:
        if st.button("🔍 Check symptoms", use_container_width=True): go("Symptom Checker")
    with q4:
        if st.button("❤️ Log vitals", use_container_width=True): go("Vitals Tracker")

    h, w = prof.get("height_cm"), prof.get("weight_kg")
    if h and w:
        bmi = w / ((h / 100) ** 2)
        cat = ("Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else
               "Overweight" if bmi < 30 else "Obese")
        st.markdown(f'<div class="card">📊 <b>Your BMI: {bmi:.1f}</b> — {cat} '
                    f'(Height {h} cm, Weight {w} kg)</div>', unsafe_allow_html=True)
    else:
        st.info("👤 Complete your Health Profile (height & weight) to see your BMI here.")

    st.subheader("🌿 Today's health tip")
    import random
    tips = [
        "Drink 2–3 litres of water through the day — most headaches and fatigue start with dehydration.",
        "A 30-minute brisk walk controls sugar, BP, cholesterol and mood. It's the closest thing to a wonder drug.",
        "Eat dinner 2–3 hours before bed for better digestion and sleep.",
        "Too much salt hides in pickles, papads and packaged snacks — check labels.",
        "7–8 hours of sleep boosts immunity more than most supplements.",
        "Wash hands for 20 seconds — still the simplest infection prevention.",
    ]
    st.markdown(f'<div class="card">💡 {random.choice(tips)}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------ chat
def _gpt_reply(message, profile):
    client = OpenAI(api_key=st.session_state.openai_key)
    sys = ("You are a helpful AI health assistant. Give general health information only, "
           "never a definitive diagnosis. Suggest common OTC options with standard adult dosing "
           "where appropriate, always advise seeing a doctor for persistent/serious symptoms, "
           "and flag emergencies. Keep answers structured with markdown, concise but complete. "
           f"User profile: {profile}. India helplines: 112 emergency, 14416 mental health.")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": sys},
                  {"role": "user", "content": message}],
        max_tokens=800,
    )
    return resp.choices[0].message.content


def _send_chat(text):
    u = st.session_state.user
    text = text.strip()
    if not text:
        return
    db.save_chat(u["id"], "user", text)
    profile = db.get_profile(u["id"])
    profile["name"] = u["name"]
    try:
        if st.session_state.openai_key and HAS_OPENAI:
            reply, urgency = _gpt_reply(text, profile), "normal"
            suggestions = []
        else:
            r = ai_reply(text, profile)
            reply, urgency, suggestions = r["text"], r["urgency"], r["suggestions"]
    except Exception as e:  # noqa: BLE001
        reply = f"⚠️ AI service error — falling back to built-in brain.\n\n{ai_reply(text, profile)['text']}"
        urgency, suggestions = "normal", []
    db.save_chat(u["id"], "assistant", reply)
    st.session_state["last_suggestions"] = suggestions
    st.session_state["last_urgency"] = urgency


def page_chat():
    u = st.session_state.user
    header("💬 AI Doctor Chat", "Describe symptoms, ask about diseases or medicines")
    if st.session_state.get("last_urgency") == "emergency":
        st.markdown(f'<div class="emg">🚨 {INDIA_HELPLINES}</div>', unsafe_allow_html=True)

    history = db.get_chats(u["id"])
    for m in history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    sugg = st.session_state.get("last_suggestions") or []
    if sugg:
        cols = st.columns(min(len(sugg), 4))
        for i, s in enumerate(sugg[:4]):
            with cols[i]:
                if st.button(s, key=f"sugg_{i}", use_container_width=True):
                    _send_chat(s)
                    st.rerun()

    if prompt := st.chat_input("e.g. I have fever and body ache since yesterday..."):
        _send_chat(prompt)
        st.rerun()

    if history and st.button("🗑️ Clear chat history"):
        db.clear_chats(u["id"])
        st.session_state["last_suggestions"] = []
        st.rerun()


# ------------------------------------------------------------ reports
def page_reports():
    u = st.session_state.user
    header("🩸 Blood Report Analyzer", "Upload a report photo/PDF — I'll explain every value")
    tab1, tab2, tab3 = st.tabs(["📤 Upload report", "✍️ Paste values", "📁 Past reports"])

    def show_results(results, filename):
        st.markdown(rp.summarize(results))
        for r in results:
            color = {"normal": "🟢", "low": "🔻", "high": "🔺"}[r["status"]]
            with st.expander(f"{color} {r['marker']}: {r['value']} {r['unit']}  (normal {r['range']})"):
                st.markdown(r["explanation"])
                st.caption(f"💡 {r['tip']}")
        db.save_report(u["id"], filename, {"results": results})
        st.success("Report saved to your history ✅")
        st.caption(DISCLAIMER)

    with tab1:
        f = st.file_uploader("Choose a PDF or image (JPG/PNG)", type=["pdf", "png", "jpg", "jpeg"])
        if f and st.button("🔍 Analyze report", type="primary"):
            with st.spinner("Reading your report..."):
                text = rp.extract_text(f)
            if not text.strip():
                st.error("Couldn't read any text. Try a clearer photo, or paste the values in the next tab.")
            else:
                with st.expander("📄 Extracted text (for verification)"):
                    st.text(text[:3000])
                results = rp.parse_markers(text)
                show_results(results, f.name)
    with tab2:
        pasted = st.text_area("Paste values, one per line", height=150,
                              placeholder="Hemoglobin 11.2\nWBC 12000\nPlatelets 180000\nFasting Glucose 110")
        if st.button("🔍 Analyze pasted values", type="primary") and pasted.strip():
            show_results(rp.parse_pasted(pasted), "pasted-values")
    with tab3:
        reps = db.get_reports(u["id"])
        if not reps:
            st.info("No reports yet — analyze one above!")
        for rep in reps:
            with st.expander(f"📄 {rep['filename']} — {rep['created_at'][:10]}"):
                st.markdown(rp.summarize(rep["analysis"]["results"]))
                for r in rep["analysis"]["results"]:
                    color = {"normal": "🟢", "low": "🔻", "high": "🔺"}[r["status"]]
                    st.markdown(f"{color} **{r['marker']}**: {r['value']} {r['unit']} _(normal {r['range']})_")


# ------------------------------------------------------------ symptom checker
def page_symptom_checker():
    header("🔍 Symptom Checker", "Select symptoms for a guided assessment")
    sel = st.multiselect("Your symptoms", ALL_SYMPTOM_OPTIONS)
    c1, c2 = st.columns(2)
    with c1:
        duration = st.selectbox("How long?", ["Less than a day", "1–3 days", "4–7 days",
                                              "1–2 weeks", "More than 2 weeks"])
    with c2:
        severity = st.selectbox("How severe?", ["Mild", "Moderate", "Severe", "Very severe"])
    if st.button("🔍 Analyze symptoms", type="primary"):
        if not sel:
            st.warning("Select at least one symptom.")
            return
        keys = symptom_checker(sel, duration, severity)
        if not keys:
            st.info("No strong match — describe it in the AI Chat for a deeper look.")
            return
        st.subheader("Possible matches (most likely first)")
        for i, k in enumerate(keys):
            c = CONDITIONS[k]
            with st.expander(f"{'⭐ ' if i == 0 else ''}{c['name']}", expanded=(i == 0)):
                st.markdown(f"**Overview:** {c['overview']}")
                st.markdown("**💊 Common medicines (general info):**")
                for m in c["medicines"]:
                    st.markdown(f"- {m}")
                st.markdown("**👨‍⚕️ See a doctor if:**")
                for s in c["see_doctor"]:
                    st.markdown(f"- {s}")
        st.markdown(f'<div class="emg">🚨 <b>Red flags — seek urgent care for:</b> chest pain, '
                    f"trouble breathing, fainting, severe bleeding, or sudden weakness on one side. "
                    f"{INDIA_HELPLINES}</div>", unsafe_allow_html=True)
        st.caption(DISCLAIMER)


# ------------------------------------------------------------ medicine lookup
def page_medicine_lookup():
    header("💊 Medicine Lookup", "What is it for, how to take it, precautions")
    q = st.text_input("Search a disease or symptom", placeholder="e.g. cold, acidity, headache...")
    if q:
        keys = _find_conditions(q)
        if not keys:
            st.info("No match found — try the AI Chat for a broader search.")
        for k in keys[:5]:
            c = CONDITIONS[k]
            with st.expander(c["name"], expanded=(k == keys[0])):
                for m in c["medicines"]:
                    st.markdown(f"- {m}")
                st.caption("⚠️ Doses are standard adult guidance. Check with a doctor/pharmacist — "
                           "especially if pregnant, elderly, a child, or on other medicines.")
    st.divider()
    st.subheader("📋 Quick medicine facts")
    facts = {
        "Paracetamol": "Fever & pain. 500–650 mg every 6–8 hrs, max 4 g/day. Overdose harms the liver — never mix with alcohol excess.",
        "Ibuprofen": "Pain & inflammation. 200–400 mg with food. Avoid on empty stomach; caution with acidity, kidney issues, or BP meds.",
        "Cetirizine": "Allergy/cold sneezing. 10 mg once daily. May cause mild drowsiness.",
        "ORS": "Dehydration from diarrhea/vomiting/heat. Dissolve 1 sachet in 1 litre clean water; sip frequently.",
        "Antacid (Gelusil/Digene type)": "Acidity/heartburn. After meals as directed. Frequent need = see a doctor.",
        "Omeprazole": "Acidity/GERD. 20 mg before breakfast. Short courses; long-term use needs medical supervision.",
        "Azithromycin": "⚠️ Prescription antibiotic — never self-start. Wrong use breeds resistance.",
    }
    for med, fact in facts.items():
        with st.expander(med):
            st.write(fact)
    st.caption(DISCLAIMER)


# ------------------------------------------------------------ vitals
VITAL_TYPES = {
    "Blood Pressure": "mmHg", "Blood Sugar": "mg/dL", "Temperature": "°F",
    "Pulse": "bpm", "SpO2": "%", "Weight": "kg",
}


def page_vitals():
    u = st.session_state.user
    header("❤️ Vitals Tracker", "Log and watch your health numbers")
    with st.form("vital_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            vt = st.selectbox("Vital", list(VITAL_TYPES.keys()))
        if vt == "Blood Pressure":
            with c2:
                sys = st.number_input("Systolic", 50, 260, 120)
            with c3:
                dia = st.number_input("Diastolic", 30, 180, 80)
            val, unit = float(sys), f"/{int(dia)} mmHg"
        else:
            with c2:
                val = st.number_input(f"Value ({VITAL_TYPES[vt]})", 0.0, 1000.0, 0.0)
            unit = VITAL_TYPES[vt]
            with c3:
                st.write("")
        if st.form_submit_button("➕ Save reading", type="primary", use_container_width=True):
            if vt == "Blood Pressure" or val > 0:
                db.add_vital(u["id"], vt, val, unit)
                st.success("Saved ✅")
                st.rerun()
            else:
                st.warning("Enter a value first.")

    vitals = db.get_vitals(u["id"])
    if not vitals:
        st.info("No readings yet — log your first one above!")
        return
    st.subheader("📈 Trends")
    for vt in VITAL_TYPES:
        rows = [v for v in vitals if v["vtype"] == vt]
        if not rows:
            continue
        with st.expander(f"{vt} — latest: {rows[0]['value']}{rows[0]['unit']}", expanded=False):
            import pandas as pd
            df = pd.DataFrame([{"date": r["taken_at"][:10], "value": r["value"]}
                               for r in reversed(rows)])
            st.line_chart(df.set_index("date"))
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)


# ------------------------------------------------------------ reminders
def page_reminders():
    u = st.session_state.user
    header("⏰ Medicine Reminders", "Never miss a dose")
    with st.form("rem_form"):
        c1, c2 = st.columns(2)
        with c1:
            med = st.text_input("Medicine name")
            dosage = st.text_input("Dosage", placeholder="e.g. 500 mg, 1 tablet")
        with c2:
            times = st.text_input("Times", placeholder="e.g. Morning, Afternoon, Night")
            notes = st.text_input("Notes", placeholder="e.g. after food")
        if st.form_submit_button("➕ Add reminder", type="primary", use_container_width=True) and med:
            db.add_reminder(u["id"], med, dosage, times, notes)
            st.success("Reminder added ✅")
            st.rerun()
    rems = db.get_reminders(u["id"])
    if not rems:
        st.info("No reminders yet.")
    for r in rems:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f'<div class="card">💊 <b>{r["medicine"]}</b> — {r["dosage"] or ""} '
                        f'⏰ {r["times"] or ""}<br><small>{r["notes"] or ""}</small></div>',
                        unsafe_allow_html=True)
        with c2:
            if st.button("✔ Done", key=f"done_{r['id']}"):
                db.delete_reminder(r["id"], u["id"])
                st.rerun()


# ------------------------------------------------------------ profile
def page_profile():
    u = st.session_state.user
    header("👤 Health Profile", "Personalizes the AI's guidance for you")
    p = db.get_profile(u["id"])
    with st.form("profile"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Age", 0, 120, int(p.get("age") or 0))
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"],
                                  index=["", "Male", "Female", "Other"].index(p.get("gender") or ""))
            bg = st.selectbox("Blood group", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                              index=["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(p.get("blood_group") or ""))
        with c2:
            h = st.number_input("Height (cm)", 0.0, 250.0, float(p.get("height_cm") or 0))
            w = st.number_input("Weight (kg)", 0.0, 300.0, float(p.get("weight_kg") or 0))
            allergies = st.text_input("Allergies", value=p.get("allergies") or "",
                                      placeholder="e.g. penicillin, dust")
            conditions = st.text_input("Existing conditions", value=p.get("conditions") or "",
                                       placeholder="e.g. diabetes, asthma")
        if st.form_submit_button("💾 Save profile", type="primary", use_container_width=True):
            db.save_profile(u["id"], {"age": age or None, "gender": gender or None,
                                      "blood_group": bg or None,
                                      "height_cm": h or None, "weight_kg": w or None,
                                      "allergies": allergies or None, "conditions": conditions or None})
            st.success("Profile saved ✅")
    if h and w:
        bmi = w / ((h / 100) ** 2)
        st.metric("Your BMI", f"{bmi:.1f}")


# ------------------------------------------------------------ router
if st.session_state.user is None:
    auth_page()
else:
    sidebar()
    page = st.session_state.page
    {
        "Dashboard": page_dashboard,
        "AI Chat": page_chat,
        "Report Analyzer": page_reports,
        "Symptom Checker": page_symptom_checker,
        "Medicine Lookup": page_medicine_lookup,
        "Vitals Tracker": page_vitals,
        "Reminders": page_reminders,
        "Health Profile": page_profile,
    }.get(page, page_dashboard)()
    st.divider()
    st.caption("🩺 " + DISCLAIMER + f" | {INDIA_HELPLINES}")
