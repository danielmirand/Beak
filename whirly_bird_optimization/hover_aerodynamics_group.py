import numpy as np
import openmdao.api as om

from openmdao.api import Group

from openaerostruct.geometry.utils import generate_mesh, scale_x
from openaerostruct.geometry.geometry_group import Geometry
from openaerostruct.aerodynamics.aero_groups import AeroPoint

from .aerodynamics_geometry_group import AerodynamicsGeometryGroup
from .hover_velocity_group import HoverVelocityGroup


class HoverAerodynamicsGroup(Group):
    def initialize(self):
        self.options.declare('shape',types=tuple)

    def setup(self):
        shape = self.options['shape']

        # group = AerodynamicsGeomGroup(
        #     shape=shape
        # )
        # self.add_subsystem('aerodynamics_geom_group', group, promotes=['*'])

        indep_var_comp = om.IndepVarComp()
        indep_var_comp.add_output('hover_drag_velocity', units='m/s')
        indep_var_comp.add_output('Mach_number', val=0.3)
        indep_var_comp.add_output('re', val=1.e6, units='1/m')
        indep_var_comp.add_output('rho', val=1.225, units='kg/m**3')
        indep_var_comp.add_output('cg', val=np.zeros((3)), units='m')
        indep_var_comp.add_output('alpha', val = 2.)

        self.add_subsystem('ivc', indep_var_comp, promotes=['*'])
        shape = (1,)
        self.add_subsystem('aerodynamics_geometry_group', AerodynamicsGeometryGroup(shape=shape), promotes=['*'])

        mesh_dict = {'num_y' : 17,
                    'num_x' : 9,
                    'wing_type' : 'rect',
                    'symmetry' : True,
                    'chord': 0.1,
                    'span' : 1.,
                    }

        mesh = generate_mesh(mesh_dict)

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

        self.add_subsystem(surface['name'], geom_group)

        aero_group = AeroPoint(surfaces=[surface])
        point_name = 'laura'
        self.add_subsystem(point_name, aero_group)

        # Connect flow properties to the analysis point
        self.connect('v', point_name + '.v')
        self.connect('alpha', point_name + '.alpha')
        self.connect('Mach_number', point_name + '.Mach_number')
        self.connect('re', point_name + '.re')
        self.connect('rho', point_name + '.rho')
        self.connect('cg', point_name + '.cg')

        # Connect the mesh from the geometry component to the analysis point
        self.connect('wing.mesh', 'laura.wing.def_mesh')

        # Perform the connections with the modified names within the 'aero_states' group.
        self.connect('wing.mesh', 'laura.aero_states.wing_def_mesh')
        self.connect('wing.t_over_c', 'laura.wing_perf.t_over_c')

        self.connect('wing_span', 'wing.mesh.stretch.span')
        self.connect('oas_wing_chord', 'wing.mesh.scale_x.chord')