# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'multi_mux.yaml'))


# noinspection PyPep8Naming
class bag_xbase_logic__multi_mux(Module):
    """Module for library xbase_logic_templates cell mult_mux.

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
            mux_stage='number of mux stage',
            n_dum='number of dummy cells',
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
               mux_stage, n_dum, dum_info, **kwargs):
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

        for stage in range(mux_stage):
            for j in range(2**stage):
                if stage == mux_stage-1:
                    i0_pin = 'i<{}>'.format(j*2)
                    i1_pin = 'i<{}>'.format(j*2+1)
                else:
                    i0_pin = 'o{}_{}'.format(stage+1, 2*j)
                    i1_pin = 'o{}_{}'.format(stage+1, 2*j+1)
                vdd_pin = 'VDD'
                vss_pin = 'VSS'
                if stage == 0:
                    o_pin = 'o'
                else:
                    o_pin = 'o{}_{}'.format(stage, j)
                sel_pin = 'sel<{}>'.format(stage)

                term_list.append({'i0': i0_pin, 'i1': i1_pin, 'o': o_pin,
                                  'sel': sel_pin, 'VDD': vdd_pin, 'VSS': vss_pin})
                name_list.append('XMUX{}_{}'.format(stage, j))

        self.array_instance('XMUX', name_list, term_list=term_list)
        for inst in self.instances['XMUX']:
            inst.design(lch=lch, wn=wn, wp=wp, nf_inv0=nf_inv0, nf_tinv_0=nf_tinv_0,
                        nf_tinv_1=nf_tinv_1, nf_inv2=nf_inv2, intent=intent,
                        dum_info=dum_info)

        if n_dum == 0:
            self.delete_instance('XDUM')
        else:
            name_list = []
            term_list = []
            for i in range(n_dum):
                i0_pin = 'di0_{}'.format(i)
                i1_pin = 'di1_{}'.format(i)
                vdd_pin = 'VDD'
                vss_pin = 'VSS'
                o_pin = 'do_{}'.format(i)
                sel_pin = 'dsel{}'.format(i)

                term_list.append({'i0': i0_pin, 'i1': i1_pin, 'o': o_pin,
                                  'sel': sel_pin, 'VDD': vdd_pin, 'VSS': vss_pin})
                name_list.append('XDUM{}'.format(i))

            self.array_instance('XDUM', name_list, term_list=term_list)
            for inst in self.instances['XDUM']:
                inst.design(lch=lch, wn=wn, wp=wp, nf_inv0=nf_inv0, nf_tinv_0=nf_tinv_0,
                            nf_tinv_1=nf_tinv_1, nf_inv2=nf_inv2, intent=intent,
                            dum_info=dum_info)

        self.rename_pin('i', 'i<{}:0>'.format(2**mux_stage-1))
        self.rename_pin('sel', 'sel<{}:0>'.format(mux_stage-1))
