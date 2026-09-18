import os
import json
import sqlite3
import uuid
import datetime
import asyncio
from typing import Dict, Any, List, Optional, cast
try:
    from app.core.config import settings
except ImportError:
    from ..core.config import settings

class Database:
    def __init__(self):
        self.use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)
        self.sqlite_path = settings.SQLITE_DB_PATH
        self.supabase_client = None
        self._logged_supabase_errors = set()

        if self.use_supabase:
            try:
                from supabase import create_client
                self.supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
            except Exception as e:
                self.use_supabase = False

    def _log_supabase_fallback(self, operation: str, error: Any):
        err_str = str(error)[:100]
        if operation not in self._logged_supabase_errors:
            self._logged_supabase_errors.add(operation)
            print(f"[DB] Notice: Supabase {operation} table not migrated yet. Operating reliably on local SQLite.")

    def _get_utc_now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _sync_init_sqlite(self):
        os.makedirs(os.path.dirname(self.sqlite_path) or ".", exist_ok=True)
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    target_country TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    problem_statement TEXT NOT NULL,
                    solution_description TEXT NOT NULL,
                    target_customers TEXT NOT NULL,
                    customer_segment TEXT,
                    competitors TEXT,
                    revenue_model TEXT NOT NULL,
                    pricing_strategy TEXT,
                    budget REAL DEFAULT 0,
                    preferred_funding REAL DEFAULT 0,
                    team_size INT DEFAULT 1,
                    timeline TEXT,
                    goals TEXT,
                    notes TEXT,
                    status TEXT DEFAULT 'draft',
                    overall_score REAL,
                    viability_score REAL,
                    market_fit_score REAL,
                    financial_score REAL,
                    is_valid_rules INTEGER DEFAULT 1,
                    rules_validation TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    category TEXT,
                    storage_path TEXT,
                    size_bytes INTEGER NOT NULL,
                    sha256_hash TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    scores TEXT DEFAULT '{}',
                    version INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'generated',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(project_id, report_type)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    scenario_name TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    projections TEXT NOT NULL,
                    ai_commentary TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    duration_ms INTEGER DEFAULT 0,
                    llm_provider TEXT,
                    llm_model TEXT,
                    summary TEXT,
                    payload TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_discussions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    agent_role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    reply_to TEXT,
                    step_index INTEGER DEFAULT 0,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    async def init_sqlite(self):
        await asyncio.to_thread(self._sync_init_sqlite)

    # ------------------ PROJECT OPERATIONS ------------------
    def _sync_create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        project_id = data.get("id") or str(uuid.uuid4())
        now = self._get_utc_now()
        data["id"] = project_id
        data["created_at"] = now
        data["updated_at"] = now
        data.setdefault("user_id", "default_founder")

        with sqlite3.connect(self.sqlite_path) as conn:
            goals_json = json.dumps(data.get("goals", []))
            rules_json = json.dumps(data.get("rules_validation", {}))
            conn.execute("""
                INSERT INTO projects (
                    id, user_id, name, industry, target_country, currency, stage,
                    problem_statement, solution_description, target_customers, customer_segment,
                    competitors, revenue_model, pricing_strategy, budget, preferred_funding,
                    team_size, timeline, goals, notes, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id, data["user_id"], data.get("name", ""), data.get("industry", ""),
                data.get("target_country", "United States"), data.get("currency", "USD"),
                data.get("stage", "idea"), data.get("problem_statement", ""),
                data.get("solution_description", ""), data.get("target_customers", ""),
                data.get("customer_segment", ""), data.get("competitors", ""),
                data.get("revenue_model", ""), data.get("pricing_strategy", ""),
                data.get("budget", 0), data.get("preferred_funding", 0),
                data.get("team_size", 1), data.get("timeline", "12 months"),
                goals_json, data.get("notes", ""), data.get("status", "draft"),
                now, now
            ))
            conn.commit()
            return data

    async def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_supabase and self.supabase_client:
            try:
                clean_data = {k: v for k, v in data.items() if k != "goals_text"}
                res = self.supabase_client.table("projects").insert(clean_data).execute()
                if res.data and len(res.data) > 0:
                    return cast(Dict[str, Any], res.data[0])
            except Exception as e:
                self._log_supabase_fallback("insert projects", e)
        return await asyncio.to_thread(self._sync_create_project, data)

    def _sync_get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["goals"] = json.loads(res.get("goals") or "[]")
            res["rules_validation"] = json.loads(res.get("rules_validation") or "{}")
            return res

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        if self.use_supabase and self.supabase_client:
            try:
                res = self.supabase_client.table("projects").select("*").eq("id", project_id).execute()
                if res.data and len(res.data) > 0:
                    return cast(Dict[str, Any], res.data[0])
            except Exception as e:
                self._log_supabase_fallback("get project", e)
        return await asyncio.to_thread(self._sync_get_project, project_id)

    def _sync_update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates["updated_at"] = self._get_utc_now()
        with sqlite3.connect(self.sqlite_path) as conn:
            set_clauses = []
            values = []
            for k, v in updates.items():
                if k in ("goals", "rules_validation") and isinstance(v, (dict, list)):
                    v = json.dumps(v)
                set_clauses.append(f"{k} = ?")
                values.append(v)
            values.append(project_id)
            conn.execute(f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ?", values)
            conn.commit()
        return self._sync_get_project(project_id)

    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.use_supabase and self.supabase_client:
            try:
                res = self.supabase_client.table("projects").update(updates).eq("id", project_id).execute()
                if res.data and len(res.data) > 0:
                    return cast(Dict[str, Any], res.data[0])
            except Exception as e:
                self._log_supabase_fallback("update project", e)
        return await asyncio.to_thread(self._sync_update_project, project_id, updates)

    def _sync_delete_project(self, project_id: str) -> bool:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.execute("DELETE FROM reports WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM simulations WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM agent_logs WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM agent_discussions WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM documents WHERE project_id = ?", (project_id,))
            conn.commit()
            return True

    async def delete_project(self, project_id: str) -> bool:
        if self.use_supabase and self.supabase_client:
            try:
                self.supabase_client.table("reports").delete().eq("project_id", project_id).execute()
                self.supabase_client.table("simulations").delete().eq("project_id", project_id).execute()
                self.supabase_client.table("agent_discussions").delete().eq("project_id", project_id).execute()
                self.supabase_client.table("documents").delete().eq("project_id", project_id).execute()
                self.supabase_client.table("projects").delete().eq("id", project_id).execute()
            except Exception as e:
                self._log_supabase_fallback("delete project", e)
        return await asyncio.to_thread(self._sync_delete_project, project_id)

    def _sync_list_projects(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
            rows = cursor.fetchall()
            projects = []
            for r in rows:
                p = dict(r)
                p["goals"] = json.loads(p.get("goals") or "[]")
                p["rules_validation"] = json.loads(p.get("rules_validation") or "{}")
                projects.append(p)
            return projects

    async def list_projects(self, user_id: str = "default_founder") -> List[Dict[str, Any]]:
        if self.use_supabase and self.supabase_client:
            try:
                res = self.supabase_client.table("projects").select("*").order("created_at", desc=True).execute()
                if res.data:
                    return cast(List[Dict[str, Any]], res.data)
            except Exception as e:
                self._log_supabase_fallback("list projects", e)
        return await asyncio.to_thread(self._sync_list_projects)

    # ------------------ REPORT OPERATIONS ------------------
    def _sync_save_report(
        self,
        project_id: str,
        report_type: str,
        title: str,
        content: Dict[str, Any],
        scores: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        report_id = str(uuid.uuid4())
        now = self._get_utc_now()
        scores_data = scores or {}
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("""
                INSERT INTO reports (id, project_id, report_type, title, content, scores, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'generated', ?, ?)
                ON CONFLICT(project_id, report_type) DO UPDATE SET
                    title=excluded.title,
                    content=excluded.content,
                    scores=excluded.scores,
                    status='generated',
                    updated_at=excluded.updated_at
            """, (report_id, project_id, report_type, title, json.dumps(content), json.dumps(scores_data), now, now))
            conn.commit()
            return {"project_id": project_id, "report_type": report_type, "title": title, "content": content, "scores": scores_data}

    async def save_report(
        self,
        project_id: str,
        report_type: str,
        title: str,
        content: Dict[str, Any],
        scores: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.use_supabase and self.supabase_client:
            try:
                now = self._get_utc_now()
                res = self.supabase_client.table("reports").upsert({
                    "project_id": project_id,
                    "report_type": report_type,
                    "title": title,
                    "content": content,
                    "scores": scores or {},
                    "status": "generated",
                    "updated_at": now
                }, on_conflict="project_id,report_type").execute()
                if res.data and len(res.data) > 0:
                    return cast(Dict[str, Any], res.data[0])
            except Exception as e:
                self._log_supabase_fallback("save report", e)
        return await asyncio.to_thread(self._sync_save_report, project_id, report_type, title, content, scores)

    def _sync_get_reports(self, project_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM reports WHERE project_id = ?", (project_id,))
            rows = cursor.fetchall()
            reports = []
            for r in rows:
                rep = dict(r)
                rep["content"] = json.loads(rep.get("content") or "{}")
                rep["scores"] = json.loads(rep.get("scores") or "{}")
                reports.append(rep)
            return reports

    async def get_reports(self, project_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase and self.supabase_client:
            try:
                res = self.supabase_client.table("reports").select("*").eq("project_id", project_id).execute()
                if res.data:
                    return cast(List[Dict[str, Any]], res.data)
            except Exception as e:
                self._log_supabase_fallback("get reports", e)
        return await asyncio.to_thread(self._sync_get_reports, project_id)

    # ------------------ SIMULATION OPERATIONS ------------------
    def _sync_save_simulation(
        self,
        project_id: str,
        scenario_name: str,
        parameters: Dict[str, Any],
        projections: Dict[str, Any],
        commentary: str = ""
    ) -> Dict[str, Any]:
        sim_id = str(uuid.uuid4())
        now = self._get_utc_now()
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("""
                INSERT INTO simulations (id, project_id, scenario_name, parameters, projections, ai_commentary, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sim_id, project_id, scenario_name, json.dumps(parameters), json.dumps(projections), commentary, now, now))
            conn.commit()
            return {"id": sim_id, "project_id": project_id, "scenario_name": scenario_name}

    async def save_simulation(
        self,
        project_id: str,
        scenario_name: str,
        parameters: Dict[str, Any],
        projections: Dict[str, Any],
        commentary: str = ""
    ) -> Dict[str, Any]:
        if self.use_supabase and self.supabase_client:
            try:
                now = self._get_utc_now()
                res = self.supabase_client.table("simulations").insert({
                    "project_id": project_id,
                    "scenario_name": scenario_name,
                    "parameters": parameters,
                    "projections": projections,
                    "ai_commentary": commentary,
                    "created_at": now,
                    "updated_at": now
                }).execute()
                if res.data and len(res.data) > 0:
                    return cast(Dict[str, Any], res.data[0])
            except Exception as e:
                self._log_supabase_fallback("save simulation", e)
        return await asyncio.to_thread(self._sync_save_simulation, project_id, scenario_name, parameters, projections, commentary)

    # ------------------ AGENT DISCUSSIONS ------------------
    def _sync_add_agent_discussion(self, project_id: str, agent_name: str, agent_role: str, message: str, step_index: int = 0):
        disc_id = str(uuid.uuid4())
        now = self._get_utc_now()
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("""
                INSERT INTO agent_discussions (id, project_id, agent_name, agent_role, message_content, step_index, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (disc_id, project_id, agent_name, agent_role, message, step_index, now))
            conn.commit()

    async def add_agent_discussion(self, project_id: str, agent_name: str, agent_role: str, message: str, step_index: int = 0):
        if self.use_supabase and self.supabase_client:
            try:
                now = self._get_utc_now()
                self.supabase_client.table("agent_discussions").insert({
                    "project_id": project_id,
                    "agent_name": agent_name,
                    "agent_role": agent_role,
                    "message_content": message,
                    "step_index": step_index,
                    "timestamp": now
                }).execute()
                return
            except Exception as e:
                self._log_supabase_fallback("add discussion", e)
        await asyncio.to_thread(self._sync_add_agent_discussion, project_id, agent_name, agent_role, message, step_index)

    def _sync_get_agent_discussions(self, project_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM agent_discussions WHERE project_id = ? ORDER BY step_index ASC", (project_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_agent_discussions(self, project_id: str) -> List[Dict[str, Any]]:
        if self.use_supabase and self.supabase_client:
            try:
                res = self.supabase_client.table("agent_discussions").select("*").eq("project_id", project_id).order("step_index", desc=False).execute()
                if res.data:
                    return cast(List[Dict[str, Any]], res.data)
            except Exception as e:
                self._log_supabase_fallback("get discussions", e)
        return await asyncio.to_thread(self._sync_get_agent_discussions, project_id)

db = Database()
