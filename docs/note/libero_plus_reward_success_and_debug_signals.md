# LIBERO-plus reward/success definition and debug signals

## Reward And Success

LIBERO-plus uses sparse task-completion reward.

In `libero/libero/envs/bddl_base_domain.py`, `reward()` returns:

- `0.0` by default
- `1.0` if `_check_success()` is true
- optionally scaled by `reward_scale`

There is no dense reward for partial progress in the standard eval path.

In the concrete task environments, `_check_success()` loads `parsed_problem["goal_state"]` from the BDDL file and evaluates every predicate. The goal is treated as a conjunction: all predicates must be true.

So the eval success is:

```text
success = all(goal_predicate_i(current_sim_state) for i in goal_state)
```

OpenTau then calls `self._env.check_success()` after every step and records `info["is_success"]`.

## Does A Non-Canonical Motion Count?

Yes, if the final BDDL predicates are satisfied.

The evaluator does not check whether the trajectory is human-like, short, safe, or demonstration-like. It checks only the simulator state predicates such as:

- object A is `In` region/container B
- object A is `On` region/object B
- drawer/cabinet/microwave is `Open` or `Close`
- stove-like object is `TurnOn` or `TurnOff`
- contact/containment relations

Therefore:

- If the robot knocks an object into the right container and all predicates are true, it can count as success.
- If the robot completes the semantic goal through an unusual but valid physical route, it counts as success.
- If the robot visually appears close but one predicate is false, it is failure.
- If the robot does many undesirable intermediate actions but ends in the required goal state, it still counts as success.

This is important: LIBERO-plus is a goal-state benchmark, not a trajectory-quality benchmark.

## Core Predicate Types

Defined in `libero/libero/envs/predicates/base_predicates.py`.

| Predicate | Meaning in code |
| --- | --- |
| `InContact` | `arg1.check_contact(arg2)` |
| `In` | container/region contact plus containment |
| `On` | target region/object `check_ontop(arg1)` |
| `Stack` | contact, containment, and vertical ordering |
| `Open` | articulated object joint passes its `is_open()` test |
| `Close` | articulated object joint passes its `is_close()` test |
| `TurnOn` | articulated affordance passes `turn_on()` test |
| `TurnOff` | articulated affordance passes `turn_off()` test |

For site/region targets, `check_contact()` may be always true because sites are not dynamic objects. Then the meaningful part is usually geometric containment / under / on-top tests.

## What You Can Inspect From A LIBERO/MuJoCo Episode

There are two levels: already exposed OpenTau observations and deeper simulator internals.

## Already Exposed In Current OpenTau Eval

Current wrapper: `OpenTau/src/opentau/envs/libero.py`.

Each observation contains:

| Key | Meaning |
| --- | --- |
| `pixels.camera0` | `agentview_image`, external camera RGB |
| `pixels.camera1` | `robot0_eye_in_hand_image`, wrist camera RGB |
| `agent_pos[:3]` | `robot0_eef_pos`, end-effector XYZ |
| `agent_pos[3:6]` | axis-angle from `robot0_eef_quat` |
| `agent_pos[6:]` | `robot0_gripper_qpos`, gripper joint position |

Action is 7D:

```text
[dx, dy, dz, d_rot1, d_rot2, d_rot3, gripper]
```

The OpenTau wrapper also has:

- `task_id`
- task language
- `reward`
- `done`
- `is_success`
- rendered video frames

## Directly Accessible MuJoCo / Robosuite State

From the raw environment, use:

```python
raw_env = env._env.env
sim = raw_env.sim
model = sim.model
data = sim.data
```

Useful fields:

| Signal | Access pattern | Use |
| --- | --- | --- |
| Global qpos | `data.qpos.copy()` | all generalized positions |
| Global qvel | `data.qvel.copy()` | all generalized velocities |
| Control | `data.ctrl.copy()` | low-level control inputs |
| Actuator force | `data.actuator_force.copy()` | actuator effort |
| Joint names | `model.joint_id2name(i)` | map qpos/qvel to joints |
| Body poses | `data.body_xpos`, `data.body_xquat` | object / robot body world poses |
| Site poses | `data.site_xpos`, `data.site_xmat` | region/site target positions |
| Geom poses | `data.geom_xpos`, `data.geom_xmat` | collision/visual geom poses |
| Contact count | `data.ncon` | number of active contacts |
| Contact pairs | `data.contact[i]` | collision diagnostics |
| Camera pose | `model.cam_pos`, `model.cam_quat` | static camera parameters |
| Light parameters | `model.light_pos`, `model.light_dir`, `model.light_diffuse`, `model.light_ambient` | light perturbation diagnosis |

