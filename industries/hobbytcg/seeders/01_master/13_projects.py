"""Seeder: Project Types, Task Types and Project Templates for Hobby & TCG."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {"project_type": "Store Launch", "description": "New store and pop-up openings"},
    {"project_type": "Event Series", "description": "Tournaments, leagues and organised play"},
    {"project_type": "Season Programme", "description": "Seasonal buying and promotion cycles"},
]

TASK_TYPES = [
    {"name": "Planning", "description": "Scoping, budgeting and scheduling", "weight": 1},
    {"name": "Fit-out", "description": "Build-out, fixtures and play space", "weight": 3},
    {"name": "Merchandising", "description": "Range planning and display", "weight": 2},
    {"name": "Staffing", "description": "Hiring and scheduling", "weight": 2},
    {"name": "Marketing", "description": "Community outreach and promotion", "weight": 2},
    {"name": "Event Ops", "description": "Tournament running and judging", "weight": 2},
    {"name": "Inventory", "description": "Buying, receiving and stock control", "weight": 2},
    {"name": "Launch", "description": "Opening day and go-live", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Store Launch Playbook",
        "project_type": "Store Launch",
        "phases": [
            {
                "subject": "Planning",
                "tasks": [
                    {"subject": "Catchment Study", "type": "Planning", "start": 0, "duration": 10},
                    {
                        "subject": "Lease Signing",
                        "type": "Planning",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Catchment Study"],
                    },
                    {
                        "subject": "Store Layout",
                        "type": "Fit-out",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Lease Signing"],
                    },
                ],
            },
            {
                "subject": "Build-out",
                "tasks": [
                    {
                        "subject": "Fixture Order",
                        "type": "Fit-out",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Lease Signing"],
                    },
                    {
                        "subject": "Play Space Build",
                        "type": "Fit-out",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Fixture Order"],
                    },
                    {
                        "subject": "Opening Range Buy",
                        "type": "Inventory",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Play Space Build"],
                    },
                ],
            },
            {
                "subject": "Stock & Staffing",
                "tasks": [
                    {
                        "subject": "Shelf Fit-out",
                        "type": "Fit-out",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Store Layout"],
                    },
                    {
                        "subject": "Stock Receiving & Pricing",
                        "type": "Inventory",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Shelf Fit-out", "Opening Range Buy"],
                    },
                    {
                        "subject": "Staff Hiring",
                        "type": "Staffing",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Stock Receiving & Pricing"],
                    },
                ],
            },
            {
                "subject": "Opening",
                "tasks": [
                    {
                        "subject": "Community Pre-launch",
                        "type": "Marketing",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Staff Hiring"],
                    },
                    {
                        "subject": "Opening Day",
                        "type": "Launch",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Community Pre-launch"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Organised Play Season",
        "project_type": "Event Series",
        "phases": [
            {
                "subject": "Calendar",
                "tasks": [
                    {"subject": "Season Calendar", "type": "Planning", "start": 0, "duration": 7},
                    {
                        "subject": "Prize Support Request",
                        "type": "Planning",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Season Calendar"],
                    },
                ],
            },
            {
                "subject": "Promotion",
                "tasks": [
                    {
                        "subject": "Event Listing & Signup",
                        "type": "Marketing",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Prize Support Request"],
                    },
                    {
                        "subject": "Judge Roster",
                        "type": "Staffing",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Event Listing & Signup"],
                    },
                ],
            },
            {
                "subject": "Run",
                "tasks": [
                    {
                        "subject": "Weekly Qualifiers",
                        "type": "Event Ops",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Judge Roster"],
                    },
                    {
                        "subject": "Regional Final",
                        "type": "Event Ops",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Weekly Qualifiers"],
                    },
                    {
                        "subject": "Prize Distribution",
                        "type": "Event Ops",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Regional Final"],
                    },
                ],
            },
            {
                "subject": "Wrap-up",
                "tasks": [
                    {
                        "subject": "Player Feedback Survey",
                        "type": "Marketing",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Prize Distribution"],
                    },
                    {
                        "subject": "Season Report",
                        "type": "Planning",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Player Feedback Survey"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Hobby & TCG Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
