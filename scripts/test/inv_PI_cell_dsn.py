import pprint
import bag

from vco_repo.layout.varactor_n_layout.varactor_n import VaractorN
from bag.layout import RoutingGrid, TemplateDB
from bag.data import load_sim_results
from BAG_framework.bag.io.file import read_yaml

import pdb

import numpy as np
import matplotlib.pyplot as plt


def make_tdb(prj, specs):

    grid_opts = specs['grid_opts'].copy()

    layers = grid_opts['layers']
    spaces = grid_opts['spaces']
    widths = grid_opts['widths']
    bot_dir = grid_opts['bot_dir']

    routing_grid = RoutingGrid(bprj.tech_info, layers, spaces, widths, bot_dir)

    tdb = TemplateDB('template_libs.def', routing_grid, impl_lib)
    return tdb


def generate(prj, temp_lib, impl_lib, cell_name, lay_params, sch_params, grid_opts, impl_cell_name=None):

    temp_db = make_tdb(prj, specs)

    print('designing module')
    # # layout
    # template = temp_db.new_template(params=lay_params, temp_cls=VaractorN, debug=True)
    # if impl_cell_name is None:
    #     temp_db.instantiate_layout(prj, template, cell_name, debug=True)
    # else:
    #     temp_db.instantiate_layout(prj, template, impl_cell_name, debug=True)

    # schematic
    if sch_params is None:
        sch_params = {}
    # sch_params.update(template.sch_params)

    print(sch_params)
    dsn = prj.create_design_module(temp_lib, cell_name)
    dsn.design(**sch_params)
    if impl_cell_name is None:
        dsn.implement_design(impl_lib, top_cell_name=cell_name)
    else:
        dsn.implement_design(impl_lib, top_cell_name=impl_cell_name)


def extract(prj):
    print('running lvs')
    lvs_passed, lvs_log = prj.run_lvs(impl_lib, cell_name)
    if not lvs_passed:
        raise Exception('oops lvs died.  See LVS log file %s' % lvs_log)
    print('lvs passed')

    # run rcx
    print('running rcx')
    rcx_passed, rcx_log = prj.run_rcx(impl_lib, cell_name)
    if not rcx_passed:
        raise Exception('oops rcx died.  See RCX log file %s' % rcx_log)
    print('rcx passed')


def simulate(prj):
    pass


if __name__ == '__main__':
    local_dict = locals()
    if 'bprj' not in local_dict:
        print('creating BAG project')
        bprj = bag.BagProject()
    else:
        print('loading BAG project')

    config_file = 'logic_repo/test/logic_parameters.yaml'
    specs = read_yaml(config_file)

    # lib and cells
    temp_lib = specs['temp_lib']
    impl_lib = specs['impl_lib']
    tb_lib = specs['tb_lib']
    cell_name = specs['inv_PI_cell_cell_name']
    tb_cell = specs['inv_PI_cell_tb_cell']

    # parameters
    grid_opts = specs['grid_opts']
    sch_params = specs['inv_PI_cell_sch_params']
    lay_params = specs['inv_PI_cell_lay_params']

    # testbench sweep parameters
    sim_envs = specs['inv_PI_cell_sim_envs']
    tb_params = specs['inv_PI_cell_tb_params'].copy()

    inv_PI_cell_opts = specs['inv_PI_cell_opts'].copy()
    run_dsn = inv_PI_cell_opts['run_dsn']
    run_simulation = inv_PI_cell_opts['run_simulation']
    run_extraction = inv_PI_cell_opts['run_extraction']

    print('generating tdb')
    if run_dsn:
        generate(bprj, temp_lib, impl_lib, cell_name, lay_params, sch_params, grid_opts)

    if run_dsn and run_extraction:
        extract(bprj)

    if run_simulation:
        simulate(bprj)
