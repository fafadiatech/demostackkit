"""Seeder: Project Types, Task Types and Project Templates for Distribution."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Warehouse Setup",
        "description": "New distribution centre and depot commissioning",
    },
    {"project_type": "Route Expansion", "description": "Opening new territories and beats"},
    {"project_type": "Trade Programme", "description": "Seasonal and promotional trade drives"},
]

TASK_TYPES = [
    {"name": "Site Selection", "description": "Location search, survey and lease", "weight": 2},
    {"name": "Fit-out", "description": "Civil work, racking and material handling", "weight": 3},
    {"name": "Systems", "description": "WMS, scanning and integration setup", "weight": 2},
    {"name": "Recruitment", "description": "Hiring pickers, drivers and supervisors", "weight": 2},
    {"name": "Training", "description": "Process and system training", "weight": 1},
    {"name": "Inventory", "description": "Stock transfer and cycle counting", "weight": 2},
    {"name": "Marketing", "description": "Trade schemes and retailer outreach", "weight": 1},
    {"name": "Audit", "description": "Safety, stock and process audits", "weight": 2},
]

TEMPLATES = [
    {
        "name": "Depot Commissioning",
        "project_type": "Warehouse Setup",
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
                        "subject": "Racking Order",
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
                        "depends_on": ["Racking Order"],
                    },
                    {
                        "subject": "Racking Installation",
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
                        "depends_on": ["WMS Configuration", "Racking Installation"],
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
        "name": "Trade Scheme Rollout",
        "project_type": "Trade Programme",
        "phases": [
            {
                "subject": "Design",
                "tasks": [
                    {"subject": "Scheme Design", "type": "Marketing", "start": 0, "duration": 7},
                    {
                        "subject": "Margin Modelling",
                        "type": "Marketing",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Scheme Design"],
                    },
                ],
            },
            {
                "subject": "Approval",
                "tasks": [
                    {
                        "subject": "Principal Approval",
                        "type": "Marketing",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Margin Modelling"],
                    },
                    {
                        "subject": "Retailer Communication",
                        "type": "Marketing",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Principal Approval"],
                    },
                ],
            },
            {
                "subject": "Execution",
                "tasks": [
                    {
                        "subject": "Stock Build-up",
                        "type": "Inventory",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Retailer Communication"],
                    },
                    {
                        "subject": "Beat-wise Rollout",
                        "type": "Marketing",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Stock Build-up"],
                    },
                    {
                        "subject": "Secondary Sales Tracking",
                        "type": "Systems",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Beat-wise Rollout"],
                    },
                ],
            },
            {
                "subject": "Settlement",
                "tasks": [
                    {
                        "subject": "Claim Reconciliation",
                        "type": "Audit",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Secondary Sales Tracking"],
                    },
                    {
                        "subject": "Scheme Closure",
                        "type": "Audit",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Claim Reconciliation"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Distribution Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
