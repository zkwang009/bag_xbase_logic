# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'ctrl_buf_array.yaml'))


# noinspection PyPep8Naming
class bag_xbase_logic__ctrl_buf_array(Module):
    """Module for library xbase_logic_templates cell ctrl_buf_array.

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
            pi_res='phase interpolator resolution',
            lch='transistor channel length',
            wn='inverter0 NMOS width',
            wp='inverter0 PMOS width',
            nf_inv0='inverter0 NMOS finger number',
            nf_inv1='inverter1 NMOS finger number',
            intent='transistor threshold',
            dum_info='dummy information',
        )

    def design(self, pi_res, lch, wn, wp, nf_inv0, nf_inv1, intent, dum_info):
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
        if pi_res % 4 != 0:
            raise ValueError("Need pi_res divisible by 4!")

        quad_res = int(pi_res / 4)

        # unit array
        # I path
        name_list = []
        term_list = []
        for i in range(pi_res):
            data_pin = 'ctrl<{}>'.format(i)
            data_o_pin = 'ctrl_o<{}>'.format(i)
            data_ob_pin = 'ctrl_ob<{}>'.format(i)
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            term_list.append({'data': data_pin, 'data_o': data_o_pin, 'data_ob': data_ob_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin})
            name_list.append('XBUF{}'.format(i))

        # generate clk_cell array
        self.array_instance('XBUF', name_list, term_list=term_list)
        for inst in self.instances['XBUF']:
            inst.design(lch=lch, wn=wn, wp=wp, nf_inv0=nf_inv0, nf_inv1=nf_inv1,
                        intent=intent)

        # dummy
        name_list = []
        term_list = []
        dum_list = [0, pi_res+1]
        for i in dum_list:
            data_pin = 'VSS'.format(i)
            data_o_pin = 'ctrl_d_{}'.format(i)
            data_ob_pin = 'ctrl_db_{}'.format(i)
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            term_list.append({'data': data_pin, 'data_o': data_o_pin, 'data_ob': data_ob_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin})
            name_list.append('XBUF{}'.format(i))
        # generate dummy
        self.array_instance('XDUM', name_list, term_list=term_list)
        for inst in self.instances['XDUM']:
            inst.design(lch=lch, wn=wn, wp=wp, nf_inv0=nf_inv0, nf_inv1=nf_inv1,
                        intent=intent)

        # rename pins
        self.rename_pin('ctrl', 'ctrl<{}:0>'.format(pi_res - 1))
        self.rename_pin('ctrl_ob', 'ctrl_ob<{}:0>'.format(pi_res - 1))
        self.rename_pin('ctrl_o', 'ctrl_o<{}:0>'.format(pi_res - 1))

        # dummy
        self.design_dummy_transistors(dum_info, 'MOSDUM', 'VDD', 'VSS')
