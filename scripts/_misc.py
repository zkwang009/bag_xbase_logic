import bag
import numpy as np
import matplotlib.pyplot as plt
from os import path
from os import mkdir
import datetime
from bag.layout.routing.grid import RoutingGrid
from bag.layout.template import TemplateDB
import yaml
import subprocess
import math
import os
from time import time
import logging
from pybag.enum import DesignOutput
from bag.design.database import ModuleDB


def np_to_float(ddict):

    for key, val in ddict.items():
        if isinstance(val, np.float64) or isinstance(val, np.float32) \
                or isinstance(val, np.float16):
            ddict[key] = val.item()
        if isinstance(val, np.float32) or isinstance(val, np.float32) \
                or isinstance(val, np.float16):
            ddict[key] = val.item()

    # return ddict


def read_yaml(fname):
    with open(fname, 'r') as f:
        content = yaml.load(f)
    return content


def save_yaml(data, yaml_file, append=False):

    lead, file = os.path.split(yaml_file)

    # check if path is exist or not?
    if not path.isdir(lead):
        os.mkdir(lead)

    if path.isfile(yaml_file):
        pass
    else:
        subprocess.call('touch {}'.format(yaml_file), shell=True)

    if path.isfile(yaml_file):
        print("Will overwrite {}".format(yaml_file))

    if append is True:
        print("Appending data...")
        yaml_data = read_yaml(yaml_file)
    else:
        print("Overwriting data...")
        yaml_data = {}
    yaml_data.update(data)

    # save to file
    with open(yaml_file, 'w') as f:
        yaml.dump(yaml_data, f)





# def extract(bprj, impl_lib, cell_name, run_lvs_flag=True):
#     if run_lvs_flag is True:
#         run_lvs(bprj, impl_lib, cell_name)
#
#     # run rcx
#     print('running rcx')
#     start_time = time()
#     rcx_passed, rcx_log = bprj.run_rcx(impl_lib, cell_name)
#     if not rcx_passed:
#         raise Exception('oops rcx died.  See RCX log file %s' % rcx_log)
#     print('rcx passed')
#     print_elapsed_time(start_time)
#
#
# def simulate(bprj, temp_lib, tb_lib, impl_lib, dut_cell, tb_cell,
#              tb_params, sim_params, swp_params,
#              sim_outputs, sim_corner, config_view, config_cell_name='',
#              run_sim=True, tb_cell_name=None):
#
#     tb_sch = bprj.create_design_module(temp_lib, tb_cell)
#     print("Testbench params are {}".format(tb_params))
#     tb_sch.design(dut_lib=impl_lib, dut_cell=dut_cell, **tb_params)
#     if tb_cell_name is None:
#         print("TB cell is {}".format(tb_cell))
#         tb_sch.implement_design(tb_lib, top_cell_name=tb_cell)
#         tb = bprj.configure_testbench(tb_lib, tb_cell)
#     else:
#         print("TB cell is {}".format(tb_cell_name))
#         tb_sch.implement_design(tb_lib, top_cell_name=tb_cell_name)
#         tb = bprj.configure_testbench(tb_lib, tb_cell_name)
#
#     print("Testbench name is {}".format(tb_cell_name))
#     print('setting testbench parameters')
#     if sim_params:
#         for param, value in sim_params.items():
#             tb.set_parameter(param, value)
#
#     print('setting sweep paramters')
#     if swp_params:
#         for param, value in swp_params.items():
#             tb.set_sweep_parameter(param, values=value)
#
#     print('Simulation corner is {}'.format(sim_corner))
#     tb.set_simulation_environments(sim_corner)
#     if config_cell_name == '':
#         config_cell_name = dut_cell
#     tb.set_simulation_view(impl_lib, config_cell_name, config_view)
#
#     print(sim_outputs.keys())
#     for key in sim_outputs.keys():
#         tb.add_output(key, sim_outputs[key])
#
#     tb.update_testbench()
#     if run_sim is True:
#         start_time = time()
#         print('running simulation')
#         tb.run_simulation()
#         print_elapsed_time(start_time)
#         print(tb.save_dir)
#         return tb.save_dir
#     else:
#         return None


def load_simres(dir):
    print('loading results')
    results = bag.data.load_sim_results(dir)
    return results


def import_library(bprj, lib_name):
    print('importing library: %s' % lib_name)
    bprj.import_design_library(lib_name)
    print('finish importing library %s.' % lib_name)


