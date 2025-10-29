import openmc
import os

os.makedirs("output", exist_ok=True)
os.chdir("output")

##############################################
                # Materials #
##############################################

inner_fuel = openmc.Material(name="metallic inner fuel")
inner_fuel.add_nuclide('U238', 60, percent_type='wo')
inner_fuel.add_nuclide('Pu238', 0.3, percent_type='wo')
inner_fuel.add_nuclide('Pu239', 12, percent_type='wo')
inner_fuel.add_nuclide('Pu240', 4, percent_type='wo')
inner_fuel.add_nuclide('Pu241', 3, percent_type='wo')
inner_fuel.add_nuclide('Pu242', 0.7, percent_type='wo')
inner_fuel.add_element('Zr', 20, percent_type='wo')
inner_fuel.set_density('g/cm3', 15.5)

outer_fuel = openmc.Material(name="metallic outer fuel")
outer_fuel.add_nuclide('U238', 63, percent_type='wo')
outer_fuel.add_nuclide('Pu238', 0.3, percent_type='wo')
outer_fuel.add_nuclide('Pu239', 10, percent_type='wo')
outer_fuel.add_nuclide('Pu240', 4, percent_type='wo')
outer_fuel.add_nuclide('Pu241', 2, percent_type='wo')
outer_fuel.add_nuclide('Pu242', 0.7, percent_type='wo')
outer_fuel.add_element('Zr', 20, percent_type='wo')
outer_fuel.set_density('g/cm3', 15.5)

steel = openmc.Material(name="stainless steel clad")
steel.add_element('C', 0.08, percent_type='wo')
steel.add_element('Si', 1.00, percent_type='wo')
steel.add_element('P', 0.045, percent_type='wo')
steel.add_element('S', 0.030, percent_type='wo')
steel.add_element('Mn', 2.00, percent_type='wo')
steel.add_element('Cr', 20.0, percent_type='wo')
steel.add_element('Ni', 11.0, percent_type='wo')
steel.add_element('Fe', 65.845, percent_type='wo')
steel.set_density('g/cm3', 8.00)

sodium = openmc.Material(name="sodium coolant")
sodium.add_element('Na', 1.0)
sodium.set_density('g/cm3', 0.87)

materials = openmc.Materials([inner_fuel, outer_fuel, steel, sodium])
materials.export_to_xml()

##############################################
                # Geometry #
##############################################

top = openmc.ZPlane(z0=+50, boundary_type='reflective')
bottom = openmc.ZPlane(z0=-50, boundary_type='reflective')

########### Inner Pincell Definition ###########

fuel_outer_radius_inner = openmc.ZCylinder(r=0.3000)
clad_inner_radius_inner = openmc.ZCylinder(r=0.3075)
clad_outer_radius_inner = openmc.ZCylinder(r=0.3575)
coolant_outer_inner = openmc.model.HexagonalPrism(edge_length=0.85)

fuel_region_inner = -fuel_outer_radius_inner
gap_region_inner = +fuel_outer_radius_inner & -clad_inner_radius_inner
clad_region_inner = +clad_inner_radius_inner & -clad_outer_radius_inner
coolant_region_inner = +clad_outer_radius_inner & -coolant_outer_inner

inner_fuel_cell = openmc.Cell(name="inner fuel cell")
inner_fuel_cell.fill = inner_fuel
inner_fuel_cell.region = fuel_region_inner

inner_gap = openmc.Cell(name="air gap")
inner_gap.region = gap_region_inner

inner_clad = openmc.Cell(name="steel clad")
inner_clad.fill = steel
inner_clad.region = clad_region_inner

inner_coolant = openmc.Cell(name="sodium coolant")
inner_coolant.fill = sodium
inner_coolant.region = coolant_region_inner

inner_pin_universe = openmc.Universe(cells=[inner_fuel_cell, inner_gap, inner_clad, inner_coolant])

########### Outer Pincell Definition ###########

fuel_outer_radius_outer = openmc.ZCylinder(r=0.2980)
clad_inner_radius_outer = openmc.ZCylinder(r=0.3050)
clad_outer_radius_outer = openmc.ZCylinder(r=0.3550)
coolant_outer_outer = openmc.model.HexagonalPrism(edge_length=0.85)

