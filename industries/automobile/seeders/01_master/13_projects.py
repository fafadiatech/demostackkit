"""Seeder: Project Types, Task Types and Project Templates for Automobile."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Workshop Setup",
        "description": "Bay expansion and new workshop commissioning",
    },
    {
        "project_type": "Service Campaign",
        "description": "Recalls, service camps and customer outreach drives",
    },
    {"project_type": "Dealer Program", "description": "Dealer-wide systems and process rollouts"},
]

TASK_TYPES = [
    {"name": "Planning", "description": "Scoping, budgeting and scheduling", "weight": 1},
    {"name": "Civil Works", "description": "Building, flooring and bay construction", "weight": 3},
    {
        "name": "Equipment",
        "description": "Lifts, diagnostics and tooling installation",
        "weight": 2,
    },
    {"name": "Training", "description": "Technician and advisor upskilling", "weight": 1},
    {"name": "Marketing", "description": "Customer outreach and promotion", "weight": 1},
    {"name": "Inspection", "description": "Quality and safety checks", "weight": 2},
    {"name": "Documentation", "description": "Manuals, checklists and sign-off", "weight": 1},
    {"name": "Rollout", "description": "Go-live and handover", "weight": 2},
]

TEMPLATES = [
    {
        "name": "Workshop Commissioning",
        "project_type": "Workshop Setup",
        "phases": [
            {
                "subject": "Planning",
                "tasks": [
                    {"subject": "Capacity Study", "type": "Planning", "start": 0, "duration": 10},
                    {
                        "subject": "Layout Drawings",
                        "type": "Planning",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Capacity Study"],
                    },
                    {
                        "subject": "Municipal Approvals",
                        "type": "Planning",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Layout Drawings"],
                    },
                ],
            },
            {
                "subject": "Build-out",
                "tasks": [
                    {
                        "subject": "Contractor Selection",
                        "type": "Planning",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Layout Drawings"],
                    },
                    {
                        "subject": "Civil Work Order",
                        "type": "Civil Works",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Contractor Selection"],
                    },
                    {
                        "subject": "Equipment Delivery",
                        "type": "Equipment",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Civil Work Order"],
                    },
                ],
            },
            {
                "subject": "Equipment & Staffing",
                "tasks": [
                    {
                        "subject": "Bay Construction",
                        "type": "Civil Works",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Municipal Approvals"],
                    },
                    {
                        "subject": "Lift & Aligner Installation",
                        "type": "Equipment",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Bay Construction", "Equipment Delivery"],
                    },
                    {
                        "subject": "Technician Training",
                        "type": "Training",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Lift & Aligner Installation"],
                    },
                ],
            },
            {
                "subject": "Go-Live",
                "tasks": [
                    {
                        "subject": "Safety Inspection",
                        "type": "Inspection",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Technician Training"],
                    },
                    {
                        "subject": "Workshop Opening",
                        "type": "Rollout",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Safety Inspection"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Service Campaign Playbook",
        "project_type": "Service Campaign",
        "phases": [
            {
                "subject": "Campaign Setup",
                "tasks": [
                    {
                        "subject": "Affected VIN Extraction",
                        "type": "Planning",
                        "start": 0,
                        "duration": 7,
                    },
                    {
                        "subject": "Parts Requirement Plan",
                        "type": "Planning",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Affected VIN Extraction"],
                    },
                ],
            },
            {
                "subject": "Outreach",
                "tasks": [
                    {
                        "subject": "Customer Call Script",
                        "type": "Marketing",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Parts Requirement Plan"],
                    },
                    {
                        "subject": "Campaign Approval",
                        "type": "Planning",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Customer Call Script"],
                    },
                ],
            },
            {
                "subject": "Execution",
                "tasks": [
                    {
                        "subject": "Customer Outreach Calls",
                        "type": "Marketing",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Campaign Approval"],
                    },
                    {
                        "subject": "Appointment Scheduling",
                        "type": "Planning",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Customer Outreach Calls"],
                    },
                    {
                        "subject": "Rectification Work",
                        "type": "Inspection",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Appointment Scheduling"],
                    },
                ],
            },
            {
                "subject": "Closure",
                "tasks": [
                    {
                        "subject": "Quality Re-check",
                        "type": "Inspection",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Rectification Work"],
                    },
                    {
                        "subject": "Campaign Report",
                        "type": "Documentation",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Quality Re-check"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Automobile Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