def remove_generated_library(bprj, impl_lib):
    # deletes the impl_lib library
    if not bprj.impl_db.get_cells_in_library(impl_lib):
        print('library %s does not exist, nothing to delete' % impl_lib)
    else:
        print('deleting library: %s' % impl_lib)
        bprj.impl_db._eval_skill('ddDeleteObj(ddGetObj("' + impl_lib +'"))')
        print('finished deleting library: %s' % impl_lib)

    # # deletes the generated cells in the impl_lib directory
    # # the directory is kept empty with its technology data
    # from shutil import move, rmtree
    # from os import rename, mkdir
    # impl_lib_full_path = bprj.impl_db.default_lib_path + '/' + impl_lib
    # print('deleting library: %s' % impl_lib)
    # impl_lib_full_path_renamed = impl_lib_full_path + '_old'
    # rename(impl_lib_full_path, impl_lib_full_path_renamed)
    # mkdir(impl_lib_full_path)   # create empty directory
    # move(impl_lib_full_path_renamed + '/cdsinfo.tag', impl_lib_full_path) # technology data
    # move(impl_lib_full_path_renamed + '/data.dm', impl_lib_full_path) # technology data
    # move(impl_lib_full_path_renamed + '/.oalib', impl_lib_full_path)
    # rmtree(impl_lib_full_path_renamed)  # remove old directory tree
    # print('finished deleting library: %s' % impl_lib)


def print_elapsed_time(start_time):
    elapsed_time = time() - start_time
    m, s = divmod(int(np.round(elapsed_time)), 60)
    h, m = divmod(m, 60)
    print('Total elapsed time is %dh : %dm : %ds' % (h, m, s))


def plot_generic(x, y_list, title_str='', legend_list=[], xlabel_str='', ylabel_str='', xscale='linear', yscale='linear',
                 plot_style_str='o-', xlim=[], ylim=[], linewidth=1.5, fontsize=15, script_name='', filename=''):

    if (xscale, yscale) == ('linear', 'linear'):
        plot_type_str = 'plot'
    elif (xscale, yscale) == ('log', 'linear'):
        plot_type_str = 'semilogx'
    elif (xscale, yscale) == ('linear', 'log'):
        plot_type_str = 'semilogy'
    elif (xscale, yscale) == ('log', 'log'):
        plot_type_str = 'loglog'
    else:
        raise Exception('xscale = %s, yscale = %s, both should be linear or log!!' % (xscale, yscale))

    # fig = plt.figure()
    # ax = fig.add_subplot(1,1,1) # a fake subplot for tick_params()
    fig, ax = plt.subplots()    # default is 1,1,1
    if (isinstance(x[0], list)) and (len(x) == len(y_list)): # several plots with different x values
        for x, y in zip(x, y_list):
            exec('ax.' + plot_type_str + '(x, y, plot_style_str, linewidth=linewidth)')
    else:
        # if (isinstance(y_list[0], list)): # several plots with the same x values
        if (~isinstance(x, list)) and (isinstance(y_list, list)):  # several plots with the same x values
            for y in y_list:
                exec('ax.' + plot_type_str + '(x, y, plot_style_str, linewidth=linewidth)')
        else: # single plot only
            exec('ax.' + plot_type_str + '(x, y_list, plot_style_str, linewidth=linewidth)')
    # xmin, xmax = plot.get_xlim()
    # plt.xlim(0, max(x))
    if xlim:
        plt.xlim(xlim)
    if ylim:
        plt.ylim(ylim)
    # plt.xlabel(xlabel_str, fontsize=fontsize)
    ax.set_xlabel(xlabel_str, fontsize=fontsize)
    plt.ylabel(ylabel_str, fontsize=fontsize)
    if not title_str:
        loc_y = 1.05
    else:
        plt.title(title_str, fontsize=fontsize)
        loc_y = 1.1
    if legend_list:
        # plt.legend(legend_list, loc=(0, loc_y))
        plt.legend(legend_list, loc=0)
        # 'best': 0,
        # 'upper right': 1,
        # 'upper left': 2,
        # 'lower left': 3,
        # 'lower right': 4,
        # 'right': 5, (same as 'center right',
        # 'center left': 6,
        # 'center right': 7,
        # 'lower center': 8,
        # 'upper center': 9,
        # 'center': 10,
    plt.grid(True, which='both')
    ax.tick_params(axis='both', which='major', labelsize=fontsize)

    if script_name != '':
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d %Hh%Mm%Ss ")
        script_path = path.dirname(path.abspath(__file__))
        dir_path = script_path + '/' + script_name
        if path.isdir(dir_path) is False:
            mkdir(dir_path)
        figure_path = dir_path + '/' + now_str + '- ' + filename
        ret = dir_path + '/' + now_str + '- '
        plt.savefig(figure_path + '.pdf', bbox_inches='tight')
        plt.savefig(figure_path + '.jpg', bbox_inches='tight')
    else:
        ret = None

    plt.show(block=False)

    return ret


