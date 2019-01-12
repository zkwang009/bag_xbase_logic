# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design.module import Module
from bag.design.database import ModuleDB


# noinspection PyPep8Naming
class bag_xbase_logic__delay_stage(Module):
    """Module for library bag_xbase_logic cell delay_stage.

    Fill in high level description here.
    """

    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'delay_stage.yaml'))

    def __init__(self, database, params, **kwargs):
        # type: (ModuleDB, Dict[str, Any], **Any) -> None
        Module.__init__(self, self.yaml_file, database, params, **kwargs)

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
            n_stage='number of stages',
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

    def design(self, buf_sch_params, dff_sch_params, n_stage, debug):
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

        for i in range(n_stage):
            if i == 0:
                in_pin = 'in'
            else:
                in_pin = 'out<{}>'.format(i-1)
            out_pin = 'out<{}>'.format(i)
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            clk_pin = 'clk_i'

            term_list.append({'in': in_pin, 'out': out_pin, 'clk': clk_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin})
            name_list.append('XDFF{}'.format(i))
        self.array_instance('XDFF', name_list, term_list=term_list)

        for i in range(n_stage):
            self.instances[f'XDFF{i}'].design(**dff_sch_params)
        self.instances['XBUF'].design(**buf_sch_params)
        # self.instances['XDFF'].design(**dff_sch_params)

        # if debug is False:
        #     self.remove_pin('clk_i')

        self.rename_pin('out', 'out<{}:0>'.format(n_stage-1))
