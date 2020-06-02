import numpy as np
import openmdao.api as om

from openaerostruct.geometry.utils import generate_mesh, scale_x
from openaerostruct.geometry.geometry_group import Geometry
from openaerostruct.aerodynamics.aero_groups import AeroPoint

from aerodynamics_geom_group import AerodynamicsGeomGroup

prob = om.Problem()

indep_var_comp = om.IndepVarComp()
indep_var_comp.add_output('v', val=50, units='m/s')
indep_var_comp.add_output('Mach_number', val=0.3)
indep_var_comp.add_output('re', val=1.e6, units='1/m')
indep_var_comp.add_output('rho', val=1.225, units='kg/m**3')
indep_var_comp.add_output('cg', val=np.zeros((3)), units='m')
indep_var_comp.add_output('alpha', val = 2.)

prob.model.add_subsystem('ivc', indep_var_comp, promotes=['*'])
shape = (1,)
prob.model.add_subsystem('AerodynamicsGeomGroup', AerodynamicsGeomGroup(shape=shape), promotes=['*'])

mesh_dict = {'num_y' : 17,
             'num_x' : 9,
             'wing_type' : 'rect',
             'symmetry' : True,
             'chord': 0.1,
             'span' : 1.,
            }

mesh = generate_mesh(mesh_dict)
print(mesh.shape)

surface = { 'name' : 'wing', 
            'symmetry' : True,
            'S_ref_type' : 'wetted',
            'twist_cp' : np.zeros(3),
            'mesh' : mesh,
            'CL0' : 0.0,
            'CD0' : 0.001,
            'k_lam' : 0.05,
            't_over_c_cp' : np.array([0.1875]),
            'c_max_t' : 0.1,
            'with_viscous' : True,
            'with_wave' : False,
            'sweep' : 0.,
            'alpha' : 0.,
            }

geom_group = Geometry(surface=surface)

prob.model.add_subsystem(surface['name'], geom_group)

aero_group = AeroPoint(surfaces=[surface])
point_name = 'laura'
prob.model.add_subsystem(point_name, aero_group)

# Connect flow properties to the analysis point
prob.model.connect('v', point_name + '.v')
prob.model.connect('alpha', point_name + '.alpha')
prob.model.connect('Mach_number', point_name + '.Mach_number')
prob.model.connect('re', point_name + '.re')
prob.model.connect('rho', point_name + '.rho')
prob.model.connect('cg', point_name + '.cg')

name = 'wing'

# Connect the mesh from the geometry component to the analysis point
prob.model.connect('wing.mesh', 'laura.wing.def_mesh')

# Perform the connections with the modified names within the
# 'aero_states' group.
prob.model.connect('wing.mesh', 'laura.aero_states.wing_def_mesh')
prob.model.connect('wing.t_over_c', 'laura.wing_perf.t_over_c')

prob.model.connect('wing_span', 'wing.mesh.stretch.span')
prob.model.connect('oas_wing_chord', 'wing.mesh.scale_x.chord')


## - - - - - - - - - - - (maybe write another script for optimization and visualization)

# prob.driver = om.ScipyOptimizeDriver()

# recorder = om.SqliteRecorder("aero_wb.db")
# prob.driver.add_recorder(recorder)
# prob.driver.recording_options['record_derivatives'] = True
# prob.driver.recording_options['includes'] = ['*']

# # # Setup problem and add design variables, constraint, and objective
# prob.model.add_design_var('wing.twist_cp', lower=-20., upper=20.)
# prob.model.add_design_var('wing.sweep', lower=0., upper=50.)
# prob.model.add_design_var('wing.alpha', lower=0., upper=10.)
# prob.model.add_constraint('laura
#.wing_perf.CL', equals=0.5)
# ## add onstraints and designvaraibles 
# prob.model.add_objective('laura
#.wing_perf.CD', scaler=1e4)

# Set up the problem
prob.setup()
prob.run_model()
prob.model.list_inputs(prom_name=True)

# print("\nWing CL:", prob['laura
#.wing_perf.CL'])
# print("Wing CD:", prob['laura
#.wing_perf.CD'])
# print("Wing Sweep:", prob['wing.sweep'])
# # print("Wing Alpha:", prob['laura
#.alpha'])
# print("Wing Twist Cp:", prob['wing.twist_cp'])
# print("CoG:", prob['laura
#.cg'])

# plot_wing aero_wb.db to plot wing over iterations
# plot_wingbox aero_wb.db of CS of airfoil (but produces error, yet to fix)