"""Independent offline provenance/physics audit for composed-v1/comparison-v2.

Does not import the production runner, decoder, credentials, or any API client.
Numerical target calculations occur only here for post-hoc diagnostic scoring.
All reconstructed actions instead come exclusively from recorded model choices.
"""
import argparse
import ast
from collections import defaultdict
from decimal import Decimal, ROUND_FLOOR
import hashlib
import inspect
import json
from pathlib import Path
import re

import gymnasium as gym
from gymnasium.envs.box2d import bipedal_walker
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
STEP = Decimal(".005")
HALF = STEP / 2
MOTORS = ["leg0_hip", "leg0_knee", "leg1_hip", "leg1_knee"]
COEFFICIENTS = [Decimal(v) for v in (".495", "2.2", ".1375", ".495", ".825", "8.25")]
INTERVAL = re.compile(r"^([-+\d.eE]+) <= number < ([-+\d.eE]+)$")
PREDICATE = re.compile(r"^Is the numerical statement ([-+\d.eE]+) (<|>|==) ([-+\d.eE]+) true\?")
RAW_CHAIN = re.compile(r"^([-+\d.eE]+) (<|<=) x (<|<=) ([-+\d.eE]+)$")
RAW_SINGLE = re.compile(r"^x (<|<=|>|>=) ([-+\d.eE]+)$")


def D(value):
    return Decimal(str(value))


def jsonlines(path):
    # Only an incomplete final physical line may be skipped during a live audit.
    data = path.read_bytes()
    lines = data.splitlines(keepends=True)
    rows = []
    for i, line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if i == len(lines) - 1 and not line.endswith(b"\n"):
                break
            raise
    return rows


