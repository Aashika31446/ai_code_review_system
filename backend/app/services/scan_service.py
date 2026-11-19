import os
import sys
import ast
import re
import uuid
import logging
import inspect
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

# Dynamic path resolution for sibling packages
current_dir = os.path.dirname(os.path.abspath(__file__))
# Check both 3 levels up (inside app/services) and 2 levels up
sibling_candidates = [
    os.path.abspath(os.path.join(current_dir, "..", "..", "..")),
    os.path.abspath(os.path.join(current_dir, "..", ".."))
]

for base_dir in sibling_candidates:
    analyzer_candidate = os.path.join(base_dir, "code-analyzer")
    if os.path.exists(analyzer_candidate) and analyzer_candidate not in sys.path:
        sys.path.insert(0, analyzer_candidate)
    ai_candidate = os.path.join(base_dir, "ai-engine")
    if os.path.exists(ai_candidate) and ai_candidate not in sys.path:
        sys.path.insert(0, ai_candidate)

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.scan import Scan
from app.models.finding import Finding
from app.models.ai_review import AIReview
from app.models.project import Project
from app.schemas.scan import DashboardStats, ScanResponse
from app.utils.file_utils import get_python_files, get_code_snippet, cleanup_directory

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Built-in Static Analysis Fallback (AST + Pattern Engine)
# -------------------------------------------------------------------------
class ASTSecurityVisitor(ast.NodeVisitor):
    """AST visitor that checks for common Python security vulnerabilities and bug risks."""

    def __init__(self, filename: str, relative_path: str):
        self.filename = filename
        self.relative_path = relative_path
        self.findings: List[Dict[str, Any]] = []

    def visit_Call(self, node: ast.Call):
        # Detect eval() and exec()
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in ("eval", "exec"):
            self.findings.append({
                "file": self.relative_path,
                "line": node.lineno,
                "category": "security",
                "severity": "critical",
                "rule": "SEC-001-DANGEROUS-EVAL",
                "message": f"Dangerous usage of '{func_name}()' can lead to arbitrary remote code execution."
            })

        # Detect os.system and shell=True in subprocess
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "system" and isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                self.findings.append({
                    "file": self.relative_path,
                    "line": node.lineno,
                    "category": "security",
                    "severity": "high",
                    "rule": "SEC-004-SHELL-INJECTION",
                    "message": "Use of 'os.system()' can be exploited for command injection; use subprocess with argument lists."
                })

            if node.func.attr in ("Popen", "run", "call", "check_call", "check_output"):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.findings.append({
                            "file": self.relative_path,
                            "line": node.lineno,
                            "category": "security",
                            "severity": "high",
                            "rule": "SEC-004-SUBPROCESS-SHELL",
                            "message": "Executing subprocess with 'shell=True' opens risk of command injection."
                        })

        # Detect open() calls without with statement - rough check
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Detect mutable default arguments
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append({
                    "file": self.relative_path,
                    "line": node.lineno,
                    "category": "bug_risk",
                    "severity": "medium",
                    "rule": "BUG-002-MUTABLE-DEFAULT-ARG",
                    "message": f"Function '{node.name}' uses a mutable default argument which is retained across calls."
                })

        # Check for too many parameters
        if len(node.args.args) > 7:
            self.findings.append({
                "file": self.relative_path,
                "line": node.lineno,
                "category": "style",
                "severity": "low",
                "rule": "STY-001-TOO-MANY-ARGS",
                "message": f"Function '{node.name}' defines {len(node.args.args)} arguments. Consider grouping into a data class."
            })

        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Bare except:
        if node.type is None:
            self.findings.append({
                "file": self.relative_path,
                "line": node.lineno,
                "category": "bug_risk",
                "severity": "medium",
                "rule": "BUG-001-BARE-EXCEPT",
                "message": "Bare 'except:' catches system exit and keyboard interrupt signals, masking fatal errors."
            })
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        # None comparison using == or !=
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(comparator, ast.Constant) and comparator.value is None:
                self.findings.append({
                    "file": self.relative_path,
                    "line": node.lineno,
                    "category": "bug_risk",
                    "severity": "low",
                    "rule": "BUG-003-NONE-COMPARISON",
                    "message": "Comparison with None should use 'is' or 'is not' instead of equality operators."
                })
        self.generic_visit(node)


