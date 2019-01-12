# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design.module import Module
from bag.design.database import ModuleDB


# noinspection PyPep8Naming
class bag_xbase_logic__dff(Module):
    """Module for library bag_xbase_logic cell dff.

    Fill in high level description here.
    """

    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'dff.yaml'))

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
            clk_inv_params='clock inverter parameters',
            drv_tinv_params='driver tinv parameters',
            ff_inv_params='feed-forward inv parameters',
            fb_tinv_params='feedback tinv parameters',
            dum_info='dummy information',
            debug='True to show inner pins',
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
            dum_info=None,
            debug=False,
        )

    def design(self, clk_inv_params, drv_tinv_params, ff_inv_params, fb_tinv_params,
               dum_info, debug, **kwargs):
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
        self.instances['INV0'].design(**ff_inv_params)
        self.instances['INV1'].design(**ff_inv_params)
        self.instances['INV2'].design(**clk_inv_params)
        self.instances['INV3'].design(**clk_inv_params)

        self.instances['TINV0'].design(**drv_tinv_params)
        self.instances['TINV1'].design(**drv_tinv_params)
        self.instances['TINV2'].design(**fb_tinv_params)
        self.instances['TINV3'].design(**fb_tinv_params)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')

        if debug is False:
            self.remove_pin('mem1')
            self.remove_pin('mem2')
            self.remove_pin('latch')
            self.remove_pin('iclk')
            self.remove_pin('iclkb')
