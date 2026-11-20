"""
J.A.R.V.I.S. High-Performance Core Engine & 24/7 Autonomous Cloud Scheduler
Integrates real-time document search, Gemini AI, and autonomous cloud reminders.
"""

import os
import sys
import json
import time
import threading
import smtplib
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(CURR_DIR, "Meeting Notes")):
    LOCAL_ROOT = CURR_DIR
elif os.path.exists(os.path.join(CURR_DIR, "..", "Meeting Notes")):
    LOCAL_ROOT = os.path.abspath(os.path.join(CURR_DIR, ".."))
elif os.path.exists(os.path.join(CURR_DIR, "..", "..", "Meeting Notes")):
    LOCAL_ROOT = os.path.abspath(os.path.join(CURR_DIR, "..", ".."))
else:
    LOCAL_ROOT = CURR_DIR

for candidate_env in [
    os.path.join(LOCAL_ROOT, ".env"),
    os.path.join(CURR_DIR, ".env"),
    os.path.join(CURR_DIR, "..", ".env")
]:
    if os.path.exists(candidate_env):
        load_dotenv(candidate_env)
        break

def get_eastern_now():
    """Returns current datetime in US/Eastern (Cincinnati, OH / EDT/EST)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        # Fallback to EDT (UTC-4 in Sep-Nov)
        return datetime.now(timezone(timedelta(hours=-4)))

app = Flask(__name__, template_folder=os.path.join(LOCAL_ROOT, "templates") if os.path.exists(os.path.join(LOCAL_ROOT, "templates")) else "templates")

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,X-Requested-With"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS,PUT,DELETE"
    return response

# Team Roster Configuration
DEFAULT_ROSTER = {
    "team": [
        {"name": "Ro", "email": "rohendrr@mail.uc.edu", "role": "Documentation & AI Integration"},
        {"name": "Aron", "email": "josepha7@mail.uc.edu", "role": "Budget, Finance & Procurement"},
        {"name": "Eli", "email": "radabaer@mail.uc.edu", "role": "Hardware & Component Inventory"},
        {"name": "Shyam", "email": "patel8s7@mail.uc.edu", "role": "Timeline & Gantt Architecture"}
    ]
}

# Master Cloud Scheduled Reminders
CLOUD_SCHEDULED_JOBS = [
    # --- SPONSOR / TEAM LEAD DOC TO JACOB CRESS (Sept 15, 2026) ---
    {
        "id": "cress_sponsor_doc_deadline",
        "target_time": datetime(2026, 9, 15, 9, 0, 0),
        "subject": "🚨 TODAY: Submit Team Lead / Sponsor 101 Document to Professor Jacob Cress",
        "message": (
            "Hi Team,\n\n"
            "Today is the deadline to submit our introductory team lead and project 101 document to Professor Jacob Cress.\n\n"
            "Please review the neutral project description ('automated user-influenced beverage dispensing table') and ensure all team details are finalized."
        ),
        "dispatched": False
    },

    # --- TEAM DESIGN PROPOSAL (Sept 23, 2026) ---
    {
        "id": "design_proposal_1w_before",
        "target_time": datetime(2026, 9, 16, 9, 0, 0),
        "subject": "📅 1-WEEK ALERT: Team Design Proposal Due Sept 23 (Quotes + Visual Drawings)",
        "message": (
            "Hi Team,\n\n"
            "This is the 1-WEEK warning for our comprehensive Team Design Proposal due Wednesday, September 23rd!\n\n"
            "Deliverables Required per Section Lead:\n"
            "• Electrical (Eli): PLC specs, 24V power supply, relays, high-wall wiring schematic\n"
            "• Lift Mechanism (Eli & Shyam): Linear rail, stepper motor, pulley/lead screw layout drawing\n"
            "• Bottling & Fluidics (Ro & Aron): 8-bottle array, peristaltic pumps, inline flow regulators, cork seals\n"
            "• Ice & Thermal (Shyam & Eli): Reusable metal ice cubes vs. mini chiller trade study\n"
            "• Finance (Aron): Itemized vendor quotes and pre-approval purchase request form"
        ),
        "dispatched": False
    },
    {
        "id": "design_proposal_1d_before",
        "target_time": datetime(2026, 9, 22, 9, 0, 0),
        "subject": "🚨 FINAL 24H ALERT: Team Design Proposal Due Tomorrow (Sept 23)",
        "message": (
            "Hi Team,\n\n"
            "Tomorrow, Wednesday, September 23rd, is the deadline for our complete Team Design Proposal!\n\n"
            "Ensure your section's material list with quotes and visual CAD/drawings are ready to compile before our 1:30 PM class."
        ),
        "dispatched": False
    },

    # --- MILESTONE 1: 5-MINUTE PITCH DECK VIDEO (Sept 28, 2026) ---
    {
        "id": "pitch_video_1w_before",
        "target_time": datetime(2026, 9, 21, 9, 0, 0),
        "subject": "📅 1-WEEK ALERT: 5-Minute Pitch Deck Video Due Sept 28 ($600 Team Payout)",
        "message": (
            "Hi Team,\n\n"
            "This is our 1-WEEK countdown reminder for Milestone 1 of the CEAS Innovation Challenge!\n\n"
            "🎯 Deliverable: 5-Minute Recorded Pitch Deck Video\n"
            "📅 Due Date: Monday, September 28, 2026 @ 11:59 PM\n"
            "💰 Reward: Unlocks $150/person ($600.00 team total) used directly as active prototype budget!\n\n"
            "Key Elements Required in Video:\n"
            "• Problem statement & target market (craft breweries & cigar lounges)\n"
            "• 8-bottle table on wheels with precision linear rail lift\n"
            "• Industrial PLC control, peristaltic dosing, and sanitary fluidics\n"
            "• Preliminary budget & BOM"
        ),
        "dispatched": False
    },
    {
        "id": "pitch_video_1d_before",
        "target_time": datetime(2026, 9, 27, 9, 0, 0),
        "subject": "🚨 FINAL 24H ALERT: Submit 5-Minute Pitch Deck Video Tomorrow (Sept 28)",
        "message": (
            "Hi Team,\n\n"
            "Tomorrow is the deadline for Milestone 1 of the CEAS Innovation Challenge!\n\n"
            "🎯 Deliverable: 5-Minute Video Pitch Submission\n"
            "📅 Due Date: Monday, September 28, 2026\n"
            "💰 Payout: Unlocks our $600.00 team payout upon submission.\n\n"
            "Please ensure the recording is uploaded and submitted to Canvas before the midnight cutoff."
        ),
        "dispatched": False
    },

    # --- MILESTONE 2: PROTOTYPE DAY SHOWCASE (Nov 4, 2026) ---
    {
        "id": "prototype_day_1w_before",
        "target_time": datetime(2026, 10, 28, 9, 0, 0),
        "subject": "📅 1-WEEK ALERT: Innovation Challenge Prototype Day on Nov 4",
        "message": (
            "Hi Team,\n\n"
            "Prototype Day is exactly 1 WEEK away (Wednesday, November 4, 2026)!\n\n"
            "🎯 Milestone Requirement: In-person demonstration of our benchtop prototype.\n"
            "• At least one team member must attend with our benchtop rig.\n"
            "• Objective: Show the 8-bottle dispensing manifold and elevator mechanism in operation."
        ),
        "dispatched": False
    },
    {
        "id": "prototype_day_1d_before",
        "target_time": datetime(2026, 11, 3, 9, 0, 0),
        "subject": "🚨 24H ALERT: Innovation Challenge Prototype Day Tomorrow (Nov 4)",
        "message": (
            "Hi Team,\n\n"
            "Tomorrow (Wednesday, November 4) is Prototype Day for the Innovation Challenge!\n\n"
            "Please confirm who will be transporting the benchtop test rig and representing the team at the showcase table."
        ),
        "dispatched": False
    },

    # --- MILESTONE 3: FINAL COMPETITION & GALA (Nov 18, 2026) ---
    {
        "id": "final_competition_1w_before",
        "target_time": datetime(2026, 11, 11, 9, 0, 0),
        "subject": "🏆 1-WEEK ALERT: Innovation Challenge Final Competition on Nov 18 ($600 Second Stipend + $1,200 Bonus)",
        "message": (
            "Hi Team,\n\n"
            "The Final Competition & Gala is 1 WEEK away (Wednesday, November 18, 2026)!\n\n"
            "⚠️ ATTENDANCE MANDATORY: All team members must attend in person.\n"
            "💰 Stakes:\n"
            "• Unlocks second $150/person stipend ($600 team total; $1,200 guaranteed completion grant)\n"
            "• $300/person ($1,200 team total) Top 25% placement bonus\n"
            "• 1st, 2nd, and 3rd place podium bonus prizes (up to $700/person) + ceremonial giant check!\n"
            "• Distribution of 100% material reimbursements from 1819 Makerspace."
        ),
        "dispatched": False
    },
    {
        "id": "final_competition_1d_before",
        "target_time": datetime(2026, 11, 17, 9, 0, 0),
        "subject": "🚨 TOMORROW: Innovation Challenge Final Competition (All Members Mandatory)",
        "message": (
            "Hi Team,\n\n"
            "Tomorrow, Wednesday, November 18, is the Final Competition!\n\n"
            "• All members are required to attend.\n"
            "• Dress code: Business casual.\n"
            "• Have the table, demo cups, and pitch deck loaded and ready.\n"
            "Let's bring home the win and secure our grant funding!"
        ),
        "dispatched": False
    }
]

def dispatch_cloud_email(subject, message):
    smtp_user = os.getenv("SMTP_EMAIL", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not smtp_user or not smtp_pass:
        print("ℹ️ Cloud SMTP credentials not configured. Skipping email dispatch.")
        return False

    success = True
    for member in DEFAULT_ROSTER["team"]:
        email = member["email"]
        name = member["name"]
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Senior Design] {subject}"
            msg["From"] = f"Senior Design Bot <{smtp_user}>"
            msg["To"] = email

            plain = f"Hi {name},\n\n{message}\n\nBest regards,\nJ.A.R.V.I.S. Project Intelligence"
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #0f172a; color: #38bdf8; padding: 18px 24px; font-weight: bold; font-size: 18px;">
                    J.A.R.V.I.S. Mark VII // Automated Project Alert
                </div>
                <div style="padding: 24px; color: #1e293b; line-height: 1.6;">
                    <p style="font-size: 16px;">Hi <strong>{name}</strong>,</p>
                    <div style="background-color: #f8fafc; border-left: 4px solid #c00000; padding: 16px; border-radius: 4px; font-size: 15px;">
                        {message.replace(chr(10), '<br>')}
                    </div>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0 16px 0;">
                    <p style="font-size: 12px; color: #94a3b8;">
                        Dispatched 24/7 autonomously by J.A.R.V.I.S. Cloud Infrastructure.<br>
                        Timestamp: {get_eastern_now().strftime('%B %d, %Y at %I:%M %p EDT')}
                    </p>
                </div>
            </div>
            """
            msg.attach(MIMEText(plain, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))

            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                print(f"✅ Cloud Email successfully sent to {email}")
        except Exception as e:
            print(f"❌ Cloud Email delivery failed for {email}: {e}")
            success = False
    return success

