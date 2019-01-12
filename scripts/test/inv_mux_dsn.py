import pprint
import bag

from xbase_logic_repo.layout.inv_mux import InvMUX
from bag.layout import RoutingGrid, TemplateDB
from bag.data import load_sim_results
from BAG_framework.bag.io.file import read_yaml
from xbase_logic_repo.dsn_scripts._misc import make_tdb

import pdb

import numpy as np
import matplotlib.pyplot as plt


def generate(prj, temp_lib, impl_lib, cell_name, lay_params, sch_params, grid_opts, impl_cell_name=None):

    temp_db = make_tdb(prj, impl_lib, grid_opts)

    print('designing module')
    # layout
    print(lay_params)
    template = temp_db.new_template(params=lay_params, temp_cls=InvMUX, debug=True)
    if impl_cell_name is None:
        temp_db.instantiate_layout(prj, template, cell_name, debug=True)
    else:
        temp_db.instantiate_layout(prj, template, impl_cell_name, debug=True)

    # schematic
    if sch_params is None:
        sch_params = {}
    sch_params.update(template.sch_params)
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

    config_file = 'bag_xbase_logic/test/logic_parameters.yaml'
    specs = read_yaml(config_file)

    # lib and cells
    temp_lib = specs['temp_lib']
    impl_lib = specs['impl_lib']
    tb_lib = specs['tb_lib']
    cell_name = specs['inv_mux_cell_name']
    tb_cell = specs['inv_mux_tb_cell']

    # parameters
    grid_opts = specs['grid_opts']
    sch_params = specs['inv_mux_sch_params']
    lay_params = specs['inv_mux_lay_params']

    # testbench sweep parameters
    sim_envs = specs['inv_mux_sim_envs']
    tb_params = specs['inv_mux_tb_params'].copy()

    inv_mux_opts = specs['inv_mux_opts'].copy()
    run_dsn = inv_mux_opts['run_dsn']
    run_simulation = inv_mux_opts['run_simulation']
    run_extraction = inv_mux_opts['run_extraction']

    print('generating tdb')
    if run_dsn:
        generate(bprj, temp_lib, impl_lib, cell_name, lay_params, sch_params, grid_opts)

    if run_dsn and run_extraction:
        extract(bprj)

    if run_simulation:
        simulate(bprj)
