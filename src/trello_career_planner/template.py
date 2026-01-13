"""Tech career planning template definition."""

from dataclasses import dataclass, field


@dataclass
class CardTemplate:
    """Template for a Trello card."""

    name: str
    description: str = ""
    labels: list[str] = field(default_factory=list)


@dataclass
class ListTemplate:
    """Template for a Trello list."""

    name: str
    cards: list[CardTemplate] = field(default_factory=list)


@dataclass
class LabelTemplate:
    """Template for a Trello label."""

    name: str
    color: str


@dataclass
class BoardTemplate:
    """Template for a Trello board."""

    name: str
    description: str
    labels: list[LabelTemplate] = field(default_factory=list)
    lists: list[ListTemplate] = field(default_factory=list)


def get_tech_career_template() -> BoardTemplate:
    """Get the tech career planning board template with hybrid weekly sprint workflow.

    Returns:
        Complete board template with sprint-based workflow for tech career planning
    """
    labels = [
        LabelTemplate(name="High Priority", color="red"),
        LabelTemplate(name="Quick Win", color="green"),
        LabelTemplate(name="Learning", color="blue"),
        LabelTemplate(name="Networking", color="purple"),
        LabelTemplate(name="Career Goal", color="orange"),
        LabelTemplate(name="Blocked", color="yellow"),
    ]

    lists = [
        ListTemplate(
            name="Sprint Backlog",
            cards=[
                CardTemplate(
                    name="Define 1-Year Career Vision",
                    description="Write a clear statement of where you want to be in your tech career one year from now. Include target role, skills, and company type.",
                    labels=["Career Goal", "High Priority"],
                ),
                CardTemplate(
                    name="Skills Gap Analysis",
                    description="Compare your current skills against requirements for target roles. Identify the most critical gaps to address.",
                    labels=["Career Goal", "High Priority"],
                ),
                CardTemplate(
                    name="Update LinkedIn Profile",
                    description="Update headline, summary, experience sections. Add skills, get endorsements, and request recommendations.",
                    labels=["Networking", "Quick Win"],
                ),
                CardTemplate(
                    name="Research Target Companies",
                    description="Create a list of target companies. Research their culture, tech stack, interview process, and recent news.",
                    labels=["Career Goal"],
                ),
                CardTemplate(
                    name="Start Certification Study",
                    description="Begin studying for a relevant certification (AWS, GCP, Azure, Kubernetes, etc.) that aligns with your career goals.",
                    labels=["Learning", "High Priority"],
                ),
                CardTemplate(
                    name="Build Side Project",
                    description="Define and start a side project that demonstrates skills relevant to your target roles. Aim for GitHub portfolio visibility.",
                    labels=["Learning"],
                ),
            ],
        ),
        ListTemplate(
            name="This Week",
            cards=[
                CardTemplate(
                    name="Complete 3 LeetCode Problems",
                    description="Solve at least 3 coding problems. Focus on data structures and algorithms relevant to interview prep.",
                    labels=["Learning", "Quick Win"],
                ),
                CardTemplate(
                    name="Send 2 Networking Messages",
                    description="Reach out to 2 industry professionals with personalized connection requests or follow-up messages.",
                    labels=["Networking", "Quick Win"],
                ),
                CardTemplate(
                    name="Study 2 Hours for Certification",
                    description="Dedicate focused study time toward your target certification. Take notes and complete practice questions.",
                    labels=["Learning"],
                ),
            ],
        ),
        ListTemplate(
            name="In Progress",
            cards=[
                CardTemplate(
                    name="Example: Currently Active Task",
                    description="Move cards here when you start actively working on them. Limit work in progress to 2-3 items for focus.",
                    labels=[],
                ),
            ],
        ),
        ListTemplate(
            name="Blocked / Review",
            cards=[
                CardTemplate(
                    name="Example: Blocked Task",
                    description="Move cards here if they're blocked by external dependencies or waiting for review/feedback. Add a comment explaining the blocker.",
                    labels=["Blocked"],
                ),
            ],
        ),
        ListTemplate(
            name="Done This Week",
            cards=[
                CardTemplate(
                    name="Example: Completed Task",
                    description="Move completed tasks here. At the end of each week, review accomplishments and archive to Completed.",
                    labels=["Quick Win"],
                ),
            ],
        ),
        ListTemplate(
            name="Career Goals & Strategy",
            cards=[
                CardTemplate(
                    name="Target Roles List",
                    description="3-5 specific job titles that align with your career goals, with required qualifications for each.",
                    labels=["Career Goal"],
                ),
                CardTemplate(
                    name="5-Year Career Vision",
                    description="Long-term career aspirations: leadership vs IC path, specialization areas, industry focus, and compensation goals.",
                    labels=["Career Goal"],
                ),
                CardTemplate(
                    name="Technical Skills Inventory",
                    description="Current technical skills with proficiency levels. Update quarterly to track growth.",
                    labels=["Career Goal"],
                ),
                CardTemplate(
                    name="Networking Strategy",
                    description="Key communities to join, mentors to find, content creation plans for thought leadership.",
                    labels=["Networking", "Career Goal"],
                ),
            ],
        ),
        ListTemplate(
            name="Learning Resources",
            cards=[
                CardTemplate(
                    name="Online Courses Roadmap",
                    description="Prioritized list of courses (Coursera, Udemy, Pluralsight, etc.) mapped to skills gaps. Track completion status.",
                    labels=["Learning"],
                ),
                CardTemplate(
                    name="Books & Reading List",
                    description="Technical books, leadership books, and industry publications to read. Check off as completed.",
                    labels=["Learning"],
                ),
                CardTemplate(
                    name="Certification Path",
                    description="Target certifications with study timelines, exam dates, and cost estimates.",
                    labels=["Learning", "High Priority"],
                ),
                CardTemplate(
                    name="Interview Prep Resources",
                    description="LeetCode patterns, system design resources, behavioral question bank, and practice platforms.",
                    labels=["Learning"],
                ),
            ],
        ),
        ListTemplate(
            name="Completed",
            cards=[
                CardTemplate(
                    name="Archive completed items here",
                    description="At the end of each week, move items from 'Done This Week' here. Review monthly to celebrate progress!",
                    labels=["Quick Win"],
                ),
            ],
        ),
    ]

    return BoardTemplate(
        name="Tech Career Planning",
        description="A hybrid weekly sprint board for tech career development. Use sprint columns (Backlog → This Week → In Progress → Done) for weekly execution, with reference lists for long-term strategy and resources.",
        labels=labels,
        lists=lists,
    )