def run_builtin_ast_analysis(upload_dir: str) -> List[Dict[str, Any]]:
    """Analyzes all Python files in upload_dir using Python's AST and pattern matching."""
    findings: List[Dict[str, Any]] = []
    py_files = get_python_files(upload_dir)

    secret_pattern = re.compile(
        r"""(?:api_key|secret|password|passwd|private_key|auth_token)\s*=\s*['"][a-zA-Z0-9_\-\.]{8,}['"]""",
        re.IGNORECASE
    )
    sql_injection_pattern = re.compile(
        r"""(?:\.execute|\.raw)\s*\(\s*(?:f['"]|['"].*%(?:s|d)|['"].*\.format\()""",
        re.IGNORECASE
    )

    for file_path in py_files:
        rel_path = os.path.relpath(file_path, upload_dir).replace("\\", "/")
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            # Line-by-line regex scanning
            for idx, line in enumerate(lines, start=1):
                # Hardcoded secrets
                if secret_pattern.search(line) and not line.strip().startswith("#"):
                    findings.append({
                        "file": rel_path,
                        "line": idx,
                        "category": "security",
                        "severity": "high",
                        "rule": "SEC-002-HARDCODED-SECRET",
                        "message": "Possible hardcoded credential or secret key detected in source code."
                    })

                # SQL injection risk
                if sql_injection_pattern.search(line) and not line.strip().startswith("#"):
                    findings.append({
                        "file": rel_path,
                        "line": idx,
                        "category": "security",
                        "severity": "critical",
                        "rule": "SEC-003-SQL-INJECTION",
                        "message": "Potential SQL injection through raw string interpolation in query execution."
                    })

            # AST parsing
            tree = ast.parse(content, filename=file_path)
            visitor = ASTSecurityVisitor(file_path, rel_path)
            visitor.visit(tree)
            findings.extend(visitor.findings)

        except Exception as e:
            logger.warning(f"Could not parse file {file_path}: {e}")
            findings.append({
                "file": rel_path,
                "line": 1,
                "category": "syntax_error",
                "severity": "high",
                "rule": "SYNTAX-001-PARSE-FAILURE",
                "message": f"Syntax or parsing error in Python file: {str(e)}"
            })

    return findings


# -------------------------------------------------------------------------
# Code Analyzer Integration
# -------------------------------------------------------------------------
def scan_codebase(upload_dir: str) -> List[Dict[str, Any]]:
    """Invokes the external code-analyzer package if available, otherwise falls back to built-in AST analyzer."""
    findings: List[Dict[str, Any]] = []

    try:
        # Try importing code_analyzer package
        import code_analyzer
        scanner_cls = None

        if hasattr(code_analyzer, "scanner") and hasattr(code_analyzer.scanner, "CodeScanner"):
            scanner_cls = code_analyzer.scanner.CodeScanner
        elif hasattr(code_analyzer, "CodeScanner"):
            scanner_cls = code_analyzer.CodeScanner

        if scanner_cls:
            scanner = scanner_cls()
            if hasattr(scanner, "scan_directory"):
                results = scanner.scan_directory(upload_dir)
            elif hasattr(scanner, "scan"):
                results = scanner.scan(upload_dir)
            else:
                results = []

            for r in results:
                # Normalize finding structure
                if isinstance(r, dict):
                    findings.append({
                        "file": str(r.get("file", "unknown")),
                        "line": int(r.get("line", 1)),
                        "category": str(r.get("category", "general")),
                        "severity": str(r.get("severity", "medium")).lower(),
                        "rule": str(r.get("rule", "ANALYZER-001")),
                        "message": str(r.get("message", "Issue detected by code analyzer"))
                    })
                elif hasattr(r, "__dict__"):
                    findings.append({
                        "file": str(getattr(r, "file", "unknown")),
                        "line": int(getattr(r, "line", 1)),
                        "category": str(getattr(r, "category", "general")),
                        "severity": str(getattr(r, "severity", "medium")).lower(),
                        "rule": str(getattr(r, "rule", "ANALYZER-001")),
                        "message": str(getattr(r, "message", "Issue detected by code analyzer"))
                    })

            if findings:
                logger.info(f"External code_analyzer discovered {len(findings)} issues.")
                return findings

    except Exception as e:
        logger.info(f"External code-analyzer package not accessible ({e}). Running built-in AST analyzer.")

    return run_builtin_ast_analysis(upload_dir)


