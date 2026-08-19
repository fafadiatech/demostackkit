"""Seeder: Project Types, Task Types and Project Templates for Crockery."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Collection Launch",
        "description": "New tableware range from concept to shelf",
    },
    {
        "project_type": "Kiln Project",
        "description": "Kiln construction, rebuild and refractory work",
    },
    {"project_type": "Retail Rollout", "description": "Own-store and shop-in-shop openings"},
]

TASK_TYPES = [
    {"name": "Design", "description": "Form, decal and colourway development", "weight": 2},
    {"name": "Prototyping", "description": "Sample throwing, casting and first fire", "weight": 2},
    {"name": "Mould Making", "description": "Master and working mould production", "weight": 2},
    {
        "name": "Glaze Development",
        "description": "Glaze formulation and firing trials",
        "weight": 2,
    },
    {"name": "Production", "description": "Series production runs", "weight": 3},
    {"name": "Inspection", "description": "QC checks and defect sorting", "weight": 2},
    {"name": "Marketing", "description": "Catalogue, photography and launch", "weight": 1},
    {"name": "Installation", "description": "Kiln and fixture installation", "weight": 3},
]

TEMPLATES = [
    {
        "name": "Collection Development",
        "project_type": "Collection Launch",
        "phases": [
            {
                "subject": "Concept",
                "tasks": [
                    {"subject": "Concept Sketches", "type": "Design", "start": 0, "duration": 10},
                    {
                        "subject": "Form Development",
                        "type": "Design",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Concept Sketches"],
                    },
                    {
                        "subject": "Colourway Approval",
                        "type": "Design",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Form Development"],
                    },
                ],
            },
            {
                "subject": "Tooling",
                "tasks": [
                    {
                        "subject": "Master Mould",
                        "type": "Mould Making",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Form Development"],
                    },
                    {
                        "subject": "Working Moulds",
                        "type": "Mould Making",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Master Mould"],
                    },
                    {
                        "subject": "Decal Artwork Order",
                        "type": "Design",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Working Moulds"],
                    },
                ],
            },
            {
                "subject": "Pilot Production",
                "tasks": [
                    {
                        "subject": "Glaze Trials",
                        "type": "Glaze Development",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Colourway Approval"],
                    },
                    {
                        "subject": "Pilot Firing Run",
                        "type": "Production",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Glaze Trials", "Decal Artwork Order"],
                    },
                    {
                        "subject": "Defect Review",
                        "type": "Inspection",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Pilot Firing Run"],
                    },
                ],
            },
            {
                "subject": "Launch",
                "tasks": [
                    {
                        "subject": "Catalogue Photography",
                        "type": "Marketing",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Defect Review"],
                    },
                    {
                        "subject": "Trade Launch",
                        "type": "Marketing",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Catalogue Photography"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Kiln Rebuild Package",
        "project_type": "Kiln Project",
        "phases": [
            {
                "subject": "Assessment",
                "tasks": [
                    {
                        "subject": "Refractory Condition Survey",
                        "type": "Inspection",
                        "start": 0,
                        "duration": 7,
                    },
                    {
                        "subject": "Rebuild Scope & Budget",
                        "type": "Design",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Refractory Condition Survey"],
                    },
                ],
            },
            {
                "subject": "Preparation",
                "tasks": [
                    {
                        "subject": "Refractory Material Order",
                        "type": "Installation",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Rebuild Scope & Budget"],
                    },
                    {
                        "subject": "Shutdown Scheduling",
                        "type": "Installation",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Refractory Material Order"],
                    },
                ],
            },
            {
                "subject": "Rebuild",
                "tasks": [
                    {
                        "subject": "Old Lining Demolition",
                        "type": "Installation",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Shutdown Scheduling"],
                    },
                    {
                        "subject": "New Lining Installation",
                        "type": "Installation",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Old Lining Demolition"],
                    },
                    {
                        "subject": "Burner Overhaul",
                        "type": "Installation",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["New Lining Installation"],
                    },
                ],
            },
            {
                "subject": "Recommissioning",
                "tasks": [
                    {
                        "subject": "Temperature Profiling",
                        "type": "Inspection",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Burner Overhaul"],
                    },
                    {
                        "subject": "Trial Firing",
                        "type": "Production",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Temperature Profiling"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Crockery Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
