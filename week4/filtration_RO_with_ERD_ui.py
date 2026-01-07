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
"""
GUI configuration for the custom RO w/ERD flowsheet.
"""

from pyomo.environ import units as pyunits, TransformationFactory

from idaes_flowsheet_processor.api import FlowsheetInterface

from filtration_RO_with_ERD import (
    build,
    scale_system,
    add_costing,
    initialize_system,
    solve_system,
)


def export_to_ui():
    """
    Exports the variables, flowsheet build, and solver results to the GUI.
    """
    return FlowsheetInterface(
        name="Filtration RO with ERD",
        do_export=export_variables,
        do_build=build_flowsheet,
        do_solve=solve_flowsheet,
    )


def export_variables(flowsheet=None, exports=None, build_options=None, **kwargs):
    """
    Exports the variables to the GUI.
    """
    fs = flowsheet
    # --- Input data ---
    # Feed operating conditions
    exports.add(
        obj=fs.feed.properties[0].flow_vol_phase["Liq"],
        name="Feed volumetric flow rate",
        ui_units=pyunits.m**3 / pyunits.s,
        display_units="m3/s",
        rounding=4,
        description="Inlet volumetric flow rate",
        is_input=True,
        input_category="Feed",
        is_output=True,
        output_category="Feed",
    )
    exports.add(
        obj=fs.feed.properties[0].conc_mass_phase_comp["Liq", "NaCl"],
        name="Feed NaCl concentration",
        ui_units=pyunits.kg / pyunits.m**3,
        display_units="kg/m3",
        rounding=2,
        description="Feed NaCl concentration",
        is_input=True,
        input_category="Feed",
        is_output=True,
        output_category="Feed",
    )
    exports.add(
        obj=fs.feed.properties[0].conc_mass_phase_comp["Liq", "TSS"],
        name="Feed TSS concentration",
        ui_units=pyunits.kg / pyunits.m**3,
        display_units="kg/m3",
        rounding=2,
        description="Feed TSS concentration",
        is_input=True,
        input_category="Feed",
        is_output=True,
        output_category="Feed",
    )
    exports.add(
        obj=fs.feed.properties[0].pressure,
        name="Feed pressure",
        ui_units=pyunits.Pa,
        display_units="Pa",
        rounding=2,
        description="Feed pressure",
        is_input=True,
        input_category="Feed",
        is_output=True,
        output_category="Feed",
    )
    exports.add(
        obj=fs.feed.properties[0].temperature,
        name="Feed temperature",
        ui_units=pyunits.K,
        display_units="K",
        rounding=2,
        description="Feed temperature",
        is_input=True,
        input_category="Feed",
        is_output=True,
        output_category="Feed",
    )

    # Filtration operating conditions
    exports.add(
        obj=fs.filtration.recovery_mass_phase_comp["Liq", "H2O"],
        name="Filtration water recovery",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=2,
        description="Filtration water recovery",
        is_input=True,
        input_category="Filtration",
        is_output=True,
        output_category="Filtration",
    )
    exports.add(
        obj=fs.filtration.removal_fraction_mass_phase_comp["Liq", "NaCl"],
        name="Filtration NaCl removal fraction",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=4,
        description="Filtration NaCl mass removal fraction",
        is_input=True,
        input_category="Filtration",
        is_output=True,
        output_category="Filtration",
    )
    exports.add(
        obj=fs.filtration.removal_fraction_mass_phase_comp["Liq", "TSS"],
        name="Filtration TSS removal fraction",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=4,
        description="Filtration TSS mass removal fraction",
        is_input=True,
        input_category="Filtration",
        is_output=True,
        output_category="Filtration",
    )

    # Pump operating conditions
    exports.add(
        obj=fs.pump.efficiency_pump[0],
        name="Pump efficiency",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=2,
        description="Pump efficiency",
        is_input=True,
        input_category="Pump",
        is_output=True,
        output_category="Pump",
    )
    exports.add(
        obj=fs.pump.control_volume.properties_out[0].pressure,
        name="Pump outlet pressure",
        ui_units=pyunits.Pa,
        display_units="Pa",
        rounding=2,
        description="Pump outlet pressure",
        is_input=True,
        input_category="Pump",
        is_output=True,
        output_category="Pump",
    )

    # Reverse osmosis operating conditions
    exports.add(
        obj=fs.RO.A_comp[0, "H2O"],
        name="RO water permeability coefficient",
        ui_units=pyunits.m / pyunits.Pa / pyunits.s,
        display_units="m/Pa/s",
        rounding=15,
        description="RO water permeability coefficient",
        is_input=True,
        input_category="Reverse Osmosis",
        is_output=True,
        output_category="Reverse Osmosis",
    )
    exports.add(
        obj=fs.RO.B_comp[0, "TDS"],
        name="RO salt permeability coefficient",
        ui_units=pyunits.m / pyunits.s,
        display_units="m/s",
        rounding=15,
        description="RO salt permeability coefficient",
        is_input=True,
        input_category="Reverse Osmosis",
        is_output=True,
        output_category="Reverse Osmosis",
    )
    exports.add(
        obj=fs.RO.recovery_vol_phase[0, "Liq"],
        name="RO volumetric recovery",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=2,
        description="RO volumetric recovery",
        is_input=True,
        input_category="Reverse Osmosis",
        is_output=True,
        output_category="Reverse Osmosis",
    )
    exports.add(
        obj=fs.RO.feed_side.channel_height,
        name="RO channel height",
        ui_units=pyunits.m,
        display_units="m",
        rounding=6,
        description="RO feed side channel height",
        is_input=True,
        input_category="Reverse Osmosis",
        is_output=True,
        output_category="Reverse Osmosis",
    )
    exports.add(
        obj=fs.RO.feed_side.spacer_porosity,
        name="RO spacer porosity",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=2,
        description="RO feed side spacer porosity",
        is_input=True,
        input_category="Reverse Osmosis",
        is_output=True,
        output_category="Reverse Osmosis",
    )
    exports.add(
        obj=fs.RO.permeate.pressure[0],
        name="RO permeate pressure",
        ui_units=pyunits.Pa,
        display_units="Pa",
        rounding=2,
        description="RO permeate pressure",
        is_input=True,
        input_category="Reverse Osmosis",
        is_output=True,
        output_category="Reverse Osmosis",
    )
    exports.add(
        obj=fs.RO.area,
        name="RO total membrane area",
        ui_units=pyunits.m**2,
        display_units="m2",
        rounding=2,
        description="RO total membrane area",
        is_input=True,
        input_category="Reverse Osmosis",
        is_output=True,
        output_category="Reverse Osmosis",
    )

    # Energy recovery device operating conditions
    exports.add(
        obj=fs.erd.efficiency_pump[0],
        name="ERD pump efficiency",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=2,
        description="Energy recovery device pump efficiency",
        is_input=True,
        input_category="Energy Recovery Device",
        is_output=True,
        output_category="Energy Recovery Device",
    )
    exports.add(
        obj=fs.erd.control_volume.properties_out[0].pressure,
        name="ERD outlet pressure",
        ui_units=pyunits.Pa,
        display_units="Pa",
        rounding=2,
        description="ERD outlet pressure",
        is_input=True,
        input_category="Energy Recovery Device",
        is_output=True,
        output_category="Energy Recovery Device",
    )

    # System costing
    exports.add(
        obj=fs.costing.utilization_factor,
        name="Utilization factor",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=2,
        description="Utilization factor - [annual use hours/total hours in year]",
        is_input=True,
        input_category="System costing",
        is_output=False,
    )
    exports.add(
        obj=fs.costing.TIC,
        name="Practical investment factor",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=1,
        description="Practical investment factor - [total investment cost/direct "
        "capital costs]",
        is_input=True,
        input_category="System costing",
        is_output=False,
    )
    exports.add(
        obj=fs.costing.plant_lifetime,
        name="Plant lifetime",
        ui_units=pyunits.year,
        display_units="years",
        rounding=1,
        description="Plant lifetime",
        is_input=True,
        input_category="System costing",
        is_output=False,
    )
    exports.add(
        obj=fs.costing.wacc,
        name="Discount rate",
        ui_units=pyunits.dimensionless,
        display_units="fraction",
        rounding=2,
        description="Discount rate used in calculating the capital annualization",
        is_input=True,
        input_category="System costing",
        is_output=False,
    )
    exports.add(
        obj=fs.costing.electricity_cost,
        name="Electricity cost",
        ui_units=fs.costing.base_currency / pyunits.kWh,
        display_units="$/kWh",
        rounding=3,
        description="Electricity cost",
        is_input=True,
        input_category="System costing",
        is_output=False,
    )

    # Cost metrics
    exports.add(
        obj=fs.costing.LCOW,
        name="Levelized cost of water",
        ui_units=fs.costing.base_currency / pyunits.m**3,
        display_units="$/m3",
        rounding=3,
        description="Levelized cost of water with respect to product water",
        is_input=False,
        is_output=True,
        output_category="Cost metrics",
    )
    exports.add(
        obj=fs.costing.total_operating_cost,
        name="Total operating cost",
        ui_units=fs.costing.base_currency / pyunits.yr,
        display_units="$/yr",
        rounding=3,
        description="Total operating cost",
        is_input=False,
        is_output=True,
        output_category="Cost metrics",
    )
    exports.add(
        obj=fs.costing.total_capital_cost,
        name="Total capital cost",
        ui_units=fs.costing.base_currency,
        display_units="$",
        rounding=3,
        description="Total capital cost",
        is_input=False,
        is_output=True,
        output_category="Cost metrics",
    )
    exports.add(
        obj=fs.costing.total_annualized_cost,
        name="Total annualized cost",
        ui_units=fs.costing.base_currency / pyunits.yr,
        display_units="$/yr",
        rounding=3,
        description="Total annualized cost",
        is_input=False,
        is_output=True,
        output_category="Cost metrics",
    )

    # Capital costs
    exports.add(
        obj=fs.filtration.costing.capital_cost,
        name="Filtration capital cost",
        ui_units=fs.costing.base_currency,
        display_units="$",
        rounding=3,
        description="Capital cost of filtration",
        is_input=False,
        is_output=True,
        output_category="Capital costs",
    )
    exports.add(
        obj=fs.pump.costing.capital_cost,
        name="Pump capital cost",
        ui_units=fs.costing.base_currency,
        display_units="$",
        rounding=3,
        description="Capital cost of pump",
        is_input=False,
        is_output=True,
        output_category="Capital costs",
    )
    exports.add(
        obj=fs.RO.costing.capital_cost,
        name="Reverse osmosis capital cost",
        ui_units=fs.costing.base_currency,
        display_units="$",
        rounding=3,
        description="Capital cost of reverse osmosis",
        is_input=False,
        is_output=True,
        output_category="Capital costs",
    )
    exports.add(
        obj=fs.erd.costing.capital_cost,
        name="ERD capital cost",
        ui_units=fs.costing.base_currency,
        display_units="$",
        rounding=3,
        description="Capital cost of energy recovery device",
        is_input=False,
        is_output=True,
        output_category="Capital costs",
    )

    # Outlets
    exports.add(
        obj=fs.product.properties[0].flow_vol_phase["Liq"],
        name="Product flow rate",
        ui_units=pyunits.m**3 / pyunits.s,
        display_units="m3/day",
        rounding=2,
        description="Product stream flow rate",
        is_input=False,
        is_output=True,
        output_category="Product",
    )
    exports.add(
        obj=fs.product.properties[0].flow_mass_phase_comp["Liq", "H2O"],
        name="Product water mass flow rate",
        ui_units=pyunits.kg / pyunits.s,
        display_units="kg/s",
        rounding=2,
        description="Product water mass flow rate",
        is_input=False,
        is_output=True,
        output_category="Product",
    )
    exports.add(
        obj=fs.product.properties[0].flow_mass_phase_comp["Liq", "TDS"],
        name="Product TDS mass flow rate",
        ui_units=pyunits.kg / pyunits.s,
        display_units="kg/s",
        rounding=2,
        description="Product TDS mass flow rate",
        is_input=False,
        is_output=True,
        output_category="Product",
    )

    # performance metrics
    recovery_vol = (
        fs.product.properties[0].flow_vol_phase["Liq"]
        / fs.feed.properties[0].flow_vol_phase["Liq"]
    )
    exports.add(
        obj=recovery_vol,
        name="Volumetric recovery",
        ui_units=pyunits.dimensionless,
        display_units="m3 of product/m3 of feed",
        rounding=5,
        description="Normalized volumetric recovery",
        is_input=False,
        is_output=True,
        output_category="Normalized performance metrics",
    )


def build_flowsheet(build_options=None, **kwargs):
    """
    Builds the initial flowsheet.
    """
    m = build()
    scale_system(m)
    add_costing(m)
    initialize_system(m)

    return m


def solve_flowsheet(flowsheet=None):
    """
    Solves the initial flowsheet.
    """
    fs = flowsheet
    results = solve_system(fs)
    return results
