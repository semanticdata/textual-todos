"""Shared type definitions for task-related widgets."""

from typing import Optional, TypedDict


class TaskData(TypedDict, total=False):
    """Type definition for task data dictionary."""

    id: int
    title: str
    description: str
    due_date: Optional[str]
    project_name: str
    completed: bool
    priority: str
    created_at: str
    modified_at: str
    project_id: int
