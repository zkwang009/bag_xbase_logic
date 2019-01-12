# -*- coding: utf-8 -*-

from typing import Dict, Any

import os
import pkg_resources

from bag.design.module import Module
from bag.design.database import ModuleDB


# noinspection PyPep8Naming
class bag_xbase_logic__buffer(Module):
    """Module for library bag_xbase_logic cell buffer.

    Fill in high level description here.
    """

    yaml_file = pkg_resources.resource_filename(__name__,
                                                os.path.join('netlist_info',
                                                             'buffer.yaml'))

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
            nf_invx='invx figner nubmer',
            nf_inv0='inv0 finger number',
            nf_inv1='inv1 finger number',
            intent='transistor threshold',
            dum_info='dummy information',
            invert='True to have 3 stages, instead of 2',
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
            invert=False,
        )

    def design(self, lch, wn, wp, nf_invx, nf_inv0, nf_inv1, intent, dum_info, invert, **kwargs):
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

        self.instances['XINVX'].design(lch=lch, wn=wn, wp=wp, nfn=nf_invx, nfp=nf_invx,
                                       intent=intent, dum_info=None)
        self.instances['XINV0'].design(lch=lch, wn=wn, wp=wp, nfn=nf_inv0, nfp=nf_inv0,
                                       intent=intent, dum_info=None)
        self.instances['XINV1'].design(lch=lch, wn=wn, wp=wp, nfn=nf_inv1, nfp=nf_inv1,
                                       intent=intent, dum_info=None)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')

        if not invert:
            self.delete_instance('XINVX')
            self.reconnect_instance_terminal('XINV0', 'in', 'data')
