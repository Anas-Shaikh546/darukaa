import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parents[1]))  # backend -> project root

from app.schemas.environment import EnvironmentInput, Soil, Climate, Land, Biodiversity
from app.services.reasoning import reason

# Construct sample environment input as per user reference
env = EnvironmentInput(
    soil=Soil(organic_carbon=0.3),
    climate=Climate(rainfall_category="low"),
    land=Land(land_use="wheat monoculture"),
    biodiversity=Biodiversity()
)

output = reason(env)

# Basic assertions
assert output.recommendation, "No recommendation returned"
required_vars = {"SOC", "Rainfall", "Land-use intensity"}
assert required_vars.issubset(set(output.reasoning.variables)), f"Missing required variables: {required_vars - set(output.reasoning.variables)}"

# Ensure at least one relationship path includes one of the required nodes
found = any(
    any(node in required_vars for node in path)
    for path in output.reasoning.relationships
)
assert found, "No relationship path contains required variable nodes"

print("Verification passed")
