import bag.core
from xbase_logic_repo.src.xbase_logic_repo.layout.prbs import PRBS
from bag.io.file import read_yaml
from xbase_logic_repo.scripts._misc import generate, extract, simulate


def run_main(prj):
    config_file = 'bag_xbase_logic/specs/logic_parameters.yaml'
    specs = read_yaml(config_file)

    # lib and cells
    temp_lib = specs['temp_lib']
    impl_lib = specs['impl_lib']
    tb_lib = specs['tb_lib']
    cell_name = specs['prbs_cell_name']
    tb_cell = specs['prbs_tb_cell']

    # get directories
    mdl_dir = specs['model_dir']

    # parameters
    grid_opts = specs['grid_opts']
    sch_params = specs['prbs_sch_params']
    lay_params = specs['prbs_lay_params']
    mdl_params = specs['prbs_mdl_params']

    # testbench sweep parameters
    sim_envs = specs['prbs_sim_envs']
    tb_params = specs['prbs_tb_params'].copy()

    prbs_opts = specs['prbs_opts'].copy()
    run_dsn = prbs_opts['run_dsn']
    run_simulation = prbs_opts['run_simulation']
    run_extraction = prbs_opts['run_extraction']

    print('generating tdb')
    if run_dsn:
        generate(prj, temp_lib, impl_lib, cell_name, lay_params, sch_params, mdl_params,
                 grid_opts, mdl_dir)

    if run_dsn and run_extraction:
        extract(prj, impl_lib, cell_name)

    if run_simulation:
        simulate(prj)


if __name__ == '__main__':
    bprj = locals().get('bprj', None)
    if bprj is None:
        print('creating BAG project')
        bprj = bag.core.BagProject()

    run_main(bprj)

