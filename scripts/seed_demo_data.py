"""Seed a realistic, idempotent TalentIQ demo workspace.

Run from the repository root with:
    python scripts/seed_demo_data.py

The records are clearly marked as demo data, preserve existing rows, and add
recruiter decisions so the supervised ranking model can be trained locally.
"""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Candidate, CandidateJobDecision, Job
from app.schemas.candidate import CandidateCreate
from app.schemas.job import JobCreate
from app.services.candidate_service import CandidateService
from app.services.decision_service import DecisionService
from app.services.job_service import JobService
from app.services.ranking_model_service import RankingModelService


CANDIDATES = [
    ("Aarav Mehta", "Software Engineer", 4, ["Python", "FastAPI", "PostgreSQL", "Docker"], ["B.Tech Computer Science"], ["Payments API modernization"]),
    ("Maya Iyer", "Frontend Engineer", 3, ["React", "TypeScript", "Next.js", "CSS"], ["B.E. Information Technology"], ["Accessibility-first design system"]),
    ("Rohan Kapoor", "Data Scientist", 5, ["Python", "SQL", "Pandas", "Machine Learning"], ["M.Tech Data Science"], ["Demand forecasting pipeline"]),
    ("Zoya Khan", "ML Engineer", 4, ["Python", "PyTorch", "NLP", "MLOps"], ["M.S. Artificial Intelligence"], ["Resume classification model"]),
    ("Neil Fernandes", "DevOps Engineer", 6, ["AWS", "Kubernetes", "Docker", "Terraform"], ["B.Tech Computer Engineering"], ["Zero-downtime deployment platform"]),
    ("Ishita Rao", "Product Designer", 4, ["Figma", "UX Research", "Design Systems", "Prototyping"], ["B.Des. Interaction Design"], ["Recruiter workspace redesign"]),
    ("Kabir Singh", "Backend Engineer", 7, ["Java", "Spring Boot", "Kafka", "PostgreSQL"], ["B.Tech Computer Science"], ["Event-driven order processing"]),
    ("Ananya Nair", "QA Automation Engineer", 3, ["Playwright", "Python", "API Testing", "CI/CD"], ["B.Tech Information Technology"], ["Automated regression framework"]),
    ("Vikram Joshi", "Security Analyst", 5, ["Threat Modeling", "SIEM", "Python", "Cloud Security"], ["M.S. Cybersecurity"], ["Cloud incident response playbook"]),
    ("Sara Thomas", "Technical Program Manager", 8, ["Program Management", "Agile", "Risk Management", "Stakeholder Management"], ["MBA Technology Management"], ["Cross-functional platform launch"]),
    ("Dev Malhotra", "Mobile Engineer", 4, ["Kotlin", "Android", "Firebase", "REST APIs"], ["B.Tech Computer Science"], ["Offline-first field application"]),
    ("Meera Shah", "Data Analyst", 2, ["SQL", "Excel", "Tableau", "Statistics"], ["B.Sc. Statistics"], ["Executive operations dashboard"]),
    ("Arjun Bhat", "Recruiter", 6, ["Sourcing", "Interview Coordination", "ATS", "Stakeholder Management"], ["MBA Human Resources"], ["Technical hiring program"]),
    ("Nisha Verma", "HR Business Partner", 7, ["Employee Relations", "People Analytics", "Policy", "Coaching"], ["M.A. Human Resources"], ["Performance framework rollout"]),
    ("Owen Dsouza", "Content Strategist", 5, ["Content Strategy", "SEO", "Editorial Planning", "Analytics"], ["B.A. Mass Communication"], ["Developer education hub"]),
    ("Priya Menon", "Finance Operations Analyst", 4, ["Financial Modeling", "Excel", "Forecasting", "Reporting"], ["B.Com Finance"], ["Quarterly planning automation"]),
    ("Yash Patel", "Customer Success Manager", 5, ["Customer Success", "CRM", "Renewals", "Presentation"], ["BBA"], ["Enterprise onboarding playbook"]),
    ("Tara Kulkarni", "Sales Operations Manager", 6, ["Salesforce", "Pipeline Analytics", "Process Design", "Forecasting"], ["MBA Marketing"], ["Revenue operations redesign"]),
    ("Adil Hussain", "Operations Manager", 9, ["Process Improvement", "Vendor Management", "KPI Design", "Six Sigma"], ["MBA Operations"], ["Regional operations transformation"]),
    ("Leah Joseph", "Learning and Development Lead", 8, ["Instructional Design", "Facilitation", "LMS", "Leadership Development"], ["M.Ed. Organizational Learning"], ["Manager capability academy"]),
]

