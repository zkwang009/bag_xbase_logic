import bag.core
from xbase_logic_repo.src.xbase_logic_repo.layout.buffer import Buffer
from bag.io.file import read_yaml
from xbase_logic_repo.scripts._misc import generate, extract, simulate


def run_main(prj):
    config_file = 'bag_xbase_logic/specs/logic_parameters.yaml'
    specs = read_yaml(config_file)

    # lib and cells
    temp_lib = specs['temp_lib']
    impl_lib = specs['impl_lib']
    tb_lib = specs['tb_lib']
    cell_name = specs['buffer_cell_name']
    tb_cell = specs['buffer_tb_cell']

    # get directories
    mdl_dir = specs['model_dir']

    # parameters
    grid_opts = specs['grid_opts']
    sch_params = specs['buffer_sch_params']
    lay_params = specs['buffer_lay_params']
    mdl_params = specs['buffer_mdl_params']

    # testbench sweep parameters
    sim_envs = specs['buffer_sim_envs']
    tb_params = specs['buffer_tb_params'].copy()

    buffer_opts = specs['buffer_opts'].copy()
    run_dsn = buffer_opts['run_dsn']
    run_simulation = buffer_opts['run_simulation']
    run_extraction = buffer_opts['run_extraction']

    print('generating tdb')
    if run_dsn:
        generate(bprj, temp_lib, impl_lib, cell_name, lay_params, sch_params, mdl_params,
                 grid_opts, mdl_dir)

    if run_dsn and run_extraction:
        extract(bprj, impl_lib, cell_name)

    if run_simulation:
        simulate(bprj)


if __name__ == '__main__':
    local_dict = locals()
    if 'bprj' not in local_dict:
        print('creating BAG project')
        bprj = bag.core.BagProject()
    else:
        print('loading BAG project')

    run_main(bprj)
