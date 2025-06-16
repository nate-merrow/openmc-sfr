import openmc
import os

os.makedirs("output", exist_ok=True)
os.chdir("output")

##############################################
                # Materials #
##############################################

metal_fuel = openmc.Material(name="metallic fuel")
metal_fuel.add_nuclide('U238', 60, percent_type='wo')
metal_fuel.add_nuclide('Pu238', 0.3, percent_type='wo')
metal_fuel.add_nuclide('Pu239', 12, percent_type='wo')
metal_fuel.add_nuclide('Pu240', 4, percent_type='wo')
metal_fuel.add_nuclide('Pu241', 3, percent_type='wo')
metal_fuel.add_nuclide('Pu242', 0.7, percent_type='wo')
metal_fuel.add_element('Zr', 20, percent_type='wo')
metal_fuel.set_density('g/cm3', 15.5)


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

materials = openmc.Materials([metal_fuel, steel, sodium])
materials.export_to_xml()

##############################################
                # Geometry #
##############################################

fuel_outer_radius = openmc.ZCylinder(r=0.3000)
clad_inner_radius = openmc.ZCylinder(r=0.3075)
clad_outer_radius = openmc.ZCylinder(r=0.3575)
coolant_outer = openmc.model.HexagonalPrism(edge_length=0.85)

fuel_region = -fuel_outer_radius
gap_region = +fuel_outer_radius & -clad_inner_radius
clad_region = +clad_inner_radius & -clad_outer_radius
coolant_region = +clad_outer_radius & -coolant_outer

fuel = openmc.Cell(name="fuel cell")
fuel.fill = metal_fuel
fuel.region = fuel_region

gap = openmc.Cell(name="air gap")
gap.region = gap_region

clad = openmc.Cell(name="steel clad")
clad.fill = steel
clad.region = clad_region

coolant = openmc.Cell(name="sodium coolant")
coolant.fill = sodium
coolant.region = coolant_region

outer_universe = openmc.Universe(name="coolant universe")
outer_cell = openmc.Cell(fill=sodium)
outer_universe.add_cell(outer_cell)

pin_universe = openmc.Universe(cells=[fuel, gap, clad, coolant])

lattice = openmc.HexLattice()
lattice.center = (0., 0.)
lattice.pitch = (0.85,)
lattice.outer = outer_universe

outer_ring = [pin_universe]*30
ring_5 = [pin_universe]*24
ring_4 = [pin_universe]*18
ring_3 = [pin_universe]*12
ring_2 = [pin_universe]*6
inner_ring = [pin_universe]

lattice.universes = [outer_ring,
                     ring_5,
                     ring_4,
                     ring_3,
                     ring_2,
                     inner_ring]

outer_surface = openmc.model.HexagonalPrism(edge_length=5.1, boundary_type='reflective')
main_cell = openmc.Cell(fill=lattice, region=-outer_surface)
geometry = openmc.Geometry([main_cell])

geometry.export_to_xml()

plot = openmc.Plot()
plot.filename = 'hex_lattice_plot'
plot.width = (15.0, 15.0)  # Set an appropriate width
plot.pixels = (400, 400)
plot.color_by = 'material'
plot.colors = {
    metal_fuel: 'green',
    steel: 'gray',
    sodium: 'blue'
}
plots = openmc.Plots([plot])
plots.export_to_xml()
openmc.plot_geometry()

source = openmc.IndependentSource(space=openmc.stats.Point((0,0,0)))

##############################################
                # Settings #
##############################################

settings = openmc.Settings()
settings.source = source
settings.batches = 100
settings.inactive = 10
settings.particles = 1000
settings.export_to_xml()

openmc.run()






