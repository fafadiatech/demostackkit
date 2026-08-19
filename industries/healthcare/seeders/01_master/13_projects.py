"""Seeder: Project Types, Task Types and Project Templates for Healthcare."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {"project_type": "Facility Setup", "description": "New wing, ward and unit commissioning"},
    {
        "project_type": "Accreditation",
        "description": "NABH, NABL and quality accreditation programmes",
    },
    {"project_type": "Clinical Programme", "description": "New clinical service line launches"},
]

TASK_TYPES = [
    {"name": "Planning", "description": "Scoping, budgeting and scheduling", "weight": 1},
    {"name": "Civil Works", "description": "Construction, partitions and finishes", "weight": 3},
    {
        "name": "Equipment",
        "description": "Medical equipment procurement and installation",
        "weight": 3,
    },
    {"name": "Recruitment", "description": "Clinical and support staff hiring", "weight": 2},
    {"name": "Training", "description": "Protocol, safety and system training", "weight": 1},
    {"name": "Documentation", "description": "SOPs, policies and records", "weight": 2},
    {"name": "Audit", "description": "Internal audits and mock inspections", "weight": 2},
    {"name": "Launch", "description": "Go-live and patient onboarding", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Clinical Facility Commissioning",
        "project_type": "Facility Setup",
        "phases": [
            {
                "subject": "Planning",
                "tasks": [
                    {"subject": "Needs Assessment", "type": "Planning", "start": 0, "duration": 10},
                    {
                        "subject": "Layout & Flow Design",
                        "type": "Planning",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Needs Assessment"],
                    },
                    {
                        "subject": "Regulatory Clearance",
                        "type": "Documentation",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Layout & Flow Design"],
                    },
                ],
            },
            {
                "subject": "Build-out",
                "tasks": [
                    {
                        "subject": "Equipment Specification",
                        "type": "Equipment",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Layout & Flow Design"],
                    },
                    {
                        "subject": "Equipment Purchase Order",
                        "type": "Equipment",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Equipment Specification"],
                    },
                    {
                        "subject": "Contractor Award",
                        "type": "Civil Works",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Equipment Purchase Order"],
                    },
                ],
            },
            {
                "subject": "Equipment & Staffing",
                "tasks": [
                    {
                        "subject": "Civil & Services Work",
                        "type": "Civil Works",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Regulatory Clearance"],
                    },
                    {
                        "subject": "Equipment Installation",
                        "type": "Equipment",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Civil & Services Work", "Contractor Award"],
                    },
                    {
                        "subject": "Staff Recruitment",
                        "type": "Recruitment",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Equipment Installation"],
                    },
                ],
            },
            {
                "subject": "Go-Live",
                "tasks": [
                    {
                        "subject": "Protocol Training",
                        "type": "Training",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Staff Recruitment"],
                    },
                    {
                        "subject": "Unit Go-Live",
                        "type": "Launch",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Protocol Training"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Accreditation Programme",
        "project_type": "Accreditation",
        "phases": [
            {
                "subject": "Assessment",
                "tasks": [
                    {"subject": "Gap Assessment", "type": "Audit", "start": 0, "duration": 7},
                    {
                        "subject": "Action Plan",
                        "type": "Planning",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Gap Assessment"],
                    },
                ],
            },
            {
                "subject": "Documentation",
                "tasks": [
                    {
                        "subject": "Policy & SOP Drafting",
                        "type": "Documentation",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Action Plan"],
                    },
                    {
                        "subject": "Committee Formation",
                        "type": "Documentation",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Policy & SOP Drafting"],
                    },
                ],
            },
            {
                "subject": "Implementation",
                "tasks": [
                    {
                        "subject": "Staff Sensitisation",
                        "type": "Training",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Committee Formation"],
                    },
                    {
                        "subject": "Records Implementation",
                        "type": "Documentation",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Staff Sensitisation"],
                    },
                    {
                        "subject": "Internal Audit Round",
                        "type": "Audit",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Records Implementation"],
                    },
                ],
            },
            {
                "subject": "Assessment Visit",
                "tasks": [
                    {
                        "subject": "Mock Assessment",
                        "type": "Audit",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Internal Audit Round"],
                    },
                    {
                        "subject": "Final Assessment Visit",
                        "type": "Audit",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Mock Assessment"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Healthcare Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
