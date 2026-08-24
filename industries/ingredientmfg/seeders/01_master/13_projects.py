"""Seeder: Project Types, Task Types and Project Templates for Ingredient Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Process Scale-up",
        "description": "Lab to plant scale-up of a new ingredient grade",
    },
    {
        "project_type": "GMP Facility Upgrade",
        "description": "Facility and compliance upgrade programme",
    },
    {
        "project_type": "Regulatory Programme",
        "description": "Registration and compliance dossiers",
    },
]

TASK_TYPES = [
    {"name": "Lab Trial", "description": "Bench and pilot scale extraction trials", "weight": 2},
    {
        "name": "Process Design",
        "description": "Mass balance, extraction flow and equipment sizing",
        "weight": 3,
    },
    {"name": "Procurement", "description": "Equipment and raw material sourcing", "weight": 2},
    {"name": "Installation", "description": "Mechanical and piping installation", "weight": 3},
    {"name": "Validation", "description": "Qualification runs and process validation", "weight": 2},
    {"name": "Safety", "description": "HAZOP, permits and safety audits", "weight": 2},
    {"name": "Regulatory", "description": "Dossiers, registrations and filings", "weight": 2},
    {"name": "Documentation", "description": "SOPs, batch records and reports", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Ingredient Scale-up Protocol",
        "project_type": "Process Scale-up",
        "phases": [
            {
                "subject": "Laboratory",
                "tasks": [
                    {
                        "subject": "Bench Scale Extraction Trial",
                        "type": "Lab Trial",
                        "start": 0,
                        "duration": 10,
                    },
                    {
                        "subject": "Yield & Potency Study",
                        "type": "Lab Trial",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Bench Scale Extraction Trial"],
                    },
                    {
                        "subject": "Food Safety Review",
                        "type": "Safety",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Yield & Potency Study"],
                    },
                ],
            },
            {
                "subject": "Engineering",
                "tasks": [
                    {
                        "subject": "Mass Balance",
                        "type": "Process Design",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Yield & Potency Study"],
                    },
                    {
                        "subject": "Extraction Equipment Sizing",
                        "type": "Process Design",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Mass Balance"],
                    },
                    {
                        "subject": "Long Lead Equipment Order",
                        "type": "Procurement",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Extraction Equipment Sizing"],
                    },
                ],
            },
            {
                "subject": "Plant Trials",
                "tasks": [
                    {
                        "subject": "Pilot Batch Run",
                        "type": "Lab Trial",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Food Safety Review"],
                    },
                    {
                        "subject": "Plant Trial Batch",
                        "type": "Validation",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Pilot Batch Run", "Long Lead Equipment Order"],
                    },
                    {
                        "subject": "Yield Optimisation",
                        "type": "Validation",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Plant Trial Batch"],
                    },
                ],
            },
            {
                "subject": "Validation",
                "tasks": [
                    {
                        "subject": "Process Validation Runs",
                        "type": "Validation",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Yield Optimisation"],
                    },
                    {
                        "subject": "SOP Release",
                        "type": "Documentation",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Process Validation Runs"],
                    },
                ],
            },
        ],
    },
    {
        "name": "GMP Facility Upgrade Package",
        "project_type": "GMP Facility Upgrade",
        "phases": [
            {
                "subject": "Preparation",
                "tasks": [
                    {
                        "subject": "Scope Freeze",
                        "type": "Process Design",
                        "start": 0,
                        "duration": 7,
                    },
                    {
                        "subject": "Spares Readiness",
                        "type": "Procurement",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Scope Freeze"],
                    },
                ],
            },
            {
                "subject": "Isolation",
                "tasks": [
                    {
                        "subject": "Permit to Work",
                        "type": "Safety",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Spares Readiness"],
                    },
                    {
                        "subject": "Shutdown Notification",
                        "type": "Documentation",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Permit to Work"],
                    },
                ],
            },
            {
                "subject": "Overhaul",
                "tasks": [
                    {
                        "subject": "Line Flushing & Isolation",
                        "type": "Installation",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Shutdown Notification"],
                    },
                    {
                        "subject": "Vessel Inspection",
                        "type": "Validation",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Line Flushing & Isolation"],
                    },
                    {
                        "subject": "Gasket & Valve Replacement",
                        "type": "Installation",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Vessel Inspection"],
                    },
                ],
            },
            {
                "subject": "Restart",
                "tasks": [
                    {
                        "subject": "Hydro Testing",
                        "type": "Validation",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Gasket & Valve Replacement"],
                    },
                    {
                        "subject": "Restart & Stabilisation",
                        "type": "Validation",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Hydro Testing"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Ingredient Manufacturing Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
