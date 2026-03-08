"""Workflow navigation system for MLFX Streamlit UI."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

import streamlit as st


class WorkflowStep(Enum):
    """Workflow steps enumeration."""
    DATA_LOADING = 1
    DATA_PREPARATION = 2
    MODEL_TRAINING = 3
    VISUAL_ANALYSIS = 4
    EXPORT_REPORTS = 5


class StepStatus(Enum):
    """Step status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowNavigation:
    """Manages workflow navigation and state."""

    def __init__(self):
        self.steps = {
            WorkflowStep.DATA_LOADING: {
                "title": "Data Loading",
                "subtitle": "Tải và kiểm tra dữ liệu",
                "icon": "📥",
                "description": "Tải dữ liệu lịch sử từ Dukascopy và kiểm tra chất lượng"
            },
            WorkflowStep.DATA_PREPARATION: {
                "title": "Data Preparation",
                "subtitle": "Chuẩn bị dữ liệu",
                "icon": "⚙️",
                "description": "Resample, feature engineering và labeling"
            },
            WorkflowStep.MODEL_TRAINING: {
                "title": "Model Training",
                "subtitle": "Huấn luyện model",
                "icon": "🤖",
                "description": "Huấn luyện và đánh giá các models"
            },
            WorkflowStep.VISUAL_ANALYSIS: {
                "title": "Visual Analysis",
                "subtitle": "Phân tích trực quan",
                "icon": "📊",
                "description": "Phân tích chi tiết với Plotly visualizations"
            },
            WorkflowStep.EXPORT_REPORTS: {
                "title": "Export & Reports",
                "subtitle": "Xuất báo cáo",
                "icon": "📄",
                "description": "Xuất báo cáo và kết quả phân tích"
            }
        }

    def initialize_workflow_state(self) -> None:
        """Initialize workflow state in session."""
        if "workflow" not in st.session_state:
            st.session_state.workflow = {
                "current_step": WorkflowStep.DATA_LOADING.value,
                "completed_steps": [],
                "step_status": {
                    step.value: StepStatus.NOT_STARTED.value
                    for step in WorkflowStep
                },
                "step_data": {
                    step.value: {}
                    for step in WorkflowStep
                }
            }
            st.session_state.workflow["step_status"][WorkflowStep.DATA_LOADING.value] = StepStatus.IN_PROGRESS.value

    def get_current_step(self) -> WorkflowStep:
        """Get current workflow step."""
        return WorkflowStep(st.session_state.workflow["current_step"])

    def set_current_step(self, step: WorkflowStep) -> None:
        """Set current workflow step."""
        st.session_state.workflow["current_step"] = step.value
        if st.session_state.workflow["step_status"][step.value] == StepStatus.NOT_STARTED.value:
            st.session_state.workflow["step_status"][step.value] = StepStatus.IN_PROGRESS.value

    def mark_step_completed(self, step: WorkflowStep) -> None:
        """Mark a step as completed."""
        if step.value not in st.session_state.workflow["completed_steps"]:
            st.session_state.workflow["completed_steps"].append(step.value)
        st.session_state.workflow["step_status"][step.value] = StepStatus.COMPLETED.value
        next_step = self.get_next_step(step)
        if next_step and next_step.value not in st.session_state.workflow["completed_steps"]:
            self.set_current_step(next_step)

    def mark_step_error(self, step: WorkflowStep, error_msg: str) -> None:
        """Mark a step as having an error."""
        st.session_state.workflow["step_status"][step.value] = StepStatus.ERROR.value
        st.session_state.workflow["step_data"][step.value]["error"] = error_msg

    def invalidate_subsequent_steps(self, current_step: WorkflowStep) -> None:
        """Invalidate all steps after the current one, used when data changes."""
        for step in WorkflowStep:
            if step.value > current_step.value:
                if step.value in st.session_state.workflow["completed_steps"]:
                    st.session_state.workflow["completed_steps"].remove(step.value)
                st.session_state.workflow["step_status"][step.value] = StepStatus.NOT_STARTED.value
                st.session_state.workflow["step_data"][step.value] = {}

    def get_next_step(self, current_step: WorkflowStep) -> Optional[WorkflowStep]:
        """Get the next step in the workflow."""
        current_value = current_step.value
        if current_value < len(WorkflowStep):
            return WorkflowStep(current_value + 1)
        return None

    def get_previous_step(self, current_step: WorkflowStep) -> Optional[WorkflowStep]:
        """Get the previous step in the workflow."""
        current_value = current_step.value
        if current_value > 1:
            return WorkflowStep(current_value - 1)
        return None

    def can_navigate_to_step(self, step: WorkflowStep) -> bool:
        """Check if user can navigate to a specific step."""
        current = self.get_current_step()
        if step.value < current.value:
            return True
        if step == current:
            return True
        current_status = st.session_state.workflow["step_status"][current.value]
        return current_status == StepStatus.COMPLETED.value

    def get_step_progress(self) -> float:
        """Get overall workflow progress (0.0 to 1.0)."""
        total_steps = len(WorkflowStep)
        completed = len(st.session_state.workflow["completed_steps"])
        return completed / total_steps

    def render_navigation(self) -> None:
        """Render the horizontal navigation bar."""
        current = self.get_current_step()
        progress = self.get_step_progress()
        st.progress(progress)
        cols = st.columns(len(WorkflowStep))
        for i, step in enumerate(WorkflowStep):
            step_info = self.steps[step]
            status = StepStatus(st.session_state.workflow["step_status"][step.value])
            is_current = step == current
            with cols[i]:
                if is_current:
                    icon_display = "✅ " + step_info["icon"] if status == StepStatus.COMPLETED else step_info["icon"]
                    st.markdown(f"""
                    <div class="workflow-step current-step">
                        <div class="step-icon">{icon_display}</div>
                        <div class="step-title">{step_info["title"]}</div>
                        <div class="step-subtitle">{step_info["subtitle"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif status == StepStatus.COMPLETED:
                    st.markdown(f"""
                    <div class="workflow-step completed-step">
                        <div class="step-icon">✅ {step_info["icon"]}</div>
                        <div class="step-title">{step_info["title"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif status == StepStatus.ERROR:
                    st.markdown(f"""
                    <div class="workflow-step error-step">
                        <div class="step-icon">❌ {step_info["icon"]}</div>
                        <div class="step-title">{step_info["title"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="workflow-step disabled-step">
                        <div class="step-icon">⏸️ {step_info["icon"]}</div>
                        <div class="step-title">{step_info["title"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            prev_step = self.get_previous_step(current)
            if prev_step and self.can_navigate_to_step(prev_step):
                if st.button("← Previous", key="nav_prev", use_container_width=True):
                    self.set_current_step(prev_step)
                    st.rerun()
        with col_next:
            next_step = self.get_next_step(current)
            if next_step and self.can_navigate_to_step(next_step):
                if st.button("Next →", key="nav_next", use_container_width=True):
                    self.set_current_step(next_step)
                    st.rerun()

    def render_step_header(self) -> None:
        """Render the current step header."""
        current = self.get_current_step()
        step_info = self.steps[current]
        status = StepStatus(st.session_state.workflow["step_status"][current.value])
        st.markdown(f"""
        <div class="step-header">
            <h1>{step_info["icon"]} {step_info["title"]}</h1>
            <p class="step-subtitle">{step_info["subtitle"]}</p>
            <p class="step-description">{step_info["description"]}</p>
        </div>
        """, unsafe_allow_html=True)
        if status == StepStatus.ERROR:
            error_msg = st.session_state.workflow["step_data"][current.value].get("error", "Unknown error")
            st.error(f"❌ {error_msg}")

    def store_step_data(self, step: WorkflowStep, data: Dict[str, Any]) -> None:
        """Store data for a specific step."""
        st.session_state.workflow["step_data"][step.value].update(data)

    def get_step_data(self, step: WorkflowStep) -> Dict[str, Any]:
        """Get stored data for a specific step."""
        return st.session_state.workflow["step_data"].get(step.value, {})


navigation = WorkflowNavigation()