JOBS = [
    ("[Demo] Senior Backend Engineer", "Build reliable APIs and event-driven services for the hiring platform.", 4, ["Python", "FastAPI", "PostgreSQL", "Docker"], ["Production API ownership", "Observability and testing experience"]),
    ("[Demo] Machine Learning Engineer", "Own semantic retrieval, ranking models, and evaluation workflows for talent intelligence.", 3, ["Python", "Machine Learning", "NLP", "MLOps"], ["Experience deploying ML services", "Strong evaluation discipline"]),
    ("[Demo] Product Designer", "Design clear, accessible workflows for recruiters and hiring managers.", 3, ["Figma", "UX Research", "Design Systems", "Prototyping"], ["Portfolio demonstrating systems thinking", "User research experience"]),
    ("[Demo] People Operations Partner", "Improve people programs, policy operations, and manager support across a growing company.", 5, ["Employee Relations", "People Analytics", "Policy", "Coaching"], ["Experience partnering with leaders", "Strong written communication"]),
    ("[Demo] Revenue Operations Manager", "Improve sales processes, forecasting, pipeline visibility, and cross-functional execution.", 4, ["Salesforce", "Pipeline Analytics", "Process Design", "Forecasting"], ["Revenue operations ownership", "Executive reporting experience"]),
]

