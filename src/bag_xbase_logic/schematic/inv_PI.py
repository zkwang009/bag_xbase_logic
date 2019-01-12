# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'inv_PI.yaml'))


# noinspection PyPep8Naming
class bag_xbase_logic__inv_PI(Module):
    """Module for library xbase_logic_templates cell inv_PI.

    Fill in high level description here.
    """

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
            pi_res='phase interpolator information',
            ctrl_sch_params='ctrl schematic parameters',
            clk_sch_params='clk schematic parameters',
            buf_sch_params='buffer schematic parameters',
            cload_sch_params='cload schematic parmaeters',
            dum_info='dummy information',
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
            rename_dict={},
            show_pins=False,
            dum_info=None,
        )

    def design(self, pi_res, ctrl_sch_params, clk_sch_params, buf_sch_params,
               cload_sch_params, dum_info, **kwargs):
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
        # cells

        self.instances['XBUFARR'].design(**ctrl_sch_params)
        self.instances['XCLKARR'].design(**clk_sch_params)
        self.instances['XBUF'].design(**buf_sch_params)
        self.instances['XCL'].design(**cload_sch_params)
        # dummy transistor
        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')
        # control signals
        self.rename_pin('ctrl', 'ctrl<{}:0>'.format(pi_res-1))

        # reconnect
        self.reconnect_instance_terminal('XBUFARR', 'ctrl<{}:0>'.format(pi_res-1), 'ctrl<{}:0>'.format(pi_res-1))
        self.reconnect_instance_terminal('XBUFARR', 'ctrl_o<{}:0>'.format(pi_res-1), 'ctrl_o<{}:0>'.format(pi_res-1))
        self.reconnect_instance_terminal('XBUFARR', 'ctrl_ob<{}:0>'.format(pi_res-1), 'ctrl_ob<{}:0>'.format(pi_res-1))

        self.reconnect_instance_terminal('XCLKARR', 'ctrl<{}:0>'.format(pi_res-1), 'ctrl_o<{}:0>'.format(pi_res - 1))
        self.reconnect_instance_terminal('XCLKARR', 'ctrlb<{}:0>'.format(pi_res-1), 'ctrl_ob<{}:0>'.format(pi_res - 1))


