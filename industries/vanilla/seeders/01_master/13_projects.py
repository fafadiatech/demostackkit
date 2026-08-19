"""Seeder: Project Types, Task Types and Project Templates for Vanilla."""

from __future__ import annotations

from demostackkit.seeder.project_seeders import ProjectTemplateSeeder as _ProjectTemplateSeederBase

PROJECT_TYPES = []  # ERPNext's own Internal / External / Other are enough for a clean-slate site

TASK_TYPES = [
    {"name": "Planning", "description": "Scoping, budgeting and scheduling", "weight": 1},
    {"name": "Analysis", "description": "Requirement gathering and assessment", "weight": 2},
    {"name": "Implementation", "description": "Build, configure and migrate", "weight": 3},
    {"name": "Testing", "description": "Verification and acceptance testing", "weight": 2},
    {"name": "Training", "description": "User enablement and handover", "weight": 1},
    {"name": "Documentation", "description": "Procedures, records and sign-off", "weight": 1},
    {"name": "Review", "description": "Checkpoints, audits and approvals", "weight": 1},
]

TEMPLATES = [
    {
        "name": "Standard Delivery Programme",
        "project_type": "External",
        "phases": [
            {
                "subject": "Discovery",
                "tasks": [
                    {
                        "subject": "Stakeholder Interviews",
                        "type": "Analysis",
                        "start": 0,
                        "duration": 10,
                    },
                    {
                        "subject": "Requirement Document",
                        "type": "Analysis",
                        "start": 10,
                        "duration": 25,
                        "depends_on": ["Stakeholder Interviews"],
                    },
                    {
                        "subject": "Scope Sign-off",
                        "type": "Review",
                        "start": 35,
                        "duration": 20,
                        "depends_on": ["Requirement Document"],
                    },
                ],
            },
            {
                "subject": "Design",
                "tasks": [
                    {
                        "subject": "Solution Design",
                        "type": "Planning",
                        "start": 35,
                        "duration": 15,
                        "depends_on": ["Requirement Document"],
                    },
                    {
                        "subject": "Effort Estimate",
                        "type": "Planning",
                        "start": 50,
                        "duration": 20,
                        "depends_on": ["Solution Design"],
                    },
                    {
                        "subject": "Resource Allocation",
                        "type": "Planning",
                        "start": 70,
                        "duration": 25,
                        "depends_on": ["Effort Estimate"],
                    },
                ],
            },
            {
                "subject": "Build & Test",
                "tasks": [
                    {
                        "subject": "Build Phase",
                        "type": "Implementation",
                        "start": 55,
                        "duration": 30,
                        "depends_on": ["Scope Sign-off"],
                    },
                    {
                        "subject": "System Testing",
                        "type": "Testing",
                        "start": 95,
                        "duration": 30,
                        "depends_on": ["Build Phase", "Resource Allocation"],
                    },
                    {
                        "subject": "User Acceptance Testing",
                        "type": "Testing",
                        "start": 125,
                        "duration": 25,
                        "depends_on": ["System Testing"],
                    },
                ],
            },
            {
                "subject": "Handover",
                "tasks": [
                    {
                        "subject": "User Training",
                        "type": "Training",
                        "start": 150,
                        "duration": 15,
                        "depends_on": ["User Acceptance Testing"],
                    },
                    {
                        "subject": "Project Handover",
                        "type": "Documentation",
                        "start": 165,
                        "duration": 10,
                        "depends_on": ["User Training"],
                    },
                ],
            },
        ],
    },
    {
        "name": "Internal Initiative",
        "project_type": "Internal",
        "phases": [
            {
                "subject": "Assessment",
                "tasks": [
                    {
                        "subject": "Current State Review",
                        "type": "Analysis",
                        "start": 0,
                        "duration": 7,
                    },
                    {
                        "subject": "Improvement Proposal",
                        "type": "Planning",
                        "start": 7,
                        "duration": 12,
                        "depends_on": ["Current State Review"],
                    },
                ],
            },
            {
                "subject": "Approval",
                "tasks": [
                    {
                        "subject": "Budget Approval",
                        "type": "Review",
                        "start": 19,
                        "duration": 18,
                        "depends_on": ["Improvement Proposal"],
                    },
                    {
                        "subject": "Implementation Plan",
                        "type": "Planning",
                        "start": 37,
                        "duration": 10,
                        "depends_on": ["Budget Approval"],
                    },
                ],
            },
            {
                "subject": "Execution",
                "tasks": [
                    {
                        "subject": "Rollout",
                        "type": "Implementation",
                        "start": 47,
                        "duration": 20,
                        "depends_on": ["Implementation Plan"],
                    },
                    {
                        "subject": "Process Update",
                        "type": "Documentation",
                        "start": 67,
                        "duration": 18,
                        "depends_on": ["Rollout"],
                    },
                    {
                        "subject": "Staff Briefing",
                        "type": "Training",
                        "start": 85,
                        "duration": 15,
                        "depends_on": ["Process Update"],
                    },
                ],
            },
            {
                "subject": "Closure",
                "tasks": [
                    {
                        "subject": "Post-implementation Review",
                        "type": "Review",
                        "start": 100,
                        "duration": 12,
                        "depends_on": ["Staff Briefing"],
                    },
                    {
                        "subject": "Closure Report",
                        "type": "Documentation",
                        "start": 112,
                        "duration": 8,
                        "depends_on": ["Post-implementation Review"],
                    },
                ],
            },
        ],
    },
]


class ProjectTemplateSeeder(_ProjectTemplateSeederBase):
    label = "Vanilla Project Templates"
    PROJECT_TYPES = PROJECT_TYPES
    TASK_TYPES = TASK_TYPES
    TEMPLATES = TEMPLATES
