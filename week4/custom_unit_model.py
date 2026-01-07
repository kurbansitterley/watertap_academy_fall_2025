# Import Pyomo libraries
from pyomo.environ import (
    Var,
    Suffix,
    check_optimal_termination,
    units as pyunits,
)
from pyomo.common.config import ConfigBlock, ConfigValue, In

# Import IDAES cores
from idaes.core import (
    declare_process_block_class,
    UnitModelBlockData,
    useDefault,
)
from idaes.core.util.config import is_physical_parameter_block
import idaes.core.util.scaling as iscale
import idaes.logger as idaeslog
from idaes.core.util.exceptions import InitializationError

# Import WaterTAP solver
from watertap.core.solvers import get_solver

# Import costing method
from custom_cost_model import cost_filtration


# When using this file the name "Filtration" is what is imported
@declare_process_block_class("Filtration")
class FiltrationData(UnitModelBlockData):
    """
    Custom filtration model
    """

    # CONFIG are options for the unit model, this simple model only has the mandatory config options
    CONFIG = ConfigBlock()

    CONFIG.declare(
        "dynamic",
        ConfigValue(
            domain=In([False]),
            default=False,
            description="Dynamic model flag - must be False",
            doc="""Indicates whether this model will be dynamic or not,
    **default** = False. The filtration unit does not support dynamic
    behavior, thus this must be False.""",
        ),
    )
    CONFIG.declare(
        "has_holdup",
        ConfigValue(
            default=False,
            domain=In([False]),
            description="Holdup construction flag - must be False",
            doc="""Indicates whether holdup terms should be constructed or not.
    **default** - False. The filtration unit does not have defined volume, thus
    this must be False.""",
        ),
    )
    CONFIG.declare(
        "property_package",
        ConfigValue(
            default=useDefault,
            domain=is_physical_parameter_block,
            description="Property package to use for control volume",
            doc="""Property parameter object used to define property calculations,
    **default** - useDefault.
    **Valid values:** {
    **useDefault** - use default package from parent model or flowsheet,
    **PhysicalParameterObject** - a PhysicalParameterBlock object.}""",
        ),
    )
    CONFIG.declare(
        "property_package_args",
        ConfigBlock(
            implicit=True,
            description="Arguments to use for constructing property packages",
            doc="""A ConfigBlock with arguments to be passed to a property block(s)
    and used when constructing these,
    **default** - None.
    **Valid values:** {
    see property package for documentation.}""",
        ),
    )

    def build(self):
        # build always starts by calling super().build()
        # This triggers a lot of boilerplate in the background for you
        super().build()

        # This creates blank scaling factors, which are populated later
        self.scaling_factor = Suffix(direction=Suffix.EXPORT)

        # Add unit variables
        self.recovery_mass_phase_comp = Var(
            self.config.property_package.phase_list,
            self.config.property_package.component_list,
            initialize=0.5,
            bounds=(1e-8, 1),
            units=pyunits.dimensionless,
        )
        self.removal_fraction_mass_phase_comp = Var(
            self.config.property_package.phase_list,
            self.config.property_package.component_list,
            initialize=0.5,
            bounds=(1e-8, 1),
            units=pyunits.dimensionless,
        )

        # Add state blocks for inlet, outlet, and waste
        # These include the state variables and any other properties on demand
        # Add inlet block
        tmp_dict = dict(**self.config.property_package_args)
        tmp_dict["has_phase_equilibrium"] = False
        tmp_dict["parameters"] = self.config.property_package
        tmp_dict["defined_state"] = True  # inlet block is an inlet
        self.properties_in = self.config.property_package.state_block_class(
            self.flowsheet().config.time, doc="Material properties of inlet", **tmp_dict
        )
        # Add outlet and waste block
        tmp_dict["defined_state"] = False  # outlet and waste block is not an inlet
        self.properties_out = self.config.property_package.state_block_class(
            self.flowsheet().config.time,
            doc="Material properties of outlet",
            **tmp_dict,
        )
        self.properties_waste = self.config.property_package.state_block_class(
            self.flowsheet().config.time, doc="Material properties of waste", **tmp_dict
        )

        # Add ports - oftentimes users interact with these rather than the state blocks
        self.add_inlet_port(name="inlet", block=self.properties_in)
        self.add_outlet_port(name="outlet", block=self.properties_out)
        self.add_outlet_port(name="waste", block=self.properties_waste)

        # Add constraints
        # Usually unit models use a control volume to do the mass, energy, and momentum
        # balances, however, they will be explicitly written out in this example
        @self.Constraint(
            self.config.property_package.component_list,
            doc="Mass balance for components",
        )
        def eq_mass_balance(b, j):
            return (
                b.properties_in[0].flow_mass_phase_comp["Liq", j]
                == b.properties_out[0].flow_mass_phase_comp["Liq", j]
                + b.properties_waste[0].flow_mass_phase_comp["Liq", j]
            )

        @self.Constraint(doc="Isothermal outlet assumption")
        def eq_isothermal_out(b):
            return b.properties_in[0].temperature == b.properties_out[0].temperature

        @self.Constraint(doc="Isothermal waste assumption")
        def eq_isothermal_waste(b):
            return b.properties_in[0].temperature == b.properties_waste[0].temperature

        @self.Constraint(doc="Isobaric outlet assumption")
        def eq_isobaric_out(b):
            return b.properties_in[0].pressure == b.properties_out[0].pressure

        @self.Constraint(doc="Isobaric waste assumption")
        def eq_isobaric_waste(b):
            return b.properties_in[0].pressure == b.properties_waste[0].pressure

        # Next, add constraints linking variables
        @self.Constraint(
            self.config.property_package.component_list,
            doc="Relationship between removal and recovery",
        )
        def eq_removal_recovery(b, j):
            return (
                b.removal_fraction_mass_phase_comp["Liq", j]
                == 1 - b.recovery_mass_phase_comp["Liq", j]
            )

        @self.Constraint(
            self.config.property_package.component_list,
            doc="Component removal equation",
        )
        def eq_removal_balance(b, j):
            return (
                b.properties_in[0].flow_mass_phase_comp["Liq", j]
                * b.removal_fraction_mass_phase_comp["Liq", j]
                == b.properties_waste[0].flow_mass_phase_comp["Liq", j]
            )

    def initialize_build(
        self,
        state_args=None,
        outlvl=idaeslog.NOTSET,
        solver=None,
        optarg=None,
    ):

        init_log = idaeslog.getInitLogger(self.name, outlvl, tag="unit")
        solve_log = idaeslog.getSolveLogger(self.name, outlvl, tag="unit")

        opt = get_solver(solver, optarg)

        # Initialize state blocks
        # Inlet state block first
        flags = self.properties_in.initialize(
            outlvl=outlvl,
            optarg=optarg,
            solver=solver,
            state_args=state_args,
            hold_state=True,
        )
        init_log.info("Initialization Step 1a Complete.")

        # Initialize outlet state block
        self.properties_out.initialize(
            outlvl=outlvl,
            optarg=optarg,
            solver=solver,
        )
        init_log.info("Initialization Step 1b Complete.")

        # Initialize waste state block
        self.properties_waste.initialize(
            outlvl=outlvl,
            optarg=optarg,
            solver=solver,
        )

        init_log.info("Initialization Step 1c Complete.")

        # Solve unit
        with idaeslog.solver_log(solve_log, idaeslog.DEBUG) as slc:
            res = opt.solve(self, tee=slc.tee)

        init_log.info("Initialization Step 2 {}.".format(idaeslog.condition(res)))

        # Release Inlet state
        self.properties_in.release_state(flags, outlvl=outlvl)
        init_log.info("Initialization Complete: {}".format(idaeslog.condition(res)))

        if not check_optimal_termination(res):
            raise InitializationError(f"Unit model {self.name} failed to initialize.")

    def calculate_scaling_factors(self):
        super().calculate_scaling_factors()

        iscale.set_scaling_factor(self.recovery_mass_phase_comp, 1)
        iscale.set_scaling_factor(self.removal_fraction_mass_phase_comp, 1)

        # Transforming constraints
        for j, c in self.eq_mass_balance.items():
            sf = iscale.get_scaling_factor(
                self.properties_in[0].flow_mass_phase_comp["Liq", j]
            )
            iscale.constraint_scaling_transform(c, sf)

        for ind, c in self.eq_isothermal_out.items():
            sf = iscale.get_scaling_factor(self.properties_in[0].temperature)
            iscale.constraint_scaling_transform(c, sf)

        for ind, c in self.eq_isothermal_waste.items():
            sf = iscale.get_scaling_factor(self.properties_in[0].temperature)
            iscale.constraint_scaling_transform(c, sf)

        for ind, c in self.eq_isobaric_out.items():
            sf = iscale.get_scaling_factor(self.properties_in[0].pressure)
            iscale.constraint_scaling_transform(c, sf)

        for ind, c in self.eq_isobaric_waste.items():
            sf = iscale.get_scaling_factor(self.properties_in[0].pressure)
            iscale.constraint_scaling_transform(c, sf)

        # Other constraints don't need to be transformed

    @property
    def default_costing_method(self):
        return cost_filtration
