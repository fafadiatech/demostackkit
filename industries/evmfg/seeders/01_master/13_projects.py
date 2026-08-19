"""Seeder: Project Types, Task Types and Project Templates for EV Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "New Product Development",
        "description": "Vehicle and powertrain development",
    },
    {"project_type": "Line Commissioning", "description": "Assembly line installation and ramp-up"},
    {"project_type": "Homologation", "description": "ARAI/ICAT approval and compliance"},
]

TASK_TYPES = [
    {"name": "Design", "description": "Vehicle, pack and powertrain design", "weight": 3},
    {"name": "Prototyping", "description": "Mule build and bench validation", "weight": 3},
    {"name": "Tooling", "description": "Fixtures, jigs and line tooling", "weight": 2},
    {"name": "Assembly", "description": "Line assembly and integration", "weight": 3},
    {"name": "Validation", "description": "Durability, thermal and safety validation", "weight": 3},
    {"name": "Homologation", "description": "Regulatory testing and certification", "weight": 2},
    {"name": "Training", "description": "Operator and technician training", "weight": 1},
    {"name": "Documentation", "description": "Drawings, SOPs and approval files", "weight": 1},
]

TEMPLATES = [
    {
        "name": "EV Product Development",
        "project_type": "New Product Development",
        "phases": [
            {
                "subject": "Concept",
                "tasks": [
                    {
                        "subject": "Requirement Definition",
                        "type": "Design",
                        "start": 0,
                        "duration": 10,
                    },
                    {
                        "subject": "Powertrain Sizing",
                        "type": "Design",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Requirement Definition"],
                    },
                    {
                        "subject": "Pack Architecture",
                        "type": "Design",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Powertrain Sizing"],
                    },
                ],
            },
            {
                "subject": "Design",
                "tasks": [
                    {
                        "subject": "Supplier Selection",
                        "type": "Tooling",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Powertrain Sizing"],
                    },
                    {
                        "subject": "Prototype Tooling",
                        "type": "Tooling",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Supplier Selection"],
                    },
                    {
                        "subject": "Long Lead Component Order",
                        "type": "Tooling",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Prototype Tooling"],
                    },
                ],
            },
            {
                "subject": "Prototype & Validate",
                "tasks": [
                    {
                        "subject": "Mule Build",
                        "type": "Prototyping",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Pack Architecture"],
                    },
                    {
                        "subject": "Bench Validation",
                        "type": "Validation",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Mule Build", "Long Lead Component Order"],
                    },
                    {
                        "subject": "Durability Testing",
                        "type": "Validation",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Bench Validation"],
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
                        "depends_on": ["Durability Testing"],
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
        "name": "Assembly Line Commissioning",
        "project_type": "Line Commissioning",
        "phases": [
            {
                "subject": "Planning",
                "tasks": [
                    {"subject": "Line Layout Design", "type": "Design", "start": 0, "duration": 7},
                    {
                        "subject": "Cycle Time Study",
                        "type": "Design",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Line Layout Design"],
                    },
                ],
            },
            {
                "subject": "Installation",
                "tasks": [
                    {
                        "subject": "Equipment Installation",
                        "type": "Assembly",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Cycle Time Study"],
                    },
                    {
                        "subject": "Utility Hook-up",
                        "type": "Assembly",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Equipment Installation"],
                    },
                ],
            },
            {
                "subject": "Trial",
                "tasks": [
                    {
                        "subject": "Fixture Commissioning",
                        "type": "Tooling",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Utility Hook-up"],
                    },
                    {
                        "subject": "Dry Run",
                        "type": "Validation",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Fixture Commissioning"],
                    },
                    {
                        "subject": "Operator Training",
                        "type": "Training",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Dry Run"],
                    },
                ],
            },
            {
                "subject": "Ramp-up",
                "tasks": [
                    {
                        "subject": "Trial Production Batch",
                        "type": "Validation",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Operator Training"],
                    },
                    {
                        "subject": "Ramp-up Sign-off",
                        "type": "Documentation",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Trial Production Batch"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "EV Manufacturing Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
