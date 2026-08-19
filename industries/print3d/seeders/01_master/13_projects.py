"""Seeder: Project Types, Task Types and Project Templates for 3D Printing."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Prototype Programme",
        "description": "Multi-iteration prototype development for a client",
    },
    {
        "project_type": "Client Print Job",
        "description": "Production print runs against a customer order",
    },
    {
        "project_type": "Capacity Expansion",
        "description": "New printers, cells and capability build-out",
    },
]

TASK_TYPES = [
    {
        "name": "Requirements",
        "description": "Client brief, tolerances and material selection",
        "weight": 1,
    },
    {
        "name": "CAD Prep",
        "description": "File repair, orientation and support generation",
        "weight": 2,
    },
    {"name": "Printing", "description": "Machine setup and print runs", "weight": 3},
    {"name": "Post-Processing", "description": "Support removal, curing and cleaning", "weight": 2},
    {"name": "Finishing", "description": "Sanding, painting and assembly", "weight": 2},
    {"name": "Inspection", "description": "Dimensional and surface inspection", "weight": 2},
    {"name": "Shipping", "description": "Packing and despatch", "weight": 1},
    {
        "name": "Installation",
        "description": "Equipment installation and commissioning",
        "weight": 3,
    },
]

TEMPLATES = [
    {
        "name": "Prototype Delivery Programme",
        "project_type": "Prototype Programme",
        "phases": [
            {
                "subject": "Definition",
                "tasks": [
                    {
                        "subject": "Client Requirement Capture",
                        "type": "Requirements",
                        "start": 0,
                        "duration": 10,
                    },
                    {
                        "subject": "Material Selection",
                        "type": "Requirements",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Client Requirement Capture"],
                    },
                    {
                        "subject": "Design for Additive Review",
                        "type": "CAD Prep",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Material Selection"],
                    },
                ],
            },
            {
                "subject": "Preparation",
                "tasks": [
                    {
                        "subject": "File Repair & Orientation",
                        "type": "CAD Prep",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Material Selection"],
                    },
                    {
                        "subject": "Support Strategy",
                        "type": "CAD Prep",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["File Repair & Orientation"],
                    },
                    {
                        "subject": "Material Procurement",
                        "type": "Printing",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Support Strategy"],
                    },
                ],
            },
            {
                "subject": "Build & Iterate",
                "tasks": [
                    {
                        "subject": "First Article Print",
                        "type": "Printing",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Design for Additive Review"],
                    },
                    {
                        "subject": "Dimensional Inspection",
                        "type": "Inspection",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["First Article Print", "Material Procurement"],
                    },
                    {
                        "subject": "Iteration Print Run",
                        "type": "Printing",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Dimensional Inspection"],
                    },
                ],
            },
            {
                "subject": "Delivery",
                "tasks": [
                    {
                        "subject": "Finishing & Assembly",
                        "type": "Finishing",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Iteration Print Run"],
                    },
                    {
                        "subject": "Client Delivery",
                        "type": "Shipping",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Finishing & Assembly"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Production Print Run",
        "project_type": "Client Print Job",
        "phases": [
            {
                "subject": "Order Setup",
                "tasks": [
                    {"subject": "Order Review", "type": "Requirements", "start": 0, "duration": 7},
                    {
                        "subject": "Quote Confirmation",
                        "type": "Requirements",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Order Review"],
                    },
                ],
            },
            {
                "subject": "Preparation",
                "tasks": [
                    {
                        "subject": "Build Plate Nesting",
                        "type": "CAD Prep",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Quote Confirmation"],
                    },
                    {
                        "subject": "Machine Scheduling",
                        "type": "Printing",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Build Plate Nesting"],
                    },
                ],
            },
            {
                "subject": "Production",
                "tasks": [
                    {
                        "subject": "Batch Printing",
                        "type": "Printing",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Machine Scheduling"],
                    },
                    {
                        "subject": "Support Removal & Curing",
                        "type": "Post-Processing",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Batch Printing"],
                    },
                    {
                        "subject": "Surface Finishing",
                        "type": "Finishing",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Support Removal & Curing"],
                    },
                ],
            },
            {
                "subject": "Despatch",
                "tasks": [
                    {
                        "subject": "Final Inspection",
                        "type": "Inspection",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Surface Finishing"],
                    },
                    {
                        "subject": "Packing & Despatch",
                        "type": "Shipping",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Final Inspection"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "3D Printing Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