# -------------------------------------------------------------------------
# AI Engine Integration & Fallback Generation
# -------------------------------------------------------------------------
async def call_gemini_api(prompt: str) -> Optional[str]:
    """Calls Google Gemini API using REST endpoint."""
    if not settings.GEMINI_API_KEY:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception as e:
            logger.warning(f"Gemini API request failed: {e}")
    return None


async def call_openai_api(prompt: str) -> Optional[str]:
    """Calls OpenAI API using REST endpoint."""
    if not settings.OPENAI_API_KEY:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a senior security engineer and code reviewer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"OpenAI API request failed: {e}")
    return None


def generate_structured_fallback_review(finding: Dict[str, Any], snippet: str) -> Dict[str, str]:
    """Generates intelligent, highly actionable code review advice based on finding metadata."""
    rule = finding.get("rule", "")
    message = finding.get("message", "")
    category = finding.get("category", "")
    severity = finding.get("severity", "")
    file_name = finding.get("file", "")
    line = finding.get("line", 1)

    if "EVAL" in rule or "EXEC" in rule:
        explanation = (
            f"The code dynamically executes code strings via eval() or exec() at line {line}. "
            "Passing unsanitized user or external input allows attackers to execute arbitrary shell "
            "commands or gain unauthorized control over the server environment."
        )
        impact = (
            "Critical Severity: Remote Code Execution (RCE). An adversary can compromise the entire "
            "host machine, read sensitive environment variables, or delete data."
        )
        suggested_fix = (
            "Replace dynamic evaluation with explicit mapping dictionaries, ast.literal_eval() for "
            "safe literals, or dedicated parsing algorithms."
        )
        fixed_code = (
            "# Safe alternative using ast.literal_eval for safe literals:\n"
            "import ast\n\n"
            "# Instead of eval(user_input):\n"
            "safe_data = ast.literal_eval(user_input)\n"
        )
    elif "SECRET" in rule:
        explanation = (
            f"A hardcoded token, password, or secret was found at line {line} in {file_name}. "
            "Committing secrets to version control risks credential leak and unauthorized access."
        )
        impact = (
            "High Severity: Credential exposure. Anyone with access to the source code or git history "
            "can compromise connected databases, APIs, or infrastructure."
        )
        suggested_fix = (
            "Move sensitive credentials to an external environment variable (.env) and read them using "
            "os.environ.get() or pydantic-settings."
        )
        fixed_code = (
            "# Read secret securely from environment variable:\n"
            "import os\n\n"
            "API_KEY = os.environ.get('SERVICE_API_KEY')\n"
            "if not API_KEY:\n"
            "    raise RuntimeError('SERVICE_API_KEY environment variable is not configured')\n"
        )
    elif "SQL-INJECTION" in rule:
        explanation = (
            f"A SQL query at line {line} appears to be constructed using formatted string interpolation. "
            "Direct string concatenation into database queries enables SQL injection."
        )
        impact = (
            "Critical Severity: Data breach and unauthorized manipulation. Attackers can bypass "
            "authentication, extract confidential customer data, or drop tables."
        )
        suggested_fix = (
            "Always use parameterized queries or an ORM (like SQLAlchemy) with bound parameters."
        )
        fixed_code = (
            "# Secure parameterized query example:\n"
            "# Instead of: cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')\n"
            "cursor.execute('SELECT * FROM users WHERE id = :id', {'id': user_id})\n"
        )
    elif "SHELL" in rule:
        explanation = (
            f"Command execution with shell=True or os.system() detected at line {line}. "
            "If any argument contains unescaped user input, it leads to shell command injection."
        )
        impact = (
            "High Severity: Arbitrary OS command execution under the process's privilege context."
        )
        suggested_fix = (
            "Use subprocess.run() with a list of arguments and set shell=False (default)."
        )
        fixed_code = (
            "import subprocess\n\n"
            "# Safe invocation without shell expansion:\n"
            "result = subprocess.run(['ls', '-la', target_dir], capture_output=True, text=True, check=True)\n"
        )
    elif "BARE-EXCEPT" in rule:
        explanation = (
            f"A bare 'except:' clause is present at line {line}. This intercepts KeyboardInterrupt, "
            "SystemExit, and MemoryError, which prevents clean process shutdowns and masks actual bugs."
        )
        impact = (
            "Medium Severity: Obscures runtime errors, complicates debugging, and prevents graceful application shutdowns."
        )
        suggested_fix = (
            "Catch specific exceptions (e.g. ValueError, KeyError) or catch 'except Exception:' at a minimum."
        )
        fixed_code = (
            "# Refactored exception handler:\n"
            "try:\n"
            "    perform_operation()\n"
            "except Exception as e:\n"
            "    logger.error(f'Operation failed: {e}', exc_info=True)\n"
        )
    elif "MUTABLE-DEFAULT" in rule:
        explanation = (
            f"A function at line {line} specifies a mutable default argument (such as a list or dictionary). "
            "In Python, default arguments are evaluated only once when the function is defined, causing mutations to persist."
        )
        impact = (
            "Medium Severity: State leaks between unrelated function invocations causing subtle, intermittent bugs."
        )
        suggested_fix = (
            "Set the parameter default to None and initialize the mutable object inside the function body."
        )
        fixed_code = (
            "# Safe pattern with None default:\n"
            "def safe_function(items=None):\n"
            "    if items is None:\n"
            "        items = []\n"
            "    items.append('new_item')\n"
            "    return items\n"
        )
    else:
        explanation = (
            f"Issue detected in {file_name} at line {line} regarding rule {rule}: {message}. "
            f"Categorized under {category} with {severity} severity."
        )
        impact = (
            f"{severity.capitalize()} impact on code quality, maintainability, or application runtime safety."
        )
        suggested_fix = (
            f"Inspect line {line} in {file_name}. Adhere to standard Python best practices and refactor according to PEP 8."
        )
        fixed_code = (
            f"# Review snippet around line {line} and implement clean error handling or refactoring.\n"
            f"# Current context:\n{snippet}"
        )

    return {
        "explanation": explanation,
        "impact": impact,
        "suggested_fix": suggested_fix,
        "fixed_code": fixed_code
    }


