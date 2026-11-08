from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.profile import Student, Faculty
from app.models.academic import SubjectResult
from app.models.student_intelligence import (
    Skill,
    StudentSkill,
    Project,
    Certification,
)
from app.models.placement import (
    CareerRole,
    RoleSkill,
    SkillEvidence,
    PlacementOpportunity,
    OpportunityRequirement,
    StudentApplication,
)
from app.models.recommendation import RecommendationCatalogue
from app.schemas.placement import (
    SkillEvidenceBase,
    SkillEvidenceResponse,
    StudentSkillDetailResponse,
    CareerRoleResponse,
    RoleSkillResponse,
    SkillGapItem,
    PlacementReadinessResponse,
    PlacementOpportunityResponse,
    OpportunityMatchForStudent,
    StudentApplicationResponse,
)

PROFICIENCY_WEIGHTS = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}

IMPORTANCE_WEIGHTS = {
    "CRITICAL": 3.0,
    "CORE": 2.0,
    "PREFERRED": 1.0,
}

CANONICAL_ROLES_DATA = [
    {
        "code": "SOFTWARE_DEVELOPER",
        "title": "Software Developer",
        "description": "Designs, develops, tests, and deploys scalable software systems using core object-oriented principles, algorithms, and modular architecture.",
        "min_experience_level": "Entry Level",
        "average_salary_range": "8-14 LPA",
        "industry_demand": "Critical",
        "skills": [
            {"name": "Python", "category": "programming", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Java", "category": "programming", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": False},
            {"name": "Data Structures", "category": "problem_solving", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Algorithms", "category": "problem_solving", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "SQL", "category": "database", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Git Collaboration", "category": "teamwork", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "System Design", "category": "problem_solving", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
        ],
    },
    {
        "code": "FULL_STACK_DEVELOPER",
        "title": "Full Stack Developer",
        "description": "Builds end-to-end responsive web applications spanning modern frontend frameworks, backend microservices, relational databases, and containerized deployment.",
        "min_experience_level": "Entry Level",
        "average_salary_range": "9-16 LPA",
        "industry_demand": "Critical",
        "skills": [
            {"name": "React", "category": "framework", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "TypeScript", "category": "programming", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Node.js", "category": "framework", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Python", "category": "programming", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "PostgreSQL", "category": "database", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Docker", "category": "cloud", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
            {"name": "REST APIs", "category": "framework", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Git Collaboration", "category": "teamwork", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
        ],
    },
    {
        "code": "DATA_ANALYST",
        "title": "Data Analyst",
        "description": "Translates complex institutional and enterprise datasets into actionable intelligence through exploratory analysis, SQL transformations, and interactive BI dashboards.",
        "min_experience_level": "Entry Level",
        "average_salary_range": "6-11 LPA",
        "industry_demand": "High",
        "skills": [
            {"name": "SQL", "category": "database", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Python", "category": "programming", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Pandas", "category": "data_science", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Tableau", "category": "data_science", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": False},
            {"name": "Data Visualization", "category": "data_science", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Statistics", "category": "data_science", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Technical Writing", "category": "communication", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
        ],
    },
    {
        "code": "DATA_SCIENTIST",
        "title": "Data Scientist",
        "description": "Applies statistical modeling, exploratory analytics, feature engineering, and predictive algorithms to discover patterns and build predictive decision systems.",
        "min_experience_level": "Entry Level",
        "average_salary_range": "10-18 LPA",
        "industry_demand": "High",
        "skills": [
            {"name": "Python", "category": "programming", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Statistics", "category": "data_science", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Machine Learning", "category": "artificial_intelligence", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "SQL", "category": "database", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Pandas", "category": "data_science", "min_proficiency": "Advanced", "importance": "CORE", "is_mandatory": True},
            {"name": "Scikit-Learn", "category": "data_science", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Deep Learning", "category": "artificial_intelligence", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
        ],
    },
    {
        "code": "AI_ML_ENGINEER",
        "title": "AI/ML Engineer",
        "description": "Architects, trains, fine-tunes, and serves deep neural networks, computer vision pipelines, and large language models for production-scale inference.",
        "min_experience_level": "Entry Level",
        "average_salary_range": "12-22 LPA",
        "industry_demand": "Critical",
        "skills": [
            {"name": "Python", "category": "programming", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Machine Learning", "category": "artificial_intelligence", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Deep Learning", "category": "artificial_intelligence", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "PyTorch", "category": "framework", "min_proficiency": "Intermediate", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Computer Vision", "category": "artificial_intelligence", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": False},
            {"name": "NLP", "category": "artificial_intelligence", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": False},
            {"name": "Docker", "category": "cloud", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "System Design", "category": "problem_solving", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
        ],
    },
    {
        "code": "CLOUD_ENGINEER",
        "title": "Cloud Solutions Engineer",
        "description": "Deploys, manages, and secures multi-region infrastructure as code across public cloud providers (AWS, GCP, Azure) using Kubernetes and CI/CD pipelines.",
        "min_experience_level": "Entry Level",
        "average_salary_range": "10-18 LPA",
        "industry_demand": "Critical",
        "skills": [
            {"name": "Linux", "category": "cloud", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Cloud Computing", "category": "cloud", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "AWS", "category": "cloud", "min_proficiency": "Intermediate", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Docker", "category": "cloud", "min_proficiency": "Advanced", "importance": "CORE", "is_mandatory": True},
            {"name": "Kubernetes", "category": "cloud", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Terraform", "category": "cloud", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
            {"name": "Network Security", "category": "cybersecurity", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
        ],
    },
    {
        "code": "CYBERSECURITY_ANALYST",
        "title": "Cybersecurity Analyst",
        "description": "Protects digital campus networks and enterprise services by conducting threat vulnerability assessments, continuous log monitoring, encryption, and incidence mitigation.",
        "min_experience_level": "Entry Level",
        "average_salary_range": "9-16 LPA",
        "industry_demand": "High",
        "skills": [
            {"name": "Network Security", "category": "cybersecurity", "min_proficiency": "Advanced", "importance": "CRITICAL", "is_mandatory": True},
            {"name": "Linux", "category": "cloud", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Cryptography", "category": "cybersecurity", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
            {"name": "Ethical Hacking", "category": "cybersecurity", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": False},
            {"name": "SOC Analysis", "category": "cybersecurity", "min_proficiency": "Intermediate", "importance": "PREFERRED", "is_mandatory": False},
            {"name": "Python", "category": "programming", "min_proficiency": "Intermediate", "importance": "CORE", "is_mandatory": True},
        ],
    },
]

CANONICAL_OPPORTUNITIES_DATA = [
    {
        "company_name": "Google",
        "title": "Associate Software Engineer - Campus Graduate",
        "opportunity_type": "JOB",
        "role_code": "SOFTWARE_DEVELOPER",
        "location": "Bangalore",
        "work_mode": "HYBRID",
        "ctc_stipend": "24.0 LPA",
        "min_cgpa": 8.0,
        "max_backlogs": 0,
        "min_attendance": 75.0,
        "eligible_departments": ["CSE", "AI_DS", "ECE"],
        "eligible_semesters": [7, 8],
        "application_deadline": date(2026, 12, 15),
        "open_positions": 8,
        "description": "Seeking exceptional campus graduates to build large-scale cloud services, search algorithms, and distributed consumer systems.",
        "skills": [
            {"name": "Data Structures", "min_proficiency": "Advanced", "is_mandatory": True},
            {"name": "Algorithms", "min_proficiency": "Advanced", "is_mandatory": True},
            {"name": "Python", "min_proficiency": "Intermediate", "is_mandatory": True},
        ],
    },
    {
        "company_name": "Microsoft",
        "title": "Cloud & AI Solutions Engineering Intern",
        "opportunity_type": "INTERNSHIP",
        "role_code": "AI_ML_ENGINEER",
        "location": "Hyderabad",
        "work_mode": "HYBRID",
        "ctc_stipend": "75,000 / month",
        "min_cgpa": 7.5,
        "max_backlogs": 0,
        "min_attendance": 75.0,
        "eligible_departments": ["CSE", "AI_DS"],
        "eligible_semesters": [5, 6, 7],
        "application_deadline": date(2026, 11, 30),
        "open_positions": 12,
        "description": "Six-month summer internship with Azure Machine Learning team working on LLM fine-tuning, retrieval agents, and automated inference optimization.",
        "skills": [
            {"name": "Python", "min_proficiency": "Intermediate", "is_mandatory": True},
            {"name": "Machine Learning", "min_proficiency": "Intermediate", "is_mandatory": True},
            {"name": "PyTorch", "min_proficiency": "Intermediate", "is_mandatory": False},
        ],
    },
    {
        "company_name": "Amazon",
        "title": "Full Stack Software Development Engineer (SDE-1)",
        "opportunity_type": "JOB",
        "role_code": "FULL_STACK_DEVELOPER",
        "location": "Bangalore",
        "work_mode": "ONSITE",
        "ctc_stipend": "19.5 LPA",
        "min_cgpa": 7.0,
        "max_backlogs": 0,
        "min_attendance": 75.0,
        "eligible_departments": ["CSE", "AI_DS", "ECE", "MECH"],
        "eligible_semesters": [7, 8],
        "application_deadline": date(2026, 12, 5),
        "open_positions": 15,
        "description": "Build high-throughput global e-commerce portals, fulfillment microservices, and customer-facing interfaces with React and AWS.",
        "skills": [
            {"name": "React", "min_proficiency": "Advanced", "is_mandatory": True},
            {"name": "Python", "min_proficiency": "Intermediate", "is_mandatory": True},
            {"name": "PostgreSQL", "min_proficiency": "Intermediate", "is_mandatory": True},
        ],
    },
    {
        "company_name": "Cisco Systems",
        "title": "Cybersecurity & Network Defense Specialist",
        "opportunity_type": "JOB",
        "role_code": "CYBERSECURITY_ANALYST",
        "location": "Bangalore",
        "work_mode": "HYBRID",
        "ctc_stipend": "16.0 LPA",
        "min_cgpa": 7.0,
        "max_backlogs": 1,
        "min_attendance": 75.0,
        "eligible_departments": ["CSE", "AI_DS", "ECE"],
        "eligible_semesters": [7, 8],
        "application_deadline": date(2026, 12, 20),
        "open_positions": 6,
        "description": "Focus on zero-trust enterprise security architectures, firewall analytics, penetration testing, and incident investigation.",
        "skills": [
            {"name": "Network Security", "min_proficiency": "Advanced", "is_mandatory": True},
            {"name": "Linux", "min_proficiency": "Intermediate", "is_mandatory": True},
            {"name": "Cryptography", "min_proficiency": "Intermediate", "is_mandatory": False},
        ],
    },
    {
        "company_name": "Morgan Stanley",
        "title": "Institutional Data Analytics & Insights Intern",
        "opportunity_type": "INTERNSHIP",
        "role_code": "DATA_ANALYST",
        "location": "Mumbai",
        "work_mode": "HYBRID",
        "ctc_stipend": "55,000 / month",
        "min_cgpa": 7.5,
        "max_backlogs": 0,
        "min_attendance": 75.0,
        "eligible_departments": ["CSE", "AI_DS", "ECE", "MECH"],
        "eligible_semesters": [5, 6],
        "application_deadline": date(2026, 11, 28),
        "open_positions": 10,
        "description": "Analyze financial risk metrics, corporate portfolios, and equity markets using SQL, Pandas, and interactive dashboards.",
        "skills": [
            {"name": "SQL", "min_proficiency": "Advanced", "is_mandatory": True},
            {"name": "Pandas", "min_proficiency": "Intermediate", "is_mandatory": True},
            {"name": "Data Visualization", "min_proficiency": "Intermediate", "is_mandatory": True},
        ],
    },
]


class PlacementService:
    @staticmethod
    def get_or_create_skill(db: Session, name: str, category: str = "programming", description: Optional[str] = None) -> Skill:
        skill = db.query(Skill).filter(Skill.name.ilike(name.strip())).first()
        if not skill:
            skill = Skill(name=name.strip(), category=category.lower(), description=description)
            db.add(skill)
            db.commit()
            db.refresh(skill)
        return skill

    @staticmethod
    def seed_canonical_career_roles(db: Session) -> List[CareerRole]:
        seeded_roles = []
        for rdata in CANONICAL_ROLES_DATA:
            role = db.query(CareerRole).filter(CareerRole.code == rdata["code"]).first()
            if not role:
                role = CareerRole(
                    code=rdata["code"],
                    title=rdata["title"],
                    description=rdata["description"],
                    min_experience_level=rdata["min_experience_level"],
                    average_salary_range=rdata["average_salary_range"],
                    industry_demand=rdata["industry_demand"],
                    is_active=True,
                )
                db.add(role)
                db.commit()
                db.refresh(role)

            # Ensure role skills exist
            for sdata in rdata["skills"]:
                skill = PlacementService.get_or_create_skill(db, sdata["name"], sdata["category"])
                existing_rs = db.query(RoleSkill).filter(
                    RoleSkill.role_id == role.id,
                    RoleSkill.skill_id == skill.id
                ).first()
                if not existing_rs:
                    importance = sdata.get("importance", "CORE")
                    weight = IMPORTANCE_WEIGHTS.get(importance, 2.0)
                    rs = RoleSkill(
                        role_id=role.id,
                        skill_id=skill.id,
                        min_proficiency=sdata.get("min_proficiency", "Intermediate"),
                        importance=importance,
                        importance_weight=weight,
                        is_mandatory=sdata.get("is_mandatory", True),
                    )
                    db.add(rs)
            db.commit()
            seeded_roles.append(role)
        return seeded_roles

    @staticmethod
    def seed_canonical_opportunities(db: Session) -> List[PlacementOpportunity]:
        seeded_opps = []
        for odata in CANONICAL_OPPORTUNITIES_DATA:
            opp = db.query(PlacementOpportunity).filter(
                PlacementOpportunity.company_name == odata["company_name"],
                PlacementOpportunity.title == odata["title"]
            ).first()

            role = db.query(CareerRole).filter(CareerRole.code == odata["role_code"]).first()

            if not opp:
                opp = PlacementOpportunity(
                    company_name=odata["company_name"],
                    title=odata["title"],
                    opportunity_type=odata["opportunity_type"],
                    role_id=role.id if role else None,
                    location=odata["location"],
                    work_mode=odata["work_mode"],
                    ctc_stipend=odata["ctc_stipend"],
                    min_cgpa=odata["min_cgpa"],
                    max_backlogs=odata["max_backlogs"],
                    min_attendance=odata["min_attendance"],
                    eligible_departments=odata["eligible_departments"],
                    eligible_semesters=odata["eligible_semesters"],
                    application_deadline=odata["application_deadline"],
                    open_positions=odata["open_positions"],
                    description=odata["description"],
                    status="OPEN",
                )
                db.add(opp)
                db.commit()
                db.refresh(opp)

                # Add specific requirements
                for req_data in odata.get("skills", []):
                    skill = PlacementService.get_or_create_skill(db, req_data["name"])
                    req = OpportunityRequirement(
                        opportunity_id=opp.id,
                        skill_id=skill.id,
                        min_proficiency=req_data.get("min_proficiency", "Intermediate"),
                        is_mandatory=req_data.get("is_mandatory", True),
                    )
                    db.add(req)
                db.commit()
            seeded_opps.append(opp)
        return seeded_opps

    # --- Student Skills & Evidence Workflows ---
    @staticmethod
    def add_or_update_student_skill(
        db: Session,
        student_id: int,
        skill_name: str,
        category: str = "programming",
        proficiency_level: str = "Intermediate",
        evidence: Optional[SkillEvidenceBase] = None
    ) -> StudentSkill:
        skill = PlacementService.get_or_create_skill(db, skill_name, category)
        student_skill = db.query(StudentSkill).filter(
            StudentSkill.student_id == student_id,
            StudentSkill.skill_id == skill.id
        ).first()

        if not student_skill:
            student_skill = StudentSkill(
                student_id=student_id,
                skill_id=skill.id,
                proficiency_level=proficiency_level,
                is_verified=False,
            )
            db.add(student_skill)
            db.commit()
            db.refresh(student_skill)
        else:
            student_skill.proficiency_level = proficiency_level
            db.commit()
            db.refresh(student_skill)

        if evidence:
            ev = SkillEvidence(
                student_skill_id=student_skill.id,
                student_id=student_id,
                evidence_type=evidence.evidence_type,
                title=evidence.title,
                url=evidence.url,
                description=evidence.description,
                project_id=evidence.project_id,
                certification_id=evidence.certification_id,
                verification_status="SELF_REPORTED",
            )
            db.add(ev)
            db.commit()

        return student_skill

    @staticmethod
    def submit_skill_evidence(
        db: Session,
        student_id: int,
        student_skill_id: int,
        evidence: SkillEvidenceBase
    ) -> SkillEvidence:
        ev = SkillEvidence(
            student_skill_id=student_skill_id,
            student_id=student_id,
            evidence_type=evidence.evidence_type,
            title=evidence.title,
            url=evidence.url,
            description=evidence.description,
            project_id=evidence.project_id,
            certification_id=evidence.certification_id,
            verification_status="PENDING_REVIEW",
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev

    @staticmethod
    def verify_skill_evidence(
        db: Session,
        evidence_id: int,
        verifier_user_id: int,
        verification_status: str,
        feedback: Optional[str] = None
    ) -> SkillEvidence:
        ev = db.query(SkillEvidence).filter(SkillEvidence.id == evidence_id).first()
        if not ev:
            raise ValueError(f"Skill evidence record {evidence_id} not found")

        ev.verification_status = verification_status
        ev.verified_by_user_id = verifier_user_id
        ev.verified_at = datetime.now(timezone.utc)
        ev.verification_feedback = feedback

        # If verified, mark parent student skill as verified
        if verification_status == "VERIFIED":
            student_skill = db.query(StudentSkill).filter(StudentSkill.id == ev.student_skill_id).first()
            if student_skill:
                student_skill.is_verified = True

        db.commit()
        db.refresh(ev)
        return ev

    @staticmethod
    def get_student_skills_detail(db: Session, student_id: int) -> List[Dict[str, Any]]:
        st_skills = db.query(StudentSkill).filter(StudentSkill.student_id == student_id).all()
        results = []
        for s in st_skills:
            evidences = db.query(SkillEvidence).filter(SkillEvidence.student_skill_id == s.id).all()
            ev_list = []
            for ev in evidences:
                ev_list.append({
                    "id": ev.id,
                    "student_skill_id": ev.student_skill_id,
                    "student_id": ev.student_id,
                    "evidence_type": ev.evidence_type,
                    "title": ev.title,
                    "url": ev.url,
                    "description": ev.description,
                    "project_id": ev.project_id,
                    "certification_id": ev.certification_id,
                    "verification_status": ev.verification_status,
                    "verified_by_user_id": ev.verified_by_user_id,
                    "verified_at": ev.verified_at,
                    "verification_feedback": ev.verification_feedback,
                    "created_at": ev.created_at,
                })

            results.append({
                "id": s.id,
                "student_id": s.student_id,
                "skill_id": s.skill_id,
                "skill_name": s.skill.name if s.skill else "",
                "category": s.skill.category if s.skill else "programming",
                "proficiency_level": s.proficiency_level,
                "is_verified": s.is_verified,
                "evidence_count": len(ev_list),
                "evidences": ev_list,
                "created_at": s.created_at,
            })
        return results

    # --- Career Roles CRUD ---
    @staticmethod
    def get_career_roles(db: Session, is_active: Optional[bool] = None) -> List[CareerRole]:
        q = db.query(CareerRole)
        if is_active is not None:
            q = q.filter(CareerRole.is_active == is_active)
        return q.all()

    @staticmethod
    def get_career_role_by_id_or_code(db: Session, identifier: Any) -> Optional[CareerRole]:
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            return db.query(CareerRole).filter(CareerRole.id == int(identifier)).first()
        return db.query(CareerRole).filter(CareerRole.code == str(identifier).upper()).first()

    # --- Skill Gap & Readiness Calculation Engine ---
    @staticmethod
    def calculate_placement_readiness(
        db: Session,
        student_id: int,
        role_identifier: Any
    ) -> PlacementReadinessResponse:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise ValueError(f"Student {student_id} not found")

        role = PlacementService.get_career_role_by_id_or_code(db, role_identifier)
        if not role:
            # Fallback to first role
            role = db.query(CareerRole).first()
            if not role:
                PlacementService.seed_canonical_career_roles(db)
                role = db.query(CareerRole).first()

        # Student's acquired skills map
        student_skills = db.query(StudentSkill).filter(StudentSkill.student_id == student_id).all()
        student_skill_map = {}
        for ss in student_skills:
            if ss.skill:
                student_skill_map[ss.skill.name.lower()] = {
                    "proficiency": ss.proficiency_level,
                    "proficiency_val": PROFICIENCY_WEIGHTS.get(ss.proficiency_level.lower(), 2),
                    "is_verified": ss.is_verified,
                    "evidence_count": len(ss.evidence_records) if hasattr(ss, "evidence_records") else 0,
                }

        # Role's required skills
        role_skills = db.query(RoleSkill).filter(RoleSkill.role_id == role.id).all()
        if not role_skills:
            role_skills = []

        total_weight = 0.0
        earned_weight = 0.0
        matched_count = 0
        below_count = 0
        missing_count = 0
        unverified_count = 0
        mandatory_all_met = True
        gap_items: List[SkillGapItem] = []

        # Catalogue lookup for missing skill suggestions
        catalogue_items = db.query(RecommendationCatalogue).filter(RecommendationCatalogue.status == "Active").all()

        for rs in role_skills:
            s_name = rs.skill.name if rs.skill else "Unknown Skill"
            s_cat = rs.skill.category if rs.skill else "programming"
            req_prof = rs.min_proficiency
            req_val = PROFICIENCY_WEIGHTS.get(req_prof.lower(), 2)
            weight = rs.importance_weight or IMPORTANCE_WEIGHTS.get(rs.importance, 2.0)
            total_weight += weight

            st_info = student_skill_map.get(s_name.lower())

            if st_info:
                st_prof = st_info["proficiency"]
                st_val = st_info["proficiency_val"]
                is_ver = st_info["is_verified"]

                if not is_ver:
                    unverified_count += 1

                if st_val >= req_val:
                    # Full credit
                    earned_weight += weight
                    matched_count += 1
                    status = "REQUIRES_VERIFICATION" if not is_ver else "MATCHED"
                    suggested_imp = "Verified competency meets role benchmark." if is_ver else "Submit project or certification evidence to verify proficiency."
                else:
                    # Partial credit proportional to proficiency shortfall
                    partial_ratio = max(0.2, st_val / float(req_val))
                    earned_weight += (weight * partial_ratio)
                    below_count += 1
                    status = "BELOW_PROFICIENCY"
                    if rs.is_mandatory:
                        mandatory_all_met = False
                    suggested_imp = f"Advance proficiency from {st_prof} to {req_prof} through hands-on practice."
            else:
                # Missing skill
                missing_count += 1
                status = "MISSING"
                if rs.is_mandatory:
                    mandatory_all_met = False
                suggested_imp = f"Acquire foundational mastery in {s_name} required for {role.title}."

            # Find matching catalogue resource
            matched_cat = None
            for cat in catalogue_items:
                if (cat.required_skill and cat.required_skill.lower() == s_name.lower()) or (s_name.lower() in cat.title.lower()):
                    matched_cat = cat
                    break

            gap_items.append(SkillGapItem(
                skill_name=s_name,
                category=s_cat,
                status=status,
                required_proficiency=req_prof,
                student_proficiency=st_info["proficiency"] if st_info else None,
                required_level_val=req_val,
                student_level_val=st_info["proficiency_val"] if st_info else 0,
                importance=rs.importance,
                importance_weight=weight,
                is_mandatory=rs.is_mandatory,
                is_verified=st_info["is_verified"] if st_info else False,
                evidence_count=st_info["evidence_count"] if st_info else 0,
                suggested_improvement=suggested_imp,
                recommended_catalog_item_id=matched_cat.id if matched_cat else None,
                recommended_resource_url=matched_cat.resource_url if matched_cat else None,
            ))

        # Overall readiness score
        readiness_score = round((earned_weight / total_weight * 100.0), 1) if total_weight > 0 else 0.0
        skill_coverage = round((matched_count / float(len(role_skills)) * 100.0), 1) if role_skills else 0.0

        # Tier classification
        if readiness_score >= 85.0 and mandatory_all_met:
            tier = "READY"
        elif readiness_score >= 70.0:
            tier = "NEAR_READY"
        elif readiness_score >= 50.0:
            tier = "DEVELOPING"
        else:
            tier = "EARLY_STAGE"

        # Projects & Certifications summary
        projects = db.query(Project).filter(Project.student_id == student_id).all()
        certs = db.query(Certification).filter(Certification.student_id == student_id).all()

        # Backlogs count
        backlog_results = db.query(SubjectResult).filter(
            SubjectResult.student_id == student_id,
            SubjectResult.is_backlog == True
        ).all()

        # Build role response
        role_skills_res = []
        for rs in role.role_skills:
            role_skills_res.append(RoleSkillResponse(
                id=rs.id,
                role_id=rs.role_id,
                skill_id=rs.skill_id,
                skill_name=rs.skill.name if rs.skill else "",
                category=rs.skill.category if rs.skill else "programming",
                min_proficiency=rs.min_proficiency,
                importance=rs.importance,
                importance_weight=rs.importance_weight,
                is_mandatory=rs.is_mandatory,
            ))

        role_res = CareerRoleResponse(
            id=role.id,
            code=role.code,
            title=role.title,
            department_id=role.department_id,
            department_code=role.department.code if role.department else None,
            description=role.description,
            min_experience_level=role.min_experience_level,
            average_salary_range=role.average_salary_range,
            industry_demand=role.industry_demand,
            is_active=role.is_active,
            skills=role_skills_res,
            created_at=role.created_at,
        )

        user_name = student.user.full_name if (student.user and student.user.full_name) else "Student"

        return PlacementReadinessResponse(
            student_id=student.id,
            student_name=user_name,
            srn=student.srn or student.usn,
            semester=student.current_semester,
            cgpa=student.cgpa,
            attendance_percentage=student.attendance_percentage,
            active_backlogs=len(backlog_results),
            target_role=role_res,
            readiness_score=readiness_score,
            skill_coverage_percentage=skill_coverage,
            mandatory_skills_met=mandatory_all_met,
            skills_matched_count=matched_count,
            skills_below_proficiency_count=below_count,
            skills_missing_count=missing_count,
            skills_unverified_count=unverified_count,
            total_role_skills_count=len(role_skills),
            skill_gaps=gap_items,
            certification_progress={
                "total_certifications": len(certs),
                "verified_certifications": len([c for c in certs if c.verification_status == "Verified"]),
                "recent_certifications": [c.title for c in certs[:3]],
            },
            project_experience={
                "total_projects": len(projects),
                "highlighted_projects": [p.title for p in projects[:3]],
            },
            readiness_tier=tier,
            disclaimer="Internal prototype readiness indicator. Does not guarantee corporate hiring or selection.",
            calculated_at=datetime.now(timezone.utc),
        )

    # --- Opportunities & Applications ---
    @staticmethod
    def list_opportunities(
        db: Session,
        opportunity_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[PlacementOpportunity]:
        q = db.query(PlacementOpportunity)
        if opportunity_type:
            q = q.filter(PlacementOpportunity.opportunity_type == opportunity_type)
        if status:
            q = q.filter(PlacementOpportunity.status == status)
        if search:
            s = f"%{search}%"
            q = q.filter(or_(
                PlacementOpportunity.company_name.ilike(s),
                PlacementOpportunity.title.ilike(s),
                PlacementOpportunity.location.ilike(s),
            ))
        return q.order_by(desc(PlacementOpportunity.created_at)).all()

    @staticmethod
    def get_matching_opportunities_for_student(
        db: Session,
        student_id: int
    ) -> List[OpportunityMatchForStudent]:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise ValueError(f"Student {student_id} not found")

        dept_code = student.department.code if student.department else "CSE"
        opps = db.query(PlacementOpportunity).filter(PlacementOpportunity.status == "OPEN").all()
        applications = db.query(StudentApplication).filter(StudentApplication.student_id == student_id).all()
        app_map = {app.opportunity_id: app.status for app in applications}

        # Backlogs count
        backlogs = db.query(SubjectResult).filter(
            SubjectResult.student_id == student_id,
            SubjectResult.is_backlog == True
        ).count()

        results = []
        for opp in opps:
            # Check eligibility
            cgpa_ok = student.cgpa >= opp.min_cgpa
            backlogs_ok = backlogs <= opp.max_backlogs
            attendance_ok = student.attendance_percentage >= opp.min_attendance
            dept_ok = dept_code in (opp.eligible_departments or [])
            sem_ok = student.current_semester in (opp.eligible_semesters or [])

            is_eligible = cgpa_ok and backlogs_ok and attendance_ok and dept_ok and sem_ok

            # Readiness score calculation for role
            readiness_score = 0.0
            if opp.role_id:
                try:
                    readiness = PlacementService.calculate_placement_readiness(db, student_id, opp.role_id)
                    readiness_score = readiness.readiness_score
                except Exception:
                    readiness_score = 65.0

            req_list = []
            for r in opp.requirements:
                req_list.append({
                    "skill_name": r.skill.name if r.skill else "",
                    "min_proficiency": r.min_proficiency,
                    "is_mandatory": r.is_mandatory,
                })

            results.append(OpportunityMatchForStudent(
                id=opp.id,
                company_name=opp.company_name,
                title=opp.title,
                opportunity_type=opp.opportunity_type,
                role_id=opp.role_id,
                role_title=opp.role.title if opp.role else None,
                location=opp.location,
                work_mode=opp.work_mode,
                ctc_stipend=opp.ctc_stipend,
                min_cgpa=opp.min_cgpa,
                max_backlogs=opp.max_backlogs,
                min_attendance=opp.min_attendance,
                eligible_departments=opp.eligible_departments,
                eligible_semesters=opp.eligible_semesters,
                application_deadline=opp.application_deadline,
                open_positions=opp.open_positions,
                description=opp.description,
                status=opp.status,
                requirements=req_list,
                application_count=len(opp.applications),
                created_at=opp.created_at,
                is_eligible=is_eligible,
                eligibility_breakdown={
                    "cgpa_eligible": cgpa_ok,
                    "student_cgpa": student.cgpa,
                    "min_cgpa": opp.min_cgpa,
                    "backlogs_eligible": backlogs_ok,
                    "student_backlogs": backlogs,
                    "max_backlogs": opp.max_backlogs,
                    "attendance_eligible": attendance_ok,
                    "student_attendance": student.attendance_percentage,
                    "min_attendance": opp.min_attendance,
                    "department_eligible": dept_ok,
                    "student_department": dept_code,
                    "semester_eligible": sem_ok,
                    "student_semester": student.current_semester,
                },
                readiness_score=readiness_score,
                application_status=app_map.get(opp.id),
            ))
        return results

    @staticmethod
    def apply_to_opportunity(
        db: Session,
        student_id: int,
        opportunity_id: int,
        resume_url: Optional[str] = None,
        cover_notes: Optional[str] = None
    ) -> StudentApplication:
        existing = db.query(StudentApplication).filter(
            StudentApplication.student_id == student_id,
            StudentApplication.opportunity_id == opportunity_id
        ).first()
        if existing:
            raise ValueError("You have already submitted an application for this opportunity.")

        opp = db.query(PlacementOpportunity).filter(PlacementOpportunity.id == opportunity_id).first()
        if not opp:
            raise ValueError("Placement opportunity not found.")

        # Compute readiness score at moment of application
        score = 0.0
        if opp.role_id:
            try:
                res = PlacementService.calculate_placement_readiness(db, student_id, opp.role_id)
                score = res.readiness_score
            except Exception:
                score = 70.0

        application = StudentApplication(
            opportunity_id=opportunity_id,
            student_id=student_id,
            status="APPLIED",
            applied_at=datetime.now(timezone.utc),
            resume_url=resume_url,
            cover_notes=cover_notes,
            readiness_score_at_application=score,
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def update_application_status(
        db: Session,
        application_id: int,
        status: str,
        reviewer_notes: Optional[str] = None
    ) -> StudentApplication:
        app = db.query(StudentApplication).filter(StudentApplication.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")

        app.status = status
        if reviewer_notes is not None:
            app.reviewer_notes = reviewer_notes
        db.commit()
        db.refresh(app)
        return app
