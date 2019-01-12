# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', '2to1mux.yaml'))


# noinspection PyPep8Naming
class bag_xbase_logic__2to1mux(Module):
    """Module for library xbase_logic_templates cell 2to1mux.

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
            lch='transistor channel length',
            wn='NMOS width',
            wp='PMOS width',
            nf_inv0='inv0 finger number',
            nf_tinv_0='tinv MOS0 finger number',
            nf_tinv_1='tinv MOS1 finger number',
            nf_inv2='inv2 finger number',
            intent='transistor threshold',
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
            dum_info=None,
        )

    def design(self, lch, wn, wp, nf_inv0, nf_tinv_0, nf_tinv_1, nf_inv2, intent,
               dum_info, **kwargs):
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
        self.instances['INV0'].design(lch=lch, wn=wn, wp=wp, nfn=nf_inv0, nfp=nf_inv0, intent=intent, dum_info=None)
        self.instances['INV1'].design(lch=lch, wn=wn, wp=wp, nfn=nf_inv0, nfp=nf_inv0, intent=intent, dum_info=None)
        self.instances['INV2'].design(lch=lch, wn=wn, wp=wp, nfn=nf_inv2, nfp=nf_inv2, intent=intent, dum_info=None)

        self.instances['TINV0'].design(lch=lch, wn=wn, wp=wp, nfn0=nf_tinv_0, nfn1=nf_tinv_1,
                                       nfp0=nf_tinv_0, nfp1=nf_tinv_1, intent=intent, dum_info=None)
        self.instances['TINV1'].design(lch=lch, wn=wn, wp=wp, nfn0=nf_tinv_0, nfn1=nf_tinv_1,
                                       nfp0=nf_tinv_0, nfp1=nf_tinv_1, intent=intent, dum_info=None)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')