async def review_finding(finding: Dict[str, Any], file_full_path: str) -> Dict[str, str]:
    """Generates an AI code review using the external ai-engine, configured cloud LLM, or smart fallback."""
    snippet = get_code_snippet(file_full_path, finding.get("line", 1), context=3)

    # 1. Try importing and using external ai-engine
    try:
        import ai_engine
        reviewer_cls = None
        if hasattr(ai_engine, "reviewer") and hasattr(ai_engine.reviewer, "AIReviewer"):
            reviewer_cls = ai_engine.reviewer.AIReviewer
        elif hasattr(ai_engine, "AIReviewer"):
            reviewer_cls = ai_engine.AIReviewer

        if reviewer_cls:
            reviewer = reviewer_cls()
            if hasattr(reviewer, "review_finding"):
                res = reviewer.review_finding(finding, snippet)
                if inspect.isawaitable(res):
                    res = await res
                if isinstance(res, dict) and "explanation" in res:
                    return res
    except Exception as e:
        logger.info(f"External ai-engine not used: {e}")

    # 2. Try configured Cloud LLM if keys are available
    prompt = (
        f"You are a principal security engineer conducting a code review.\n"
        f"File: {finding.get('file')}\n"
        f"Line: {finding.get('line')}\n"
        f"Severity: {finding.get('severity')}\n"
        f"Rule: {finding.get('rule')}\n"
        f"Message: {finding.get('message')}\n\n"
        f"Code Context:\n{snippet}\n\n"
        "Provide your review in valid JSON format with exactly four keys:\n"
        "{\n"
        '  "explanation": "concise explanation of the flaw",\n'
        '  "impact": "security and operational impact",\n'
        '  "suggested_fix": "clear steps to fix",\n'
        '  "fixed_code": "clean replacement code snippet"\n'
        "}"
    )

    llm_response = None
    if settings.AI_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        llm_response = await call_gemini_api(prompt)
    elif settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        llm_response = await call_openai_api(prompt)

    if llm_response:
        try:
            # Clean markdown codeblocks if returned
            clean_json = re.sub(r"^```json\s*|\s*```$", "", llm_response.strip(), flags=re.MULTILINE)
            import json
            parsed = json.loads(clean_json)
            if all(k in parsed for k in ("explanation", "impact", "suggested_fix", "fixed_code")):
                return parsed
        except Exception as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")

    # 3. Use deterministic, high-quality structured fallback
    return generate_structured_fallback_review(finding, snippet)