DETAILS = {
    "Aarav Mehta": (["B.Tech Computer Science, VJTI Mumbai"], ["AWS Certified Developer", "Docker Certified Associate"], ["Payments API modernization", "Idempotent transaction workflow"], ["Backend Engineer at FinEdge Labs: owned Python services processing 2M monthly transactions.", "Software Engineer at CloudCart: reduced API p95 latency by 31% through query and cache improvements."]),
    "Maya Iyer": (["B.E. Information Technology, PES University"], ["Google UX Design Certificate", "Microsoft Certified: Power Platform Fundamentals"], ["Accessibility-first design system", "Recruiter onboarding experience"], ["Frontend Engineer at Northstar Products: shipped React workflows used by 40K monthly users.", "UI Engineer at BrightDesk: introduced component standards that reduced duplicated frontend work."]),
    "Rohan Kapoor": (["M.Tech Data Science, IIT Hyderabad"], ["AWS Certified Machine Learning Specialty", "TensorFlow Developer Certificate"], ["Demand forecasting pipeline", "Customer churn prediction"], ["Data Scientist at MarketPulse: built forecasting models used for quarterly inventory planning.", "Analytics Associate at RetailGrid: automated SQL and Python reporting for regional operations."]),
    "Zoya Khan": (["M.S. Artificial Intelligence, IIIT Hyderabad"], ["NVIDIA Deep Learning Institute Certificate", "AWS Machine Learning Specialty"], ["Resume classification model", "Semantic skill extraction service"], ["ML Engineer at TalentWorks: deployed NLP classification services with monitored precision and drift checks.", "Research Assistant at Language Lab: evaluated transformer-based entity extraction across noisy documents."]),
    "Neil Fernandes": (["B.Tech Computer Engineering, NIT Goa"], ["AWS Solutions Architect Associate", "Certified Kubernetes Administrator"], ["Zero-downtime deployment platform", "Infrastructure cost observability"], ["DevOps Engineer at HarborStack: managed Kubernetes workloads and automated blue-green deployments.", "Cloud Engineer at DataForge: cut infrastructure spend by 18% through capacity and observability work."]),
    "Ishita Rao": (["B.Des. Interaction Design, Srishti Institute"], ["NN/g UX Certification", "Figma Advanced Design Certificate"], ["Recruiter workspace redesign", "Candidate comparison flow"], ["Product Designer at HireFlow: designed recruiter workflows from discovery interviews through production release.", "UX Designer at Studio Loop: led usability studies and translated findings into reusable interaction patterns."]),
    "Kabir Singh": (["B.Tech Computer Science, BITS Pilani"], ["Oracle Certified Professional Java", "Confluent Kafka Fundamentals"], ["Event-driven order processing", "Notification delivery platform"], ["Backend Engineer at ShipRight: built Java and Kafka services with replayable event processing.", "Software Engineer at CoreSystems: maintained PostgreSQL services and introduced contract testing."]),
    "Ananya Nair": (["B.Tech Information Technology, Amrita Vishwa Vidyapeetham"], ["ISTQB Foundation", "Playwright Automation Certificate"], ["Automated regression framework", "API contract test suite"], ["QA Automation Engineer at FinServe: created Playwright coverage for critical payment and onboarding flows.", "Test Engineer at AppHarbor: integrated API regression checks into CI and triage workflows."]),
    "Vikram Joshi": (["M.S. Cybersecurity, University of Maryland"], ["CompTIA Security+", "AWS Certified Security Specialty"], ["Cloud incident response playbook", "Identity access review automation"], ["Security Analyst at SecureCloud: investigated cloud alerts and improved incident response runbooks.", "SOC Analyst at BlueShield: tuned SIEM detections and delivered monthly risk summaries to engineering leaders."]),
    "Sara Thomas": (["MBA Technology Management, SP Jain"], ["PMP", "Certified Scrum Professional"], ["Cross-functional platform launch", "Quarterly delivery operating model"], ["Technical Program Manager at Orbit Systems: coordinated six teams through a multi-region platform launch.", "Program Manager at EduTech Co: built risk reviews, dependency tracking, and executive reporting rhythms."]),
    "Dev Malhotra": (["B.Tech Computer Science, Manipal Institute of Technology"], ["Google Associate Android Developer", "Firebase Application Development"], ["Offline-first field application", "Mobile analytics instrumentation"], ["Mobile Engineer at FieldOps: delivered Kotlin workflows for low-connectivity field teams.", "Android Developer at QuickServe: improved crash-free sessions and introduced structured mobile analytics."]),
    "Meera Shah": (["B.Sc. Statistics, University of Pune"], ["Tableau Desktop Specialist", "Microsoft Excel Expert"], ["Executive operations dashboard", "Support volume analysis"], ["Data Analyst at ServiceLane: built Tableau dashboards that gave leaders weekly operational visibility.", "Reporting Analyst at HelpDeskPro: standardized SQL extracts and reduced manual reporting time."]),
    "Arjun Bhat": (["MBA Human Resources, MICA"], ["LinkedIn Recruiter Certified", "SHRM Talent Acquisition Specialty"], ["Technical hiring program", "Structured interview scorecard"], ["Recruiter at ScaleWorks: delivered engineering sourcing for backend, data, and platform roles across India.", "Talent Acquisition Specialist at NovaTech: introduced structured intake meetings and interviewer calibration."]),
    "Nisha Verma": (["M.A. Human Resources, TISS"], ["SHRM-SCP", "People Analytics Certificate"], ["Performance framework rollout", "Manager coaching program"], ["HR Business Partner at Meridian: partnered with product and engineering leaders on performance and org planning.", "People Partner at GrowthWorks: used engagement and attrition data to guide manager interventions."]),
    "Owen Dsouza": (["B.A. Mass Communication, St. Xavier's Mumbai"], ["HubSpot Content Marketing", "Google Analytics Certification"], ["Developer education hub", "SEO content operations"], ["Content Strategist at DevBridge: built editorial planning for technical education and product adoption.", "Content Writer at SignalWorks: improved organic acquisition through research-led landing pages and guides."]),
    "Priya Menon": (["B.Com Finance, Christ University"], ["CFA Level I", "Microsoft Excel Expert"], ["Quarterly planning automation", "Vendor spend analysis"], ["Finance Operations Analyst at FinOpsly: supported quarterly planning and variance analysis for a 120-person business.", "Financial Analyst at Apex Services: automated reconciliations and created management reporting packs."]),
    "Yash Patel": (["BBA, Symbiosis International University"], ["Gainsight Customer Success Certification", "HubSpot Inbound Certification"], ["Enterprise onboarding playbook", "Renewal risk dashboard"], ["Customer Success Manager at CloudDesk: managed enterprise onboarding and renewal planning for a SaaS portfolio.", "Account Manager at WorkSuite: improved adoption through executive reviews and customer health tracking."]),
    "Tara Kulkarni": (["MBA Marketing, IIM Kozhikode"], ["Salesforce Administrator", "Lean Six Sigma Green Belt"], ["Revenue operations redesign", "Pipeline forecasting model"], ["Sales Operations Manager at RevPilot: redesigned CRM stages and improved forecast discipline across three regions.", "Operations Analyst at MarketHub: built pipeline dashboards and standardized weekly revenue reviews."]),
    "Adil Hussain": (["MBA Operations, NMIMS"], ["Lean Six Sigma Black Belt", "APICS Certified Supply Chain Professional"], ["Regional operations transformation", "Vendor performance program"], ["Operations Manager at SwiftLogix: led process improvement across 14 regional hubs and vendor partners.", "Process Excellence Lead at TransitCo: reduced cycle time through KPI reviews and root-cause workshops."]),
    "Leah Joseph": (["M.Ed. Organizational Learning, University of Melbourne"], ["ATD Instructional Design Certificate", "ICAgile Certified Professional"], ["Manager capability academy", "Learning impact measurement"], ["Learning and Development Lead at PeopleFirst: built manager programs and blended learning paths for 600 employees.", "Learning Designer at ElevateWorks: translated business capability needs into measurable curricula and workshops."]),
}


