import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from dotenv import load_dotenv
import json
import base64
from fpdf import FPDF

# Load .env for GEMINI_API_KEY
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Import Modules
from backend.modules.agent.engine import AgentEngine
from backend.modules.fines.lookup import FineLookup
from backend.modules.rules.loader import RulesLoader
from backend.modules.geofencing.engine import GeofencingEngine
from backend.modules.sync.router import router as sync_router

class UTF8JSONResponse(JSONResponse):
    """Preserve ₹ and other Unicode in JSON responses."""

    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


app = FastAPI(
    title="DriveLegal API",
    description="AI-powered Indian traffic law assistant with agentic tool calling.",
    version="2.0.0",
    default_response_class=UTF8JSONResponse,
)

# ── CORS (required for web/browser clients) ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Tighten to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to DriveLegal API",
        "docs": "/docs",
        "health": "/health",
        "status": "online"
    }

# ── Data paths ────────────────────────────────────────────────────────────────
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
FINES_DB   = os.path.join(DATA_DIR, "fines.db")
RULES_JSON = os.path.join(DATA_DIR, "rules.json")
ZONES_DIR  = os.path.join(DATA_DIR, "zones")
REPORTS_DIR = r"d:\drive\report"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── Initialize backend modules ────────────────────────────────────────────────
fine_lookup    = FineLookup(FINES_DB)   if os.path.exists(FINES_DB)   else None
rules_loader   = RulesLoader(RULES_JSON)
geofencing     = GeofencingEngine(ZONES_DIR)

# ── Initialize the AI Agent ───────────────────────────────────────────────────
agent = AgentEngine(fine_lookup, rules_loader, geofencing)

# ── Request / Response Models ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    text: str
    gps: Optional[Dict[str, float]] = None
    image_base64: Optional[str] = None
    image_mime: Optional[str] = "image/jpeg"
    # Conversation history for multi-turn context
    # Each entry: {"role": "user"|"model", "parts": ["message text"]}
    history: List[Dict] = Field(default_factory=list)


class ChallanRequest(BaseModel):
    vehicle_number: str

class ReportRequest(BaseModel):
    id: str
    type: str
    typeLabel: str
    location: str
    description: str
    image_base64: str
    timestamp: str
    vehicle_number: Optional[str] = None

# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/query")
async def handle_query(request: QueryRequest = Body(...)):
    """
    Main AI agent endpoint.
    
    The agent autonomously decides which tools to call
    (fine lookup, rule lookup, zone check) and synthesizes a natural language
    response grounded in real data.
    
    Falls back to keyword-based matching if neither Ollama nor Gemini is available.
    """
    result = agent.run(
        user_text=request.text,
        conversation_history=request.history,
        gps=request.gps,
        image_base64=request.image_base64,
        image_mime=request.image_mime or "image/jpeg",
    )
    result["citations"] = _citations_from_tools(result.get("tools_used") or [])
    return result


def _citations_from_tools(tools_used: list) -> list:
    """Human-readable source lines for the mobile trust footer."""
    lines = []
    for entry in tools_used:
        tool = entry.get("tool")
        res = entry.get("result") or {}
        if tool == "lookup_fine" and res.get("found"):
            section = res.get("section_ref") or "Traffic Law"
            display = res.get("amount_display") or f"₹{res.get('amount_inr', '?')}"
            when = res.get("data_as_of") or res.get("fetched_at") or ""
            country = res.get("country", "IN")
            source = "local fines.db"
            lines.append(f"{section}: {display} ({source}{f', updated {when[:10]}' if when else ''})")
        elif tool == "lookup_rule" and res.get("found"):
            lines.append(f"{res.get('section') or res.get('rule_id')}: rules.json")
        elif tool == "search_rules" and res.get("found"):
            # Multiple rules might be returned
            rules = res.get("rules", [])
            for r in rules:
                lines.append(f"{r.get('section') or r.get('rule_id')}: rules.json")
    if not lines and tools_used:
        lines.append("AI synthesis — confirm on official portals")
    # De-duplicate
    return list(dict.fromkeys(lines))


@app.post("/challan/calculate")
async def calculate_challan(request: ChallanRequest = Body(...)):
    """
    Look up pending challans by vehicle registration number.
    Currently uses mock data — integrate with official Parivahan API for production.
    """
    v_num = request.vehicle_number.upper().replace(" ", "").replace("-", "")

    demo_notice = (
        "Demo sample data only — not linked to Parivahan / eChallan. "
        "Do not use for real payment decisions."
    )

    if "TN" in v_num:
        return {
            "demo": True,
            "demo_notice": demo_notice,
            "vehicle_number": request.vehicle_number,
            "owner": "J*** S***",
            "vehicle_type": "Motor Car (LMV)",
            "pending_challans": [
                {"date": "2024-03-15", "violation": "Over Speeding",     "amount": 1000, "status": "Pending", "location": "Anna Salai, Chennai"},
                {"date": "2024-04-02", "violation": "No Helmet (Pillion)", "amount": 500,  "status": "Pending", "location": "OMR, Chennai"},
            ],
            "total_fine": 1500,
            "last_updated": datetime.now().isoformat(),
        }
    elif "DL" in v_num:
        return {
            "demo": True,
            "demo_notice": demo_notice,
            "vehicle_number": request.vehicle_number,
            "owner": "A*** K***",
            "vehicle_type": "Two Wheeler",
            "pending_challans": [
                {"date": "2024-02-10", "violation": "Red Light Jumping", "amount": 1000, "status": "Pending", "location": "Connaught Place, Delhi"},
            ],
            "total_fine": 1000,
            "last_updated": datetime.now().isoformat(),
        }
    else:
        return {
            "demo": True,
            "demo_notice": demo_notice,
            "vehicle_number": request.vehicle_number,
            "owner": "N/A",
            "vehicle_type": "Unknown",
            "pending_challans": [],
            "total_fine": 0,
            "last_updated": datetime.now().isoformat(),
            "message": "No pending challans found for this vehicle number.",
        }