# -------------------------------------------------------------------------
# Core Background Scan Executor
# -------------------------------------------------------------------------
async def execute_scan_task(scan_id: UUID, upload_dir: str, db: AsyncSession) -> None:
    """Core scanning execution logic."""
    # Step 1: Update status to 'running'
    query = select(Scan).where(Scan.id == scan_id)
    result = await db.execute(query)
    scan = result.scalar_one_or_none()

    if not scan:
        logger.error(f"Scan {scan_id} not found in database.")
        cleanup_directory(upload_dir)
        return

    scan.status = "running"
    await db.commit()

    try:
        # Step 2: Discover files and invoke scanner
        py_files = get_python_files(upload_dir)
        scan.total_files = len(py_files)
        await db.commit()

        findings_data = scan_codebase(upload_dir)

        # Step 3 & 4: Review each finding and persist to DB
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for item in findings_data:
            severity = str(item.get("severity", "low")).lower()
            if severity == "critical":
                critical_count += 1
            elif severity == "high":
                high_count += 1
            elif severity == "medium":
                medium_count += 1
            else:
                severity = "low"
                low_count += 1

            finding = Finding(
                scan_id=scan.id,
                file=item.get("file", "unknown"),
                line=int(item.get("line", 1)),
                category=item.get("category", "general"),
                severity=severity,
                rule=item.get("rule", "RULE-001"),
                message=item.get("message", "Issue detected")
            )
            db.add(finding)
            await db.flush()  # Generate finding.id

            # Locate local full path for snippet extraction
            rel_file = item.get("file", "")
            full_file_path = os.path.join(upload_dir, rel_file)

            review_dict = await review_finding(item, full_file_path)

            ai_review = AIReview(
                finding_id=finding.id,
                explanation=review_dict["explanation"],
                impact=review_dict["impact"],
                suggested_fix=review_dict["suggested_fix"],
                fixed_code=review_dict["fixed_code"]
            )
            db.add(ai_review)

        # Step 5: Update scan status to 'completed' with counts
        scan.total_issues = len(findings_data)
        scan.critical_count = critical_count
        scan.high_count = high_count
        scan.medium_count = medium_count
        scan.low_count = low_count
        scan.status = "completed"
        scan.completed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Scan {scan_id} successfully completed. Total findings: {len(findings_data)}")

    except Exception as e:
        logger.exception(f"Scan {scan_id} failed with error: {e}")
        await db.rollback()
        scan.status = "failed"
        scan.completed_at = datetime.now(timezone.utc)
        await db.commit()

    finally:
        # Step 7: Clean up temporary extraction directory
        cleanup_directory(upload_dir)


