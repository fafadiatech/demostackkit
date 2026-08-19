"""Seeder: Project Types, Task Types and Project Templates for Drones."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = [
    {
        "project_type": "New Product Development",
        "description": "Concept to production release of a new airframe",
    },
    {"project_type": "Certification", "description": "DGCA type certification and airworthiness"},
    {"project_type": "Fleet Deployment", "description": "Customer fleet rollout and field support"},
]

TASK_TYPES = [
    {
        "name": "Requirements",
        "description": "Mission profile and specification capture",
        "weight": 1,
    },
    {"name": "Design", "description": "Airframe, avionics and payload design", "weight": 3},
    {"name": "Prototyping", "description": "Build and bench test of prototypes", "weight": 3},
    {"name": "Firmware", "description": "Flight controller and calibration software", "weight": 2},
    {"name": "Flight Test", "description": "Airworthiness and endurance flying", "weight": 3},
    {"name": "Certification", "description": "Regulatory testing and documentation", "weight": 2},
    {"name": "Production", "description": "Pilot build and series release", "weight": 2},
    {"name": "Documentation", "description": "Manuals, logs and training material", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Drone NPD Programme",
        "project_type": "New Product Development",
        "phases": [
            {
                "subject": "Definition",
                "tasks": [
                    {
                        "subject": "Mission Profile Study",
                        "type": "Requirements",
                        "start": 0,
                        "duration": 10,
                    },
                    {
                        "subject": "Specification Freeze",
                        "type": "Requirements",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Mission Profile Study"],
                    },
                    {
                        "subject": "Airframe Design",
                        "type": "Design",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Specification Freeze"],
                    },
                ],
            },
            {
                "subject": "Design",
                "tasks": [
                    {
                        "subject": "Avionics Architecture",
                        "type": "Design",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Specification Freeze"],
                    },
                    {
                        "subject": "Payload Interface Design",
                        "type": "Design",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Avionics Architecture"],
                    },
                    {
                        "subject": "Component Sourcing",
                        "type": "Production",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Payload Interface Design"],
                    },
                ],
            },
            {
                "subject": "Prototype & Test",
                "tasks": [
                    {
                        "subject": "Prototype Build",
                        "type": "Prototyping",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Airframe Design"],
                    },
                    {
                        "subject": "Bench Integration Test",
                        "type": "Prototyping",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Prototype Build", "Component Sourcing"],
                    },
                    {
                        "subject": "Flight Test Campaign",
                        "type": "Flight Test",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["Bench Integration Test"],
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
                        "depends_on": ["Flight Test Campaign"],
                    },
                    {
                        "subject": "Pilot Production Batch",
                        "type": "Production",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["Design Freeze"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Type Certification Package",
        "project_type": "Certification",
        "phases": [
            {
                "subject": "Dossier",
                "tasks": [
                    {
                        "subject": "Compliance Matrix",
                        "type": "Certification",
                        "start": 0,
                        "duration": 7,
                    },
                    {
                        "subject": "Design Data Pack",
                        "type": "Certification",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Compliance Matrix"],
                    },
                ],
            },
            {
                "subject": "Ground Tests",
                "tasks": [
                    {
                        "subject": "EMI/EMC Testing",
                        "type": "Certification",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Design Data Pack"],
                    },
                    {
                        "subject": "Environmental Testing",
                        "type": "Certification",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["EMI/EMC Testing"],
                    },
                ],
            },
            {
                "subject": "Flight Tests",
                "tasks": [
                    {
                        "subject": "Endurance Flight Trials",
                        "type": "Flight Test",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Environmental Testing"],
                    },
                    {
                        "subject": "Failure Mode Trials",
                        "type": "Flight Test",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Endurance Flight Trials"],
                    },
                    {
                        "subject": "Flight Manual Preparation",
                        "type": "Documentation",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Failure Mode Trials"],
                    },
                ],
            },
            {
                "subject": "Submission",
                "tasks": [
                    {
                        "subject": "DGCA Submission",
                        "type": "Certification",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Flight Manual Preparation"],
                    },
                    {
                        "subject": "Certificate Issue",
                        "type": "Certification",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["DGCA Submission"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Drones Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
