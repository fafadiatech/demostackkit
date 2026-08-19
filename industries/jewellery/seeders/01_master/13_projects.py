"""Seeder: Project Types, Task Types and Project Templates for Jewellery."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Collection Launch",
        "description": "New retail collection from concept to counter",
    },
    {"project_type": "Bespoke Commission", "description": "Made-to-order client commissions"},
    {"project_type": "Exhibition", "description": "Trade shows and exhibition participation"},
]

TASK_TYPES = [
    {"name": "Design", "description": "Sketching, CAD and client approval", "weight": 2},
    {"name": "Casting", "description": "Wax, investment and casting", "weight": 3},
    {"name": "Setting", "description": "Stone selection and setting", "weight": 3},
    {"name": "Finishing", "description": "Filing, polishing and plating", "weight": 2},
    {"name": "Hallmarking", "description": "Assaying and BIS hallmarking", "weight": 2},
    {"name": "Inspection", "description": "Quality and weight verification", "weight": 2},
    {"name": "Merchandising", "description": "Display, catalogue and pricing", "weight": 1},
    {"name": "Logistics", "description": "Secure transport and insurance", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Collection Development",
        "project_type": "Collection Launch",
        "phases": [
            {
                "subject": "Concept",
                "tasks": [
                    {"subject": "Theme Research", "type": "Design", "start": 0, "duration": 10},
                    {
                        "subject": "Design Sketches",
                        "type": "Design",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Theme Research"],
                    },
                    {
                        "subject": "CAD Modelling",
                        "type": "Design",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Design Sketches"],
                    },
                ],
            },
            {
                "subject": "Prototyping",
                "tasks": [
                    {
                        "subject": "Stone Sourcing",
                        "type": "Setting",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Design Sketches"],
                    },
                    {
                        "subject": "Bullion Allocation",
                        "type": "Casting",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Stone Sourcing"],
                    },
                    {
                        "subject": "Master Wax",
                        "type": "Casting",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Bullion Allocation"],
                    },
                ],
            },
            {
                "subject": "Production",
                "tasks": [
                    {
                        "subject": "Prototype Casting",
                        "type": "Casting",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["CAD Modelling"],
                    },
                    {
                        "subject": "Stone Setting",
                        "type": "Setting",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Prototype Casting", "Master Wax"],
                    },
                    {
                        "subject": "Polishing & Plating",
                        "type": "Finishing",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Stone Setting"],
                    },
                ],
            },
            {
                "subject": "Launch",
                "tasks": [
                    {
                        "subject": "Hallmarking",
                        "type": "Hallmarking",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Polishing & Plating"],
                    },
                    {
                        "subject": "Counter Launch",
                        "type": "Merchandising",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Hallmarking"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Bespoke Commission Flow",
        "project_type": "Bespoke Commission",
        "phases": [
            {
                "subject": "Brief",
                "tasks": [
                    {"subject": "Client Brief", "type": "Design", "start": 0, "duration": 7},
                    {
                        "subject": "Budget & Estimate",
                        "type": "Design",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Client Brief"],
                    },
                ],
            },
            {
                "subject": "Design",
                "tasks": [
                    {
                        "subject": "CAD Rendering",
                        "type": "Design",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Budget & Estimate"],
                    },
                    {
                        "subject": "Client Approval",
                        "type": "Design",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["CAD Rendering"],
                    },
                ],
            },
            {
                "subject": "Make",
                "tasks": [
                    {
                        "subject": "Stone Selection",
                        "type": "Setting",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Client Approval"],
                    },
                    {
                        "subject": "Casting & Assembly",
                        "type": "Casting",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Stone Selection"],
                    },
                    {
                        "subject": "Setting & Finishing",
                        "type": "Finishing",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Casting & Assembly"],
                    },
                ],
            },
            {
                "subject": "Delivery",
                "tasks": [
                    {
                        "subject": "Hallmark & Certify",
                        "type": "Hallmarking",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Setting & Finishing"],
                    },
                    {
                        "subject": "Client Delivery",
                        "type": "Logistics",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Hallmark & Certify"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Jewellery Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