def seed():
    # Ensures the script also works on a fresh local database before migrations
    # have been run manually.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    created_candidates = 0
    created_jobs = 0
    try:
        candidate_models = []
        for name, role, years, skills, education, projects in CANDIDATES:
            email = f"demo.{name.lower().replace(' ', '.')}@talentiq.local"
            candidate = db.query(Candidate).filter(Candidate.email == email).first()
            if not candidate:
                result = CandidateService.create(
                    db,
                    CandidateCreate(
                        full_name=f"{name} · {role}",
                        email=email,
                        years_experience=years,
                        skills=skills,
                        education=education,
                        projects=projects,
                        certifications=["TalentIQ Demo Profile"],
                        work_history=[f"{role} experience across product and operations teams"],
                        source_text=f"Demo profile for {role}. Skills: {', '.join(skills)}.",
                        extraction_metadata={"source": "synthetic-demo-seed", "role": role},
                    ),
                )
                candidate = result["candidate"]
                created_candidates += 1
            education_detail, certifications, projects_detail, work_history = DETAILS[name]
            candidate.full_name = f"{name} · {role}"
            candidate.education = education_detail
            candidate.certifications = certifications
            candidate.projects = projects_detail
            candidate.work_history = work_history
            candidate.source_text = (
                f"{name} is a {role} with {years} years of experience. "
                f"Core skills: {', '.join(skills)}. "
                f"Projects: {'; '.join(projects_detail)}. "
                f"Work history: {' '.join(work_history)}"
            )
            candidate.extraction_metadata = {
                "source": "synthetic-demo-seed",
                "role": role,
                "profile_version": "detailed-v2",
            }
            db.commit()
            db.refresh(candidate)
            candidate_models.append(candidate)

        job_models = []
        for title, description, years, skills, requirements in JOBS:
            job = db.query(Job).filter(Job.title == title).first()
            if not job:
                job = JobService.create(
                    db,
                    JobCreate(
                        title=title,
                        description=description,
                        min_experience=years,
                        skills=skills,
                        requirements=requirements,
                    ),
                )
                created_jobs += 1
            else:
                job.description = description
                job.min_experience = years
                job.skills = skills
                job.requirements = requirements
                db.commit()
                db.refresh(job)
            job_models.append(job)

        # Build a reproducible candidate-job training matrix. These are
        # explicitly synthetic workflow labels for the demo, derived from
        # transparent job-fit and role-evidence signals rather than arbitrary
        # random outcomes. Real deployments must replace them with audited
        # recruiter feedback.
        for candidate in candidate_models:
            for job in job_models:
                features = RankingModelService._features(candidate, job)
                evidence_score = (
                    features["baseline_match_score"] * 0.8
                    + features["role_evidence_overlap"] * 100 * 0.2
                )
                if evidence_score >= 78:
                    outcome = "interview"
                elif evidence_score >= 35 and features["experience_coverage"] >= 1:
                    outcome = "shortlisted"
                else:
                    outcome = "rejected"
                DecisionService.upsert(
                    db,
                    candidate.id,
                    job.id,
                    outcome,
                    "Synthetic demo workflow label derived from stated job-fit and role evidence; not a real hiring outcome.",
                )

        training = RankingModelService.train(db)
        return {
            "created_candidates": created_candidates,
            "total_demo_candidates": len(candidate_models),
            "created_jobs": created_jobs,
            "total_demo_jobs": len(job_models),
            "training": training,
        }
    finally:
        db.close()


if __name__ == "__main__":
    print(json.dumps(seed(), indent=2, default=str))
