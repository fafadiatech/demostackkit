"""Seeder: Project Types, Task Types and Project Templates for EPC."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {"project_type": "Turnkey EPC", "description": "Single-point design, supply and construction"},
    {"project_type": "Civil Works", "description": "Structural and civil packages"},
    {"project_type": "MEP Retrofit", "description": "Mechanical, electrical and plumbing fit-out"},
]

TASK_TYPES = [
    {"name": "Survey", "description": "Site measurement and investigation", "weight": 1},
    {"name": "Design", "description": "Drawings and engineering calculations", "weight": 2},
    {"name": "Approval", "description": "Statutory and client sign-off", "weight": 1},
    {"name": "Procurement", "description": "Vendor selection, orders and delivery", "weight": 2},
    {"name": "Civil Works", "description": "Foundations, structures and finishes", "weight": 3},
    {"name": "MEP", "description": "Electrical, mechanical and plumbing installation", "weight": 3},
    {"name": "Testing", "description": "Inspection, testing and commissioning", "weight": 2},
    {"name": "Safety", "description": "Site safety audits and toolbox talks", "weight": 1},
    {"name": "Handover", "description": "Documentation and client handover", "weight": 1},
]

TEMPLATES = [
    {
        "name": "EPC Turnkey Delivery",
        "project_type": "Turnkey EPC",
        "phases": [
            {
                "subject": "Engineering",
                "tasks": [
                    {"subject": "Site Survey", "type": "Survey", "start": 0, "duration": 10},
                    {
                        "subject": "Design Package",
                        "type": "Design",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Site Survey"],
                    },
                    {
                        "subject": "Statutory Approvals",
                        "type": "Approval",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Design Package"],
                    },
                ],
            },
            {
                "subject": "Procurement",
                "tasks": [
                    {
                        "subject": "Vendor Selection",
                        "type": "Procurement",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Design Package"],
                    },
                    {
                        "subject": "Long Lead Purchase Orders",
                        "type": "Procurement",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Vendor Selection"],
                    },
                    {
                        "subject": "Material Delivery to Site",
                        "type": "Procurement",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Long Lead Purchase Orders"],
                    },
                ],
            },
            {
                "subject": "Construction",
                "tasks": [
                    {
                        "subject": "Foundation Works",
                        "type": "Civil Works",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Statutory Approvals"],
                    },
                    {
                        "subject": "Structural Erection",
                        "type": "Civil Works",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Foundation Works", "Material Delivery to Site"],
                    },
                    {
                        "subject": "MEP Installation",
                        "type": "MEP",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Structural Erection"],
                    },
                ],
            },
            {
                "subject": "Commissioning",
                "tasks": [
                    {
                        "subject": "Integrated Testing",
                        "type": "Testing",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["MEP Installation"],
                    },
                    {
                        "subject": "Client Handover",
                        "type": "Handover",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Integrated Testing"],
                    },
                ],
            },
        ],
    },
    {
        "name": "MEP Retrofit Package",
        "project_type": "MEP Retrofit",
        "phases": [
            {
                "subject": "Assessment",
                "tasks": [
                    {"subject": "Site Assessment", "type": "Survey", "start": 0, "duration": 7},
                    {
                        "subject": "Electrical Load Study",
                        "type": "Design",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Site Assessment"],
                    },
                ],
            },
            {
                "subject": "Retrofit Design",
                "tasks": [
                    {
                        "subject": "Retrofit Drawings",
                        "type": "Design",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Electrical Load Study"],
                    },
                    {
                        "subject": "Client Design Approval",
                        "type": "Approval",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Retrofit Drawings"],
                    },
                ],
            },
            {
                "subject": "Execution",
                "tasks": [
                    {
                        "subject": "Cable Pulling",
                        "type": "MEP",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Client Design Approval"],
                    },
                    {
                        "subject": "Panel Installation",
                        "type": "MEP",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Cable Pulling"],
                    },
                    {
                        "subject": "Fixture Installation",
                        "type": "MEP",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Panel Installation"],
                    },
                ],
            },
            {
                "subject": "Handover",
                "tasks": [
                    {
                        "subject": "Testing & Balancing",
                        "type": "Testing",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Fixture Installation"],
                    },
                    {
                        "subject": "Handover Documentation",
                        "type": "Handover",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Testing & Balancing"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "EPC Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
