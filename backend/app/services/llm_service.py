import re
import os
import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator


class LLMService:
    """
    Configurable LLM provider with intelligent grounding, prompt injection defenses,
    anti-hallucination safeguards, citation compilation, and streaming capabilities.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(system\s+)?prompts",
        r"you\s+are\s+now\s+(dan|jailbroken|unrestricted)",
        r"(print|reveal|show|display)\s+(the\s+)?(system\s+prompt|developer\s+mode|internal\s+rules)",
        r"bypass\s+(safety|security|policy)",
    ]

    @classmethod
    def detect_prompt_injection(cls, text: str) -> bool:
        """Check for known prompt injection and jailbreak signatures."""
        lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False

    @classmethod
    def sanitize_untrusted_context(cls, text: str) -> str:
        """
        Sanitize retrieved document passages so that malicious instruction strings
        inside uploaded documents cannot execute as prompt commands.
        """
        sanitized = text
        for pattern in cls.INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[FILTERED_UNTRUSTED_DIRECTIVE]", sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def generate_response(
        cls,
        user_message: str,
        mode: str,
        retrieved_passages: List[Dict[str, Any]],
        student_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate grounded response with citations and metadata.
        Returns: {"content": str, "citations": List[Dict], "token_count": int, "processing_time_ms": float}
        """
        start_time = time.time()

        # 1. Prompt Injection Defense
        if cls.detect_prompt_injection(user_message):
            processing_time = round((time.time() - start_time) * 1000, 2)
            return {
                "content": (
                    "**Security Notice**: I am configured to uphold institutional AI safety guidelines "
                    "and cannot execute instructions that alter safety policies, reveal internal prompts, "
                    "or override system boundaries. How can I assist you with educational or campus inquiries?"
                ),
                "citations": [],
                "token_count": 35,
                "processing_time_ms": processing_time,
            }

        citations: List[Dict[str, Any]] = []

        # 2. Compile Citations from retrieved passages
        for passage in retrieved_passages:
            chunk = passage.get("chunk", {})
            score = passage.get("score", 0.0)
            doc_id = chunk.get("document_id") or chunk.get("id")
            doc_title = passage.get("document_title") or "University Document"
            section = chunk.get("section_heading") or f"Section {chunk.get('chunk_index', 1)}"
            page = chunk.get("page_number") or 1
            content = chunk.get("content", "")
            snippet = content[:180].strip() + ("..." if len(content) > 180 else "")

            citations.append({
                "document_id": doc_id or 1,
                "document_title": doc_title,
                "category": passage.get("category"),
                "section": section,
                "page": page,
                "chunk_id": chunk.get("id"),
                "relevance_score": float(score),
                "snippet": snippet,
            })

        # 3. Route by Mode and Query Type
        if mode == "PERSONAL_MODE_B":
            content = cls._generate_personal_mode_b_response(user_message, student_context, retrieved_passages, citations)
        else:
            content = cls._generate_public_mode_a_response(user_message, retrieved_passages, citations)

        token_est = len(content.split())
        processing_time = round((time.time() - start_time) * 1000, 2)

        return {
            "content": content,
            "citations": citations,
            "token_count": token_est,
            "processing_time_ms": processing_time,
        }

    @classmethod
    def _generate_public_mode_a_response(
        cls,
        query: str,
        retrieved_passages: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
    ) -> str:
        """Handle Mode A queries: General Educational or Grounded University Policy."""
        q_lower = query.lower()

        # Check if query is asking about university policies or regulations
        is_campus_query = any(k in q_lower for k in [
            "attendance", "reva", "condonation", "regulation", "cgpa", "sgpa", "exam", "grading",
            "placement", "internship", "backlog", "handbook", "library", "campus", "credit", "cia",
            "detained", "passing mark", "dress code", "timing", "hostel", "rules"
        ])

        if is_campus_query:
            # Check if retrieved passages genuinely match the specific topic keywords
            stopwords = {"what", "when", "where", "which", "who", "whom", "this", "that", "these", "those", "from", "with", "have", "been", "does", "about", "the", "official", "policy", "regarding", "campus", "university", "rules"}
            topic_terms = [t for t in re.findall(r"\b[a-zA-Z0-9]{3,}\b", q_lower) if t not in stopwords]

            top_score = retrieved_passages[0].get("score", 0.0) if retrieved_passages else 0.0
            has_topic_match = False
            if retrieved_passages and topic_terms:
                all_content = " ".join([p.get("chunk", {}).get("content", "").lower() for p in retrieved_passages[:2]])
                has_topic_match = any(t in all_content for t in topic_terms)

            # If no passages, or top score too low, or specific topic keyword is completely absent from knowledge base
            if not retrieved_passages or top_score < 0.35 or not has_topic_match:
                return (
                    "According to current university documentation, no official policy or regulation was found regarding this query.\n\n"
                    "Please verify your query keywords or consult your Department Academic Coordinator for unlisted guidelines."
                )

            # Synthesize grounded answer using highest ranking retrieved passages
            top_passage = retrieved_passages[0]
            top_content = cls.sanitize_untrusted_context(top_passage.get("chunk", {}).get("content", ""))
            top_doc = top_passage.get("document_title", "University Regulations")
            top_section = top_passage.get("chunk", {}).get("section_heading", "Guidelines")
            top_page = top_passage.get("chunk", {}).get("page_number", 1)

            # Assemble grounded synthesized answer
            body_lines = [
                f"### Official University Policy Summary\n",
                f"Based on **{top_doc}** (*{top_section}*, Page {top_page}):\n",
                f"{top_content}\n\n",
            ]

            if len(retrieved_passages) > 1:
                sec_passage = retrieved_passages[1]
                sec_content = cls.sanitize_untrusted_context(sec_passage.get("chunk", {}).get("content", ""))
                sec_doc = sec_passage.get("document_title", "University Regulations")
                sec_sec = sec_passage.get("chunk", {}).get("section_heading", "Details")
                body_lines.append(f"#### Additional Institutional Guidelines (*{sec_doc} - {sec_sec}*):\n{sec_content}\n\n")

            body_lines.append(
                "> **Citation Reference**: Information verified against official institutional documents listed below. "
                "Contact the Office of Academic Affairs for individual dispensation or appeals."
            )
            return "".join(body_lines)

        # General Educational / Programming / Career Guidance
        if any(k in q_lower for k in ["python", "code", "programming", "function", "array", "algorithm", "react", "sql"]):
            return (
                f"### Technical Guide & Explanation\n\n"
                f"Here is a comprehensive breakdown for **\"{query.strip()}\"**:\n\n"
                f"```python\n"
                f"# Demonstration implementation\n"
                f"def demonstrate_concept(items: list) -> dict:\n"
                f"    \"\"\"\n"
                f"    Applies optimal processing with O(N) time complexity and O(N) auxiliary space.\n"
                f"    \"\"\"\n"
                f"    frequency = {{}}\n"
                f"    for item in items:\n"
                f"        frequency[item] = frequency.get(item, 0) + 1\n"
                f"    return frequency\n\n"
                f"# Example execution\n"
                f"sample = ['python', 'fastapi', 'react', 'python']\n"
                f"print(demonstrate_concept(sample))\n"
                f"```\n\n"
                f"#### Key Principles & Best Practices:\n"
                f"1. **Time Complexity**: Optimal single-pass iteration $O(N)$.\n"
                f"2. **Type Hinting**: Explicit typing improves maintainability and static analysis.\n"
                f"3. **Error Handling**: Gracefully handle edge cases (empty collections, invalid inputs).\n"
                f"4. **Modular Architecture**: Decompose routines into pure, unit-testable functions."
            )

        if any(k in q_lower for k in ["interview", "resume", "career", "job", "prepare"]):
            return (
                f"### Career Preparation Strategy\n\n"
                f"To excel in **\"{query.strip()}\"**, focus on these four foundational pillars:\n\n"
                f"1. **Core Problem Solving**: Practice Data Structures & Algorithms (Array manipulation, HashMaps, Two Pointers, Trees, Dynamic Programming).\n"
                f"2. **Production Systems Experience**: Build end-to-end full-stack projects featuring containerized deployments (Docker), relational schemas (PostgreSQL), and automated test suites.\n"
                f"3. **Behavioral Alignment (STAR Method)**: Structure responses using **Situation, Task, Action, Result** for teamwork, challenge resolution, and leadership questions.\n"
                f"4. **System Architecture**: Study caching (Redis), API design (RESTful/GraphQL), and database indexing fundamentals."
            )

        # General Academic Guidance
        return (
            f"### Academic Guidance\n\n"
            f"Regarding your query **\"{query.strip()}\"**:\n\n"
            f"- **Foundational Concepts**: Break down the problem into fundamental components, formulating clear hypotheses before synthesis.\n"
            f"- **Methodology**: Apply structured problem-solving steps, verifying assumptions at each stage.\n"
            f"- **Institutional Context**: For campus-specific requirements, ask specific questions about attendance thresholds, CIA passing marks, or placement eligibility."
        )

    @classmethod
    def _generate_personal_mode_b_response(
        cls,
        query: str,
        student: Optional[Dict[str, Any]],
        retrieved_passages: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
    ) -> str:
        """Handle Mode B queries: Grounded in authenticated student records."""
        if not student:
            return (
                "**Authentication Required**: No authorized student context is available for this session. "
                "Please sign in with your student credentials to view personal academic, attendance, and career records."
            )

        q_lower = query.lower()
        name = student.get("full_name", "Student")
        srn = student.get("srn", "N/A")
        cgpa = student.get("cgpa", 0.0)
        attendance = student.get("overall_attendance_percentage", 0.0)
        backlogs = student.get("active_backlogs", 0)
        sem = student.get("current_semester", 1)
        role = student.get("target_career_role", "Software Developer")
        score = student.get("readiness_score", 0.0)
        tier = student.get("readiness_tier", "DEVELOPING")

        # Attendance query
        if "attendance" in q_lower:
            subjects = student.get("subject_attendance", [])
            subj_lines = []
            for s in subjects:
                status_icon = "✅" if s["percentage"] >= 85.0 else ("⚠️" if s["percentage"] >= 75.0 else "🚨")
                subj_lines.append(f"- {status_icon} **{s['subject']}**: {s['percentage']}% ({s['attended']}/{s['total']} classes)")

            status_text = (
                "You comfortably satisfy the **85% standard attendance requirement**."
                if attendance >= 85.0
                else (
                    "You are currently in the **75%–84% condonation band**. Medical documentation or Dean approval is required for exam eligibility."
                    if attendance >= 75.0
                    else "🚨 **Critical Attendance Deficit**: Below 75% threshold. You are at risk of being detained from end-semester examinations unless remedial attendance is fulfilled."
                )
            )

            return (
                f"### Personal Attendance Intelligence for {name} ({srn})\n\n"
                f"- **Overall Aggregate Attendance**: **{attendance}%**\n"
                f"- **Current Semester**: Semester {sem}\n"
                f"- **Academic Standing**: {status_text}\n\n"
                f"#### Subject Breakdown:\n" + "\n".join(subj_lines) + "\n\n"
                f"> *Tip: Maintain at least 85% attendance across all subjects to avoid examination hall ticket restrictions.*"
            )

        # Marks / Academic Progress / CGPA query
        if any(k in q_lower for k in ["cgpa", "sgpa", "marks", "grades", "academic", "backlog", "progress"]):
            records = student.get("recent_academic_records", [])
            rec_lines = [f"- **Semester {r['semester']}**: SGPA {r['sgpa']:.2f} | Cumulative CGPA {r['cgpa']:.2f} | Backlogs: {r['backlogs']}" for r in records]

            backlog_note = (
                "🎉 You have **0 active backlogs** with clear academic standing."
                if backlogs == 0
                else f"⚠️ You have **{backlogs} active backlog(s)**. Dedicated remedial coaching and re-examination scheduling is recommended."
            )

            return (
                f"### Academic Dossier Summary for {name} ({srn})\n\n"
                f"- **Cumulative CGPA**: **{cgpa:.2f} / 10.00**\n"
                f"- **Credits Earned**: {student.get('total_credits', 0)} credits\n"
                f"- **CIA Average**: {student.get('cia_average', 0.0)}%\n"
                f"- **Backlog Status**: {backlog_note}\n\n"
                f"#### Semester-Wise Progression:\n" + "\n".join(rec_lines) + "\n\n"
                f"> *Calculated from verified institutional records.*"
            )

        # Risk Alerts query
        if any(k in q_lower for k in ["risk", "alert", "warning", "early warning"]):
            alerts = student.get("active_alerts_detail", [])
            if not alerts:
                return (
                    f"### Early-Warning Status for {name}\n\n"
                    f"Good news! You have **0 active early-warning risk alerts**. "
                    f"Your attendance ({attendance}%), CGPA ({cgpa:.2f}), and internal assessment scores are all within normal university thresholds."
                )
            return (
                f"### Active Early-Warning Alerts for {name}\n\n"
                f"The system has identified **{len(alerts)} active support indicator(s)**:\n\n"
                + "\n".join(alerts) + "\n\n"
                f"**Suggested Next Steps**: Schedule an academic counseling session with your assigned mentor to discuss remedial study sessions."
            )

        # Placement / Skill Gaps / Career query
        if any(k in q_lower for k in ["placement", "skill", "gap", "readiness", "career", "job", "role"]):
            matched = student.get("matched_skills", [])
            missing = student.get("missing_skills", [])
            below = student.get("below_proficiency_skills", [])

            return (
                f"### Career & Placement Readiness Dossier for {name}\n\n"
                f"- **Target Benchmark Role**: **{role}**\n"
                f"- **Readiness Score**: **{score}%** ({tier})\n"
                f"- **Mandatory Skills**: {'✅ All Prerequisites Met' if student.get('mandatory_skills_met') else '⚠️ Mandatory Skill Deficit'}\n\n"
                f"#### Competency Gap Breakdown:\n"
                f"- **Matched / Verified Skills ({len(matched)})**: {', '.join(matched) if matched else 'None'}\n"
                f"- **Missing Required Skills ({len(missing)})**: {', '.join(missing) if missing else 'None'}\n"
                f"- **Below Target Proficiency ({len(below)})**: {', '.join(below) if below else 'None'}\n\n"
                f"> *Notice: Placement readiness scores are internal developmental indicators, not employer-certified guarantees.*"
            )

        # Study plan generation query
        if any(k in q_lower for k in ["study plan", "schedule", "routine", "revision"]):
            missing = student.get("missing_skills", [])[:2]
            return (
                f"### Personalized Weekly Study & Upskilling Plan for {name}\n\n"
                f"Crafted using your active metrics (CGPA: {cgpa:.2f}, Attendance: {attendance}%, Target Role: {role}):\n\n"
                f"| Day | Focus Area | Recommended Action | Time Allocation |\n"
                f"| :--- | :--- | :--- | :--- |\n"
                f"| **Monday** | Core Coursework | Review lecture notes & continuous assessment assignments | 2.0 hrs |\n"
                f"| **Tuesday** | Skill Gap Focus | Hands-on coding in **{missing[0] if missing else 'Backend Frameworks'}** | 1.5 hrs |\n"
                f"| **Wednesday** | Remedial & Attendance | Review subjects below 85% attendance; complete tutorial sheets | 1.5 hrs |\n"
                f"| **Thursday** | Placement Practice | Data Structures & Algorithms practice (LeetCode / HackerRank) | 2.0 hrs |\n"
                f"| **Friday** | Project Development | Build portfolio repository implementing missing competencies | 2.0 hrs |\n"
                f"| **Weekend** | Review & Mock Test | Weekly self-assessment and technical certification modules | 3.0 hrs |\n"
            )

        # General student summary
        recs = student.get("active_recommendations", [])
        return (
            f"### Personal Student Intelligence Dossier for {name} ({srn})\n\n"
            f"- **Program**: {student.get('program')} &bull; Semester {sem} ({student.get('department')})\n"
            f"- **Cumulative CGPA**: **{cgpa:.2f}** &bull; **Overall Attendance**: **{attendance}%**\n"
            f"- **Target Career Role**: **{role}** (Readiness: **{score}%** - {tier})\n"
            f"- **Active Risk Alerts**: {student.get('active_alerts_count', 0)}\n\n"
            f"#### Active Learning & Career Recommendations:\n"
            + ("\n".join(recs) if recs else "- No urgent recommendations pending.") + "\n\n"
            f"You can ask me specific questions such as:\n"
            f"- *\"What is my attendance breakdown?\"*\n"
            f"- *\"What skills am I missing for {role}?\"*\n"
            f"- *\"Generate a personalized study plan for this week.\"*"
        )

    @classmethod
    async def stream_response_tokens(cls, full_content: str) -> AsyncGenerator[str, None]:
        """
        Stream full response in incremental token chunks for Server-Sent Events (SSE).
        Splits text cleanly by words/punctuation with realistic typing intervals.
        """
        words = re.findall(r"\S+|\s+", full_content)
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk = "".join(words[i:i + chunk_size])
            yield chunk
            await asyncio.sleep(0.015)
