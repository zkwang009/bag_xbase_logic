# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'or_gate.yaml'))


# noinspection PyPep8Naming
class bag_xbase_logic__or_gate(Module):
    """Module for library xbase_logic_templates cell or_gate.

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
            nfn='NMOS finger number',
            nfp='PMOS finger number',
            nf_inv='inverter finger number',
            intent='transistor threshold',
            dum_info='dummy info',
            debug='True to have ns pin'
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

    def design(self, lch, wn, wp, nfn, nfp, nf_inv, intent, dum_info, debug, **kwargs):
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
        self.instances['XN0'].design(w=wn, l=lch, nf=nfn, intent=intent)
        self.instances['XN1'].design(w=wn, l=lch, nf=nfn, intent=intent)
        self.instances['XN2'].design(w=wn, l=lch, nf=nf_inv, intent=intent)

        self.instances['XP0'].design(w=wp, l=lch, nf=nfp, intent=intent)
        self.instances['XP1'].design(w=wp, l=lch, nf=nfp, intent=intent)
        self.instances['XP2'].design(w=wp, l=lch, nf=nf_inv, intent=intent)

        self.design_dummy_transistors(dum_info, 'XDUM', 'VDD', 'VSS')
        if debug is False:
            self.remove_pin('ps')
            self.remove_pin('o_b')
