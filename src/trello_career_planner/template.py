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
    """Get the tech career planning board template.

    Returns:
        Complete board template with lists and cards for tech career planning
    """
    labels = [
        LabelTemplate(name="High Priority", color="red"),
        LabelTemplate(name="In Progress", color="yellow"),
        LabelTemplate(name="Completed", color="green"),
        LabelTemplate(name="Learning", color="blue"),
        LabelTemplate(name="Networking", color="purple"),
        LabelTemplate(name="Long Term", color="orange"),
    ]

    lists = [
        ListTemplate(
            name="Career Goals",
            cards=[
                CardTemplate(
                    name="Define 1-Year Career Vision",
                    description="Write a clear statement of where you want to be in your tech career one year from now. Include target role, skills, and company type.",
                    labels=["High Priority"],
                ),
                CardTemplate(
                    name="Define 5-Year Career Vision",
                    description="Outline your long-term career aspirations. Consider leadership vs individual contributor paths, specialization areas, and industry focus.",
                    labels=["Long Term"],
                ),
                CardTemplate(
                    name="Identify Target Roles",
                    description="Research and list 3-5 specific job titles that align with your career goals. Include required qualifications for each.",
                    labels=["High Priority"],
                ),
                CardTemplate(
                    name="Salary & Compensation Goals",
                    description="Research market rates for your target roles. Set realistic compensation goals for 1, 3, and 5 year timeframes.",
                    labels=["Long Term"],
                ),
            ],
        ),
        ListTemplate(
            name="Skills Assessment",
            cards=[
                CardTemplate(
                    name="Current Technical Skills Inventory",
                    description="List all your current technical skills with proficiency levels (beginner, intermediate, advanced, expert).",
                    labels=["In Progress"],
                ),
                CardTemplate(
                    name="Soft Skills Assessment",
                    description="Evaluate your communication, leadership, problem-solving, and collaboration skills. Identify strengths and areas for improvement.",
                    labels=["In Progress"],
                ),
                CardTemplate(
                    name="Skills Gap Analysis",
                    description="Compare your current skills against requirements for target roles. Identify the most critical gaps to address.",
                    labels=["High Priority"],
                ),
                CardTemplate(
                    name="Competitive Advantage Identification",
                    description="Identify unique combinations of skills, experiences, or perspectives that differentiate you from other candidates.",
                    labels=["In Progress"],
                ),
            ],
        ),
        ListTemplate(
            name="Learning & Development",
            cards=[
                CardTemplate(
                    name="Online Courses to Complete",
                    description="List prioritized online courses (Coursera, Udemy, Pluralsight, etc.) that address your skills gaps.",
                    labels=["Learning"],
                ),
                CardTemplate(
                    name="Certifications to Pursue",
                    description="Research and list relevant certifications (AWS, GCP, Azure, Kubernetes, etc.) with timelines and costs.",
                    labels=["Learning", "High Priority"],
                ),
                CardTemplate(
                    name="Books & Reading List",
                    description="Curate a list of technical books, leadership books, and industry publications to read.",
                    labels=["Learning"],
                ),
                CardTemplate(
                    name="Side Projects",
                    description="Define 2-3 side projects that demonstrate skills relevant to your target roles. Include GitHub portfolio goals.",
                    labels=["Learning", "In Progress"],
                ),
                CardTemplate(
                    name="Conference & Workshop Attendance",
                    description="Identify conferences, meetups, and workshops to attend. Include both virtual and in-person options.",
                    labels=["Learning", "Networking"],
                ),
            ],
        ),
        ListTemplate(
            name="Networking",
            cards=[
                CardTemplate(
                    name="LinkedIn Profile Optimization",
                    description="Update headline, summary, experience sections. Add skills, get endorsements, and request recommendations.",
                    labels=["Networking", "High Priority"],
                ),
                CardTemplate(
                    name="Build Professional Network",
                    description="Set goals for connecting with industry professionals. Aim for quality connections with personalized messages.",
                    labels=["Networking"],
                ),
                CardTemplate(
                    name="Find Mentors",
                    description="Identify potential mentors in your target career path. Develop a strategy for reaching out and building relationships.",
                    labels=["Networking", "High Priority"],
                ),
                CardTemplate(
                    name="Join Professional Communities",
                    description="Research and join relevant Slack communities, Discord servers, subreddits, and professional associations.",
                    labels=["Networking"],
                ),
                CardTemplate(
                    name="Content Creation & Thought Leadership",
                    description="Plan blog posts, tweets, or talks that showcase your expertise. Build your personal brand in the tech community.",
                    labels=["Networking", "Long Term"],
                ),
            ],
        ),
        ListTemplate(
            name="Job Search Preparation",
            cards=[
                CardTemplate(
                    name="Update Resume",
                    description="Tailor resume for target roles. Quantify achievements, use action verbs, and optimize for ATS systems.",
                    labels=["High Priority"],
                ),
                CardTemplate(
                    name="Prepare Portfolio",
                    description="Create or update your portfolio website. Showcase best projects with clear descriptions of your contributions.",
                    labels=["High Priority"],
                ),
                CardTemplate(
                    name="Practice Technical Interviews",
                    description="Schedule regular practice on LeetCode, HackerRank, or similar. Focus on data structures, algorithms, and system design.",
                    labels=["In Progress"],
                ),
                CardTemplate(
                    name="Practice Behavioral Interviews",
                    description="Prepare STAR format stories for common behavioral questions. Practice with peers or use platforms like Pramp.",
                    labels=["In Progress"],
                ),
                CardTemplate(
                    name="Research Target Companies",
                    description="Create a list of target companies. Research their culture, tech stack, interview process, and recent news.",
                    labels=["In Progress"],
                ),
            ],
        ),
        ListTemplate(
            name="Weekly Actions",
            cards=[
                CardTemplate(
                    name="Weekly Learning Block",
                    description="Block 5+ hours per week for focused learning. Track progress on courses and certifications.",
                    labels=["Learning", "In Progress"],
                ),
                CardTemplate(
                    name="Weekly Networking Activity",
                    description="Send at least 2 meaningful connection requests or messages per week. Engage with content from your network.",
                    labels=["Networking", "In Progress"],
                ),
                CardTemplate(
                    name="Weekly Coding Practice",
                    description="Solve at least 3 coding problems per week. Review and learn from solutions.",
                    labels=["Learning", "In Progress"],
                ),
                CardTemplate(
                    name="Weekly Reflection",
                    description="Every Friday, review progress on career goals. Adjust priorities and celebrate wins.",
                    labels=["In Progress"],
                ),
            ],
        ),
        ListTemplate(
            name="Completed",
            cards=[
                CardTemplate(
                    name="Archive completed items here",
                    description="Move cards here as you complete them. Regularly review to see your progress!",
                    labels=["Completed"],
                ),
            ],
        ),
    ]

    return BoardTemplate(
        name="Tech Career Planning",
        description="A comprehensive board for planning and tracking your tech career development. Includes goals, skills assessment, learning plans, networking strategies, and job search preparation.",
        labels=labels,
        lists=lists,
    )