Depending on robosuite version, additional robot observables may exist in raw observation:

- `robot0_joint_pos`
- `robot0_joint_vel`
- `robot0_eef_pos`
- `robot0_eef_quat`
- `robot0_gripper_qpos`
- `robot0_gripper_qvel`

Current OpenTau only forwards eef pose/orientation and gripper qpos into policy state. The rest can be logged by extending the wrapper.

## Object And Goal Debug Signals

LIBERO has object state wrappers:

| Object state call | Meaning |
| --- | --- |
| `object_state.get_geom_state()` | object/site position and orientation |
| `object_state.get_joint_state()` | articulated-object joint qpos |
| `object_state.check_contact(other)` | contact relation |
| `object_state.check_contain(other)` | geometric containment |
| `object_state.check_ontop(other)` | on-top relation |
| `object_state.is_open()` | open predicate |
| `object_state.is_close()` | close predicate |
| `object_state.turn_on()` | turn-on predicate |
| `object_state.turn_off()` | turn-off predicate |

Important dictionaries on the raw env:

```python
raw_env.object_states_dict
raw_env.objects_dict
raw_env.fixtures_dict
raw_env.object_sites_dict
raw_env.obj_body_id
raw_env.parsed_problem["goal_state"]
```

These are the best places to build a failure analyzer because they expose exactly what the success evaluator checks.

## Recommended Failure Categories To Log

For future policy comparisons, log these categories per failed episode.

| Failure type | What to check |
| --- | --- |
| No grasp / missed grasp | gripper-object distance, contact with target, gripper qpos never closes around object |
| Wrong object | target object unchanged, distractor object moved/contacted |
| Wrong placement | target picked but final `In`/`On` predicate false |
| Partial completion | some predicates true, at least one remaining false |
| Articulation failure | drawer/microwave/stove joint not open/closed/on enough |
| Collision-induced displacement | target or distractor knocked out of region |
| Timeout after near-success | final state close to goal but predicate threshold not crossed |
| Viewpoint grounding failure | action approaches wrong spatial location under camera perturbation |
| Initial-state recovery failure | early approach is off and policy cannot recover |
| Sensor-noise drift | action oscillation, slow wandering, or full-horizon timeout |
| Gripper saturation | gripper command mostly saturated while object not secured |
| Action saturation / instability | action norm large or repeated clipping |

## Minimal Debug Log To Add

For each episode, save a JSON record with:

```json
{
  "task_id": 0,
  "task_name": "...",
  "language": "...",
  "success": false,
  "reward": 0.0,
  "episode_len": 520,
  "goal_state": [["On", "object", "region"]],
  "predicate_values_final": {"On(object, region)": false},
  "predicate_values_over_time": "... optional ...",
  "eef_pos_final": [0, 0, 0],
  "gripper_qpos_final": [0, 0],
  "target_object_pose_final": {"pos": [0, 0, 0], "quat": [1, 0, 0, 0]},
  "contacts_final": [["robot0_gripper", "target_object"]],
  "action_stats": {
    "mean_norm": 0.0,
    "max_norm": 0.0,
    "gripper_open_fraction": 0.0,
    "gripper_close_fraction": 0.0
  }
}
```

Highest-value additions:

1. final predicate truth table
2. per-step predicate truth table
3. object poses and eef pose
4. contact pairs
5. action norm and gripper command statistics
6. episode length until success/failure

## Practical Interpretation

The benchmark answer is binary: did the final state satisfy the symbolic BDDL goal?

For failure diagnosis, do not rely on success rate alone. The most useful split is:

- perception failure: wrong object/location from images
- control failure: object identified but grasp/placement fails
- state-distribution failure: robot/object initial state outside recovery basin
- predicate-threshold failure: visually close but symbolic predicate false
- timeout failure: full horizon with no success

For LIBERO-plus, this maps well to the observed weak perturbations:

- `Camera Viewpoints`: likely perception/spatial-grounding failures
- `Robot Initial States`: likely recovery/control basin failures
- `Sensor Noise`: likely feedback/control drift and timeout failures
