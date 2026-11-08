import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.recommendation import (
    RecommendationCatalogue,
    RecommendationResource,
    Recommendation,
    RecommendationProgress,
    RecommendationFeedback,
)
from app.models.profile import Student, Faculty, Mentor
from app.models.academic import (
    SubjectResult,
    SubjectAttendance,
    StudentAssessment,
    StudentSemesterRecord,
    Subject,
)
from app.models.student_intelligence import StudentSkill, Certification, Project, Skill
from app.models.user import User

logger = logging.getLogger(__name__)


# Standard Career Goal Skill Map for Gap Analysis
CAREER_GOAL_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "AI/ML Engineer": {
        "required_skills": ["Python", "Machine Learning", "PyTorch", "TensorFlow", "Pandas", "SQL"],
        "certifications": ["AWS Certified Machine Learning", "TensorFlow Developer Certificate"],
        "projects": ["Deep Learning Model Deployment", "End-to-End NLP Pipeline"],
    },
    "Full Stack Developer": {
        "required_skills": ["JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "Docker"],
        "certifications": ["Meta Front-End Developer", "AWS Certified Developer"],
        "projects": ["Full Stack SaaS Platform", "RESTful Microservices Architecture"],
    },
    "Cloud Architect": {
        "required_skills": ["AWS", "Docker", "Kubernetes", "Linux", "Terraform", "Networking"],
        "certifications": ["AWS Certified Solutions Architect", "CKA Certified Kubernetes Administrator"],
        "projects": ["Multi-Region Cloud Infrastructure", "CI/CD GitOps Pipeline"],
    },
    "Data Engineer": {
        "required_skills": ["Python", "SQL", "Apache Spark", "PostgreSQL", "Docker", "Data Warehousing"],
        "certifications": ["Databricks Certified Data Engineer", "Google Professional Data Engineer"],
        "projects": ["Real-Time Streaming ETL Pipeline", "Lakehouse Analytics Architecture"],
    },
    "Cybersecurity Analyst": {
        "required_skills": ["Network Security", "Linux", "Ethical Hacking", "Cryptography", "Python"],
        "certifications": ["CompTIA Security+", "Certified Ethical Hacker (CEH)"],
        "projects": ["Vulnerability Assessment & Penetration Test", "Security Information & Event Log Monitor"],
    },
}


