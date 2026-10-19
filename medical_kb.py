"""Medical knowledge base: conditions, medicines, red flags, lab ranges, chat engine.

General-information only. Not a substitute for professional medical advice.
Medicine info covers common over-the-counter options with standard adult dosing;
always check with a doctor or pharmacist, especially if pregnant, elderly,
a child, or on other medication.
"""
import re

DISCLAIMER = (
    "_This is general health information, not medical advice. "
    "If you're unsure or symptoms persist, please see a doctor._"
)

# ---------------------------------------------------------------- conditions
# Each condition: keywords for matching, overview, medicines (OTC guidance),
# self_care, see_doctor, emergency (bool)
CONDITIONS = {
    "common_cold": {
        "name": "Common Cold",
        "keywords": ["cold", "runny nose", "sneezing", "stuffy nose", "blocked nose",
                     "nasal congestion", "sniffle"],
        "overview": "A viral infection of the nose and throat. Usually mild and clears up in 7–10 days.",
        "medicines": [
            "**Paracetamol 500–650 mg** every 6–8 hours for fever/body ache (max 4 g per day).",
            "**Cetirizine 10 mg** once daily for sneezing/runny nose.",
            "**Saline nasal spray** or steam inhalation for congestion.",
            "Avoid antibiotics — they don't work on viral colds.",
        ],
        "self_care": ["Rest and drink plenty of fluids", "Warm soups and honey-ginger tea",
                      "Steam inhalation 2–3 times a day", "Gargle with warm salt water"],
        "see_doctor": ["Fever above 101°F (38.3°C) for more than 3 days", "Symptoms worse after 10 days",
                       "Difficulty breathing or wheezing", "Severe sinus pain"],
    },
    "flu": {
        "name": "Flu (Influenza)",
        "keywords": ["flu", "influenza", "body ache", "bodyache", "chills", "high fever",
                     "muscle pain all over"],
        "overview": "A contagious viral illness with sudden fever, body aches, chills and fatigue. More intense than a cold.",
        "medicines": [
            "**Paracetamol 500–650 mg** every 6–8 hours for fever and aches.",
            "**Antihistamine** (cetirizine/loratadine) if nose symptoms present.",
            "Prescription antivirals (like oseltamivir) only if a doctor prescribes within 48 hours of onset.",
        ],
        "self_care": ["Complete rest for 3–5 days", "Lots of fluids — water, ORS, soups",
                      "Isolate to avoid spreading it", "Warm baths for body aches"],
        "see_doctor": ["Difficulty breathing or chest pain", "Fever beyond 4–5 days",
                       "Dizziness, confusion, or severe weakness", "You are pregnant, elderly, or have asthma/diabetes"],
    },
    "fever": {
        "name": "Fever",
        "keywords": ["fever", "temperature", "pyrexia", "burning body"],
        "overview": "Fever is the body's defense against infection. Note the exact temperature and other symptoms.",
        "medicines": [
            "**Paracetamol 500–650 mg** every 6–8 hours (first choice for fever).",
            "Sponge with lukewarm water; avoid cold water/alcohol sponges.",
            "Do NOT take antibiotics for fever without a doctor's diagnosis.",
        ],
        "self_care": ["Rest and hydrate well", "Light clothing, cool room",
                      "Track temperature every 4–6 hours"],
        "see_doctor": ["Fever above 103°F (39.4°C)", "Fever lasting more than 3 days",
                       "Fever with rash, stiff neck, vomiting, or confusion", "Fever in infants under 3 months"],
    },
    "headache": {
        "name": "Headache / Migraine",
        "keywords": ["headache", "head ache", "migraine", "head pain", "throbbing head"],
        "overview": "Most headaches are tension-type (stress, eye strain, dehydration). Migraines throb, often one-sided, with nausea or light sensitivity.",
        "medicines": [
            "**Paracetamol 500–650 mg** or **Ibuprofen 200–400 mg** with food for tension headache.",
            "For migraine: rest in a dark quiet room; **paracetamol/ibuprofen** early helps. Frequent migraines need a doctor's preventive plan.",
        ],
        "self_care": ["Drink water — dehydration is a top trigger", "Limit screen time, take breaks",
                      "Regular sleep schedule", "Cold compress on forehead"],
        "see_doctor": ["Sudden severe 'worst ever' headache", "Headache with vision changes, weakness, or slurred speech",
                       "Headache after a head injury", "Headaches more than 3–4 times a week"],
        "emergency_words": ["worst headache", "thunderclap"],
    },
    "acidity": {
        "name": "Acidity / GERD / Heartburn",
        "keywords": ["acidity", "heartburn", "gerd", "acid reflux", "burning chest",
                     "sour burp", "gas trouble", "bloating", "indigestion"],
        "overview": "Burning in the chest or sour burps from stomach acid rising up. Often triggered by spicy/oily food, late meals, or stress.",
        "medicines": [
            "**Antacid** (e.g. Gelusil/Digene type) after meals for quick relief.",
            "**Omeprazole/Pantoprazole 20–40 mg** once daily before breakfast for frequent acidity (short courses).",
            "Avoid self-medicating long-term — see a doctor if needed daily.",
        ],
        "self_care": ["Eat smaller, earlier dinners (2–3 hrs before bed)", "Avoid spicy, fried food, excess tea/coffee, alcohol",
                      "Don't lie down right after eating", "Raise head of bed slightly"],
        "see_doctor": ["Chest pain — rule out heart issues first", "Difficulty swallowing",
                       "Vomiting blood or black stools", "Needing antacids daily for weeks"],
    },
    "diarrhea": {
        "name": "Diarrhea / Food Poisoning",
        "keywords": ["diarrhea", "diarrhoea", "loose motion", "loose motions", "food poisoning",
                     "vomiting and loose", "stomach infection"],
        "overview": "Frequent loose stools, often from contaminated food/water. The main danger is dehydration.",
        "medicines": [
            "**ORS (oral rehydration salts)** — the most important treatment. Sip after every loose motion.",
            "**Probiotic** (curd/yogurt or sachets) helps recovery.",
            "Avoid anti-diarrheal tablets (loperamide) unless a doctor advises — they can trap infection inside.",
        ],
        "self_care": ["ORS, coconut water, thin buttermilk", "Bananas, rice, toast (BRAT-type foods)",
                      "Avoid dairy, fried and spicy food for 2–3 days", "Wash hands thoroughly"],
        "see_doctor": ["Blood in stool", "Signs of dehydration: very little urine, dizziness, dry mouth",
                       "High fever with diarrhea", "Lasting more than 3 days"],
    },
    "constipation": {
        "name": "Constipation",
        "keywords": ["constipation", "hard stool", "not passing stool", "bowel not clear"],
        "overview": "Infrequent or hard stools, usually from low fiber, low water, or inactivity.",
        "medicines": [
            "**Isabgol (psyllium husk)** 1–2 tsp with warm water/milk at bedtime.",
            "**Lactulose syrup** as a gentle option if needed short-term.",
            "Avoid stimulant laxatives regularly without medical advice.",
        ],
        "self_care": ["25–30 g fiber daily: fruits, vegetables, whole grains", "2–3 litres of water daily",
                      "Daily walk or exercise", "Don't ignore the urge to go"],
        "see_doctor": ["Blood in stool", "Sudden change in bowel habits lasting weeks",
                       "Severe abdominal pain or vomiting", "Unexplained weight loss"],
    },
    "cough": {
        "name": "Cough",
        "keywords": ["cough", "coughing", "dry cough", "wet cough", "phlegm", "mucus"],
        "overview": "Dry cough = irritation/allergy/viral; wet cough with phlegm = chest congestion. Duration matters.",
        "medicines": [
            "Dry cough: **honey + warm water**, or a **dextromethorphan**-based syrup as directed.",
            "Wet cough: **steam inhalation**, warm fluids; **guaifenesin**-based expectorant as directed.",
            "Honey (1 tsp) is effective for adults — not for children under 1 year.",
        ],
        "self_care": ["Steam inhalation twice daily", "Warm turmeric milk / ginger tea",
                      "Avoid cold drinks, smoke and dust", "Honey-lemon warm water"],
        "see_doctor": ["Cough with blood", "Cough lasting more than 3 weeks",
                       "Wheezing or shortness of breath", "High fever with chest pain"],
    },
    "sore_throat": {
        "name": "Sore Throat",
        "keywords": ["sore throat", "throat pain", "pain while swallowing", "throat infection"],
        "overview": "Usually viral. Strep throat (bacterial) causes severe pain with fever and white patches — needs a doctor.",
        "medicines": [
            "**Paracetamol** for pain/fever.",
            "Throat lozenges or warm salt-water gargles 3–4 times daily.",
            "Antibiotics only if a doctor confirms bacterial infection.",
        ],
        "self_care": ["Warm salt-water gargle", "Honey-ginger tea", "Avoid shouting, smoking, cold drinks"],
        "see_doctor": ["White patches on tonsils with high fever", "Difficulty swallowing or breathing",
                       "Throat pain beyond a week", "Rash with sore throat"],
    },
    "allergy": {
        "name": "Allergies (Dust/Pollen)",
        "keywords": ["allergy", "dust allergy", "sneezing every morning", "itchy eyes",
                     "skin allergy", "rashes itching", "hives"],
        "overview": "Overreaction of the immune system to dust, pollen, or foods. Antihistamines control it well.",
        "medicines": [
            "**Cetirizine 10 mg** or **Loratadine 10 mg** once daily.",
            "For itchy skin: **calamine lotion**; avoid scratching.",
            "Severe swelling/breathing trouble = emergency, not a tablet situation.",
        ],
        "self_care": ["Keep bedroom dust-free; wash pillow covers weekly", "Saline nasal rinse",
                      "Note and avoid your triggers"],
        "see_doctor": ["Swelling of lips/tongue or breathing difficulty (emergency)",
                       "Symptoms daily despite antihistamines", "Suspected food allergy with severe reactions"],
    },
    "uti": {
        "name": "Urinary Tract Infection (UTI)",
        "keywords": ["uti", "urine infection", "burning urination", "burning while urinating",
                     "frequent urination"],
        "overview": "Burning or pain while urinating, frequent urge, sometimes lower abdominal pain. Needs proper diagnosis.",
        "medicines": [
            "Drink lots of water; **cranberry** products may help mildly.",
            "UTIs usually need **prescription antibiotics** — see a doctor for a urine test rather than self-medicating.",
        ],
        "self_care": ["Drink 2–3 litres of water", "Don't hold urine", "Urinate after intercourse",
                      "Wipe front to back"],
        "see_doctor": ["Fever with UTI symptoms", "Back/flank pain", "Blood in urine",
                       "Recurrent UTIs — get evaluated"],
    },
    "fungal_skin": {
        "name": "Fungal Skin Infection (Ringworm)",
        "keywords": ["ringworm", "fungal infection", "itchy skin patch", "skin fungus",
                     "jock itch", "athlete foot"],
        "overview": "Itchy, red, ring-shaped patches — common in warm, sweaty areas. Spreads by contact.",
        "medicines": [
            "**Clotrimazole 1% cream** applied twice daily for 2–4 weeks (continue 1 week after clearing).",
            "Keep the area clean and dry; antifungal powder helps.",
        ],
        "self_care": ["Keep area dry; change sweaty clothes", "Don't share towels",
                      "Wear loose cotton clothing"],
        "see_doctor": ["Spreading despite 2 weeks of cream", "Infection on scalp or nails",
                       "Pus or severe pain (may be bacterial)"],
    },
    "body_ache": {
        "name": "Body Ache / Muscle Pain",
        "keywords": ["body ache", "bodyache", "muscle pain", "muscle strain", "sprain",
                     "neck pain", "shoulder pain"],
        "overview": "Often from exertion, poor posture, or viral illness. Most settle in a few days.",
        "medicines": [
            "**Paracetamol** or **Ibuprofen 200–400 mg** with food for pain.",
            "**Diclofenac gel** for local muscle/joint pain.",
            "Muscle relaxants only on a doctor's prescription.",
        ],
        "self_care": ["Rest the strained muscle 24–48 hrs", "Ice for fresh injury, heat for stiffness",
                      "Gentle stretching once pain eases", "Good posture and ergonomics"],
        "see_doctor": ["Pain after significant trauma", "Numbness, weakness, or tingling",
                       "Pain not improving in a week", "Swelling that keeps increasing"],
    },
    "back_pain": {
        "name": "Lower Back Pain",
        "keywords": ["back pain", "lower back", "backache", "slipped disc", "sciatica"],
        "overview": "Very common — usually muscle strain or posture-related. Most cases improve within 2–6 weeks.",
        "medicines": [
            "**Ibuprofen 200–400 mg** with food or **paracetamol** for pain.",
            "Topical **diclofenac gel** for local relief.",
        ],
        "self_care": ["Stay gently active — bed rest beyond a day worsens it", "Heat pack 15–20 min",
                      "Core-strengthening once acute pain settles", "Avoid heavy lifting, mind posture"],
        "see_doctor": ["Pain shooting down the leg with numbness", "Loss of bladder/bowel control (emergency)",
                       "Pain after a fall/accident", "Fever with back pain", "No improvement in 6 weeks"],
    },
    "insomnia": {
        "name": "Insomnia / Poor Sleep",
        "keywords": ["insomnia", "can't sleep", "cannot sleep", "sleepless", "sleep problem",
                     "sleeping pills"],
        "overview": "Difficulty falling or staying asleep. Sleep hygiene fixes most cases without pills.",
        "medicines": [
            "Avoid sleeping pills without a doctor — they cause dependence.",
            "**Melatonin 1–3 mg** occasionally may help jet lag-type issues; discuss with a doctor first.",
        ],
        "self_care": ["Fixed sleep/wake time, even weekends", "No screens 1 hr before bed",
                      "No caffeine after 2 pm", "Cool, dark, quiet bedroom",
                      "Daylight exposure and exercise during the day"],
        "see_doctor": ["Insomnia beyond 3–4 weeks", "Loud snoring with gasping (possible sleep apnea)",
                       "Daytime sleepiness affecting work/driving", "Anxiety/depression alongside"],
    },
    "anemia": {
        "name": "Anemia (Low Hemoglobin)",
        "keywords": ["anemia", "anaemia", "low hemoglobin", "low hb", "weakness tired",
                     "pale", "dizzy spells"],
        "overview": "Low hemoglobin reduces oxygen delivery — fatigue, paleness, dizziness. Iron deficiency is the commonest cause.",
        "medicines": [
            "**Iron + folic acid** supplements as a doctor advises (best absorbed on empty stomach with vitamin C).",
            "Don't self-start iron long-term without checking levels — get a CBC first.",
        ],
        "self_care": ["Iron-rich foods: leafy greens, dates, jaggery, meat, lentils",
                      "Vitamin C (lemon, amla) with meals boosts iron absorption",
                      "Avoid tea/coffee right with meals — they block iron"],
        "see_doctor": ["Hb below 10 g/dL", "Fainting or chest pain", "Heavy menstrual bleeding as cause",
                       "No improvement after 3 months of treatment"],
    },
    "mouth_ulcer": {
        "name": "Mouth Ulcers",
        "keywords": ["mouth ulcer", "ulcer in mouth", "canker sore"],
        "overview": "Painful small sores from stress, vitamin deficiency, or cheek bites. Heal in 7–14 days.",
        "medicines": [
            "**Topical anesthetic gel** (e.g. lignocaine-based) before meals.",
            "**Vitamin B-complex** if recurrent.",
        ],
        "self_care": ["Avoid spicy, acidic foods till healed", "Rinse with warm salt water",
                      "Don't touch/pick at it"],
        "see_doctor": ["Ulcers lasting more than 3 weeks", "Very large or many ulcers",
                       "Recurring constantly — check B12/iron"],
    },
    "hypertension": {
        "name": "High Blood Pressure (Hypertension)",
        "keywords": ["high bp", "hypertension", "blood pressure high", "bp high"],
        "overview": "Often symptomless — the 'silent killer'. Diagnosed by repeated readings ≥140/90 mmHg.",
        "medicines": [
            "BP medicines are **prescription-only and lifelong** — never start/stop on your own.",
            "If prescribed, take daily at the same time; don't skip when 'feeling fine'.",
        ],
        "self_care": ["Cut salt below 5 g/day", "30 min brisk walk daily", "Maintain healthy weight",
                      "Limit alcohol, quit smoking", "Manage stress and sleep"],
        "see_doctor": ["BP ≥180/120 with chest pain, breathlessness, vision changes (emergency)",
                       "Newly detected high readings — confirm with a doctor", "For medicine review yearly"],
    },
    "diabetes": {
        "name": "Diabetes / High Blood Sugar",
        "keywords": ["diabetes", "sugar high", "blood sugar", "diabetic"],
        "overview": "High blood glucose from insulin problems. Early stages are reversible with lifestyle.",
        "medicines": [
            "Diabetes medicines are **prescription-only** — type and dose need a doctor's evaluation.",
            "Never adjust doses based on one reading.",
        ],
        "self_care": ["Cut sugary drinks and refined carbs", "Walk 30 min after meals",
                      "Maintain healthy weight", "Check sugar as your doctor advises"],
        "see_doctor": ["Fasting sugar repeatedly >126 or HbA1c ≥6.5", "Excessive thirst, urination, weight loss",
                       "Blurry vision or numb feet", "Sugar >300 with nausea/confusion (emergency)"],
    },
    "dehydration": {
        "name": "Dehydration / Heat Exhaustion",
        "keywords": ["dehydration", "dehydrated", "heat stroke", "heat exhaustion",
                     "less urine", "dry mouth"],
        "overview": "Fluid loss from heat, vomiting, or diarrhea. Watch for dark urine, dizziness, dry mouth.",
        "medicines": ["**ORS** — small frequent sips. The cornerstone treatment."],
        "self_care": ["Move to shade/cool place", "Sip ORS, water, coconut water",
                      "Loosen clothing, cool the skin"],
        "see_doctor": ["Confusion or fainting", "No urine for 8+ hours", "Rapid heartbeat",
                       "Hot dry skin with high fever (heatstroke — emergency)"],
    },
    "migraine_detail": {
        "name": "Migraine",
        "keywords": ["migraine attack", "one side headache", "aura", "nausea with headache",
                     "light sensitivity headache"],
        "overview": "Throbbing, often one-sided headache with nausea and light/sound sensitivity. Attacks last hours to days.",
        "medicines": [
            "Take **paracetamol/ibuprofen** at the first sign — early treatment works best.",
            "Triptans are prescription-only for confirmed migraine — ask a doctor if attacks are frequent.",
        ],
        "self_care": ["Dark, quiet room during attacks", "Track triggers: sleep loss, skipping meals, stress, certain foods",
                      "Regular meals and sleep prevent attacks", "Caffeine in small amounts may help some people"],
        "see_doctor": ["New severe headaches after age 50", "Attacks more than 4 times a month",
                       "Weakness, vision loss, or speech trouble with headache (emergency)"],
    },
}