def get_lib_cell(specs, cell):

    temp_lib = specs['temp_lib']
    impl_lib = specs['impl_lib']
    name = cell+"_cell_name"
    cell_name = specs[name]
    tb_lib = specs['tb_lib']
    tb_name = cell+"_tb_cell"
    tb_cell = specs[tb_name]

    return temp_lib, impl_lib, cell_name, tb_lib, tb_cell


def osc_cal(ind, cap, freq=None):

    if freq is None:
        freq = 1/2/math.pi/math.sqrt(ind*cap)
        return freq
    elif ind is None:
        ind = (1/2/math.pi/freq)**2/cap
        return ind
    elif cap is None:
        cap = (1/2/math.pi/freq)**2/ind
        return cap
    else:
        print("Please check your input!!")
        return None


def constant(f):

    def fset(self, value):
        raise TypeError

    def fget(self):
        return f()
    return property(fget, fset)


class Const(object):
    @constant
    def k():
        return 1.3806485279e-23

    @constant
    def t():
        return 300


def write_log(log_file, level=logging.INFO, fmt='', overwrite=True, stream=False):

    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    formatter = logging.Formatter(fmt)
    if overwrite is True:
        file_handler = logging.FileHandler(log_file, 'w')
    else:
        file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # if stream is True:
    #     stream_handler = logging.StreamHandler()
    #     stream_handler.flush()
    #     logger.addHandler(stream_handler)

    return logger


def get_model_type(type_x):

    if type_x == 'sv':
        return DesignOutput.SYSVERILOG
    elif type_x == 'v':
        return DesignOutput.VERILOG
    elif type_x == 'cdl':
        return DesignOutput.CDL
    elif type_x == 'yaml':
        return DesignOutput.YAML
    elif type_x == 'schematic' or type_x == 'sch':
        return DesignOutput.SCHEMATIC
    else:
        print("Only support model type with 'sv', 'v', 'cdl', 'yaml' and "
              "'schematic' or 'sch'.")


def make_tdb(prj, impl_lib, grid_opts):
    """
        make layout database.
    """

    layers = grid_opts['layers']
    widths = grid_opts['widths']
    spaces = grid_opts['spaces']
    bot_dir = grid_opts['bot_dir']
    width_override = grid_opts.get('width_override', None)

    routing_grid = RoutingGrid(prj.tech_info, layers, spaces, widths, bot_dir,
                               width_override=width_override)
    tdb = TemplateDB('template_libs.def', routing_grid, impl_lib, use_cybagoa=True)

    return tdb


def run_lvs(bprj, impl_lib, cell_name, impl_cell_name=None):
    """
        run lvs.
    """

    if impl_cell_name is not None:
        cell_name = impl_cell_name

    print('running lvs')
    start_time = time()
    lvs_passed, lvs_log = bprj.run_lvs(impl_lib, cell_name)
    if not lvs_passed:
        raise Exception('oops lvs died.  See LVS log file %s' % lvs_log)
    print('lvs passed')
    print_elapsed_time(start_time)


def generate(prj, temp_lib, impl_lib, cell_name, lay_params, sch_params, mdl_params,
             grid_opts, mdl_dir, mdl_opts=None, impl_cell_name=None):
    """
        generate layout, schematic and model.
    """

    # temp_db = make_tdb(prj, impl_loib, grid_opts)
    #
    # print('designing module')
    # # layout
    # print(lay_params)
    # template = temp_db.new_template(params=lay_params, temp_cls=NAND, debug=True)
    # if impl_cell_name is None:
    #     temp_db.instantiate_layout(prj, template, cell_name, debug=True)
    # else:
    #     temp_db.instantiate_layout(prj, template, impl_cell_name, debug=True)

    # generate schematic
    if sch_params is None:
        sch_params = {}
    # sch_params.update(template.sch_params)
    print(sch_params)

    sch_db = ModuleDB(prj.tech_info, impl_lib, prj=prj)
    gen_cls = sch_db.get_schematic_class(temp_lib, cell_name)
    dsn = sch_db.new_master(gen_cls, params=sch_params)
    if impl_cell_name is None:
        sch_db.instantiate_master(DesignOutput.SCHEMATIC, dsn)
    else:
        sch_db.instantiate_master(DesignOutput.SCHEMATIC, dsn, top_cell_name=impl_cell_name)

    # generate model
    file_name = f"{mdl_dir}/{cell_name}.sv"
    top_cell_name = cell_name if impl_cell_name is None else impl_cell_name
    if mdl_opts is None:
        mdl_opts = {}
    sch_db.instantiate_model(dsn, mdl_params, top_cell_name=top_cell_name,
                             fname=file_name, **mdl_opts)


def extract(prj, impl_lib, cell_name, impl_cell_name=None):
    """
        run extraction.
    """

    if impl_cell_name is not None:
        cell_name = impl_cell_name

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