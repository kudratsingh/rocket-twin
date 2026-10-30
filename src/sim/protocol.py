"""WO-02 protocol identity; controller evaluation is frozen in WO-06.

Paired reference comparisons use identical explicit physical inputs, not tuning
against a desired altitude. Uncertainty corners are design sensitivities, not
probabilities or Monte-Carlo confidence claims. PID/RL protocol is not yet active.
Reference: project ADR-0001 and docs/work-orders/WO-02-six-dof-sim-validation.md.
"""

PROTOCOL = "wo02-source-hypotheses-v1"
CONTROLLER = "none; gimbal locked"