# ------------------------------------------------------------ emergency words
EMERGENCY_PATTERNS = [
    (r"chest pain|pressure in chest|tightness in chest", "Chest pain can signal a heart attack. **Call emergency (112 in India) or go to the ER now.** Don't drive yourself. Chew **aspirin 300 mg** only if a doctor previously advised it for you and you're not allergic."),
    (r"(can't|cannot|difficulty|trouble|shortness of|hard to)\s+(breathe|breathing|breath)", "Trouble breathing is an emergency. **Call 112 / go to the ER immediately.** Sit upright, stay calm, don't lie flat."),
    (r"stroke|face droop|slurred speech|one side (weak|numb)|paralysis", "Possible **stroke** — remember **FAST**: Face drooping, Arm weakness, Speech difficulty = **Time to call 112 immediately**. Every minute counts."),
    (r"suicid|kill myself|end my life|self.?harm", "I'm really glad you told me. Please reach out right now — call a trusted person, or in India call the **Tele MANAS helpline 14416** or **112**. You matter, and help is available 24×7."),
    (r"heavy bleeding|blood won't stop|unconscious|fainted and|seizure|convulsion", "This needs urgent care. **Call 112 or go to the nearest emergency department now.**"),
    (r"snake bite|dog bite|scorpion", "Animal bites/stings need prompt medical care — **go to a hospital now** for proper wound care and vaccines/anti-venom. Wash the wound with soap and water meanwhile."),
    (r"burn.*(severe|large|blister)|acid burn", "For serious burns: cool under running water 20 min, cover loosely, and **go to the ER**. Don't apply toothpaste/oil."),
    (r"poison|overdose|consumed phenyl|drank acid", "Possible poisoning — **call 112 / go to ER immediately**. Don't induce vomiting unless told to. Carry the container/packet with you."),
]

