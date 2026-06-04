from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    name:             str
    agent_filter:     str   # value passed to ChromaDB metadata filter
    role:             str   # key into generator.ROLE_PROMPTS
    description:      str
    fallback_contact: str


AGENT_REGISTRY: dict[str, AgentConfig] = {
    "admissions": AgentConfig(
        name             = "Admissions Agent",
        agent_filter     = "admissions",
        role             = "student",
        description      = "Fees, eligibility, application process, deadlines",
        fallback_contact = "admissions@northfield.edu.in | +91-97777-88888",
    ),
    "academics": AgentConfig(
        name             = "Academics Agent",
        agent_filter     = "academics",
        role             = "student",
        description      = "Courses, timetable, exam schedule, attendance rules",
        fallback_contact = "academics@northfield.edu.in | +91-97777-88888",
    ),
    "student": AgentConfig(
        name             = "Student Services Agent",
        agent_filter     = "student",
        role             = "student",
        description      = "Conduct, library, hostel, clubs, grievances",
        fallback_contact = "welfare@northfield.edu.in | Dr Priya Menon, Room 203 | +91-97777-88888",
    ),
    "faculty": AgentConfig(
        name             = "Faculty Agent",
        agent_filter     = "faculty",
        role             = "faculty",
        description      = "Pay scales, research policy, leave, lab resources",
        fallback_contact = "hr@northfield.edu.in",
    ),
    "admin": AgentConfig(
        name             = "Admin Agent",
        agent_filter     = "admin",
        role             = "admin",
        description      = "Certificates, IT portals, transport, procurement",
        fallback_contact = "registrar@northfield.edu.in | ithelpdesk@northfield.edu.in",
    ),
}