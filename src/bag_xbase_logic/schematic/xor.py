# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design.module import Module
from bag.design.database import ModuleDB


# noinspection PyPep8Naming
class bag_xbase_logic__xor(Module):
    """Module for library bag_xbase_logic cell xor.

    Fill in high level description here.
    """

    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'xor.yaml'))

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
            inv_params='inverter parameters',
            lch='transistor channel length',
            wn='NMOS width',
            wp='PMOS width',
            nfn_xor='xor nmos finger number',
            nfp_xor='xor pmos finger number',
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

    def design(self, inv_params, lch, wn, wp, nfn_xor, nfp_xor, intent, dum_info):
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

        inv_params.update(dict(dum_info=None))
        self.instances['XINV0'].design(**inv_params)
        self.instances['XINV1'].design(**inv_params)

        self.instances['XN0'].design(w=wn, l=lch, nf=nfn_xor, intent=intent)
        self.instances['XN1'].design(w=wn, l=lch, nf=nfn_xor, intent=intent)
        self.instances['XN2'].design(w=wn, l=lch, nf=nfn_xor, intent=intent)
        self.instances['XN3'].design(w=wn, l=lch, nf=nfn_xor, intent=intent)
        self.instances['XP0'].design(w=wp, l=lch, nf=nfp_xor, intent=intent)
        self.instances['XP1'].design(w=wp, l=lch, nf=nfp_xor, intent=intent)
        self.instances['XP2'].design(w=wp, l=lch, nf=nfp_xor, intent=intent)
        self.instances['XP3'].design(w=wp, l=lch, nf=nfp_xor, intent=intent)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')