INDIA_HELPLINES = "Emergency: **112** (all-India) | Ambulance: **108** | Mental health (Tele MANAS): **14416**"

GREETING_WORDS = ["hi", "hello", "hey", "namaste", "good morning", "good evening", "good afternoon"]

# --------------------------------------------------------------- chat engine
def _find_conditions(text: str):
    text = text.lower()
    scored = []
    for key, cond in CONDITIONS.items():
        hits = sum(1 for kw in cond["keywords"] if kw in text)
        if hits:
            scored.append((hits, key))
    scored.sort(reverse=True)
    return [k for _, k in scored]


def _emergency_check(text: str):
    t = text.lower()
    for pattern, advice in EMERGENCY_PATTERNS:
        if re.search(pattern, t):
            return advice
    return None


def _format_condition(key: str, profile: dict) -> str:
    c = CONDITIONS[key]
    allergy_note = ""
    if profile.get("allergies"):
        allergy_note = f"\n\n⚠️ You noted allergies ({profile['allergies']}) — mention them to your pharmacist before taking any medicine."
    parts = [
        f"### {c['name']}",
        c["overview"],
        "",
        "**💊 Common medicines (general info):**",
    ]
    parts += [f"- {m}" for m in c["medicines"]]
    parts += ["", "**🏠 Self-care:**"] + [f"- {s}" for s in c["self_care"]]
    parts += ["", "**👨‍⚕️ See a doctor if:**"] + [f"- {s}" for s in c["see_doctor"]]
    if allergy_note:
        parts.append(allergy_note)
    parts += ["", DISCLAIMER]
    return "\n".join(parts)