class RecommendationService:
    """
    Transparent, Rule-Based Personalized Recommendation Engine.
    Evaluates academic records, skills, career goals, and interests to generate
    targeted, explainable academic and career development plans.
    """

    CANONICAL_CATALOGUE = [
        # 1. Subject Improvement
        {
            "title": "Database Management Systems: Relational Algebra & SQL Mastery",
            "category": "SUBJECT_IMPROVEMENT",
            "description": "Foundational review of SQL joins, indexing, query optimization, and normalization for students facing DBMS challenges.",
            "required_skill": "SQL",
            "target_audience": "Students scoring < 50% in Database Systems or relational data assessments",
            "difficulty_level": "Intermediate",
            "provider": "NPTEL / IIT Kharagpur",
            "resource_url": "https://nptel.ac.in/courses/106105175",
            "estimated_duration": "3 Weeks",
            "eligibility_conditions": {"weak_subjects": ["CS501", "DBMS", "Database Management Systems"]},
            "expected_learning_outcome": "Master complex subqueries, transaction ACID properties, and B-Tree indexing.",
            "status": "Active",
            "resources": [
                {"resource_type": "Course", "title": "NPTEL DBMS Video Series", "url": "https://nptel.ac.in/courses/106105175", "platform": "NPTEL", "is_free": True},
                {"resource_type": "Practice", "title": "SQLZoo Interactive Exercises", "url": "https://sqlzoo.net", "platform": "SQLZoo", "is_free": True},
            ],
        },
        {
            "title": "Computer Networks: Socket Programming & TCP/IP Architecture",
            "category": "SUBJECT_IMPROVEMENT",
            "description": "Comprehensive tutorial covering OSI layering, TCP sliding window, subnetting, and socket programming in Python.",
            "required_skill": "Computer Networks",
            "target_audience": "Students requiring academic reinforcement in Networking",
            "difficulty_level": "Intermediate",
            "provider": "Stanford Online / Coursera",
            "resource_url": "https://online.stanford.edu/courses/cs144-introduction-computer-networking",
            "estimated_duration": "4 Weeks",
            "eligibility_conditions": {"weak_subjects": ["CS502", "CN", "Computer Networks"]},
            "expected_learning_outcome": "Demonstrate protocol debugging using Wireshark and socket client-server architectures.",
            "status": "Active",
            "resources": [
                {"resource_type": "Course", "title": "Stanford CS144 Networking", "url": "https://cs144.github.io", "platform": "Stanford", "is_free": True},
            ],
        },
        # 2. Programming Practice
        {
            "title": "Data Structures & Algorithms: 75 Essential LeetCode Patterns",
            "category": "PROGRAMMING_PRACTICE",
            "description": "Curated collection of fundamental patterns: Two Pointers, Sliding Window, Trees, and Dynamic Programming.",
            "required_skill": "Data Structures",
            "target_audience": "All technical students preparing for technical interviews and coding contests",
            "difficulty_level": "Intermediate",
            "provider": "LeetCode / Blind 75",
            "resource_url": "https://leetcode.com/problem-list/top-interview-questions/",
            "estimated_duration": "6 Weeks",
            "eligibility_conditions": {"career_goals": ["Full Stack Developer", "AI/ML Engineer", "Data Engineer"]},
            "expected_learning_outcome": "Solve medium-level algorithmic challenges within 25 minutes with optimal time complexity.",
            "status": "Active",
            "resources": [
                {"resource_type": "Practice", "title": "Blind 75 Core Problem Set", "url": "https://leetcode.com/discuss/general-discussion/460599/blind-75-leetcode-questions", "platform": "LeetCode", "is_free": True},
            ],
        },
        # 3. Learning Courses
        {
            "title": "Full Stack Modern Web Development with React & Node.js",
            "category": "LEARNING_COURSES",
            "description": "Hands-on course building modular component architectures, state management with Redux, and REST APIs with Express.",
            "required_skill": "React",
            "target_audience": "Students aspiring towards Full Stack or Front-End Engineering",
            "difficulty_level": "Intermediate",
            "provider": "University of Helsinki (Full Stack Open)",
            "resource_url": "https://fullstackopen.com/en/",
            "estimated_duration": "8 Weeks",
            "eligibility_conditions": {"target_skills": ["React", "JavaScript", "TypeScript"], "career_goals": ["Full Stack Developer"]},
            "expected_learning_outcome": "Architect and deploy end-to-end full stack web applications with automated testing.",
            "status": "Active",
            "resources": [
                {"resource_type": "Course", "title": "Full Stack Open Official Platform", "url": "https://fullstackopen.com/en/", "platform": "Univ of Helsinki", "is_free": True},
            ],
        },
        {
            "title": "Deep Learning Specialization: Neural Networks & PyTorch",
            "category": "LEARNING_COURSES",
            "description": "Learn deep neural networks, convolutional networks, transformers, and hyperparameter tuning using PyTorch.",
            "required_skill": "PyTorch",
            "target_audience": "Students pursuing AI/ML and Data Science careers",
            "difficulty_level": "Advanced",
            "provider": "DeepLearning.AI / Andrew Ng",
            "resource_url": "https://www.coursera.org/specializations/deep-learning",
            "estimated_duration": "6 Weeks",
            "eligibility_conditions": {"target_skills": ["PyTorch", "Machine Learning", "Python"], "career_goals": ["AI/ML Engineer"]},
            "expected_learning_outcome": "Train, evaluate, and fine-tune convolutional neural networks and transformer models.",
            "status": "Active",
            "resources": [
                {"resource_type": "Course", "title": "Deep Learning Specialization", "url": "https://www.deeplearning.ai", "platform": "Coursera", "is_free": False},
            ],
        },
        # 4. Technical Certifications
        {
            "title": "AWS Certified Solutions Architect — Associate (SAA-C03)",
            "category": "TECHNICAL_CERTIFICATIONS",
            "description": "Official certification roadmap covering VPC networking, IAM security, S3 storage tiers, EC2 compute, and high availability.",
            "required_skill": "AWS",
            "target_audience": "Students aiming for Cloud Architect, DevOps, or Backend Engineering",
            "difficulty_level": "Advanced",
            "provider": "Amazon Web Services",
            "resource_url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
            "estimated_duration": "8 Weeks",
            "eligibility_conditions": {"target_skills": ["AWS", "Cloud Computing"], "career_goals": ["Cloud Architect", "Full Stack Developer"]},
            "expected_learning_outcome": "Attain industry-standard validation of cloud architecture and operational design principles.",
            "status": "Active",
            "resources": [
                {"resource_type": "Exam", "title": "AWS Official Exam Guide", "url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/", "platform": "AWS", "is_free": False},
            ],
        },
        # 5. Soft Skills
        {
            "title": "Technical Communication & Structured Interview Storytelling",
            "category": "SOFT_SKILLS",
            "description": "Frameworks (STAR method) for articulating complex engineering projects, code trade-offs, and team collaborations.",
            "required_skill": "Communication",
            "target_audience": "Semester 5-8 students preparing for campus corporate placement drives",
            "difficulty_level": "Beginner",
            "provider": "Campus Placement Cell",
            "resource_url": "https://smartcampus.edu/placement/soft-skills",
            "estimated_duration": "2 Weeks",
            "eligibility_conditions": {"min_semester": 5},
            "expected_learning_outcome": "Deliver concise 3-minute project walkthroughs and structured behavioral interview responses.",
            "status": "Active",
            "resources": [
                {"resource_type": "Video", "title": "Engineering Behavioral Interview Masterclass", "url": "https://smartcampus.edu/placement/star-framework", "platform": "Internal", "is_free": True},
            ],
        },
        # 6. Project Suggestions
        {
            "title": "Autonomous Edge IoT Gateway & Sensor Analytics Pipeline",
            "category": "PROJECT_SUGGESTIONS",
            "description": "Design an embedded telemetry pipeline transmitting temperature and vibration metrics via MQTT to a central dashboard.",
            "required_skill": "Embedded Systems",
            "target_audience": "ECE and Mechanical students with IoT or embedded systems interests",
            "difficulty_level": "Intermediate",
            "provider": "Internal Capstone Repository",
            "resource_url": "https://github.com/smartcampus/iot-gateway-starter",
            "estimated_duration": "5 Weeks",
            "eligibility_conditions": {"interests": ["IoT", "Embedded Systems", "Robotics"]},
            "expected_learning_outcome": "Build a production-grade IoT sensor ingestion node with local SQLite buffering.",
            "status": "Active",
            "resources": [
                {"resource_type": "Template", "title": "IoT MQTT Starter Repository", "url": "https://github.com/smartcampus/iot-gateway-starter", "platform": "GitHub", "is_free": True},
            ],
        },
        # 7. Internship & Placement Preparation
        {
            "title": "Corporate Placement Readiness: Operating Systems & System Design",
            "category": "PLACEMENT_PREPARATION",
            "description": "Intensive review of memory management, virtual memory, process concurrency, deadlocks, and low-level system design.",
            "required_skill": "Operating Systems",
            "target_audience": "Pre-final and final year students appearing for top-tier recruitment drives",
            "difficulty_level": "Intermediate",
            "provider": "Campus Career Development Center",
            "resource_url": "https://smartcampus.edu/placement/os-prep",
            "estimated_duration": "4 Weeks",
            "eligibility_conditions": {"min_semester": 5},
            "expected_learning_outcome": "Confidently address core systems questions and architecture scalability trade-offs.",
            "status": "Active",
            "resources": [
                {"resource_type": "Documentation", "title": "Operating Systems Interview Notes", "url": "https://smartcampus.edu/placement/os-notes", "platform": "Internal", "is_free": True},
            ],
        },
        # 8. Hackathon Participation
        {
            "title": "National Smart India Hackathon (SIH) Preparation Track",
            "category": "HACKATHON_PARTICIPATION",
            "description": "Guidelines for team formation, problem statement selection, rapid prototyping, and pitching innovative engineering solutions.",
            "required_skill": "Teamwork",
            "target_audience": "Students interested in competitive hackathons and innovative software prototyping",
            "difficulty_level": "Intermediate",
            "provider": "Ministry of Education / Internal Innovation Cell",
            "resource_url": "https://www.sih.gov.in",
            "estimated_duration": "3 Weeks",
            "eligibility_conditions": {"interests": ["Hackathons", "Innovation", "Product Design"]},
            "expected_learning_outcome": "Deliver a validated working minimum viable product (MVP) under 36-hour competitive hackathon conditions.",
            "status": "Active",
            "resources": [
                {"resource_type": "Documentation", "title": "SIH Problem Statement Portal", "url": "https://www.sih.gov.in", "platform": "Gov Portal", "is_free": True},
            ],
        },
        # 9. Examination Preparation
        {
            "title": "End-Semester Examination Prep: Model Question Bank & Solutions",
            "category": "EXAMINATION_PREPARATION",
            "description": "Official 5-year solved question papers and faculty revision notes for core engineering subjects.",
            "required_skill": "Academic Prep",
            "target_audience": "Students preparing for upcoming semester end examinations",
            "difficulty_level": "Intermediate",
            "provider": "Controller of Examinations",
            "resource_url": "https://smartcampus.edu/academics/question-bank",
            "estimated_duration": "2 Weeks",
            "eligibility_conditions": {"min_semester": 1},
            "expected_learning_outcome": "Familiarize with examination answer schemas, mark distributions, and standard derivation steps.",
            "status": "Active",
            "resources": [
                {"resource_type": "Documentation", "title": "Solved Question Paper Archives", "url": "https://smartcampus.edu/academics/question-bank", "platform": "Internal", "is_free": True},
            ],
        },
    ]

    # -------------------------------------------------------------------------
    # CATALOGUE SEEDING & CRUD
    # -------------------------------------------------------------------------
    @classmethod
    def seed_default_catalogue_if_needed(cls, db: Session, user_id: Optional[int] = None) -> List[RecommendationCatalogue]:
        """Ensures canonical learning catalogue is populated with approved items."""
        existing_titles = {c.title for c in db.query(RecommendationCatalogue).all()}
        created_items = []

        for item_data in cls.CANONICAL_CATALOGUE:
            if item_data["title"] not in existing_titles:
                resources_data = item_data.get("resources", [])
                cat_item = RecommendationCatalogue(
                    title=item_data["title"],
                    category=item_data["category"],
                    description=item_data["description"],
                    required_skill=item_data.get("required_skill"),
                    target_audience=item_data.get("target_audience"),
                    difficulty_level=item_data.get("difficulty_level", "Intermediate"),
                    provider=item_data.get("provider"),
                    resource_url=item_data.get("resource_url"),
                    estimated_duration=item_data.get("estimated_duration"),
                    eligibility_conditions=item_data.get("eligibility_conditions"),
                    expected_learning_outcome=item_data.get("expected_learning_outcome"),
                    status=item_data.get("status", "Active"),
                    created_by_id=user_id,
                )
                db.add(cat_item)
                db.flush()

                for res in resources_data:
                    res_obj = RecommendationResource(
                        catalogue_id=cat_item.id,
                        resource_type=res["resource_type"],
                        title=res["title"],
                        url=res["url"],
                        platform=res.get("platform"),
                        is_free=res.get("is_free", True),
                    )
                    db.add(res_obj)

                created_items.append(cat_item)

        if created_items:
            db.commit()
            for item in created_items:
                db.refresh(item)

        return db.query(RecommendationCatalogue).options(joinedload(RecommendationCatalogue.resources)).all()

    @staticmethod
    def get_catalogue(
        db: Session,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        status: Optional[str] = "Active",
    ) -> List[RecommendationCatalogue]:
        query = db.query(RecommendationCatalogue).options(joinedload(RecommendationCatalogue.resources))
        if category:
            query = query.filter(RecommendationCatalogue.category == category)
        if difficulty:
            query = query.filter(RecommendationCatalogue.difficulty_level == difficulty)
        if status:
            query = query.filter(RecommendationCatalogue.status == status)
        return query.order_by(RecommendationCatalogue.category.asc(), RecommendationCatalogue.title.asc()).all()

    @staticmethod
    def create_catalogue_item(db: Session, data: Dict[str, Any], user_id: Optional[int] = None) -> RecommendationCatalogue:
        resources_data = data.pop("resources", None) or []
        item = RecommendationCatalogue(**data, created_by_id=user_id)
        db.add(item)
        db.flush()

        for res in resources_data:
            res_obj = RecommendationResource(
                catalogue_id=item.id,
                resource_type=res["resource_type"],
                title=res["title"],
                url=res["url"],
                platform=res.get("platform"),
                is_free=res.get("is_free", True),
                duration_minutes=res.get("duration_minutes"),
            )
            db.add(res_obj)

        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_catalogue_item(db: Session, item: RecommendationCatalogue, data: Dict[str, Any]) -> RecommendationCatalogue:
        for k, v in data.items():
            if v is not None and hasattr(item, k):
                setattr(item, k, v)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_catalogue_item(db: Session, item: RecommendationCatalogue) -> None:
        db.delete(item)
        db.commit()

    # -------------------------------------------------------------------------
    # RECOMMENDATION GENERATION ENGINE (RULE-BASED & FACT-GROUNDED)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_recommendations_for_student(
        cls,
        db: Session,
        student_id: int,
        force_regenerate: bool = False,
    ) -> List[Recommendation]:
        """
        Analyzes student academic metrics, assessments, skill gaps, interests,
        and career goals to generate personalized, non-arbitrary recommendations.
        """
        # Ensure default catalogue exists
        cls.seed_default_catalogue_if_needed(db)

        student = (
            db.query(Student)
            .options(
                joinedload(Student.user),
                joinedload(Student.department),
                joinedload(Student.subject_results).joinedload(SubjectResult.subject),
                joinedload(Student.assessments).joinedload(StudentAssessment.subject),
                joinedload(Student.skills).joinedload(StudentSkill.skill),
                joinedload(Student.certifications),
                joinedload(Student.projects),
                joinedload(Student.recommendations),
            )
            .filter(Student.id == student_id)
            .first()
        )
        if not student:
            return []

        # Existing active or completed recommendation titles to prevent duplicates
        existing_recs = student.recommendations or []
        existing_rec_titles = {
            r.title.strip().lower()
            for r in existing_recs
            if r.status in ["SUGGESTED", "ACCEPTED", "IN_PROGRESS", "COMPLETED"]
        }

        # Existing student skills (lowercase)
        student_skill_names = {
            s.skill.name.strip().lower() for s in student.skills if s.skill and s.skill.name
        }
        # Existing certifications (lowercase)
        certified_titles = {c.title.strip().lower() for c in student.certifications}

        generated: List[Recommendation] = []
        catalogue_items = db.query(RecommendationCatalogue).filter(RecommendationCatalogue.status == "Active").all()
        cat_by_cat: Dict[str, List[RecommendationCatalogue]] = {}
        for c in catalogue_items:
            cat_by_cat.setdefault(c.category, []).append(c)

        career_goals = student.career_goals or []
        interests = student.interests or []

        # ---------------------------------------------------------------------
        # 1. EVALUATE WEAK SUBJECTS & ASSESSMENT PERFORMANCE
        # ---------------------------------------------------------------------
        weak_subjects: List[Tuple[str, str, float, str]] = []  # (code, name, score, reason)

        # Check Subject Results (< 50% or Backlog)
        for res in student.subject_results or []:
            if res.is_backlog or res.total_marks < 50.0 or res.letter_grade in ["F", "C"]:
                subj_name = res.subject.name if res.subject else "Core Subject"
                subj_code = res.subject.code if res.subject else "COURSE"
                weak_subjects.append((
                    subj_code,
                    subj_name,
                    res.total_marks,
                    f"Exam score of {res.total_marks:.1f}/100 (Grade {res.letter_grade})"
                ))

        # Check Continuous Assessments (< 50%)
        for asm in student.assessments or []:
            if asm.percentage < 50.0:
                subj_name = asm.subject.name if asm.subject else "Continuous Assessment"
                subj_code = asm.subject.code if asm.subject else "COURSE"
                weak_subjects.append((
                    subj_code,
                    subj_name,
                    asm.percentage,
                    f"CIA assessment '{asm.assessment_type}' score of {asm.percentage:.1f}% ({asm.marks_obtained}/{asm.max_marks})"
                ))

        # Recommend Subject Improvement & Study Resources for Weak Subjects
        for code, name, score, detail in weak_subjects:
            matched_items = [
                c for c in cat_by_cat.get("SUBJECT_IMPROVEMENT", [])
                if (c.eligibility_conditions and any(
                    k in name.lower() or k in code.lower()
                    for k in c.eligibility_conditions.get("weak_subjects", [])
                )) or (name.lower() in c.title.lower())
            ]

            if not matched_items:
                # Use general academic preparation or study resources
                matched_items = cat_by_cat.get("STUDY_RESOURCES", []) + cat_by_cat.get("EXAMINATION_PREPARATION", [])

            for item in matched_items:
                if item.title.strip().lower() not in existing_rec_titles:
                    rec = Recommendation(
                        student_id=student.id,
                        catalogue_id=item.id,
                        title=f"{item.title} — Targeted for {name}",
                        category="SUBJECT_IMPROVEMENT",
                        reason=(
                            f"Identified academic vulnerability in {name} ({code}) based on your {detail}. "
                            f"Completing this structured learning track will reinforce foundational concepts before semester exams."
                        ),
                        gap_type="ACADEMIC_WEAKNESS",
                        gap_detail=f"Low score in {name} ({detail})",
                        expected_outcome=item.expected_learning_outcome or f"Attain score recovery above 65% in {name}.",
                        priority="HIGH" if score < 40.0 else "MEDIUM",
                        resource_url=item.resource_url,
                        suggested_completion_time=item.estimated_duration or "3 Weeks",
                        status="SUGGESTED",
                        source="SYSTEM",
                    )
                    db.add(rec)
                    generated.append(rec)
                    existing_rec_titles.add(rec.title.strip().lower())
                    break  # One targeted recommendation per weak subject

        # ---------------------------------------------------------------------
        # 2. EVALUATE CAREER GOAL SKILL GAPS
        # ---------------------------------------------------------------------
        for goal in career_goals:
            reqs = CAREER_GOAL_REQUIREMENTS.get(goal)
            if not reqs:
                continue

            missing_skills = [
                s for s in reqs["required_skills"]
                if s.lower() not in student_skill_names
            ]

            for skill in missing_skills:  # Check all missing skills for matching catalogue courses
                # Find matching learning courses or programming practice
                skill_items = [
                    c for c in (cat_by_cat.get("LEARNING_COURSES", []) + cat_by_cat.get("PROGRAMMING_PRACTICE", []))
                    if (c.required_skill and c.required_skill.lower() == skill.lower())
                    or (skill.lower() in c.title.lower())
                    or (c.eligibility_conditions and skill.lower() in [s.lower() for s in c.eligibility_conditions.get("target_skills", [])])
                ]

                for item in skill_items:
                    if item.title.strip().lower() not in existing_rec_titles:
                        rec = Recommendation(
                            student_id=student.id,
                            catalogue_id=item.id,
                            title=item.title,
                            category=item.category,
                            reason=(
                                f"You have selected '{goal}' as your career goal. Proficiency in '{skill}' "
                                f"is an industry prerequisite but is currently missing from your recorded skills."
                            ),
                            gap_type="SKILL_DEFICIT",
                            gap_detail=f"Missing skill '{skill}' required for {goal}",
                            expected_outcome=item.expected_learning_outcome or f"Demonstrate working competency in {skill}.",
                            priority="HIGH",
                            resource_url=item.resource_url,
                            suggested_completion_time=item.estimated_duration or "4 Weeks",
                            status="SUGGESTED",
                            source="SYSTEM",
                        )
                        db.add(rec)
                        generated.append(rec)
                        existing_rec_titles.add(item.title.strip().lower())
                        break

                if len([r for r in generated if r.gap_type == "SKILL_DEFICIT"]) >= 2:
                    break  # Up to 2 skill gap recommendations per student

            # Recommend Target Certifications (if not certified yet)
            for cert_name in reqs.get("certifications", []):
                if any(cert_name.lower() in c_t for c_t in certified_titles):
                    continue

                cert_items = [
                    c for c in cat_by_cat.get("TECHNICAL_CERTIFICATIONS", [])
                    if any(w in c.title.lower() for w in cert_name.lower().split()[:2])
                ]
                for item in cert_items:
                    if item.title.strip().lower() not in existing_rec_titles:
                        rec = Recommendation(
                            student_id=student.id,
                            catalogue_id=item.id,
                            title=item.title,
                            category="TECHNICAL_CERTIFICATIONS",
                            reason=(
                                f"Industry certification '{cert_name}' provides formal third-party credentialing "
                                f"for your career goal as '{goal}', significantly elevating placement competitiveness."
                            ),
                            gap_type="CAREER_ALIGNMENT",
                            gap_detail=f"Uncertified in {cert_name} for target role {goal}",
                            expected_outcome=item.expected_learning_outcome or f"Attain {cert_name} certification.",
                            priority="MEDIUM",
                            resource_url=item.resource_url,
                            suggested_completion_time=item.estimated_duration or "8 Weeks",
                            status="SUGGESTED",
                            source="SYSTEM",
                        )
                        db.add(rec)
                        generated.append(rec)
                        existing_rec_titles.add(item.title.strip().lower())
                        break

        # ---------------------------------------------------------------------
        # 3. EVALUATE STUDENT INTERESTS & PROJECT SUGGESTIONS
        # ---------------------------------------------------------------------
        for interest in interests:
            interest_items = [
                c for c in (cat_by_cat.get("PROJECT_SUGGESTIONS", []) + cat_by_cat.get("HACKATHON_PARTICIPATION", []))
                if (c.eligibility_conditions and interest.lower() in [
                    i.lower() for i in c.eligibility_conditions.get("interests", [])
                ]) or (interest.lower() in c.title.lower())
            ]

            for item in interest_items:
                if item.title.strip().lower() not in existing_rec_titles:
                    rec = Recommendation(
                        student_id=student.id,
                        catalogue_id=item.id,
                        title=item.title,
                        category=item.category,
                        reason=(
                            f"Matched to your expressed interest in '{interest}'. Engaging in practical engineering "
                            f"projects builds tangible portfolio artifacts for campus recruitment."
                        ),
                        gap_type="INTEREST_EXPLORATION",
                        gap_detail=f"Practical project experience in {interest}",
                        expected_outcome=item.expected_learning_outcome or f"Build an end-to-end prototype in {interest}.",
                        priority="MEDIUM",
                        resource_url=item.resource_url,
                        suggested_completion_time=item.estimated_duration or "5 Weeks",
                        status="SUGGESTED",
                        source="SYSTEM",
                    )
                    db.add(rec)
                    generated.append(rec)
                    existing_rec_titles.add(item.title.strip().lower())
                    break

        # ---------------------------------------------------------------------
        # 4. PLACEMENT & INTERNSHIP READINESS (Semesters 5-8)
        # ---------------------------------------------------------------------
        if student.current_semester >= 5:
            placement_items = cat_by_cat.get("PLACEMENT_PREPARATION", []) + cat_by_cat.get("SOFT_SKILLS", [])
            for item in placement_items:
                if item.title.strip().lower() not in existing_rec_titles:
                    rec = Recommendation(
                        student_id=student.id,
                        catalogue_id=item.id,
                        title=item.title,
                        category=item.category,
                        reason=(
                            f"As a Semester {student.current_semester} student preparing for campus recruitment drives, "
                            f"mastering technical interview problem-solving and structured communication is critical."
                        ),
                        gap_type="CAREER_ALIGNMENT",
                        gap_detail="Campus placement technical readiness & communication",
                        expected_outcome=item.expected_learning_outcome or "Perform strongly in technical & HR interview rounds.",
                        priority="HIGH",
                        resource_url=item.resource_url,
                        suggested_completion_time=item.estimated_duration or "3 Weeks",
                        status="SUGGESTED",
                        source="SYSTEM",
                    )
                    db.add(rec)
                    generated.append(rec)
                    existing_rec_titles.add(item.title.strip().lower())
                    break

        # ---------------------------------------------------------------------
        # 5. NO IDENTIFIED GAPS FALLBACK (HEALTHY / STAR PROFILE)
        # ---------------------------------------------------------------------
        if not generated and not existing_recs:
            # For students meeting all benchmarks, recommend advanced hackathons and competitive DSA
            star_items = cat_by_cat.get("PROGRAMMING_PRACTICE", []) + cat_by_cat.get("HACKATHON_PARTICIPATION", [])
            for item in star_items[:2]:
                if item.title.strip().lower() not in existing_rec_titles:
                    rec = Recommendation(
                        student_id=student.id,
                        catalogue_id=item.id,
                        title=item.title,
                        category=item.category,
                        reason=(
                            "Outstanding academic standing and strong baseline performance observed. "
                            "Recommended advanced technical challenge to accelerate elite placement and competition readiness."
                        ),
                        gap_type="CAREER_ALIGNMENT",
                        gap_detail="Advanced challenge track for high performers",
                        expected_outcome=item.expected_learning_outcome or "Excel in competitive national programming challenges.",
                        priority="MEDIUM",
                        resource_url=item.resource_url,
                        suggested_completion_time=item.estimated_duration or "4 Weeks",
                        status="SUGGESTED",
                        source="SYSTEM",
                    )
                    db.add(rec)
                    generated.append(rec)
                    existing_rec_titles.add(item.title.strip().lower())

        if generated:
            db.commit()
            for r in generated:
                db.refresh(r)

        return (
            db.query(Recommendation)
            .options(
                joinedload(Recommendation.catalogue),
                joinedload(Recommendation.progress_logs),
                joinedload(Recommendation.feedback),
            )
            .filter(Recommendation.student_id == student_id)
            .order_by(
                desc(Recommendation.priority == "CRITICAL"),
                desc(Recommendation.priority == "HIGH"),
                desc(Recommendation.created_at),
            )
            .all()
        )

    # -------------------------------------------------------------------------
    # STUDENT LEARNING PATH & PLAN COMPILATION
    # -------------------------------------------------------------------------
    @classmethod
    def get_student_learning_path(cls, db: Session, student_id: int) -> Dict[str, Any]:
        """
        Retrieves the structured academic improvement and career development plan
        for a student, splitting recommendations into categorized tracks.
        """
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {}

        # Fetch or auto-generate recommendations if none exist
        recs = (
            db.query(Recommendation)
            .options(
                joinedload(Recommendation.student).joinedload(Student.user),
                joinedload(Recommendation.student).joinedload(Student.department),
                joinedload(Recommendation.catalogue),
                joinedload(Recommendation.progress_logs),
                joinedload(Recommendation.feedback),
                joinedload(Recommendation.created_by),
            )
            .filter(Recommendation.student_id == student_id)
            .order_by(
                desc(Recommendation.priority == "CRITICAL"),
                desc(Recommendation.priority == "HIGH"),
                desc(Recommendation.created_at),
            )
            .all()
        )

        if not recs:
            recs = cls.generate_recommendations_for_student(db, student_id)

        # Academic Improvement Plan (Subject improvement, examination prep, study resources)
        academic_categories = {"SUBJECT_IMPROVEMENT", "EXAMINATION_PREPARATION", "STUDY_RESOURCES"}
        academic_plan = [r for r in recs if r.category in academic_categories or r.gap_type == "ACADEMIC_WEAKNESS"]

        # Career Development Plan (Skills, certifications, projects, internship, placement, hackathon)
        career_plan = [r for r in recs if r not in academic_plan]

        accepted_c = sum(1 for r in recs if r.status == "ACCEPTED")
        in_progress_c = sum(1 for r in recs if r.status == "IN_PROGRESS")
        completed_c = sum(1 for r in recs if r.status == "COMPLETED")

        student_name = student.user.full_name if student.user else student.roll_number
        summary = (
            f"Personalized Learning Roadmap for {student_name} ({student.roll_number}): "
            f"Compiled {len(recs)} data-grounded recommendations ({len(academic_plan)} academic interventions, "
            f"{len(career_plan)} career development milestones). Focus areas: "
            f"{', '.join(student.career_goals or ['General Engineering Excellence'])}."
        )

        return {
            "student_id": student.id,
            "student_name": student_name,
            "roll_number": student.roll_number,
            "department": student.department.name if student.department else "",
            "current_semester": student.current_semester,
            "career_goals": student.career_goals or [],
            "interests": student.interests or [],
            "academic_improvement_plan": academic_plan,
            "career_development_plan": career_plan,
            "total_recommendations": len(recs),
            "accepted_count": accepted_c,
            "in_progress_count": in_progress_c,
            "completed_count": completed_c,
            "summary_explanation": summary,
        }

    # -------------------------------------------------------------------------
    # RECOMMENDATION LIFECYCLE & TRACKING
    # -------------------------------------------------------------------------
    @staticmethod
    def accept_recommendation(db: Session, recommendation_id: int, user_id: int) -> Recommendation:
        rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError("Recommendation not found")

        rec.status = "ACCEPTED"
        rec.accepted_at = datetime.utcnow()

        progress = RecommendationProgress(
            recommendation_id=rec.id,
            status="ACCEPTED",
            percent_complete=0,
            notes="Recommendation accepted by student into active learning plan.",
            hours_spent=0.0,
            updated_by_id=user_id,
        )
        db.add(progress)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def reject_recommendation(db: Session, recommendation_id: int, reason: str) -> Recommendation:
        rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError("Recommendation not found")

        rec.status = "REJECTED"
        rec.rejected_at = datetime.utcnow()
        rec.rejection_reason = reason
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def update_progress(
        db: Session,
        recommendation_id: int,
        status: str,
        percent_complete: int,
        notes: Optional[str],
        hours_spent: float,
        user_id: int,
    ) -> Recommendation:
        rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError("Recommendation not found")

        rec.status = status
        if percent_complete >= 100:
            rec.status = "COMPLETED"
            rec.completed_at = datetime.utcnow()
        elif status == "IN_PROGRESS" and rec.status != "COMPLETED":
            rec.status = "IN_PROGRESS"

        progress = RecommendationProgress(
            recommendation_id=rec.id,
            status=rec.status,
            percent_complete=percent_complete,
            notes=notes,
            hours_spent=hours_spent,
            updated_by_id=user_id,
        )
        db.add(progress)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def submit_feedback(
        db: Session,
        recommendation_id: int,
        student_id: int,
        rating: int,
        helpful: bool,
        relevance_score: int,
        comments: Optional[str],
        outcome_achieved: bool,
    ) -> RecommendationFeedback:
        existing = db.query(RecommendationFeedback).filter(
            RecommendationFeedback.recommendation_id == recommendation_id
        ).first()

        if existing:
            existing.rating = rating
            existing.helpful = helpful
            existing.relevance_score = relevance_score
            existing.comments = comments
            existing.outcome_achieved = outcome_achieved
            feedback = existing
        else:
            feedback = RecommendationFeedback(
                recommendation_id=recommendation_id,
                student_id=student_id,
                rating=rating,
                helpful=helpful,
                relevance_score=relevance_score,
                comments=comments,
                outcome_achieved=outcome_achieved,
            )
            db.add(feedback)

        db.commit()
        db.refresh(feedback)
        return feedback

    # -------------------------------------------------------------------------
    # MENTOR & FACULTY WORKFLOW
    # -------------------------------------------------------------------------
    @staticmethod
    def create_mentor_suggestion(db: Session, data: Dict[str, Any], mentor_user_id: int) -> Recommendation:
        rec = Recommendation(
            student_id=data["student_id"],
            catalogue_id=data.get("catalogue_id"),
            title=data["title"],
            category=data["category"],
            reason=data["reason"],
            gap_type=data.get("gap_type", "CAREER_ALIGNMENT"),
            gap_detail=data.get("gap_detail"),
            expected_outcome=data.get("expected_outcome"),
            priority=data.get("priority", "HIGH"),
            resource_url=data.get("resource_url"),
            suggested_completion_time=data.get("suggested_completion_time", "3 Weeks"),
            status="SUGGESTED",
            source="MENTOR",
            created_by_id=mentor_user_id,
            mentor_approval_status="APPROVED",
            mentor_guidance_notes=data.get("mentor_guidance_notes"),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def approve_mentor_suggestion(db: Session, recommendation_id: int, user_id: int) -> Recommendation:
        rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError("Recommendation not found")

        rec.mentor_approval_status = "APPROVED"
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def add_guidance_notes(db: Session, recommendation_id: int, notes: str) -> Recommendation:
        rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError("Recommendation not found")

        time_tag = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        rec.mentor_guidance_notes = (rec.mentor_guidance_notes or "") + f"\n[{time_tag}] {notes}"
        db.commit()
        db.refresh(rec)
        return rec
