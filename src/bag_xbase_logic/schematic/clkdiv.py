# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'clkdiv.yaml'))


# noinspection PyPep8Naming
class bag_xbase_logic__clkdiv(Module):
    """Module for library xbase_logic_templates cell clkdiv.

    Fill in high level description here.
    """

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    def __init__(self, bag_config, parent=None, prj=None, **kwargs):
        Module.__init__(self, bag_config, yaml_file, parent=parent, prj=prj, **kwargs)

    @classmethod
    def get_params_info(cls):
        # type: () -> Dict[str, str]
        """Returns a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : Optional[Dict[str, str]]
            dictionary from parameter names to descriptions.
        """
        return dict(
            buf_sch_params='buffer schematic parameters',
            dff_sch_params='dff schematic parameters',
            div_ratio='divider ratio',
            rst_list='rst list for each dff',
            out_list='output list for dffs',
            debug='True to debug',
        )

    @classmethod
    def get_default_param_values(cls):
        """Returns a dictionary containing default parameter values.

        Override this method to define default parameter values.  As good practice,
        you should avoid defining default values for technology-dependent parameters
        (such as channel length, transistor width, etc.), but only define default
        values for technology-independent parameters (such as number of tracks).

        Returns
        -------
        default_params : dict[str, any]
            dictionary of default parameter values.
        """
        return dict(
            debug=False,
        )

    def design(self, buf_sch_params, dff_sch_params, div_ratio, rst_list, out_list, debug):
        """To be overridden by subclasses to design this module.

        This method should fill in values for all parameters in
        self.parameters.  To design instances of this module, you can
        call their design() method or any other ways you coded.

        To modify schematic structure, call:

        rename_pin()
        delete_instance()
        replace_instance_master()
        reconnect_instance_terminal()
        restore_instance()
        array_instance()
        """

        name_list = []
        term_list = []

        for i in range(div_ratio):
            # get o_pin
            if i in out_list:
                idx = out_list.index(i)
                if len(out_list) != 1:      # check if output list have only 1 cell
                    o_pin = 'o<{}>'.format(idx)
                else:
                    o_pin = 'o'
            else:
                o_pin = 'o_{}'.format(i)

            # get i_pin
            if i == 0:
                if div_ratio-1 in out_list:
                    idx = out_list.index(div_ratio-1)
                    if len(out_list) != 1:
                        i_pin = 'o<{}>'.format(idx)
                    else:
                        i_pin = 'o'
                else:
                    i_pin = 'o_{}'.format(div_ratio-1)
            elif i-1 in out_list:
                idx = out_list.index(i-1)
                if len(out_list) != 1:
                    i_pin = 'o<{}>'.format(idx)
                else:
                    i_pin = 'o'
            else:
                i_pin = 'o_{}'.format(i-1)

            # get rst/st
            if rst_list[i] == 1:
                st_pin = 'rst_i'
                rst_pin = 'VSS'
            elif rst_list[i] == 0:
                st_pin = 'VSS'
                rst_pin = 'rst_i'
            else:
                raise ValueError('In rst_list, value can only be 1 or 0.')

            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            clk_pin = 'clk_i'

            term_list.append({'I': i_pin, 'O': o_pin, 'CLK': clk_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin, 'RST': rst_pin,
                              'ST': st_pin})
            name_list.append('XDFF{}'.format(i))

        self.array_instance('XDFF', name_list, term_list=term_list)
        for inst in self.instances['XDFF']:
            inst.design(**dff_sch_params)

        self.instances['XCLKBUF'].design(**buf_sch_params)
        self.instances['XRSTBUF'].design(**buf_sch_params)

        if debug is False:
            self.remove_pin('clk_i')

        if len(out_list) != 1:
            self.rename_pin('o', 'o<{}:0>'.format(len(out_list)-1))
