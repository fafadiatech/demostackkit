"""Seeder: Project Types, Task Types and Project Templates for Garment."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "Seasonal Collection",
        "description": "Season-led design and production programme",
    },
    {
        "project_type": "Buyer Programme",
        "description": "Export buyer order development and ramp-up",
    },
    {
        "project_type": "Compliance Audit",
        "description": "Social and technical compliance certification",
    },
]

TASK_TYPES = [
    {"name": "Design", "description": "Sketching, tech packs and colour stories", "weight": 2},
    {"name": "Sampling", "description": "Proto, fit and salesman samples", "weight": 2},
    {"name": "Sourcing", "description": "Fabric, trim and accessory procurement", "weight": 2},
    {"name": "Cutting", "description": "Marker making, spreading and cutting", "weight": 2},
    {"name": "Stitching", "description": "Line loading and sewing", "weight": 3},
    {"name": "Finishing", "description": "Pressing, packing and labelling", "weight": 2},
    {"name": "Inspection", "description": "In-line and final quality audits", "weight": 2},
    {"name": "Shipping", "description": "Documentation and despatch", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Seasonal Collection Development",
        "project_type": "Seasonal Collection",
        "phases": [
            {
                "subject": "Design",
                "tasks": [
                    {"subject": "Trend Research", "type": "Design", "start": 0, "duration": 10},
                    {
                        "subject": "Line Sheet Freeze",
                        "type": "Design",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Trend Research"],
                    },
                    {
                        "subject": "Tech Pack Release",
                        "type": "Design",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Line Sheet Freeze"],
                    },
                ],
            },
            {
                "subject": "Sampling",
                "tasks": [
                    {
                        "subject": "Fabric Sourcing",
                        "type": "Sourcing",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Line Sheet Freeze"],
                    },
                    {
                        "subject": "Trim Sourcing",
                        "type": "Sourcing",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Fabric Sourcing"],
                    },
                    {
                        "subject": "Proto Sample",
                        "type": "Sampling",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Trim Sourcing"],
                    },
                ],
            },
            {
                "subject": "Production",
                "tasks": [
                    {
                        "subject": "Fit Sample Approval",
                        "type": "Sampling",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Tech Pack Release"],
                    },
                    {
                        "subject": "Bulk Cutting",
                        "type": "Cutting",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Fit Sample Approval", "Proto Sample"],
                    },
                    {
                        "subject": "Line Loading",
                        "type": "Stitching",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Bulk Cutting"],
                    },
                ],
            },
            {
                "subject": "Despatch",
                "tasks": [
                    {
                        "subject": "Final Inspection",
                        "type": "Inspection",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["Line Loading"],
                    },
                    {
                        "subject": "Despatch to Buyer",
                        "type": "Shipping",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Final Inspection"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Export Order Execution",
        "project_type": "Buyer Programme",
        "phases": [
            {
                "subject": "Order Setup",
                "tasks": [
                    {"subject": "Order Confirmation", "type": "Design", "start": 0, "duration": 7},
                    {
                        "subject": "Costing Sign-off",
                        "type": "Design",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Order Confirmation"],
                    },
                ],
            },
            {
                "subject": "Sampling",
                "tasks": [
                    {
                        "subject": "Fabric Booking",
                        "type": "Sourcing",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Costing Sign-off"],
                    },
                    {
                        "subject": "Pre-production Sample",
                        "type": "Sampling",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Fabric Booking"],
                    },
                ],
            },
            {
                "subject": "Bulk",
                "tasks": [
                    {
                        "subject": "Bulk Fabric Inspection",
                        "type": "Inspection",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Pre-production Sample"],
                    },
                    {
                        "subject": "Cutting & Bundling",
                        "type": "Cutting",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Bulk Fabric Inspection"],
                    },
                    {
                        "subject": "Sewing & Finishing",
                        "type": "Stitching",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Cutting & Bundling"],
                    },
                ],
            },
            {
                "subject": "Shipment",
                "tasks": [
                    {
                        "subject": "Buyer Final Audit",
                        "type": "Inspection",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Sewing & Finishing"],
                    },
                    {
                        "subject": "Shipment Documentation",
                        "type": "Shipping",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Buyer Final Audit"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Garment Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