def _format_brief(key: str) -> str:
    c = CONDITIONS[key]
    return f"**{c['name']}** — {c['overview']}"


def ai_reply(message: str, profile: dict = None) -> dict:
    """Return dict(text=..., urgency='normal'|'high'|'emergency', suggestions=[...])."""
    profile = profile or {}
    text = message.strip()
    low = text.lower()

    emg = _emergency_check(low)
    if emg:
        return {
            "text": f"🚨 **This sounds urgent.**\n\n{emg}\n\n{INDIA_HELPLINES}\n\n{DISCLAIMER}",
            "urgency": "emergency",
            "suggestions": ["Chest pain", "Difficulty breathing", "High fever remedies"],
        }

    if any(low == g or low.startswith(g + " ") for g in GREETING_WORDS) or len(low) < 4:
        name = f" {profile.get('name')}" if profile.get("name") else ""
        return {
            "text": (
                f"Hello{name}! 👋 I'm your AI health assistant.\n\n"
                "Tell me your **symptoms** (e.g. *\"fever and body ache since 2 days\"*), "
                "ask about a **disease** (*\"what is acidity?\"*), a **medicine** (*\"medicine for cold\"*), "
                "or upload a **blood report** from the Report Analyzer page.\n\n"
                f"{DISCLAIMER}"
            ),
            "urgency": "normal",
            "suggestions": ["I have fever and cold", "Medicine for headache", "What is acidity?", "Analyze my blood report"],
        }

    if any(w in low for w in ["thank", "thanks", "dhanyavad", "shukriya"]):
        return {"text": "You're welcome! 🌿 Take care, and I'm here if you need anything else.",
                "urgency": "normal", "suggestions": ["I have a new symptom", "Medicine lookup"]}

    matches = _find_conditions(low)
    is_medicine_q = any(w in low for w in ["medicine", "tablet", "drug", "dose", "dosage", "treatment", "cure", " dawai", "dawai"])

    if matches:
        best = matches[0]
        if len(matches) > 1 and not is_medicine_q:
            briefs = "\n".join(f"{i+1}. {_format_brief(k)}" for i, k in enumerate(matches[:3]))
            follow = (
                f"Based on what you described, here are the closest matches:\n\n{briefs}\n\n"
                f"Here's detailed guidance for the most likely one:\n\n"
                + _format_condition(best, profile)
                + "\n\n💬 **To narrow it down, tell me:** how long have you had this? Any fever, pain level, or other symptoms?"
            )
            return {"text": follow, "urgency": "normal",
                    "suggestions": [CONDITIONS[k]["name"] for k in matches[:3]]}
        return {"text": _format_condition(best, profile)
                + "\n\n💬 Anything else — e.g. how long you've had it, or other symptoms?",
                "urgency": "normal",
                "suggestions": ["How long is it serious?", "Medicine for " + CONDITIONS[best]["name"].lower(),
                                "I have another symptom"]}

    if any(w in low for w in ["report", "blood test", "lab report", "cbc"]):
        return {"text": "🩸 For blood reports, use the **Report Analyzer** page in the sidebar — upload your report photo/PDF or paste the values, and I'll explain every marker in detail.",
                "urgency": "normal", "suggestions": ["I have fever", "What is anemia?"]}

    if any(w in low for w in ["bmi", "body mass"]):
        return {"text": "You can calculate your BMI on the **Dashboard** — just save your height and weight in your Profile first!",
                "urgency": "normal", "suggestions": ["I have a headache"]}

    return {
        "text": (
            "I want to help accurately, but I didn't catch enough detail. 🤔\n\n"
            "Try describing it like: *\"sore throat and mild fever since yesterday\"* or *\"burning in chest after meals\"*.\n\n"
            "Or pick a topic below. " + DISCLAIMER
        ),
        "urgency": "normal",
        "suggestions": ["Fever", "Cold and cough", "Acidity", "Headache", "Diarrhea", "Skin allergy"],
    }


