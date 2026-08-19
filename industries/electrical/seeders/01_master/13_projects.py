"""Seeder: Project Types, Task Types and Project Templates for Electrical."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "New Product Development",
        "description": "New switchgear and transformer development",
    },
    {
        "project_type": "Panel Build",
        "description": "Customer-specific panel manufacture and delivery",
    },
    {"project_type": "Type Testing", "description": "IEC type test and certification campaigns"},
]

TASK_TYPES = [
    {"name": "Design", "description": "Electrical and mechanical design", "weight": 3},
    {"name": "Prototyping", "description": "First article build and bench test", "weight": 3},
    {"name": "Fabrication", "description": "Sheet metal, tank and enclosure work", "weight": 2},
    {"name": "Assembly", "description": "Coil, core and switchgear assembly", "weight": 3},
    {"name": "Testing", "description": "Routine, HV and type testing", "weight": 3},
    {"name": "Certification", "description": "Third-party certification and reports", "weight": 2},
    {"name": "Documentation", "description": "Drawings, manuals and test reports", "weight": 1},
    {"name": "Dispatch", "description": "Packing, despatch and site handover", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Electrical NPD Programme",
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
                        "subject": "Electrical Design",
                        "type": "Design",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Market Requirement Study"],
                    },
                    {
                        "subject": "Mechanical Design",
                        "type": "Design",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Electrical Design"],
                    },
                ],
            },
            {
                "subject": "Design",
                "tasks": [
                    {
                        "subject": "BOM Costing",
                        "type": "Design",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Electrical Design"],
                    },
                    {
                        "subject": "Tooling Order",
                        "type": "Fabrication",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["BOM Costing"],
                    },
                    {
                        "subject": "Component Sourcing",
                        "type": "Fabrication",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Tooling Order"],
                    },
                ],
            },
            {
                "subject": "Prototype & Test",
                "tasks": [
                    {
                        "subject": "Prototype Assembly",
                        "type": "Prototyping",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Mechanical Design"],
                    },
                    {
                        "subject": "Routine Test",
                        "type": "Testing",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Prototype Assembly", "Component Sourcing"],
                    },
                    {
                        "subject": "Temperature Rise Test",
                        "type": "Testing",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Routine Test"],
                    },
                ],
            },
            {
                "subject": "Release",
                "tasks": [
                    {
                        "subject": "Design Freeze",
                        "type": "Design",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Temperature Rise Test"],
                    },
                    {
                        "subject": "Production Release",
                        "type": "Documentation",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Design Freeze"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Panel Build Order",
        "project_type": "Panel Build",
        "phases": [
            {
                "subject": "Engineering",
                "tasks": [
                    {
                        "subject": "Customer Drawing Approval",
                        "type": "Design",
                        "start": 0,
                        "duration": 7,
                    },
                    {
                        "subject": "Bill of Material Release",
                        "type": "Design",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Customer Drawing Approval"],
                    },
                ],
            },
            {
                "subject": "Fabrication",
                "tasks": [
                    {
                        "subject": "Enclosure Fabrication",
                        "type": "Fabrication",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Bill of Material Release"],
                    },
                    {
                        "subject": "Powder Coating",
                        "type": "Fabrication",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Enclosure Fabrication"],
                    },
                ],
            },
            {
                "subject": "Assembly",
                "tasks": [
                    {
                        "subject": "Busbar Assembly",
                        "type": "Assembly",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Powder Coating"],
                    },
                    {
                        "subject": "Wiring & Termination",
                        "type": "Assembly",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Busbar Assembly"],
                    },
                    {
                        "subject": "Routine Testing",
                        "type": "Testing",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Wiring & Termination"],
                    },
                ],
            },
            {
                "subject": "Despatch",
                "tasks": [
                    {
                        "subject": "Inspection Call",
                        "type": "Certification",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Routine Testing"],
                    },
                    {
                        "subject": "Packing & Despatch",
                        "type": "Dispatch",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Inspection Call"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Electrical Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
