# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design.module import Module
from bag.design.database import ModuleDB


# noinspection PyPep8Naming
class bag_xbase_logic__dff_strst(Module):
    """Module for library bag_xbase_logic cell dff_strst.

    Fill in high level description here.
    """

    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'dff_strst.yaml'))

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
            clk_inv_params='clock inv parameters',
            r_st_inv_params='set/reset inv params',
            drv_tinv_params='driver tinv parameters',
            ff_nand_params='feed-forward nand parameters',
            fb_nand_params='feedback nand parameters',
            fb_tgate_params='feedback tgate parameters',
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

    def design(self, clk_inv_params, r_st_inv_params, drv_tinv_params, ff_nand_params,
               fb_nand_params, fb_tgate_params, dum_info, debug, **kwargs):
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
        self.instances['INV0'].design(**clk_inv_params)
        self.instances['INV1'].design(**clk_inv_params)
        self.instances['INV2'].design(**r_st_inv_params)
        self.instances['INV3'].design(**r_st_inv_params)

        self.instances['TINV0'].design(**drv_tinv_params)
        self.instances['TINV1'].design(**drv_tinv_params)
        self.instances['NAND0'].design(**ff_nand_params)
        self.instances['NAND1'].design(**ff_nand_params)
        self.instances['NAND2'].design(**fb_nand_params)
        self.instances['NAND3'].design(**fb_nand_params)
        self.instances['TGATE0'].design(**fb_tgate_params)
        self.instances['TGATE1'].design(**fb_tgate_params)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')

        if debug is False:
            self.remove_pin('mem1')
            self.remove_pin('mem2')
            self.remove_pin('latch')
            self.remove_pin('iclk')
            self.remove_pin('iclkb')
            self.remove_pin('rstm1')
            self.remove_pin('rstm2')
            self.remove_pin('stb')
            self.remove_pin('rstb')

