from pydantic import BaseModel, Field
from typing import Any


class ScanRequest(BaseModel):
    target: str
    scripts: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


class ModuleExecutionResult(BaseModel):
    module_id: str
    module_name: str
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    ok: bool


class ScanResponse(BaseModel):
    scan_id: str
    module_id: str
    module_name: str
    created_at: str
    target: str
    scripts: list[str]
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    ok: bool
    json_artifact_url: str
    pdf_artifact_url: str


class SessionCreateRequest(BaseModel):
    target: str
    modules: list[str] = Field(default_factory=list)
    results: list[ModuleExecutionResult] = Field(default_factory=list)


class SessionResponse(BaseModel):
    scan_id: str
    module_id: str
    module_name: str
    created_at: str
    target: str
    scripts: list[str] = Field(default_factory=list)
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    ok: bool
    json_artifact_url: str
    pdf_artifact_url: str


class ModuleSchema(BaseModel):
    identifier: str
    name: str
    description: str
    category: str
    source: str


class ScanHistoryEntry(BaseModel):
    scan_id: str
    module_id: str
    module_name: str
    created_at: str
    target: str
    scripts: list[str]
    command: str
    exit_code: int
    duration_seconds: float
    ok: bool
    json_artifact_url: str
    pdf_artifact_url: str