def symptom_checker(selected_symptoms, duration, severity):
    """Score conditions against selected symptom keywords. Returns list of (key, score)."""
    scored = []
    for key, cond in CONDITIONS.items():
        score = sum(1 for kw in cond["keywords"] if kw in [s.lower() for s in selected_symptoms])
        if score:
            if severity in ("Severe", "Very severe"):
                score += 0.5
            if duration in ("More than 2 weeks",):
                score += 0.5
            scored.append((score, key))
    scored.sort(reverse=True)
    return [k for _, k in scored[:5]]


ALL_SYMPTOM_OPTIONS = sorted({
    kw for c in CONDITIONS.values() for kw in c["keywords"]
    if len(kw.split()) <= 3
})


# ------------------------------------------------------------ lab ranges
# value: (low, high) typical adult reference; explain_low / explain_high plain language
LAB_MARKERS = {
    "Hemoglobin": {
        "aliases": ["hemoglobin", "haemoglobin", "hb%", "hb"],
        "unit": "g/dL", "range": (12.0, 17.5),
        "low": "Low hemoglobin suggests **anemia** — common causes: iron deficiency, B12/folate deficiency, blood loss. Symptoms: fatigue, paleness, dizziness.",
        "high": "High hemoglobin can occur with dehydration, smoking, or living at altitude. Rarely, bone-marrow conditions — discuss with a doctor if very high.",
        "tip": "Iron-rich foods (leafy greens, dates, lentils) + vitamin C help maintain healthy levels.",
    },
    "WBC": {
        "aliases": ["wbc", "tlc", "total leukocyte", "leucocyte", "white blood cell"],
        "unit": "/µL", "range": (4000, 11000),
        "low": "Low WBC (**leukopenia**) may follow viral infections, or rarely bone-marrow/vitamin issues — needs medical review.",
        "high": "High WBC (**leukocytosis**) usually means the body is fighting a **bacterial infection or inflammation**.",
        "tip": "A single high/low value with symptoms like fever should be reviewed by a doctor.",
    },
    "Platelets": {
        "aliases": ["platelet", "thrombocyte"],
        "unit": "/µL", "range": (150000, 450000),
        "low": "Low platelets (**thrombocytopenia**) raise bleeding risk — seen in dengue, viral fevers, B12 deficiency. Avoid injury-prone activity; see a doctor.",
        "high": "High platelets (**thrombocytosis**) often follow infection/inflammation or iron deficiency; very high values need evaluation.",
        "tip": "In dengue/viral fever, doctors track the platelet trend, not just one value.",
    },
    "RBC": {
        "aliases": ["rbc count", "red blood cell", "rbc -"],
        "unit": "million/µL", "range": (4.0, 5.5),
        "low": "Low RBC count usually goes with anemia — less oxygen delivery, causing fatigue.",
        "high": "High RBC can reflect dehydration or, rarely, polycythemia — confirm with a doctor.",
        "tip": "Read together with hemoglobin and hematocrit.",
    },
    "Hematocrit": {
        "aliases": ["hematocrit", "haematocrit", "hct", "pcv"],
        "unit": "%", "range": (36, 54),
        "low": "Low hematocrit mirrors anemia — the blood carries less oxygen.",
        "high": "High hematocrit suggests dehydration or excess red cells.",
        "tip": "Dehydration falsely raises it — hydrate normally before tests.",
    },
    "MCV": {
        "aliases": ["mcv"],
        "unit": "fL", "range": (80, 100),
        "low": "Low MCV (small red cells) points to **iron deficiency**.",
        "high": "High MCV (large red cells) points to **B12 or folate deficiency**, thyroid or liver issues.",
        "tip": "MCV helps identify the *type* of anemia.",
    },
    "MCH": {
        "aliases": ["mch "],
        "unit": "pg", "range": (27, 33),
        "low": "Low MCH often accompanies iron deficiency.",
        "high": "High MCH can occur with B12/folate deficiency.",
        "tip": "Interpret with MCV and hemoglobin.",
    },
    "ESR": {
        "aliases": ["esr"],
        "unit": "mm/hr", "range": (0, 20),
        "low": "Low ESR is generally not a concern.",
        "high": "High ESR is a **non-specific inflammation marker** — infections, arthritis, autoimmune conditions raise it. Needs clinical context.",
        "tip": "ESR alone never diagnoses anything — doctors pair it with symptoms and other tests.",
    },
    "Fasting Glucose": {
        "aliases": ["fasting glucose", "fasting blood sugar", "fbs", "glucose fasting", "blood sugar fasting"],
        "unit": "mg/dL", "range": (70, 100),
        "low": "Below 70 = **hypoglycemia** — shakiness, sweating, confusion. Have fast sugar/juice; diabetics on medication should inform their doctor.",
        "high": "100–125 = prediabetes range; ≥126 on repeat = diabetes range. Confirm with HbA1c and a doctor.",
        "tip": "True fasting = 8–12 hours, water only.",
    },
    "Postprandial Glucose": {
        "aliases": ["pp glucose", "postprandial", "ppbs", "post prandial", "glucose pp"],
        "unit": "mg/dL", "range": (70, 140),
        "low": "Unusually low after meals is uncommon — discuss with a doctor if symptomatic.",
        "high": "Above 140 after meals suggests impaired glucose tolerance; ≥200 is in the diabetes range. Confirm with a doctor.",
        "tip": "Measured 2 hours after a meal.",
    },
    "HbA1c": {
        "aliases": ["hba1c", "glycated hemoglobin", "glycosylated"],
        "unit": "%", "range": (4.0, 5.6),
        "low": "Very low HbA1c is uncommon — discuss with a doctor.",
        "high": "5.7–6.4% = **prediabetes**; ≥6.5% = **diabetes** range. Lifestyle changes can reverse prediabetes — see a doctor for a plan.",
        "tip": "Reflects average sugar over ~3 months.",
    },
    "Total Cholesterol": {
        "aliases": ["total cholesterol", "cholesterol total", "serum cholesterol"],
        "unit": "mg/dL", "range": (0, 200),
        "low": "Very low cholesterol is rarely a problem on its own.",
        "high": "Above 200 = high; raises long-term heart risk, especially with high LDL. Diet, exercise, and sometimes medication bring it down.",
        "tip": "Fasting 9–12 hrs gives the most accurate lipid profile.",
    },
    "LDL": {
        "aliases": ["ldl", "ldl cholesterol"],
        "unit": "mg/dL", "range": (0, 100),
        "low": "Low LDL is generally good.",
        "high": "'Bad' cholesterol — above 100 is above optimal; above 160 is high. Main driver of artery blockage risk.",
        "tip": "Cut fried food, ghee/butter excess; add oats, nuts, and exercise.",
    },
    "HDL": {
        "aliases": ["hdl", "hdl cholesterol"],
        "unit": "mg/dL", "range": (40, 100),
        "low": "Below 40 = low 'good' cholesterol — exercise raises it.",
        "high": "Higher HDL is protective for the heart.",
        "tip": "Brisk walking 30 min daily is the best HDL booster.",
    },
    "Triglycerides": {
        "aliases": ["triglyceride", "triglycerides", "tgl"],
        "unit": "mg/dL", "range": (0, 150),
        "low": "Low triglycerides are generally fine.",
        "high": "Above 150 = high; linked to sugary diet, alcohol, and heart risk. Above 500 needs prompt medical attention.",
        "tip": "Cut sugar, refined carbs, and alcohol — the fastest way to lower it.",
    },
    "Creatinine": {
        "aliases": ["creatinine", "serum creatinine"],
        "unit": "mg/dL", "range": (0.6, 1.3),
        "low": "Low creatinine usually just reflects low muscle mass — not concerning.",
        "high": "High creatinine suggests the **kidneys aren't filtering well** — dehydration, medicines, or kidney disease. Needs a doctor's review with eGFR.",
        "tip": "Avoid NSAID painkillers (ibuprofen/diclofenac) excess — they strain kidneys.",
    },
    "Urea": {
        "aliases": ["urea", "blood urea", "bun"],
        "unit": "mg/dL", "range": (15, 40),
        "low": "Low urea is rarely concerning.",
        "high": "High urea can mean dehydration, high protein intake, or reduced kidney function — interpret with creatinine.",
        "tip": "Dehydration is the commonest benign cause.",
    },
    "SGOT": {
        "aliases": ["sgot", "ast"],
        "unit": "U/L", "range": (10, 40),
        "low": "Low SGOT/AST is not concerning.",
        "high": "Elevated liver enzyme — possible liver inflammation from fatty liver, alcohol, medicines, or infection. Needs medical review.",
        "tip": "Avoid alcohol and unnecessary medicines till reviewed.",
    },
    "SGPT": {
        "aliases": ["sgpt", "alt"],
        "unit": "U/L", "range": (7, 56),
        "low": "Low SGPT/ALT is not concerning.",
        "high": "Elevated liver enzyme — most commonly **fatty liver**; also alcohol, medicines, hepatitis. Needs medical review.",
        "tip": "Weight loss and cutting alcohol/sugar often normalize mild elevations.",
    },
    "Bilirubin": {
        "aliases": ["bilirubin", "total bilirubin"],
        "unit": "mg/dL", "range": (0.1, 1.2),
        "low": "Low bilirubin is not concerning.",
        "high": "High bilirubin causes **jaundice** (yellow eyes/skin) — liver or bile-duct issue, or excess red-cell breakdown. See a doctor promptly.",
        "tip": "Yellow eyes + dark urine + pale stools = see a doctor soon.",
    },
    "TSH": {
        "aliases": ["tsh"],
        "unit": "mIU/L", "range": (0.4, 4.0),
        "low": "Low TSH with symptoms suggests **hyperthyroidism** (overactive thyroid) — weight loss, palpitations, anxiety.",
        "high": "High TSH suggests **hypothyroidism** (underactive thyroid) — weight gain, fatigue, hair fall. Usually managed well with thyroxine prescribed by a doctor.",
        "tip": "Take thyroid medicine empty stomach, 30–60 min before breakfast.",
    },
    "Vitamin D": {
        "aliases": ["vitamin d", "25-oh", "25 oh vitamin"],
        "unit": "ng/mL", "range": (30, 100),
        "low": "Below 20 = deficiency; 20–30 = insufficiency. Causes bone pain, fatigue, low immunity. Very common in India.",
        "high": "Above 100 is excessive — usually from over-supplementation. Don't megadose without a doctor.",
        "tip": "15–20 min morning sunlight + supplements as a doctor advises.",
    },
    "Vitamin B12": {
        "aliases": ["vitamin b12", "b12"],
        "unit": "pg/mL", "range": (200, 900),
        "low": "Low B12 causes fatigue, numbness/tingling, memory issues — common in vegetarians.",
        "high": "High B12 is usually from supplements — generally not dangerous.",
        "tip": "Vegetarians should check B12 yearly.",
    },
    "Calcium": {
        "aliases": ["calcium", "serum calcium"],
        "unit": "mg/dL", "range": (8.5, 10.5),
        "low": "Low calcium can cause muscle cramps and tingling — often with low vitamin D.",
        "high": "High calcium needs medical evaluation (parathyroid, vitamin D excess, etc.).",
        "tip": "Dairy, ragi, sesame seeds are good sources.",
    },
    "Sodium": {
        "aliases": ["sodium", "serum sodium", "na+"],
        "unit": "mEq/L", "range": (135, 145),
        "low": "Low sodium causes confusion, nausea — can follow excess water intake, some medicines, or illness.",
        "high": "High sodium usually means dehydration — drink water; persistent elevation needs a doctor.",
        "tip": "Don't chug extreme amounts of water rapidly.",
    },
    "Potassium": {
        "aliases": ["potassium", "serum potassium", "k+"],
        "unit": "mEq/L", "range": (3.5, 5.0),
        "low": "Low potassium causes muscle weakness/cramps — from vomiting, diarrhea, or diuretics.",
        "high": "High potassium can disturb heart rhythm — needs prompt medical attention, especially with kidney disease.",
        "tip": "Bananas and coconut water help mild lows.",
    },
}
