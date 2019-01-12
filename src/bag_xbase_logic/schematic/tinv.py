# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design.module import Module
from bag.design.database import ModuleDB


# noinspection PyPep8Naming
class bag_xbase_logic__tinv(Module):
    """Module for library bag_xbase_logic cell tinv.

    Fill in high level description here.
    """

    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'tinv.yaml'))

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
            lch='transistor channel length',
            wn='NMOS width',
            wp='PMOS width',
            nfn0='bottom NMOS finger number',
            nfn1='switch NMOS finger number',
            nfp0='bottom PMOS finger number',
            nfp1='switch PMOS finger number',
            intent='transistor threshold',
            dum_info='dummy info',
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
        )

    def design(self, lch, wn, wp, nfn0, nfn1, nfp0, nfp1, intent, dum_info, **kwargs):
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
        self.instances['XN0'].design(w=wn, l=lch, nf=nfn0, intent=intent)
        self.instances['XN1'].design(w=wn, l=lch, nf=nfn1, intent=intent)
        self.instances['XP0'].design(w=wp, l=lch, nf=nfp0, intent=intent)
        self.instances['XP1'].design(w=wp, l=lch, nf=nfp1, intent=intent)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')