async def run_scan(scan_id: UUID, upload_dir: str, db: Optional[AsyncSession] = None) -> None:
    """Entry point for running a code review scan.

    Instantiates a dedicated DB session if invoked asynchronously in background tasks.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            await execute_scan_task(scan_id, upload_dir, session)
    else:
        await execute_scan_task(scan_id, upload_dir, db)


# -------------------------------------------------------------------------
# Scan Query Services
# -------------------------------------------------------------------------
async def get_project_scans(db: AsyncSession, project_id: UUID) -> List[Scan]:
    """Retrieves all scans associated with a given project."""
    query = (
        select(Scan)
        .where(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_scan_by_id(db: AsyncSession, scan_id: UUID) -> Optional[Scan]:
    """Retrieves a scan by its UUID."""
    query = select(Scan).where(Scan.id == scan_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_scan_findings(
    db: AsyncSession,
    scan_id: UUID,
    severity: Optional[str] = None
) -> List[Finding]:
    """Retrieves findings for a scan, with optional severity filtering."""
    query = (
        select(Finding)
        .where(Finding.scan_id == scan_id)
        .options(selectinload(Finding.ai_review))
        .order_by(Finding.file, Finding.line)
    )
    if severity:
        query = query.where(Finding.severity == severity.lower().strip())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_finding_review(db: AsyncSession, finding_id: UUID) -> Optional[AIReview]:
    """Retrieves the AI review for a specific finding."""
    query = select(AIReview).where(AIReview.finding_id == finding_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_dashboard_stats(db: AsyncSession, user_id: UUID) -> DashboardStats:
    """Aggregates metrics and statistics across all projects owned by the user."""
    # Find all project IDs for user
    projects_query = select(Project.id).where(Project.user_id == user_id)
    project_result = await db.execute(projects_query)
    project_ids = [p for p in project_result.scalars().all()]

    if not project_ids:
        return DashboardStats(
            total_scans=0,
            total_issues=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            recent_scans=[]
        )

    # Aggregate stats across scans
    stats_query = select(
        func.count(Scan.id).label("total_scans"),
        func.coalesce(func.sum(Scan.total_issues), 0).label("total_issues"),
        func.coalesce(func.sum(Scan.critical_count), 0).label("critical_count"),
        func.coalesce(func.sum(Scan.high_count), 0).label("high_count"),
        func.coalesce(func.sum(Scan.medium_count), 0).label("medium_count"),
        func.coalesce(func.sum(Scan.low_count), 0).label("low_count"),
    ).where(Scan.project_id.in_(project_ids))

    stats_res = await db.execute(stats_query)
    row = stats_res.one()

    # Get 5 recent scans
    recent_query = (
        select(Scan)
        .where(Scan.project_id.in_(project_ids))
        .order_by(Scan.created_at.desc())
        .limit(5)
    )
    recent_res = await db.execute(recent_query)
    recent_scans = [ScanResponse.model_validate(s) for s in recent_res.scalars().all()]

    return DashboardStats(
        total_scans=int(row.total_scans),
        total_issues=int(row.total_issues),
        critical_count=int(row.critical_count),
        high_count=int(row.high_count),
        medium_count=int(row.medium_count),
        low_count=int(row.low_count),
        recent_scans=recent_scans
    )