def arithmetic(expression):
    """Strict Decimal parser; accepts numerical literals, +/-/* and parentheses."""
    def walk(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return D(ast.get_source_segment(expression, node))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return -walk(node.operand) if isinstance(node.op, ast.USub) else walk(node.operand)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            return left * right
        raise ValueError(f"Unsupported arithmetic: {expression}")
    return walk(ast.parse(expression, mode="eval").body)


def telemetry(observation, env):
    rounded = [round(float(value), 6) for value in observation]
    body = dict(zip(("torso_angle", "torso_angular_velocity_scaled", "vx_scaled", "vy_scaled"), rounded[:4]))
    leg_keys = ("hip_angle", "hip_speed", "knee_angle_plus1", "knee_speed", "ground_contact")
    body["leg0"] = dict(zip(leg_keys, rounded[4:9]))
    body["leg1"] = dict(zip(leg_keys, rounded[9:14]))
    body["lidar_fractions_down_to_forward"] = rounded[14:]
    body["privileged_torso_x"] = round(float(env.unwrapped.hull.position.x), 4)
    body["privileged_torso_y"] = round(float(env.unwrapped.hull.position.y), 4)
    return body


def state_transition(phase, moving, predicates):
    # Independently express the chained transition, preserving LOWER's hip goal.
    next_phase, next_moving = phase, moving
    kind = "PUSH"
    if phase == 1:
        kind = "SWING"
        if predicates["behind"]:
            next_phase = 2
    if next_phase == 2:
        kind = "LOWER"
        if predicates["contact"]:
            next_phase = 3
            kind = "LOWER_PUSH"
    if next_phase == 3 and (predicates["knee_high"] or predicates["fast"]):
        kind += "_SWITCH"
        next_phase, next_moving = 1, 1 - moving
    return kind, next_phase, next_moving


def templates(kind, moving):
    other = 1 - moving
    goals = {name: None for name in MOTORS}
    if kind == "SWING":
        goals[f"leg{moving}_hip"] = 1.1
        goals[f"leg{moving}_knee"] = -.6
        goals[f"leg{other}_knee"] = 0.
    elif kind == "LOWER":
        goals[f"leg{moving}_hip"] = .1
        goals[f"leg{moving}_knee"] = .1
        goals[f"leg{other}_knee"] = 0.
    else:
        if kind.startswith("LOWER_PUSH"):
            goals[f"leg{moving}_hip"] = .1
        goals[f"leg{moving}_knee"] = 0.
        goals[f"leg{other}_knee"] = 1.
    return goals


def exact_terms(observation, goals):
    hg, kg, damp, bal, rot, vert = COEFFICIENTS
    values = {
        "body_balance": bal * D(observation["torso_angle"]),
        "body_rotation": rot * D(observation["torso_angular_velocity_scaled"]),
        "body_vertical": -vert * D(observation["vy_scaled"]),
    }
    components = {}
    for motor in MOTORS:
        leg, joint = motor.split("_")
        keys = []
        if goals[motor] is not None:
            angle = "hip_angle" if joint == "hip" else "knee_angle_plus1"
            values[motor + "_p"] = (hg if joint == "hip" else kg) * (D(goals[motor]) - D(observation[leg][angle]))
            values[motor + "_d"] = -damp * D(observation[leg][joint + "_speed"])
            keys += [motor + "_p", motor + "_d"]
        keys += ["body_balance", "body_rotation"] if joint == "hip" else ["body_vertical"]
        components[motor] = keys
    return values, components


def expected_descriptors(observation, goals):
    hg, kg, damp, bal, rot, vert = COEFFICIENTS
    descriptors = {"body_balance": (D(observation["torso_angle"]), bal, D(0)),
                   "body_rotation": (D(observation["torso_angular_velocity_scaled"]), rot, D(0)),
                   "body_vertical": (D(observation["vy_scaled"]), -vert, D(0))}
    for motor, goal in goals.items():
        if goal is None:
            continue
        leg, joint = motor.split("_")
        angle = "hip_angle" if joint == "hip" else "knee_angle_plus1"
        descriptors[motor + "_p"] = (D(observation[leg][angle]), -hg if joint == "hip" else -kg, D(goal))
        descriptors[motor + "_d"] = (D(observation[leg][joint + "_speed"]), -damp, D(0))
    return descriptors


def inverse_criterion(criterion, descriptor, check, detail):
    """Recover output-bin bounds from printed raw-input inequalities alone."""
    value, slope, origin = descriptor
    chain, single = RAW_CHAIN.fullmatch(criterion), RAW_SINGLE.fullmatch(criterion)
    check(bool(chain or single), "inverse_criterion_parse", detail)
    lower, upper, lower_inclusive, upper_inclusive = None, None, False, False
    if chain:
        lower, lower_inclusive = D(chain[1]), chain[2] == "<="
        upper, upper_inclusive = D(chain[4]), chain[3] == "<="
    elif single[1].startswith(">"):
        lower, lower_inclusive = D(single[2]), single[1] == ">="
    else:
        upper, upper_inclusive = D(single[2]), single[1] == "<="
    check(lower is None or upper is None or lower < upper, "inverse_input_order", detail)
    check((lower is None or lower_inclusive == (slope > 0)) and (upper is None or upper_inclusive == (slope < 0)), "inverse_edge_inclusion", detail)

    def index(printed, is_start):
        if printed is None:
            return 0 if is_start else 6401
        mapped_y = slope * (printed - origin)
        candidate = int(((mapped_y + HALF) / STEP + 3200).to_integral_value())
        check(0 <= candidate <= 6401, "inverse_output_range", detail)
        exact_boundary = STEP * (candidate - 3200) - HALF
        independently_rounded = (exact_boundary / slope + origin).quantize(D(".000000000001"))
        check(independently_rounded == printed, "inverse_threshold_equation", detail)
        return candidate

    start = index(lower if slope > 0 else upper, True)
    end = index(upper if slope > 0 else lower, False)
    check(start < end, "inverse_bin_order", detail)
    contains = ((lower is None or value > lower or lower_inclusive and value == lower)
                and (upper is None or value < upper or upper_inclusive and value == upper))
    return (STEP * (start - 3200) - HALF, STEP * (end - 3200) - HALF), contains


def stats(errors):
    a = np.asarray(errors, dtype=float)
    if not len(a):
        return {"count": 0}
    return {"count": len(a), "mean_signed_error": float(np.mean(a)), "mae": float(np.mean(abs(a))),
            "p95_absolute_error": float(np.quantile(abs(a), .95)), "max_absolute_error": float(np.max(abs(a))),
            "abs_error_gt_0025": int(np.sum(abs(a) > .025)), "abs_error_gt_005": int(np.sum(abs(a) > .05)),
            "abs_error_gt_02": int(np.sum(abs(a) > .2))}


def continuation_ancestry(directory, source_id, prior, check):
    """Resolve trajectory identity through archived, immediate-source links."""
    seen, chain = {directory.name}, []
    cursor_id, cursor = source_id, prior
    while True:
        check(cursor_id == Path(cursor_id).name and cursor_id not in (".", ".."),
              "continuation_ancestry", "Ancestor must name an archived sibling run")
        check(cursor_id not in seen, "continuation_ancestry", "Cyclic continuation metadata")
        seen.add(cursor_id)
        chain.append(cursor_id)
        check(cursor["id"] == cursor_id, "continuation_ancestry", "Ancestor summary identity")
        check(cursor["protocol"] == prior["protocol"] and cursor["seed"] == prior["seed"],
              "continuation_ancestry", "Ancestor protocol or seed changed")
        parent_id = cursor.get("continuation_of")
        if not parent_id:
            return cursor_id, chain
        check(parent_id == Path(parent_id).name and parent_id not in (".", ".."),
              "continuation_ancestry", "Parent must name an archived sibling run")
        cursor_id = parent_id
        cursor = json.loads((directory.parent / cursor_id / "summary.json").read_text())


def continuation_context(directory, summary, records, actions, check):
    origin_path = directory / "response-origin.jsonl"
    if not origin_path.exists():
        check(not summary or not summary.get("continuation_of"), "continuation_metadata", "Missing response provenance")
        return None, None
    source_id = summary.get("continuation_of") if summary else None
    if not source_id:
        check(directory.name.endswith("-resumed"), "continuation_metadata", "Cannot identify partial continuation source")
        source_id = directory.name.removesuffix("-resumed")
    check(source_id == Path(source_id).name and source_id not in (".", ".."), "continuation_metadata", "Source must name an archived sibling run")
    source = directory.parent / source_id
    prior = json.loads((source / "summary.json").read_text())
    trajectory_id, ancestry = continuation_ancestry(directory, source_id, prior, check)
    prefix_records = jsonlines(source / "api-records.jsonl")
    prefix_actions = jsonlines(source / "actions.jsonl")
    origins = jsonlines(origin_path)
    event_path = directory / "transport-events.jsonl"
    events = jsonlines(event_path) if event_path.exists() else []
    check(prior["id"] == source_id and prior["stop_reason"] == "api_or_runner_error", "continuation_source", source_id)
    check(not prior["terminated"] and not prior["truncated"], "continuation_source", "Cannot continue a terminated episode")
    check(prior["steps"] == sum(row["executed_frames"] for row in prefix_actions), "continuation_source", "Prefix frame count")
    check(len(origins) >= len(records), "continuation_provenance", "Missing per-response origin")
    failed_attempts = defaultdict(list)
    for event in events:
        index = event["request_index"]
        check(index >= len(prefix_records), "transport_retries", "Network retry within cached prefix")
        failed_attempts[index].append(event)
    for index, attempts in failed_attempts.items():
        check([item["attempt"] for item in attempts] == list(range(1, len(attempts) + 1)), "transport_retries", index)
        check(len(attempts) <= 6 and all(item["retryable"] for item in attempts[:-1]), "transport_retries", index)
    for index, record in enumerate(records):
        origin = origins[index]
        check(origin["request_index"] == index, "continuation_provenance", index)
        if index < len(prefix_records):
            old = prefix_records[index]
            check(origin["response_origin"] == "recorded_prefix" and origin["source_request_index"] == index, "cached_response_origin", index)
            check(record["kind"] == old["kind"] and record["request"] == old["request"], "cached_request_identity", index)
            check(record["response"] == old["response"], "cached_response_identity", index)
            check(origin["source_model_latency_s"] == old["latency_s"], "cached_source_latency", index)
        else:
            check(origin["response_origin"] == "live_api" and "source_request_index" not in origin, "fresh_response_origin", index)
            expected_attempts = index - len(prefix_records) + 1 + sum(len(v) for k, v in failed_attempts.items() if k <= index)
            check(origin["network_attempts_so_far"] == expected_attempts, "network_attempt_count", index)
    for index, (new, old) in enumerate(zip(actions, prefix_actions)):
        new_without_latency = {key: value for key, value in new.items() if key != "latency_s"}
        old_without_latency = {key: value for key, value in old.items() if key != "latency_s"}
        check(new_without_latency == old_without_latency, "cached_action_prefix_identity", index)
    finalized = bool(summary and summary.get("continuation_of"))
    if finalized:
        check(summary["prefix_physics_frames"] == prior["steps"] and summary["cached_prefix_requests"] == len(prefix_records), "continuation_summary", "Prefix sizes")
        check(summary["successful_logical_responses"] == len(records) == len(origins), "continuation_summary", "Logical response count")
        check(summary["new_network_attempts"] == max(0, len(records) - len(prefix_records)) + len(events), "continuation_summary", "Network attempts")
        check(summary["api_calls"] == prior["api_calls"] + summary["new_network_attempts"], "continuation_summary", "Combined network accounting")
        check(summary["source_session_wall_seconds"] == prior["wall_seconds"], "continuation_summary", "Source wall time")
        check(abs(summary["wall_seconds"] - summary["source_session_wall_seconds"] - summary["resume_session_wall_seconds"]) < 1e-8, "continuation_summary", "Combined wall time")
        check(summary["mean_action_latency_s"] is None and summary["p95_action_latency_s"] is None, "continuation_summary", "Cached/live mixed latency must be omitted")
        snapshot_id = summary.get("resume_snapshot_id", "resume-v1")
        check(snapshot_id == Path(snapshot_id).name and snapshot_id not in (".", ".."), "immutable_resume_snapshots", "Invalid snapshot ID")
        for name in ("run_resume.py", "resume_transport.py"):
            check((directory / name).read_bytes() == (ROOT / "snapshots" / snapshot_id / name).read_bytes(), "immutable_resume_snapshots", name)
    public = {"continuation_of": source_id, "independent_episode": False,
              "unique_trajectory_id": trajectory_id, "continuation_ancestry": ancestry,
              "resume_snapshot_id": summary.get("resume_snapshot_id", "resume-v1") if finalized else None,
              "source_prefix_physics_frames": prior["steps"], "source_prefix_successful_requests": len(prefix_records),
              "cached_requests_matched": min(len(records), len(prefix_records)),
              "cached_actions_matched": min(len(actions), len(prefix_actions)),
              "new_successful_logical_requests": max(0, len(records) - len(prefix_records)),
              "recorded_failed_network_attempts": len(events), "restored_physics_boundary_verified": False,
              "interpretation": "Linked continuation of an interrupted trajectory. Cached responses restore the recorded physical prefix; this is not an independent rollout."}
    return prior, public


def audit(directory):
    directory = directory.resolve()
    summary_path = directory / "summary.json"
    try:
        summary = json.loads(summary_path.read_text()) if summary_path.exists() else None
    except json.JSONDecodeError:
        summary = None  # The live writer may currently be finalizing this file.
    # Read action-prefix first, so the subsequent API snapshot includes its calls.
    actions = jsonlines(directory / "actions.jsonl")
    records = jsonlines(directory / "api-records.jsonl")
    protocol = actions[0]["trace"][0]["protocol"] if actions else (summary or {}).get("protocol")
    if not protocol:
        match = re.search(r"-seed\d+-(composed-v1|comparison-v2)(?:-resumed)*$", directory.name)
        protocol = match.group(1) if match else None
    finalized = bool(summary and summary.get("protocol") == protocol)
    seed = int(re.search(r"-seed(\d+)-", directory.name).group(1))
    checks = defaultdict(int)

    def check(condition, category, detail):
        checks[category] += 1
        if not condition:
            raise AssertionError(f"{directory.name}: {category}: {detail}")

    check(protocol in ("composed-v1", "comparison-v2"), "protocol", protocol)
    continuation_source, continuation = continuation_context(directory, summary, records, actions, check)

    # Inspect, but never execute, source snapshots.
    runner_path = directory / "runner-snapshot.py"
    config = None
    for node in ast.parse(runner_path.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "CONFIG" for target in node.targets):
            config = ast.literal_eval(node.value)["bipedalwalker"]
    check(config is not None, "source", "Missing literal BipedalWalker config")
    check(config["environment"] == "BipedalWalker-v3" and config["kwargs"] == {"hardcore": False}, "source", "Altered environment")
    check(config["limit"] == 1600 and config["fps"] == 50, "source", "Altered horizon or physics rate")
    groups = []
    for record in records:
        if record["kind"] == "gait_predicates":
            groups.append([record])
        else:
            expected_record_kind = "numeric_terms" if protocol == "composed-v1" else "comparison_terms"
            check(bool(groups) and record["kind"] == expected_record_kind, "api_grouping", record["kind"])
            groups[-1].append(record)
    check(len(groups) >= len(actions), "api_grouping", "Insufficient API groups for executed actions")
    env = gym.make("BipedalWalker-v3", hardcore=False, max_episode_steps=1600)
    observation, _ = env.reset(seed=seed)
    phase, moving, total, frames = 1, 0, 0., 0
    term_errors, motor_errors = defaultdict(list), []
    predicate_counts = defaultdict(lambda: {"count": 0, "incorrect": 0})
    first_wrong_depth = defaultdict(int)
    comparison_choices = {"count": 0, "incorrect": 0}
    worst_terms, wrong_predicates, phase_errors, material_motor_errors = [], [], [], []
    max_reward_error = 0.
    terminated = truncated = False
    try:
        for i, row in enumerate(actions):
            check(row["decision"] == i and row["step"] == frames, "sequence", i)
            check(row["executed_frames"] == 1, "hold", i)
            check(row["observation"] == telemetry(observation, env), "raw_observation_replay", i)
            check(not terminated and not truncated, "terminal", "Action after episode termination")
            header, *trace = row["trace"]
            check(header["protocol"] == protocol, "protocol", i)
            check(header["previous_model_memory"] == {"phase": phase, "moving_leg": moving}, "memory", i)
            group = groups[i]
            check(len(group) == 4 and len(trace) == 3, "api_grouping", {"decision": i, "records": len(group)})
            predicate_record = group[0]
            check(set(predicate_record["request"]["state"]) == {"task"}, "model_state_access", (i, "predicates"))
            questions = predicate_record["request"]["questions"]
            answers = predicate_record["response"]["answers"]
            support, mover = row["observation"][f"leg{1-moving}"], row["observation"][f"leg{moving}"]
            expected_comparisons = {"behind": (support["hip_angle"], "<", .1), "contact": (mover["ground_contact"], "==", 1),
                                    "knee_high": (support["knee_angle_plus1"], ">", .88), "fast": (row["observation"]["vx_scaled"], ">", .348)}
            check(set(questions) == set(answers) == set(expected_comparisons), "predicate_schema", i)
            predicates, truth = {}, {}
            for name, (value, operator, threshold) in expected_comparisons.items():
                match = PREDICATE.match(questions[name]["instructions"])
                check(bool(match), "predicate_question", (i, name))
                check((D(match[1]), match[2], D(match[3])) == (D(value), operator, D(threshold)), "predicate_question", (i, name))
                choice = answers[name]["choice"]
                check(choice in ("yes", "no"), "predicate_answer", (i, name))
                predicates[name] = choice == "yes"
                truth[name] = value < threshold if operator == "<" else value > threshold if operator == ">" else value == threshold
                predicate_counts[name]["count"] += 1
                predicate_counts[name]["incorrect"] += predicates[name] != truth[name]
                if predicates[name] != truth[name]:
                    wrong_predicates.append({"decision": i, "name": name, "value": value, "comparison": operator, "threshold": threshold, "choice": choice})
            check(predicates == header["model_predicates"], "predicate_trace", i)
            kind, next_phase, next_moving = state_transition(phase, moving, predicates)
            check(kind == header["model_chosen_gait_case"], "gait_composition", i)
            check(header["next_model_memory"] == {"phase": next_phase, "moving_leg": next_moving}, "gait_composition", i)
            oracle_kind, oracle_phase, oracle_moving = state_transition(phase, moving, truth)
            if (kind, next_phase, next_moving) != (oracle_kind, oracle_phase, oracle_moving):
                phase_errors.append({"decision": i, "model_case": kind, "oracle_case_from_same_previous_memory": oracle_kind})
            goals = templates(kind, moving)
            check(goals == header["disclosed_angle_goal_template"], "goal_template", i)
            exact, components = exact_terms(row["observation"], goals)
            check(components == header["components"], "component_template", i)
            if protocol == "composed-v1":
                expressions = header["expressions"]
                check(set(exact) == set(expressions), "expression_template", i)
                for name, expression in expressions.items():
                    check(arithmetic(expression) == exact[name], "expression_template", (i, name))
                descriptors = {}
            else:
                descriptors = expected_descriptors(row["observation"], goals)
                check(set(header["affine_descriptors"]) == set(descriptors), "descriptor_template", i)
                for name, descriptor in descriptors.items():
                    logged = header["affine_descriptors"][name]
                    check(tuple(D(logged[key]) for key in ("value", "slope", "origin")) == descriptor, "descriptor_template", (i, name))
                expressions = {name: f"{slope}*({value}-({origin}))" for name, (value, slope, origin) in descriptors.items()}
            selected = {name: (D("-16.0025"), D("16.0025")) for name in exact}
            wrong_at = {}
            for depth, record in enumerate(group[1:]):
                qs, response = record["request"]["questions"], record["response"]["answers"]
                active = {name for name, (lo, hi) in selected.items() if hi - lo > STEP}
                check(set(qs) == set(response) == active, "term_schema", (i, depth))
                check(set(record["request"]["state"]) == {"task"}, "model_state_access", (i, depth))
                for name, question in qs.items():
                    if protocol == "composed-v1":
                        prefix = "Calculate this single signed arithmetic term: "
                        check(question["instructions"].startswith(prefix), "term_question", (i, depth, name))
                        expression = question["instructions"][len(prefix):].split(". Select the interval", 1)[0]
                        check(expression == expressions[name], "term_question", (i, depth, name))
                    else:
                        match = re.match(r"^The observed number x = ([-+\d.eE]+)\. Which numerical interval contains x\?", question["instructions"])
                        check(bool(match) and D(match[1]) == descriptors[name][0], "comparison_question", (i, depth, name))
                    intervals = {}
                    comparison_truth = {}
                    for key, criterion in question["criteria"].items():
                        if protocol == "composed-v1":
                            match = INTERVAL.fullmatch(criterion)
                            check(bool(match), "criterion_parse", (i, depth, name, key))
                            intervals[key] = (D(match[1]), D(match[2]))
                        else:
                            intervals[key], comparison_truth[key] = inverse_criterion(criterion, descriptors[name], check, (i, depth, name, key))
                    cells = sorted(intervals.values())
                    check(cells[0][0] == selected[name][0] and cells[-1][1] == selected[name][1], "criterion_partition", (i, depth, name))
                    check(all(a < b for a, b in cells) and all(a[1] == b[0] for a, b in zip(cells, cells[1:])), "criterion_partition", (i, depth, name))
                    check(len(cells) == min(20, int((selected[name][1] - selected[name][0]) / STEP)), "criterion_partition", (i, depth, name))
                    choice = response[name]["choice"]
                    check(choice in intervals, "model_choice", (i, depth, name))
                    if protocol == "comparison-v2":
                        comparison_choices["count"] += 1
                        comparison_choices["incorrect"] += not comparison_truth[choice]
                    chosen = intervals[choice]
                    check(choice == trace[depth]["choices"][name], "choice_trace", (i, depth, name))
                    boundary_indices = [(bound + HALF) / STEP + 3200 for bound in chosen]
                    check(all(index == int(index) for index in boundary_indices), "criterion_grid", (i, depth, name))
                    check([int(index) for index in boundary_indices] == trace[depth]["windows"][name], "window_trace", (i, depth, name))
                    selected[name] = chosen
                    exact_clipped = max(D(-16), min(D(16), exact[name]))
                    if name not in wrong_at and not chosen[0] <= exact_clipped < chosen[1]:
                        wrong_at[name] = depth
                        first_wrong_depth[str(depth)] += 1
            units = {}
            for name, (lo, hi) in selected.items():
                check(hi - lo == STEP, "final_term_width", (i, name))
                midpoint = (lo + hi) / 2
                unit_value = midpoint / STEP
                check(unit_value == int(unit_value), "final_term_grid", (i, name))
                units[name] = int(unit_value)
                error = float(midpoint - exact[name])
                category = re.sub(r"^leg[01]_", "", name)
                term_errors[category].append(error)
                worst_terms.append({"decision": i, "term": name, "expression": expressions[name], "model_value": float(midpoint),
                                    "exact_value": float(exact[name]), "signed_error": error, "first_wrong_depth": wrong_at.get(name)})
            check(units == header["model_term_units"] and D(header["unit_step"]) == STEP, "term_units", i)
            check(row["action_names"] == MOTORS and list(header["components"]) == MOTORS, "motor_order", i)
            reconstructed = [float(STEP * max(-200, min(199, sum(units[name] for name in components[motor])))) for motor in MOTORS]
            check(reconstructed == row["action"], "executed_motor_composition", i)
            oracle_units = {name: max(-3200, min(3200, int((value / STEP + D(".5")).to_integral_value(rounding=ROUND_FLOOR)))) for name, value in exact.items()}
            oracle_motors = [float(STEP * max(-200, min(199, sum(oracle_units[name] for name in components[motor])))) for motor in MOTORS]
            motor_errors.extend(a - b for a, b in zip(reconstructed, oracle_motors))
            for motor, selected_motor, oracle_motor in zip(MOTORS, reconstructed, oracle_motors):
                if abs(selected_motor - oracle_motor) > .05:
                    material_motor_errors.append({"decision": i, "motor": motor, "model_value": selected_motor,
                                                  "quantized_oracle_same_model_gait": oracle_motor, "signed_error": selected_motor - oracle_motor})
            phase, moving = next_phase, next_moving
            observation, reward, terminated, truncated, _ = env.step(np.asarray(reconstructed, dtype=np.float32))
            frames += 1
            total += float(reward)
            error = max(abs(float(reward) - row["reward_increment"]), abs(total - row["reward_total"]))
            max_reward_error = max(max_reward_error, error)
            check(error < 1e-9, "reward_replay", (i, error))
            check(bool(terminated) == row["terminated"] and bool(truncated) == row["truncated"], "terminal_replay", i)
            if continuation and frames == continuation["source_prefix_physics_frames"]:
                check(telemetry(observation, env) == continuation_source["final_observation"], "continuation_physics_boundary", "Observation and torso position")
                check(abs(total - continuation_source["reward"]) < 1e-9, "continuation_physics_boundary", "Cumulative reward")
                check(not terminated and not truncated, "continuation_physics_boundary", "Prefix must still be active")
                continuation["restored_physics_boundary_verified"] = True
                continuation["boundary_reward"] = total
                continuation["boundary_x"] = float(env.unwrapped.hull.position.x)
        final_observation = telemetry(observation, env)
        finish = (bipedal_walker.TERRAIN_LENGTH - bipedal_walker.TERRAIN_GRASS) * bipedal_walker.TERRAIN_STEP
        check(abs(finish - 88.66666666666667) < 1e-12, "terrain_finish", finish)
        success = bool(terminated and not env.unwrapped.game_over and env.unwrapped.hull.position.x > finish)
        if finalized:
            check(summary["seed"] == seed and summary["steps"] == frames and summary["decision_count"] == len(actions), "summary", "Counts")
            check(abs(summary["reward"] - total) < 1e-9, "summary", "Reward")
            check(summary["final_observation"] == final_observation, "summary", "Final observation")
            check(summary["success"] == success and summary["terminated"] == bool(terminated) and summary["truncated"] == bool(truncated), "summary", "Terminal result")
            if terminated or truncated:
                reason = "terrain_finished" if success else "fall" if env.unwrapped.game_over else "left_boundary" if terminated else "environment_time_limit"
                check(summary["stop_reason"] == reason, "summary", "Stop reason")
            check(summary["gymnasium_version"] == gym.__version__ and summary["environment"] == "BipedalWalker-v3", "summary", "Environment")
            check(summary["action_hold_frames"] == 1 and summary["executed_action_overrides"] == 0, "summary", "Control method")
            check([D(v) for v in summary["coefficients"]] == COEFFICIENTS, "summary", "Coefficients")
            snapshot_names = ["prompt-runner-snapshot.py", "compositional-snapshot.py"] + (["comparison-snapshot.py"] if protocol == "comparison-v2" else [])
            for name in snapshot_names:
                immutable = ROOT / "snapshots" / protocol / name
                check((directory / name).read_bytes() == immutable.read_bytes(), "immutable_snapshots", name)
            if continuation:
                check(continuation["restored_physics_boundary_verified"], "continuation_physics_boundary", "Full cached prefix was not restored")
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob("*-snapshot.py")}
        for name in ("run_resume.py", "resume_transport.py"):
            if (directory / name).exists():
                hashes[name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        hashes["installed_bipedal_walker.py"] = hashlib.sha256(Path(inspect.getfile(bipedal_walker)).read_bytes()).hexdigest()
        all_errors = [error for values in term_errors.values() for error in values]
        return {"run": str(directory), "protocol": protocol, "audit": "PASS", "run_finalized": finalized,
                "independent_episode": continuation is None,
                "unique_trajectory_id": continuation["unique_trajectory_id"] if continuation else directory.name,
                "linked_continuation": continuation,
                "status": "complete_run_audit" if finalized else "partial_live_prefix_audit",
                "audit_scope": "Independent recorded-criterion midpoint reconstruction, integer motor composition, model-predicate phase logic, and unchanged Gymnasium physical replay. Exact term arithmetic is post-hoc diagnostic only.",
                "seed": seed, "frames_replayed": frames, "actions_reconstructed": len(actions), "api_records_read": len(records),
                "api_records_for_executed_actions": len(actions) * 4, "unexecuted_api_records": len(records) - len(actions) * 4,
                "checks": dict(checks), "reward": total, "max_reward_error": max_reward_error,
                "terminated": bool(terminated), "truncated": bool(truncated), "torso_fall": bool(env.unwrapped.game_over),
                "x": float(env.unwrapped.hull.position.x), "finish_x": finish, "success": success,
                "term_error_overall": stats(all_errors), "term_error_by_type": {name: stats(values) for name, values in term_errors.items()},
                "motor_error_against_quantized_oracle_same_model_gait": stats(motor_errors),
                "first_wrong_numeric_refinement_depth": dict(first_wrong_depth), "predicate_accuracy": dict(predicate_counts),
                "comparison_choice_accuracy": comparison_choices if protocol == "comparison-v2" else None,
                "predicate_error_examples": wrong_predicates[:20], "gait_case_errors_from_predicates": phase_errors,
                "earliest_term_errors_over_0025": [item for item in worst_terms if abs(item["signed_error"]) > .025][:20],
                "earliest_motor_errors_over_005": material_motor_errors[:20],
                "worst_term_errors": sorted(worst_terms, key=lambda item: abs(item["signed_error"]), reverse=True)[:20],
                "snapshot_sha256": hashes, "gymnasium_version": gym.__version__}
    finally:
        env.close()


def discover_runs():
    directories = []
    for directory in (ROOT / "runs").iterdir():
        if not directory.is_dir():
            continue
        try:
            summary = json.loads((directory / "summary.json").read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            summary = {}
        # Metadata admits arbitrarily named continuations; the name fallback also
        # discovers live runs before their final summary has been written.
        if (summary.get("protocol") in ("composed-v1", "comparison-v2")
                or re.fullmatch(r"bipedalwalker-seed\d+-(?:composed-v1|comparison-v2)(?:-resumed)*", directory.name)):
            directories.append(directory)
    return sorted(directories)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="*", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    directories = args.runs or discover_runs()
    reports = [audit(directory) for directory in directories]
    result = {"provenance": "OFFLINE INDEPENDENT AUDIT OF LIVE NUMERICJEV RECORDS; NO API CALLS", "reports": reports}
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