fuel_region_outer = -fuel_outer_radius_outer
gap_region_outer = +fuel_outer_radius_outer & -clad_inner_radius_outer
clad_region_outer = +clad_inner_radius_outer & -clad_outer_radius_outer
coolant_region_outer = +clad_outer_radius_outer & -coolant_outer_outer

outer_fuel_cell = openmc.Cell(name="outer fuel cell")
outer_fuel_cell.fill = outer_fuel
outer_fuel_cell.region = fuel_region_outer

outer_gap = openmc.Cell(name="air gap")
outer_gap.region = gap_region_outer

outer_clad = openmc.Cell(name="steel clad")
outer_clad.fill = steel
outer_clad.region = clad_region_outer

outer_coolant = openmc.Cell(name="sodium coolant")
outer_coolant.fill = sodium
outer_coolant.region = coolant_region_outer

outer_pin_universe = openmc.Universe(cells=[outer_fuel_cell, outer_gap, outer_clad, outer_coolant])

########## Reflector and Sodium Universe ##########

outer_universe = openmc.Universe(name="coolant universe")
outer_cell = openmc.Cell(fill=sodium)
outer_universe.add_cell(outer_cell)

reflector_pin = openmc.Cell(name="stainless steel pincell")
reflector_pin.region = -fuel_outer_radius_outer
reflector_pin.fill = steel

reflector_coolant = openmc.Cell(name="reflector coolant", fill=sodium, region=+fuel_outer_radius_outer & -coolant_outer_outer)

reflector_pin_universe = openmc.Universe(cells=[reflector_pin, reflector_coolant])

reflector_universe = openmc.Universe(name="reflector")
reflector_cell = openmc.Cell(fill=steel)
reflector_universe.add_cell(reflector_cell)

########## Inner Lattice Definition ##########

inner_lattice = openmc.HexLattice()
inner_lattice.center = (0., 0.)
inner_lattice.pitch = (0.85,)
inner_lattice.orientation = 'x'
inner_lattice.outer = outer_universe

inner_lattice.universes = [
    [inner_pin_universe]*18,
    [inner_pin_universe]*12,
    [inner_pin_universe]*6,
    [inner_pin_universe]
]

inner_out_surface = -openmc.model.HexagonalPrism(edge_length=8.0)

main_inner_assembly = openmc.Cell(fill=inner_lattice, region=inner_out_surface & -top & +bottom)
inner_out_assembly = openmc.Cell(fill=sodium, region=~inner_out_surface & -top & +bottom)

main_inner_universe = openmc.Universe(cells=[main_inner_assembly, inner_out_assembly])

########## Outer Lattice Definition ##########

outer_lattice = openmc.HexLattice()
outer_lattice.center = (0., 0.)
outer_lattice.pitch = (0.85,)
outer_lattice.orientation = 'x'
outer_lattice.outer = outer_universe

outer_lattice.universes = [
    [outer_pin_universe]*30,
    [outer_pin_universe]*24,
    [outer_pin_universe]*18,
    [outer_pin_universe]*12,
    [outer_pin_universe]*6,
    [outer_pin_universe]
]

outer_out_surface = -openmc.model.HexagonalPrism(edge_length=12.2)

main_outer_assembly = openmc.Cell(fill=outer_lattice, region=outer_out_surface & -top & +bottom)
outer_out_assembly = openmc.Cell(fill=sodium, region=~outer_out_surface & -top & +bottom)

main_outer_universe = openmc.Universe(cells=[main_outer_assembly, outer_out_assembly])

########## Reflector Lattice Definition ##########

reflector_lattice = openmc.HexLattice()
reflector_lattice.center= (0.,0.)
reflector_lattice.pitch = (0.85,)
reflector_lattice.orientation = 'x'
reflector_lattice.outer = outer_universe

reflector_lattice.universes = [
    [reflector_pin_universe]*18,
    [reflector_pin_universe]*12,
    [reflector_pin_universe]*6,
    [reflector_pin_universe]
]