def execute_scheduler_checks():
    now_dt = get_eastern_now().replace(tzinfo=None)
    dispatched_count = 0
    for job in CLOUD_SCHEDULED_JOBS:
        # Only trigger if target_time is reached and within a 2-hour window
        time_diff = (now_dt - job["target_time"]).total_seconds()
        if not job["dispatched"] and 0 <= time_diff <= 7200:
            print(f"🔔 [CLOUD TRIGGER] Executing Job: {job['id']} at {now_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            dispatch_cloud_email(job["subject"], job["message"])
            job["dispatched"] = True
            dispatched_count += 1
    return dispatched_count

def cloud_scheduler_background_thread():
    print("🚀 J.A.R.V.I.S. Autonomous Cloud Scheduler Thread Active.")
    while True:
        try:
            execute_scheduler_checks()
        except Exception as e:
            print(f"Scheduler loop error: {e}")
        time.sleep(30)

# Start background scheduler thread on boot
threading.Thread(target=cloud_scheduler_background_thread, daemon=True).start()

def get_live_workspace_context():
    """Reads priority master project documents with strict size bounds for instant <4s latency."""
    context_sections = []
    
    priority_files = [
        ("Meeting Notes", "2026-09-09_Team_Meeting_Minutes.md"),
        ("Timeline", "Master_Gantt_Chart_Fall2026.md"),
        ("Timeline", "milestones.md"),
        ("Funding", "CEAS_Innovation_Challenge_Fall2026_Guide.md"),
        ("Architecture", "system_overview.md"),
        ("Budget", "procurement_and_funding.md")
    ]
    
    for folder, fname in priority_files:
        p = os.path.join(LOCAL_ROOT, folder, fname) if folder else os.path.join(LOCAL_ROOT, fname)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    context_sections.append(f"### [DOCUMENT: {folder}/{fname}]\n{f.read()[:2500]}")
            except Exception:
                pass

    # Include team roster
    for r_path in [os.path.join(LOCAL_ROOT, "team_roster.json"), os.path.join(LOCAL_ROOT, "Tools", "reminders", "team_roster.json")]:
        if os.path.exists(r_path):
            try:
                with open(r_path, "r", encoding="utf-8") as f:
                    context_sections.append(f"### [DOCUMENT: team_roster.json]\n{f.read()[:2000]}")
                    break
            except Exception:
                pass

    return "\n\n".join(context_sections)

def query_gemini_ai(sender, query_text, operator_auth=False):
    """High-speed Gemini AI via direct REST API call with Public vs Operator clearance tiers."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        now_eastern = get_eastern_now()
        today_date_str = now_eastern.strftime("%A, %B %d, %Y")
        current_time_str = now_eastern.strftime("%I:%M %p EDT").lstrip("0")
        
        if operator_auth:
            salutation = "Sir / Mr. Rohendhar" if sender.lower() in ["ro", "operator", "rohendhar"] else f"Mr. {sender}"
            system_instruction = (
                f"You are J.A.R.V.I.S., the advanced AI Engineering Co-Pilot and Operating System for Kinetic Pour (University of Cincinnati Capstone MECH5051/EECE5001).\n"
                f"CLEARANCE LEVEL: LEVEL 5 TACTICAL OPERATOR (Direct access granted to: {salutation}).\n\n"
                f"CORE CAPABILITY DIRECTIVE — CRITICAL THINKING & RIGOROUS ENGINEERING:\n"
                f"You are NOT a keyword-matching chatbot or a canned script regurgitator. You are an exceptionally capable, mathematically rigorous senior systems engineer, mechanical designer, and electrical automation architect.\n"
                f"When asked ANY technical, architectural, operational, or mathematical question:\n"
                f"- Engage in deep, multi-step critical thinking and technical reasoning.\n"
                f"- Solve calculations step-by-step with exact formulas (e.g. lead screw torque tau = (F*l)/(2*pi*eta), fluid flow rates Q = dV/dt, Reynolds numbers, pressure drops, motor torque curves, Ohm's/Kirchhoff's law current budgets, heat dissipation, stepper step/microstep timing, PLC scan times).\n"
                f"- Propose concrete, viable engineering solutions with specific component part numbers, materials (304 stainless, PETG, food-grade silicone, PVDF), tolerances, and wiring schematics.\n"
                f"- Analyze design trade-offs (pros vs cons, failure modes, safety factors, siphoning risks, contamination hazards, thermal dissipation).\n"
                f"- Never give canned one-liners or deflect with vague statements like 'we are waiting for CAD'. Provide the actionable engineering answer immediately, followed by strategic next steps.\n"
                f"- You have complete, unrestricted visibility into all project documents, dates, budgets ($1,200 total grant, $600 upfront working capital, $300/person), BOM quotes, and team tasks.\n\n"
                f"TEMPORAL ANCHOR (CRITICAL):\n"
                f"- TODAY'S DATE IS: {today_date_str}.\n"
                f"- CURRENT LOCAL TIME IS: {current_time_str} (Cincinnati, Ohio / EDT).\n"
                f"- MASTER TIMELINE & MILESTONES:\n"
                f"  * Wednesday, September 23, 2026: Team Design Proposal deadline (BOM vendor quotes + CAD layout drawings).\n"
                f"  * Monday, September 28, 2026: 5-Minute Pitch Deck Video due (Unlocks $600.00 upfront team payout).\n"
                f"  * Friday, October 2, 2026: Senior Design Draft Proposal for Prof. Jacob Cress.\n"
                f"  * Wednesday, November 4, 2026: Prototype Demo Day at 1819 Innovation Hub.\n"
                f"  * Wednesday, November 18, 2026: Final Competition & Innovation Showcase.\n"
                f"  * Tuesday, December 1, 2026: Formal Senior Design Course Defense.\n"
                f"  * Standing meetings: Twice weekly — before (12:45 PM) and after (2:45 PM) Wednesday 1:30 PM class.\n\n"
                f"TEAM ROSTER & SUBSYSTEM LEADS:\n"
                f"• Rohendhar (Ro): Project Manager, Systems Integration, Fluidics Manifold Co-Lead.\n"
                f"• Eli Radabaugh: Electrical Subsystem Lead (Click PLC, Mean Well 24V PSU, wiring, E-stop, relays, sensors).\n"
                f"• Aron Joseph: Finance, Procurement, Bottling Subsystem Co-Lead (BOM cost rollup, pump sourcing, purchase requests).\n"
                f"• Shyam Patel: Operations, Kinematics & Elevator Lead (MGN12H linear rail, T8 lead screw, NEMA 17, Gantt schedule).\n\n"
                f"RULES OF CONDUCT:\n"
                f"1. Tone: Refined British poise, sharp intelligence, concise and proactive with subtle dry humor.\n"
                f"2. Provide clear, direct engineering answers with specific component numbers, dates, formulas, or team member assignments.\n"
                f"3. Operator is: {salutation}."
            )
        else:
            salutation = "Guest"
            system_instruction = (
                f"You are J.A.R.V.I.S., the systems intelligence and technical guide for Kinetic Pour at the University of Cincinnati.\n"
                f"CLEARANCE: PUBLIC GUEST (SURFACE ARCHITECTURE).\n\n"
                f"CRITICAL ACCESS & PRIVACY PROTOCOLS:\n"
                f"1. Do NOT disclose internal calendar deadlines (e.g. Sept 23, Sept 28, Oct 15) or presentation deadlines.\n"
                f"2. Do NOT disclose internal grant finances, team payouts ($600 / $150 per person), budget breakdowns ($1,200), or Canvas Purchase Request forms. If asked about money or internal deadlines, politely explain that financial figures and internal schedules are restricted under Level 5 Operator Clearance.\n"
                f"3. INSTEAD, discuss:\n"
                f"   - What Kinetic Pour is: an automated, precision drink-crafting table with 8 modular bottles, GROTHEN 24V peristaltic pumps, a NEMA 17 stepper T8 lead screw elevator lift, food-grade silicone lines, and industrial PLC control.\n"
                f"   - Milestones Achieved: Completed 8-bottle fluidics Three.js simulation, CAD modeled modular 2x4 reservoir chassis and dispensing manifold, and mapped 8-step PLC safety sequence with optical interlocks.\n"
                f"   - Next Milestone: Team Design Proposal & CAD BOM submission (hardware procurement phase).\n"
                f"   - General technical subsystem specifications and features.\n"
                f"4. Tone: Helpful, articulate, sophisticated British AI host."
            )
        
        context_data = get_live_workspace_context()
        prompt = (
            f"PROJECT ARCHITECTURE DATA:\n{context_data}\n\n"
            f"OPERATOR AUTHENTICATED: {operator_auth}\n"
            f"USER IDENTIFIER: {sender}\n"
            f"QUERY: {query_text}"
        )
        
        # High-speed REST cascade: eliminates 35s SDK backoff sleep and achieves <2.5s responses
        CANDIDATE_MODELS = [
            "gemini-flash-lite-latest",
            "gemini-flash-latest"
        ]
        
        for candidate in CANDIDATE_MODELS:
            try:
                t0 = time.time()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent?key={api_key}"
                payload = {
                    "system_instruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.45, "maxOutputTokens": 2500}
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        print(f"[{candidate}] answered in {time.time()-t0:.2f}s")
                        return text
            except Exception as ex:
                print(f"[{candidate}] skipped: {ex}")
                continue
                
    except Exception as e:
        print(f"Gemini API error: {e}")
    return None

def fallback_answer(sender, query_text, operator_auth=False):
    """Comprehensive intelligent offline fallback engine with Public vs Operator clearance tiers."""
    q = query_text.lower()

    if not operator_auth:
        # ==============================
        # PUBLIC GUEST MODE (SURFACE-LEVEL)
        # ==============================
        if any(w in q for w in ["deadline", "timeline", "gantt", "due", "when", "schedule", "calendar", "milestone", "date", "submit"]):
            return (
                "Here is the verified **Kinetic Pour Milestone Progress**:\n\n"
                "### ✅ Milestones Achieved:\n"
                "• **3D Fluidics Architecture**: 8-bottle hydraulic layout & Three.js interactive simulation completed and validated.\n"
                "• **Modular Caddy & Manifold**: Engineered 2x4 bottle mounting chassis and 8-nozzle dispensing head in CAD.\n"
                "• **PLC Safety State Machine**: Designed 8-step safety sequence with optical cup-presence interlocks.\n\n"
                "### 🎯 Next Upcoming Milestone:\n"
                "• **Team Design Proposal & CAD BOM Submission**: Finalizing structural drawings, vendor datasheets, and procurement quotes for hardware assembly.\n\n"
                "🔒 *Note: Specific calendar dates, pitch video submission requirements, and internal task checklists require Level 5 Operator Clearance.*"
            )

        if any(w in q for w in ["fund", "money", "grant", "stipend", "reimburse", "challenge", "1819", "prize", "budget", "payout", "cost"]):
            return (
                "**Kinetic Pour** is an undergraduate Senior Design capstone project developed at the University of Cincinnati, supported through collegiate engineering innovation grants.\n\n"
                "🔒 **Access Restricted**: Specific grant allocations ($1,200.00 total), upfront working capital payouts ($600.00 on Sept 28), and reimbursement procedures are reserved for authorized Level 5 Operators. Please select an Operator profile and enter your passcode to view internal finances."
            )

        if any(w in q for w in ["task", "action", "todo", "what should i", "do i need", "deliverable", "assignment", "work on"]):
            return (
                "Individual team member task allocations and internal accountability checklists require Level 5 Operator authentication.\n\n"
                "Please select your operator profile (Ro, Aron, Eli, or Shyam) and enter your passcode to access your active deliverables."
            )

        if any(w in q for w in ["role", "who", "team", "assign", "members", "roster"]):
            return (
                "**Kinetic Pour Engineering Team:**\n\n"
                "• **Rohendhar** — Project Manager & Systems Integration Lead\n"
                "• **Aron Joseph** — Finance & Bottling Subsystem Lead\n"
                "• **Eli Radabaugh** — Electrical & Industrial Automation Lead\n"
                "• **Shyam Patel** — Mechanical Kinematics & Operations Lead\n\n"
                "🔒 *Internal task checklists and deliverable tracking require Operator login.*"
            )

        if any(w in q for w in ["bottle", "fluid", "pump", "liquid", "peristaltic", "grothen", "tube", "dispens"]):
            return (
                "Here are the engineering parameters for the **8-Bottle Fluidics Subsystem**:\n\n"
                "• **Reservoirs**: 8x 750ml Bordeaux-style modular bottles in a 2x4 3D-printed caddy.\n"
                "• **Check Valves**: 1/4\" inline one-way check valves to prevent backflow and keep lines primed.\n"
                "• **Dosing Pumps**: 8x GROTHEN 24V peristaltic pumps with 3-roller rotor heads for positive displacement metering.\n"
                "• **Tubing**: High-temperature food-grade 3x5mm silicone tubing converging at the central 3D-printed manifold.\n"
                "• **Sanitation**: Clean-in-place (CIP) purge cycle compatible."
            )

        if any(w in q for w in ["lift", "rail", "motor", "elevator", "carriage", "screw", "stepper"]):
            return (
                "Regarding the **T8 Linear Elevator Subsystem**:\n\n"
                "• **Mechanism**: NEMA 17 stepper motor driving a T8 stainless lead screw with dual precision guide rods.\n"
                "• **Stroke Travel**: 100 mm vertical stroke (lowers cup into dispensing bay, then lifts flush with tabletop).\n"
                "• **Sensors**: Optical photocell cup-presence verification and microswitch endstops.\n"
                "• **Cycle Time**: ~4 seconds full stroke transit."
            )

        if any(w in q for w in ["ice", "cool", "thermal", "fridge", "chiller"]):
            return (
                "Regarding the **Thermal Management Subsystem**:\n\n"
                "• **Architecture Decision**: Motorized compressors were ruled out due to bulk, plumbing, and power draw.\n"
                "• **Current Baseline**: Insulated cold bay utilizing **reusable food-grade 304 stainless steel whiskey stones** or compact 12V thermoelectric (Peltier) cold plates.\n"
                "• **Insulation**: Closed-cell neoprene barrier preventing condensation in the electrical bay."
            )

        # General Public Fallback
        return (
            "Greetings! I am **J.A.R.V.I.S.**, systems intelligence for the **Kinetic Pour Automated Drink Table**.\n\n"
            "I am currently operating in **Public Guest Mode** (Surface Telemetry). I can answer questions regarding:\n"
            "• **Project Overview & Specs**: Hardware architecture and dispensing capabilities.\n"
            "• **Milestones Achieved**: 3D fluidics simulation, CAD manifold, and PLC safety logic.\n"
            "• **Next Milestone**: Team Design Proposal & CAD BOM submission.\n"
            "• **Subsystems**: GROTHEN 24V pumps, T8 elevator lift, and capacitive touchscreen HMI.\n\n"
            "*(For internal team task lists, CEAS grant allocations, or submission deadlines, team operators should access the dedicated [Operator Command Portal](https://rohendhar.github.io/jarvis-operator/)).*"
        )

    # ==============================
    # OPERATOR MODE (LEVEL 5 UNLOCKED)
    # ==============================
    salutation = "Sir" if sender.lower() in ["ro", "operator"] else sender

    # 0. Tasks, Action Items & Deliverables (Member-Specific)
    if any(w in q for w in ["task", "action", "todo", "what should i", "do i need", "deliverable", "assignment", "work on"]):
        sender_lower = sender.lower()
        if "eli" in sender_lower or "radaba" in sender_lower:
            return (
                f"Good day, **Mr. Radabaugh**. Here are your active engineering deliverables as **Electrical Lead**:\n\n"
                "### ⚡ Eli's Priority Action Items (Target: Wednesday, Sept 23):\n"
                "1. **BOM Vendor Quotes**: Finalize exact quotes and datasheets for the Click PLC (AutomationDirect) or Siemens LOGO!, Mean Well LRS-350-24 power supply, 24V relay module, flyback diodes, and terminal blocks.\n"
                "2. **Electrical CAD Layout**: Produce single-line wiring schematic and bulkhead IP-rated enclosure layout.\n"
                "3. **Z-Axis Lift Co-Lead**: Finalize wiring and mount locations for upper/lower normally-closed optical limit switches on the lift carriage with Shyam.\n"
                "4. **Innovation Challenge**: Confirm you have joined the Canvas course page (mandatory for $300 payout)."
            )
        elif "aron" in sender_lower or "joseph" in sender_lower:
            return (
                f"Good day, **Mr. Joseph**. Here are your active deliverables as **Finance & Bottling Co-Lead**:\n\n"
                "### 💰 Aron's Priority Action Items (Target: Wednesday, Sept 23):\n"
                "1. **BOM Cost Rollup**: Compile itemized quotes from all 4 section leads for the Team Design Proposal.\n"
                "2. **Bottling Hardware Quotes**: Finalize vendor quotes for 8 uniform flat-bottom bottles (500ml–750ml), food-grade rubber corks with silicone check valves, 12V peristaltic pumps, and silicone tubing.\n"
                "3. **Purchase Request Forms**: Prepare Canvas Purchase Request drafts for Innovation Chair authorization (pre-approval required prior to any spending).\n"
                "4. **Innovation Challenge**: Confirm Canvas enrollment for $300 individual stipend."
            )
        elif "shyam" in sender_lower or "patel" in sender_lower:
            return (
                f"Good day, **Mr. Patel**. Here are your active deliverables as **Operations & Gantt Lead**:\n\n"
                "### 📐 Shyam's Priority Action Items (Target: Wednesday, Sept 23):\n"
                "1. **Lift Mechanism CAD Layout**: Complete CAD drawing and sizing for the MGN12H linear guide rail (350mm–400mm) and 8mm lead screw with NEMA 17 motor.\n"
                "2. **Master Gantt Maintenance**: Update the master Excel schedule for upcoming deliverables (Sept 23 Proposal, Sept 28 Pitch Video).\n"
                "3. **Ice / Thermal Study**: Finalize recommendation (reusable 304 stainless steel whiskey stones cold bay vs thermoelectric Peltier plate).\n"
                "4. **Innovation Challenge**: Confirm Canvas enrollment for $300 individual stipend."
            )
        else:  # Rohendhar / PM
            return (
                f"Good day, **Sir (Mr. Rohendhar)**. Here are your active executive directives as **Project Manager & Systems Lead**:\n\n"
                "### 🎯 Ro's Priority Action Items (Target: Wednesday, Sept 23):\n"
                "1. **Bottling CAD & Fluid Routing**: Complete CAD layout drawing for the 8-nozzle dispensing manifold, cup centering ring, and fluid routing lines.\n"
                "2. **Jacob Cress Documentation**: Finalize and submit the Team Lead / Project Sponsor introductory document.\n"
                "3. **Team Proposal Synthesis**: Merge all 4 section BOM quotes and CAD layouts into the master submission by Sept 23.\n"
                "4. **5-Minute Pitch Deck Video**: Structure slides and script for the Sept 28 submission ($600 upfront team payout)."
            )

    # 0b. Time, Date, and System Clock
    if any(w in q for w in ["what time", "current time", "what is the time", "clock", "what date", "today's date", "todays date", "time is it", "time now"]):
        now_eastern = get_eastern_now()
        time_str = now_eastern.strftime("%I:%M %p EDT").lstrip("0")
        date_str = now_eastern.strftime("%A, %B %d, %Y")
        return (
            f"The current local time in Cincinnati, Ohio is **{time_str}** on **{date_str}**, **{salutation}**.\n\n"
            f"All Project AVENGERS operational deadlines and meeting schedules are calibrated to Eastern Daylight Time (EDT)."
        )

    # 1. Timeline, Deadlines & Gantt
    if any(w in q for w in ["deadline", "timeline", "gantt", "due", "when", "schedule", "calendar"]):
        return (
            f"Good day, **{salutation}**. Here is our verified Master Milestone Schedule:\n\n"
            "### 📅 Master Project Deadlines:\n"
            "• **🚨 Wednesday, Sept 23**: **Team Design Proposal** *(BOM Quotes + Section CAD Layouts)* — **1 WEEK AWAY**.\n"
            "• **💰 Monday, Sept 28**: **5-Minute Pitch Deck Video** *(Unlocks $600.00 team payout for prototype capital)*.\n"
            "• **Friday, Oct 2**: Senior Design Draft Proposal for Prof. Jacob Cress.\n"
            "• **Wednesday, Nov 4**: Innovation Challenge **Prototype Day** (In-person benchtop rig demo).\n"
            "• **🎉 Wednesday, Nov 18**: **Final Competition & Gala** *($600 second stipend + $1,200 bonus + 100% reimbursement)*.\n"
            "• **Tuesday, Dec 1**: Formal Senior Design Course Defense.\n\n"
            "⏰ *Meeting Cadence*: Twice weekly — immediately before (12:45 PM) and after (2:45 PM) Wednesday 1:30 PM class."
        )

    # 2. Team Roles & Section Leads
    if any(w in q for w in ["role", "who", "eli", "aron", "shyam", "ro", "team", "assign"]):
        return (
            f"At your command, **{salutation}**. Here are the assigned Subsystem Section Leads:\n\n"
            "### 👥 Subsystem Leadership Roster:\n"
            "• **Eli Radabaugh**: **Electrical Subsystem Lead** & Lift Mechanism Co-Lead *(PLC specs, 24V supply, relays, wiring)*.\n"
            "• **Aron Joseph**: **Finance & Procurement Lead** & Bottling Subsystem Co-Lead *(Purchase requests, $600 capital, 8 bottles, tubing)*.\n"
            "• **Shyam Patel**: **Operations & Master Gantt Lead**, Lift Mechanism Co-Lead & Ice Lead *(Gantt chart, linear rail, ice study)*.\n"
            "• **Rohendhar**: **Project Manager & Systems Integration Lead** & Bottling Co-Lead *(Overall architecture, Cress sponsor doc, nozzle manifold)*."
        )

    # 3. Lift Mechanism & Mechanics
    if any(w in q for w in ["lift", "rail", "motor", "elevator", "carriage", "screw"]):
        return (
            f"Here are the engineering parameters for the **Linear Elevator Mechanism**, **{salutation}**:\n\n"
            "• **Linear Guide**: Precision MGN12H linear rail (350mm–400mm) with dual bearing blocks.\n"
            "• **Drive Mechanism**: NEMA 17 stepper motor driving an 8mm lead screw (T8x8, 2mm pitch, 8mm lead) or high-torque 12V worm-drive DC gearmotor.\n"
            "• **Travel Stroke**: 100mm vertical stroke.\n"
            "• **Limit Switches**: Normally-closed optical microswitches at top and bottom limits for fail-safe PLC homing.\n"
            "• **Cup Safety**: Centering ring with infrared presence sensor.\n"
            "• **Leads**: Shyam Patel & Eli Radabaugh."
        )

    # 4. Bottling & Fluidics System
    if any(w in q for w in ["bottle", "fluid", "pump", "liquid", "cork", "manifold", "nozzle", "tubing", "valves"]):
        return (
            f"Here are the finalized parameters for the **8-Bottle Fluidics Subsystem**, **{salutation}**:\n\n"
            "• **Reservoir Matrix**: 8 uniform glass bottles (500ml–750ml) in a 2×4 modular bay.\n"
            "• **Corks & Seals**: Food-grade silicone rubber bungs with dual barbed ports (fluid delivery + pressure equalization check valve).\n"
            "• **Metering Pumps**: 8x 12V/24V food-grade peristaltic metering pumps (~100–150 ml/min).\n"
            "• **Dispensing Manifold**: Custom 3D-printed food-safe PETG manifold focusing all 8 lines into a 2.5\" diameter dispensing cone.\n"
            "• **Tubing**: 1/4\" OD food-grade silicone tubing.\n"
            "• **Leads**: Rohendhar & Aron Joseph."
        )

    # 5. Electrical, PLC & Controls
    if any(w in q for w in ["plc", "wire", "power", "relay", "schematic", "electric", "fuse", "diode"]):
        return (
            f"Regarding the **Electrical & Industrial Control Subsystem**, **{salutation}**:\n\n"
            "• **Controller**: AutomationDirect Click PLC (or Siemens LOGO! 24RCE) running 24V sinking/sourcing I/O.\n"
            "• **Power Supply**: Mean Well LRS-350-24 (24V DC, 14.6A, 350W) with terminal distribution blocks.\n"
            "• **Pump Switching**: 8-channel 24V optoisolated relay module with 1N4007 flyback diodes across inductive pump coils.\n"
            "• **Safety Circuit**: Physical Mushroom E-Stop cutting all 24V actuator power while keeping PLC logic energized.\n"
            "• **Enclosure**: IP65 sealed polycarbonate bulkhead enclosure with gland connectors.\n"
            "• **Lead**: Eli Radabaugh."
        )

    # 6. Ice & Thermal System
    if any(w in q for w in ["ice", "cool", "thermal", "fridge", "chiller"]):
        return (
            f"Regarding the **Thermal Management & Ice Subsystem**, **{salutation}**:\n\n"
            "• **Architecture Decision**: Motorized ice makers and compressors were permanently ruled out due to bulk, plumbing, and drainage.\n"
            "• **Current Baseline**: Insulated cold bay utilizing **reusable food-grade 304 stainless steel whiskey stones** or a compact 12V thermoelectric (Peltier) cold plate.\n"
            "• **Insulation**: Closed-cell neoprene foam to prevent condensation dripping into the electrical compartment.\n"
            "• **Leads**: Shyam Patel & Eli Radabaugh."
        )

    # 7. Funding & Innovation Challenge
    if any(w in q for w in ["fund", "money", "grant", "stipend", "reimburse", "challenge", "1819", "prize"]):
        return (
            f"Here is the financial breakdown for the **CEAS Innovation Challenge**, **{salutation}**:\n\n"
            "• **Total Guaranteed Grant**: **$1,200.00** ($300.00 per student) for completing the 3 deliverables.\n"
            "• **Upfront Working Capital**: **$600.00** ($150/person) awarded upon submitting the **5-Minute Pitch Deck Video (Sept 28)**, used directly as active prototype budget.\n"
            "• **Top 25% Bonus**: Additional **$1,200.00** ($300/person); podium prizes up to **$700/person**.\n"
            "• **100% Material Reimbursement**: Covers all hardware, fasteners, and 1819 Makerspace equipment.\n"
            "• **⚠️ Critical Rule**: You MUST complete the Canvas **Purchase Request Form** and obtain Innovation Chair authorization **BEFORE** buying anything. Itemized receipts only; NO gift cards."
        )

    # General Fallback
    return (
        f"At your service, **{salutation}**. J.A.R.V.I.S. neural telemetry is fully operational.\n\n"
        "### 🚀 Kinetic Pour Status Summary:\n"
        "• **Form Factor**: Automated 8-Bottle Mobile Table on Wheels (~30\" × 17\" × 10\").\n"
        "• **Immediate Focus**: **Team Design Proposal due Wednesday, September 23rd** (BOM quotes + CAD drawings per section).\n"
        "• **Upcoming Payout**: 5-Minute Pitch Deck Video due September 28th ($600.00 team payout).\n\n"
        "How may I assist you further with CAD specs, wiring diagrams, or milestone tracking?"
    )

@app.route("/operator")
@app.route("/command")
def operator_portal():
    for p in [os.path.join(LOCAL_ROOT, "templates", "operator.html"), os.path.join(LOCAL_ROOT, "operator.html")]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    try:
        return render_template("operator.html")
    except Exception as e:
        return f"<h3>Operator Portal: {e}</h3>"

@app.route("/void")
@app.route("/portal")
@app.route("/simulation")
def chromatic_void_portal():
    for p in [os.path.join(LOCAL_ROOT, "templates", "chromatic_void.html"), os.path.join(LOCAL_ROOT, "chromatic_void.html")]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    try:
        return render_template("chromatic_void.html")
    except Exception as e:
        return f"<h3>Chromatic Void Engine: {e}</h3>"

@app.route("/")
def home():
    return chromatic_void_portal()

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json(force=True, silent=True) or {}
        sender = data.get("sender", "Guest")
        message = data.get("message", "")
        operator_auth = bool(
            data.get("operatorAuth", False) or 
            data.get("operator_auth", False) or
            sender.lower() in ["ro", "eli", "aron", "shyam", "operator", "admin", "rohendhar"]
        )
        
        reply = query_gemini_ai(sender, message, operator_auth=operator_auth)
        if not reply:
            reply = fallback_answer(sender, message, operator_auth=operator_auth)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"⚠️ J.A.R.V.I.S. Telemetry Error: {str(e)}"})

@app.route("/api/cron", methods=["GET", "POST"])
def cron_endpoint():
    """Heartbeat endpoint: keeps Render awake 24/7 and triggers any due scheduled emails."""
    dispatched = execute_scheduler_checks()
    return jsonify({
        "status": "HEARTBEAT_ACKNOWLEDGED",
        "system": "J.A.R.V.I.S. Mark VII",
        "dispatched_jobs": dispatched,
        "timestamp": get_eastern_now().isoformat()
    })

@app.route("/api/status", methods=["GET"])
def status():
    now_eastern = get_eastern_now()
    return jsonify({
        "status": "ONLINE",
        "system": "J.A.R.V.I.S. Mark VII",
        "team": "Kinetic Pour Engineering Team",
        "today": now_eastern.strftime("%A, %B %d, %Y"),
        "time": now_eastern.strftime("%I:%M %p EDT").lstrip("0"),
        "scheduler": "24/7 ACTIVE",
        "version": "7.5.1"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
