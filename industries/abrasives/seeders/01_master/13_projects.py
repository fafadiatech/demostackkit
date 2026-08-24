"""Seeder: Project Types, Task Types and Project Templates for Alpha Abrasives."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "New Product Development",
        "description": "New abrasive product line development and commissioning",
    },
    {
        "project_type": "Quality Certification",
        "description": "ISI / third-party certification campaigns for abrasive products",
    },
    {
        "project_type": "Export Market Development",
        "description": "New export buyer onboarding and market entry programmes",
    },
]

TASK_TYPES = [
    {"name": "Design", "description": "Product and process design", "weight": 3},
    {"name": "Sourcing", "description": "Raw material, tooling and machine sourcing", "weight": 2},
    {"name": "Production", "description": "Mixing, pressing, curing and trial runs", "weight": 3},
    {
        "name": "Testing",
        "description": "Grit, balance, burst/RPM and bond hardness testing",
        "weight": 3,
    },
    {"name": "Certification", "description": "Third-party certification and audits", "weight": 2},
    {
        "name": "Documentation",
        "description": "Specifications, reports and export paperwork",
        "weight": 1,
    },
    {
        "name": "Onboarding",
        "description": "Buyer qualification and account onboarding",
        "weight": 2,
    },
    {"name": "Dispatch", "description": "Packing and despatch to first order", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Abrasive NPD Programme",
        "project_type": "New Product Development",
        "phases": [
            {
                "subject": "Definition",
                "tasks": [
                    {
                        "subject": "Market Requirement Study",
                        "type": "Design",
                        "start": 0,
                        "duration": 10,
                    },
                    {
                        "subject": "Formulation Design",
                        "type": "Design",
                        "start": 10,
                        "duration": 20,
                        "depends_on": ["Market Requirement Study"],
                    },
                    {
                        "subject": "Mould & Tooling Design",
                        "type": "Design",
                        "start": 30,
                        "duration": 18,
                        "depends_on": ["Formulation Design"],
                    },
                ],
            },
            {
                "subject": "Sourcing",
                "tasks": [
                    {
                        "subject": "Raw Material Sourcing",
                        "type": "Sourcing",
                        "start": 48,
                        "duration": 20,
                        "depends_on": ["Mould & Tooling Design"],
                    },
                    {
                        "subject": "Tooling Fabrication",
                        "type": "Sourcing",
                        "start": 48,
                        "duration": 25,
                        "depends_on": ["Mould & Tooling Design"],
                    },
                ],
            },
            {
                "subject": "Trial & Test",
                "tasks": [
                    {
                        "subject": "Trial Batch Production",
                        "type": "Production",
                        "start": 73,
                        "duration": 20,
                        "depends_on": ["Raw Material Sourcing", "Tooling Fabrication"],
                    },
                    {
                        "subject": "Burst/RPM Safety Testing",
                        "type": "Testing",
                        "start": 93,
                        "duration": 20,
                        "depends_on": ["Trial Batch Production"],
                    },
                    {
                        "subject": "Grit & Bond Hardness Testing",
                        "type": "Testing",
                        "start": 93,
                        "duration": 18,
                        "depends_on": ["Trial Batch Production"],
                    },
                ],
            },
            {
                "subject": "Release",
                "tasks": [
                    {
                        "subject": "Specification Freeze",
                        "type": "Documentation",
                        "start": 113,
                        "duration": 12,
                        "depends_on": ["Burst/RPM Safety Testing", "Grit & Bond Hardness Testing"],
                    },
                    {
                        "subject": "Production Release",
                        "type": "Documentation",
                        "start": 125,
                        "duration": 8,
                        "depends_on": ["Specification Freeze"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Abrasives Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
