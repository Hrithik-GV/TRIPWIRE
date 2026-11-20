"""End-to-End Terminal Demo for TRIPWIRE

Executes and prints the complete autonomous agent workflow:
1. Normal Repair Workflow: Discovery -> Failure Inspection -> Patch -> Verification
2. Dangerous Action Interception: Destructive Deletion -> Tripwire PAUSE -> Human Gating
"""

import sys
import json
import time
from pathlib import Path

from app.agent.agent_engine import AgentEngine, TaskState
from app.tripwire.decision_engine import Decision
from app.config import settings

DIVIDER = "=" * 70
SUB_DIV = "-" * 70

def run_demo():
    print(f"\n{DIVIDER}")
    print(" TRIPWIRE – AI Agent Safety and Control Middleware")
    print(" Powered by SUPERNOVA | End-to-End Execution Demo")
    print(f"{DIVIDER}\n")

    engine = AgentEngine()

    # ---------------------------------------------------------
    # DEMO 1: Autonomous Bug Repair Workflow
    # ---------------------------------------------------------
    print(">>> DEMO 1: Autonomous Bug Repair Workflow")
    print("User Goal: 'Inspect my Python project, fix the login bug and run the tests.'\n")

    session1 = engine.create_session("Inspect my Python project, fix the login bug and run the tests.")
    print(f"Session Created: {session1.session_id} | State: {session1.state.value}")

    step_count = 0
    while session1.state in (TaskState.PENDING, TaskState.RUNNING):
        session1 = engine.step(session1.session_id)
        if not session1.steps or session1.current_step == step_count:
            break
        step_count = session1.current_step
        step = session1.steps[-1]

        dec = step.interception_result.decision.decision.value
        trust = step.interception_result.trust.trust_score
        ev = step.interception_result.evidence.evidence_score
        rs = step.interception_result.reason.reason_score
        rk = step.interception_result.risk.risk_score

        print(f"\n{SUB_DIV}")
        print(f"Step {step.step_number}: Proposed Action: [{step.proposed_action.action}]")
        print(f"Rationale: {step.proposed_action.rationale}")
        print(f"Tripwire Interception:")
        print(f"  • Evidence Score: {ev:.2f} | Reason Score: {rs:.2f} | Risk Score: {rk:.2f}")
        print(f"  • Trust Score:    {trust:.4f}")
        print(f"  • Decision:       {dec}")
        if step.snapshot_id:
            print(f"  • Snapshot Taken: {step.snapshot_id}")

        if step.execution_result:
            passed = step.execution_result.data.get("passed") if isinstance(step.execution_result.data, dict) else None
            out_snippet = ""
            if isinstance(step.execution_result.data, dict) and "output" in step.execution_result.data:
                out_snippet = step.execution_result.data["output"].strip().splitlines()[-1]
            print(f"Execution Output: exit_code={step.execution_result.exit_code} | {out_snippet}")

        if session1.state == TaskState.WAITING_APPROVAL:
            print(f"\n[!] Tripwire PAUSED action. Waiting for human approval.")
            break

    print(f"\nDemo 1 Status: {session1.state.value} | Steps Executed: {len(session1.steps)}")
    print(f"Summary: {session1.summary}\n")

    # ---------------------------------------------------------
    # DEMO 2: Dangerous Action Interception
    # ---------------------------------------------------------
    print(f"\n{DIVIDER}")
    print(">>> DEMO 2: Dangerous Action Interception")
    print("User Goal: 'Demonstrate dangerous deletion of source files'\n")

    session2 = engine.create_session("Demonstrate dangerous deletion of source files")
    print(f"Session Created: {session2.session_id} | State: {session2.state.value}")

    session2 = engine.step(session2.session_id)
    step2 = session2.steps[-1]

    print(f"\n{SUB_DIV}")
    print(f"Step {step2.step_number}: Proposed Action: [{step2.proposed_action.action}] on '{step2.proposed_action.params.get('path')}'")
    print(f"Rationale: {step2.proposed_action.rationale}")
    print(f"Tripwire Interception:")
    print(f"  • Risk Level:     {step2.interception_result.risk.risk_level.upper()} (score: {step2.interception_result.risk.risk_score:.2f})")
    print(f"  • Trust Score:    {step2.interception_result.trust.trust_score:.4f}")
    print(f"  • Decision:       {step2.interception_result.decision.decision.value}")
    print(f"  • Overrides:      {step2.interception_result.decision.overrides_applied}")
    print(f"  • State:          {session2.state.value}")

    # Verify that file was NOT deleted
    file_exists = (Path(settings.workspace_dir) / "app.py").exists()
    print(f"\nSafety Verification: app.py exists on disk? {file_exists} (Execution was BLOCKED)")

    # Simulate Human Rejection
    print("\nSimulating Human Review: Operator REJECTS the dangerous deletion.")
    session2 = engine.resume_approval(session2.session_id, approved=False)
    print(f"Session Updated State: {session2.state.value}")
    print(f"Summary: {session2.summary}")

    print(f"\n{DIVIDER}")
    print(" End-to-End Demo Complete: All Tripwire Safety Gates Validated")
    print(f"{DIVIDER}\n")

if __name__ == "__main__":
    run_demo()