@app.post("/report/submit")
async def submit_report(request: ReportRequest = Body(...)):
    """
    Receives incident reports from the mobile app and saves them as files.
    """
    report_id = request.id
    
    # Calculate Fine based on Incident Type
    # Mapping incident types to DB offence codes
    offence_map = {
        "traffic": "RED_LIGHT_JUMPING",
        "parking": "NO_PARKING",
        "accident": "SECTION_184" # Dangerous driving
    }
    
    fine_amount = 0
    rule_section = "N/A"
    
    db_code = offence_map.get(request.type)
    if db_code and fine_lookup:
        fine_data = fine_lookup.query(db_code, "ALL", "TN", country="IN") # Using TN for Tamil Nadu challan
        if fine_data:
            fine_amount = fine_data.get("amount_inr", 0)
            rule_section = fine_data.get("section_ref", "N/A")

    # Save Image
    image_path = os.path.join(REPORTS_DIR, f"{report_id}.jpg")
    try:
        base64_data = request.image_base64
        if "base64," in base64_data:
            base64_data = base64_data.split("base64,")[1]
            
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(base64_data))
    except Exception as e:
        print(f"Error saving image: {e}")
        return {"status": "error", "message": "Failed to decode image base64."}
        
    # Save JSON data
    data_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
    report_data = {
        "id": report_id,
        "type": request.type,
        "typeLabel": request.typeLabel,
        "location": request.location,
        "description": request.description,
        "vehicle_number": request.vehicle_number,
        "timestamp": request.timestamp,
        "image_file": f"{report_id}.jpg",
        "status": "unverified",
        "fine_amount": fine_amount,
        "rule_section": rule_section
    }
    
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)
        
    # Generate Official E-Challan PDF
    try:
        pdf_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
        pdf = FPDF()
        pdf.add_page()
        
        # Header Box
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 15, "TAMIL NADU POLICE DEPARTMENT", border=1, ln=True, align='C', fill=True)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(190, 10, "E-CHALLAN RECEIPT", border=1, ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Helper for table rows
        def add_row(label, value, is_bold=False):
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(60, 10, label, border=1)
            pdf.set_font("Arial", 'B' if is_bold else '', 11)
            pdf.cell(130, 10, str(value), border=1, ln=True)

        # Details Table
        add_row("E-Challan No:", report_id, True)
        add_row("Date & Time:", request.timestamp)
        add_row("Vehicle Number:", request.vehicle_number or 'N/A', True)
        add_row("Place of Offence:", request.location)
        add_row("Offence Type:", request.typeLabel)
        add_row("Violated Rule (Section):", rule_section)
        
        pdf.set_text_color(200, 0, 0)
        add_row("Total Fine Amount:", f"Rs. {fine_amount}", True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(5)
        
        # Evidence Image section
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "PHOTO EVIDENCE", border=1, ln=True, align='C', fill=True)
        
        # Embed the image if it exists
        if os.path.exists(image_path):
            # Calculate aspect ratio to fit the image
            pdf.image(image_path, x=15, y=pdf.get_y() + 5, w=180, h=100, keep_aspect_ratio=True)
            pdf.set_y(pdf.get_y() + 110) # move cursor below the image
        else:
            pdf.cell(190, 50, "No Image Evidence Available", border=1, ln=True, align='C')
            
        pdf.ln(5)
        
        # Footer Status
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 15, "STATUS: PENDING REVIEW", border=1, ln=True, align='C')
        
        pdf.output(pdf_path)
    except Exception as e:
        print(f"Error generating PDF: {e}")
        
    return {
        "status": "success", 
        "message": f"Report {report_id} saved successfully.",
        "fine_amount": fine_amount,
        "rule_section": rule_section
    }

@app.get("/health")
async def get_health():
    """Server and database status."""
    db_age       = fine_lookup.get_db_age() if fine_lookup else "DB not found"
    rules_count  = len(rules_loader.rules)  if rules_loader else 0
    agent_mode = "keyword-fallback"
    if agent.ollama_available:
        agent_mode = f"ollama/{agent.ollama_model}"
    elif agent.gemini_available:
        agent_mode = "gemini-2.0-flash"
    return {
        "status":        "ok",
        "agent_mode":    agent_mode,
        "db_age":        db_age,
        "rules_count":   rules_count,
        "chat_handler":  "v3-memory",
    }


# ── Sync router (for mobile offline sync) ─────────────────────────────────────
app.include_router(sync_router)


if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
