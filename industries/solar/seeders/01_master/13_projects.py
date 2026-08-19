"""Seeder: Project Types, Task Types and Project Templates for Solar."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Ground-Mount Farm",
        "description": "Utility-scale ground mounted solar plants",
    },
    {
        "project_type": "Rooftop Install",
        "description": "Commercial and residential rooftop systems",
    },
    {"project_type": "O&M Contract", "description": "Operations and maintenance service contracts"},
]

TASK_TYPES = [
    {"name": "Survey", "description": "Site survey, shadow analysis and feasibility", "weight": 1},
    {
        "name": "Design",
        "description": "Layout, string sizing and single line diagrams",
        "weight": 2,
    },
    {
        "name": "Approval",
        "description": "DISCOM, net metering and statutory approvals",
        "weight": 2,
    },
    {"name": "Procurement", "description": "Module, inverter and BOS sourcing", "weight": 2},
    {
        "name": "Civil Works",
        "description": "Foundations, mounting structure and cabling trenches",
        "weight": 3,
    },
    {
        "name": "Installation",
        "description": "Module mounting, wiring and inverter fitment",
        "weight": 3,
    },
    {
        "name": "Commissioning",
        "description": "Testing, synchronisation and performance ratio",
        "weight": 2,
    },
    {"name": "Safety", "description": "Site safety audits and toolbox talks", "weight": 1},
    {"name": "Handover", "description": "Documentation, training and handover", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Utility Solar Delivery",
        "project_type": "Ground-Mount Farm",
        "phases": [
            {
                "subject": "Engineering",
                "tasks": [
                    {"subject": "Site Survey", "type": "Survey", "start": 0, "duration": 10},
                    {
                        "subject": "Plant Layout Design",
                        "type": "Design",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Site Survey"],
                    },
                    {
                        "subject": "DISCOM Approval",
                        "type": "Approval",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Plant Layout Design"],
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
                        "depends_on": ["Plant Layout Design"],
                    },
                    {
                        "subject": "Module & Inverter Order",
                        "type": "Procurement",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Vendor Selection"],
                    },
                    {
                        "subject": "BOS Material Delivery",
                        "type": "Procurement",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Module & Inverter Order"],
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
                        "depends_on": ["DISCOM Approval"],
                    },
                    {
                        "subject": "Structure & Module Mounting",
                        "type": "Installation",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Foundation Works", "BOS Material Delivery"],
                    },
                    {
                        "subject": "Cabling & Inverter Fitment",
                        "type": "Installation",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Structure & Module Mounting"],
                    },
                ],
            },
            {
                "subject": "Commissioning",
                "tasks": [
                    {
                        "subject": "Grid Synchronisation",
                        "type": "Commissioning",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Cabling & Inverter Fitment"],
                    },
                    {
                        "subject": "Plant Handover",
                        "type": "Handover",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Grid Synchronisation"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Rooftop Solar Installation",
        "project_type": "Rooftop Install",
        "phases": [
            {
                "subject": "Assessment",
                "tasks": [
                    {
                        "subject": "Roof Structural Assessment",
                        "type": "Survey",
                        "start": 0,
                        "duration": 7,
                    },
                    {
                        "subject": "Shadow Analysis",
                        "type": "Survey",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Roof Structural Assessment"],
                    },
                ],
            },
            {
                "subject": "Design & Approval",
                "tasks": [
                    {
                        "subject": "System Design",
                        "type": "Design",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Shadow Analysis"],
                    },
                    {
                        "subject": "Net Metering Approval",
                        "type": "Approval",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["System Design"],
                    },
                ],
            },
            {
                "subject": "Installation",
                "tasks": [
                    {
                        "subject": "Mounting Structure Erection",
                        "type": "Installation",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Net Metering Approval"],
                    },
                    {
                        "subject": "Module Mounting",
                        "type": "Installation",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Mounting Structure Erection"],
                    },
                    {
                        "subject": "Inverter & Cabling",
                        "type": "Installation",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Module Mounting"],
                    },
                ],
            },
            {
                "subject": "Handover",
                "tasks": [
                    {
                        "subject": "Performance Testing",
                        "type": "Commissioning",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Inverter & Cabling"],
                    },
                    {
                        "subject": "Handover Documentation",
                        "type": "Handover",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Performance Testing"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Solar Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
