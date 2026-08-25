"""Seeder: Project Types, Task Types and Project Templates for Ingredient Trading."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Depot Setup",
        "description": "New regional depot and godown commissioning",
    },
    {
        "project_type": "Network Expansion",
        "description": "Opening new distributor territories and zones",
    },
    {
        "project_type": "Supply Contract",
        "description": "Bulk supply and offtake contract negotiation and renewal",
    },
]

TASK_TYPES = [
    {"name": "Site Selection", "description": "Location search, survey and lease", "weight": 2},
    {
        "name": "Fit-out",
        "description": "Civil work, racking and material handling",
        "weight": 3,
    },
    {"name": "Systems", "description": "WMS, weighbridge and integration setup", "weight": 2},
    {
        "name": "Recruitment",
        "description": "Hiring warehouse and dispatch staff",
        "weight": 2,
    },
    {"name": "Training", "description": "Process and system training", "weight": 1},
    {"name": "Inventory", "description": "Stock transfer and cycle counting", "weight": 2},
    {
        "name": "Contracting",
        "description": "Supplier and distributor negotiation",
        "weight": 2,
    },
    {"name": "Audit", "description": "Compliance, stock and process audits", "weight": 2},
]

TEMPLATES = [
    {
        "name": "Depot Commissioning",
        "project_type": "Depot Setup",
        "phases": [
            {
                "subject": "Site",
                "tasks": [
                    {
                        "subject": "Location Survey",
                        "type": "Site Selection",
                        "start": 0,
                        "duration": 10,
                    },
                    {
                        "subject": "Lease Negotiation",
                        "type": "Site Selection",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Location Survey"],
                    },
                    {
                        "subject": "Layout Design",
                        "type": "Fit-out",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Lease Negotiation"],
                    },
                ],
            },
            {
                "subject": "Fit-out",
                "tasks": [
                    {
                        "subject": "Racking & Silo Order",
                        "type": "Fit-out",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Lease Negotiation"],
                    },
                    {
                        "subject": "Civil & Flooring",
                        "type": "Fit-out",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Racking & Silo Order"],
                    },
                    {
                        "subject": "Weighbridge Installation",
                        "type": "Fit-out",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Civil & Flooring"],
                    },
                ],
            },
            {
                "subject": "Systems & Staffing",
                "tasks": [
                    {
                        "subject": "WMS Configuration",
                        "type": "Systems",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Layout Design"],
                    },
                    {
                        "subject": "Staff Recruitment",
                        "type": "Recruitment",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["WMS Configuration", "Weighbridge Installation"],
                    },
                    {
                        "subject": "Process Training",
                        "type": "Training",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Staff Recruitment"],
                    },
                ],
            },
            {
                "subject": "Go-Live",
                "tasks": [
                    {
                        "subject": "Opening Stock Transfer",
                        "type": "Inventory",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Process Training"],
                    },
                    {
                        "subject": "Depot Go-Live",
                        "type": "Systems",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Opening Stock Transfer"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Bulk Supply Contract Rollout",
        "project_type": "Supply Contract",
        "phases": [
            {
                "subject": "Negotiation",
                "tasks": [
                    {
                        "subject": "Volume & Pricing Terms",
                        "type": "Contracting",
                        "start": 0,
                        "duration": 15,
                    },
                    {
                        "subject": "Contract Finalisation",
                        "type": "Contracting",
                        "start": 15,
                        "duration": 12,
                        "depends_on": ["Volume & Pricing Terms"],
                    },
                ],
            },
            {
                "subject": "Execution",
                "tasks": [
                    {
                        "subject": "Stock Build-up",
                        "type": "Inventory",
                        "start": 27,
                        "duration": 20,
                        "depends_on": ["Contract Finalisation"],
                    },
                    {
                        "subject": "Dispatch Scheduling",
                        "type": "Systems",
                        "start": 47,
                        "duration": 15,
                        "depends_on": ["Stock Build-up"],
                    },
                ],
            },
            {
                "subject": "Closure",
                "tasks": [
                    {
                        "subject": "Delivery Reconciliation",
                        "type": "Audit",
                        "start": 62,
                        "duration": 12,
                        "depends_on": ["Dispatch Scheduling"],
                    },
                    {
                        "subject": "Contract Renewal Review",
                        "type": "Audit",
                        "start": 74,
                        "duration": 8,
                        "depends_on": ["Delivery Reconciliation"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Ingredient Trading Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
