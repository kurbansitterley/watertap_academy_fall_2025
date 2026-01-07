#################################################################################
# WaterTAP Copyright (c) 2020-2024, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National Laboratory,
# National Renewable Energy Laboratory, and National Energy Technology
# Laboratory (subject to receipt of any required approvals from the U.S. Dept.
# of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/watertap-org/watertap/"
#################################################################################

import pyomo.environ as pyo
from watertap.costing.util import (
    register_costing_parameter_block,
    make_capital_cost_var,
    make_fixed_operating_cost_var,
)


def build_filtration_cost_param_block(blk):
    """
    Create a costing parameter block for the custom filtration unit model.
    """

    blk.capital_cost_eq_base = pyo.Var(
        initialize=0.72557e6,
        units=pyo.units.USD_2014,
        doc="Capital cost coefficient A for custom filtration",
    )
    blk.capital_cost_eq_exponent = pyo.Var(
        initialize=0.5862,
        units=pyo.units.dimensionless,
        doc="Capital cost exponent b for custom filtration",
    )
    blk.fixed_op_cost_frac = pyo.Var(
        initialize=0.05,
        units=pyo.units.year**-1,
        doc="Fixed operating cost as a fraction of capital cost for custom filtration",
    )
    blk.electricity_intensity = pyo.Var(
        initialize=0.1,
        units=pyo.units.kWh / pyo.units.m**3,
        doc="Electricity intensity for custom filtration",
    )


@register_costing_parameter_block(
    build_rule=build_filtration_cost_param_block, parameter_block_name="filtration"
)
def cost_filtration(blk):
    """
    Costing method for Custom Filtration unit model.
    """

    # Capital cost
    make_capital_cost_var(blk)

    flow_vol_MGD = pyo.units.convert(
        blk.unit_model.properties_in[0].flow_vol_phase["Liq"]
        / (pyo.units.Mgallons / pyo.units.day),
        to_units=pyo.units.dimensionless,
    )
    filtration_params = blk.costing_package.filtration

    blk.costing_package.add_cost_factor(blk, "TPEC")
    blk.capital_cost_constraint = pyo.Constraint(
        expr=blk.capital_cost
        == blk.cost_factor
        * pyo.units.convert(
            filtration_params.capital_cost_eq_base
            * flow_vol_MGD**filtration_params.capital_cost_eq_exponent,
            to_units=blk.costing_package.base_currency,
        )
    )

    # Fixed operating cost
    make_fixed_operating_cost_var(blk)

    blk.fixed_operating_cost_constraint = pyo.Constraint(
        expr=blk.fixed_operating_cost
        == pyo.units.convert(
            filtration_params.fixed_op_cost_frac * blk.capital_cost,
            to_units=blk.costing_package.base_currency
            / blk.costing_package.base_period,
        )
    )

    blk.power_required = pyo.Expression(
        expr=pyo.units.convert(
            blk.unit_model.properties_in[0].flow_vol_phase["Liq"]
            * filtration_params.electricity_intensity,
            to_units=pyo.units.kW,
        )
    )

    blk.costing_package.cost_flow(blk.power_required, "electricity")
