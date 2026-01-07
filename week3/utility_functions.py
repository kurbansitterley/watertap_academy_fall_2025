# Imports from Pyomo
from pyomo.environ import (
    ConcreteModel,
    Var,
    Param,
    Constraint,
    Objective,
    value,
    assert_optimal_termination,
    TransformationFactory,
    units as pyunits,
)
from pyomo.network import Arc

# Imports from IDAES
from idaes.core import FlowsheetBlock
from idaes.models.unit_models import Feed, Product
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.core.util.scaling import calculate_scaling_factors, set_scaling_factor
from idaes.core.util.initialization import propagate_state

# Imports from WaterTAP
from watertap.property_models.seawater_prop_pack import SeawaterParameterBlock
from watertap.unit_models.pressure_changer import Pump
from watertap.unit_models.pressure_changer import EnergyRecoveryDevice
from watertap.unit_models.reverse_osmosis_0D import (
    ReverseOsmosis0D,
    ConcentrationPolarizationType,
    MassTransferCoefficient,
    PressureChangeType,
)
from watertap.core.solvers import get_solver


import matplotlib.pyplot as plt
import numpy as np


def get_break_down_values(m):
    LCOW_breakdown_data = {
        # --- Capital Expenditure (CAPEX) Components (Annualized to LCOW) ---
        # 1. Direct CAPEX for Pump
        "Pump CAPEX": value(m.fs.costing.LCOW_aggregate_direct_capex["Pump"]),
        # 2. Direct CAPEX for RO Unit (e.g., pressure vessels, piping)
        "RO CAPEX": value(m.fs.costing.LCOW_aggregate_direct_capex["ReverseOsmosis0D"]),
        # 3. Direct CAPEX for Energy Recovery Device (ERD)
        "ERD CAPEX": value(
            m.fs.costing.LCOW_aggregate_direct_capex["EnergyRecoveryDevice"]
        ),
        # 4. Indirect CAPEX (Aggregates items like engineering, contingency, etc.)
        "Indirect CAPEX": value(
            sum(i for i in m.fs.costing.LCOW_aggregate_indirect_capex.values())
        ),
        # --- Operating Expenditure (OPEX) Components (normalized to LCOW) ---
        # 5. RO Fixed OPEX (Membrane replacement, maintenance)
        "RO OPEX": value(m.fs.costing.LCOW_aggregate_fixed_opex["ReverseOsmosis0D"]),
        # 6. Electricity OPEX (Variable OPEX, calculated from Specific Energy Consumption)
        "Electricity": value(m.fs.costing.LCOW_aggregate_variable_opex["electricity"]),
        # 7. Other Fixed OPEX (All remaining fixed OPEX components, excluding RO OPEX)
        "Other OPEX": value(
            sum(i for i in m.fs.costing.LCOW_aggregate_fixed_opex.values())
            - m.fs.costing.LCOW_aggregate_fixed_opex["ReverseOsmosis0D"]
        ),
    }
    return LCOW_breakdown_data


def table_view(simulation_results):
    """
    Prints LCOW breakdown results in a simple, readable table format

    Args:
        simulation_results (dict): A dictionary of LCOW cost component.
    """
    key_width = max(
        len("Cost Breakdown"), max(len(k) for k in simulation_results.keys())
    )
    value_width = 10
    total_width = key_width + value_width + 5
    separator = "-" * total_width
    total_lcow = 0

    print(separator)
    print(f"| {'Cost Breakdown':<{key_width}} | {'Value ($/m³)':>{value_width}} |")
    print(separator)

    for component, value in simulation_results.items():
        print(f"| {component:<{key_width}} | {value:>{value_width}.3f} |")
        total_lcow += value

    print(separator)
    print(f"| {'TOTAL LCOW':<{key_width}} | {total_lcow:>{value_width}.3f} |")
    print(separator)


def visualize_breakdown(breakdown_data_dict, title="LCOW Breakdown", barwidth=0.4):
    if not breakdown_data_dict:
        print("No data provided for visualization.")
        return

    categories = list(breakdown_data_dict.keys())

    # Get the list of all cost component labels (e.g., "Pump CAPEX")
    first_dict = next(iter(breakdown_data_dict.values()), None)
    if not first_dict:
        print("Breakdown dictionary is empty.")
        return

    labels = list(first_dict.keys())

    # Restructure data: plot_data will hold the values for stacking the bars.
    # Each inner list corresponds to one cost component (label) across all scenarios.
    plot_data = []
    for label in labels:
        # Collect the value for the current cost component (label) from every scenario dict
        plot_data.append([d.get(label, 0) for d in breakdown_data_dict.values()])

    # 2. Configure the plot
    x = np.arange(len(categories))
    fig, ax = plt.subplots(figsize=(8, 6))

    # 'bottom' tracks the current vertical position for stacking the bars
    bottom = np.zeros(len(categories))

    # 3. Draw the stacked bars
    for group, label in zip(plot_data, labels):
        # Draw bars for the current cost component (group) stacked on the 'bottom'
        bars = ax.bar(x, group, width=barwidth, bottom=bottom, label=label)

        # Add numerical labels to the center of each bar segment
        for bar, value in zip(bars, group):
            height = bar.get_height()
            # Only label non-zero values for cleaner visualization
            if value > 1e-4:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height / 2,
                    f"{value:.3f}",  # Format the value to 3 decimal places
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="black",
                )

        # Update the bottom position for the next stack layer
        bottom += group

    # 4. Final plot aesthetics
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_xlim(-0.5, len(categories) - 0.5)
    ax.set_ylabel("Levelized Cost of Water ($/m3)")
    ax.set_title(title)
    # Legend placed above the plot for clear viewing
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.05), ncol=4)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()