reflector_out_surface = -openmc.model.HexagonalPrism(edge_length=8.0)

reflector_inner_assembly = openmc.Cell(fill=reflector_lattice, region=reflector_out_surface & -top & +bottom)
reflector_out_assembly = openmc.Cell(fill=sodium, region=~reflector_out_surface & -top & +bottom)

reflector_pincell_universe = openmc.Universe(cells=[reflector_inner_assembly, reflector_out_assembly])

########## Core Lattice Definition ##########

core_lattice = openmc.HexLattice(name='core')
core_lattice.center = (0.,0.)
core_lattice.pitch = (14.085,)
core_lattice.orientation = 'x'
core_lattice.outer = outer_universe

ring_10 = [reflector_pincell_universe]*60
ring_9 = [reflector_pincell_universe]*54
ring_8 = [reflector_pincell_universe]*48
ring_7 = [reflector_pincell_universe]*42
ring_6 = [main_outer_universe]*36
ring_5 = [main_outer_universe]*30
ring_4 = [main_outer_universe]*24
ring_3 = [main_inner_universe]*18
ring_2 = [main_inner_universe]*12
ring_1 = [main_inner_universe]*6
center = [main_inner_universe]


core_lattice.universes = [ring_10, ring_9, ring_8, ring_7, ring_6, ring_5, ring_4, ring_3, ring_2, ring_1, center]

core_prism = openmc.model.HexagonalPrism(10*14.085, orientation='x', boundary_type='reflective')
core_cell = openmc.Cell(fill=core_lattice, region=-core_prism & -top & +bottom)
core_universe = openmc.Universe(cells=[core_cell])

geometry = openmc.Geometry(core_universe)
geometry.export_to_xml()

########## Geometry Plot ##########

import matplotlib.pyplot as plt

plot = openmc.Plot()
plot.filename = 'sfr_core_geometry'
plot.basis = 'xy'
plot.width = (350.0, 350.0)
plot.pixels = (1000, 1000)
plot.color_by = 'material'

plot.colors = {
    inner_fuel: 'red',
    outer_fuel: 'orange',
    steel: 'gray',
    sodium: 'skyblue',
}

plots = openmc.Plots([plot])
plots.export_to_xml()
openmc.plot_geometry()

##############################################
                # Settings #
##############################################

bounds = [-50,-50,-50,50,50,50]
uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:], only_fissionable=True)
source = openmc.IndependentSource(space=uniform_dist)

settings = openmc.Settings()
settings.batches = 100
settings.inactive = 10
settings.particles = 20000
settings.source = source
settings.run_mode = 'eigenvalue'
settings.temperature = {'method': 'interpolation'}

settings.output = {'tallies': True}
settings.trigger_active = True
settings.trigger_max_batches = 200
settings.trigger_batch_interval = 10

##############################################
                # Tallies #
##############################################

mesh = openmc.RegularMesh()
mesh.dimension = [100, 100, 1]
mesh.lower_left = [-150, -150, -50]
mesh.upper_right = [150, 150, 50]

flux_tally = openmc.Tally(name='flux')
flux_tally.filters = [openmc.MeshFilter(mesh)]
flux_tally.scores = ['flux']

openmc.run()

##############################################
              # Visualization #
##############################################

import numpy as np
import matplotlib.pyplot as plt

sp = openmc.StatePoint('statepoint.100.h5')

flux_tally = sp.get_tally(name='flux')
flux_mean = flux_tally.mean
flux_shape = flux_tally.find_filter(openmc.MeshFilter).mesh.dimension

flux_data = flux_mean.reshape(flux_shape)
flux_data_xy = flux_data[:,:,0]
flux_data_xy /= flux_data_xy.max()

plt.figure(figsize=(6,5))
plt.imshow(flux_data_xy.T, origin='lower', cmap='inferno', extent=[-150, 150, -150, 150], aspect='equal')
plt.colorbar(label='Flux')
plt.title('Neutron Flux Distribution')
plt.xlabel('x [cm]')
plt.ylabel('y [cm]')
plt.tight_layout()
plt.savefig("sfr_full_flux_plot.png")









