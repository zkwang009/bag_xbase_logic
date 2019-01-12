# -*- coding: utf-8 -*-

from typing import Dict

import os
import pkg_resources

from bag.design import Module


yaml_file = pkg_resources.resource_filename(__name__, os.path.join('netlist_info', 'clk_cell_array.yaml'))


# noinspection PyPep8Naming
class bag_xbase_logic__clk_cell_array(Module):
    """Module for library xbase_logic_templates cell clk_cell_array.

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
            nf_inv='inverter NMOS finger number',
            nf_tinv0='tri-inverter0 NMOS finger number',
            nf_tinv1='tri-inverter1 PMOS finger number',
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

    def design(self, pi_res, lch, wn, wp, nf_inv, nf_tinv0, nf_tinv1,
               intent, dum_info, **kwargs):
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
        for i in range(quad_res):
            ctrl_pin = 'ctrl<{}>'.format(i)
            ctrlb_pin = 'ctrlb<{}>'.format(i)
            clki_pin = 'clk_i'
            clko_pin = 'clko'
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            clk_ib_pin = 'clk_m{}'.format(4*i+1)
            ns_pin = 'ns_{}'.format(4*i+1)
            ps_pin = 'ps_{}'.format(4*i+1)
            term_list.append({'ctrl': ctrl_pin, 'ctrl_b': ctrlb_pin, 'clki': clki_pin, 'clko': clko_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin, 'clk_ib': clk_ib_pin, 'ns': ns_pin, 'ps': ps_pin})
            name_list.append('XCLKI{}'.format(i))

        # Q path
        for i in range(quad_res):
            ctrl_pin = 'ctrl<{}>'.format(i + quad_res)
            ctrlb_pin = 'ctrlb<{}>'.format(i + quad_res)
            clki_pin = 'clk_q'
            clko_pin = 'clko'
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            clk_ib_pin = 'clk_m{}'.format(4*i+2)
            ns_pin = 'ns_{}'.format(4*i+2)
            ps_pin = 'ps_{}'.format(4*i+2)
            term_list.append({'ctrl': ctrl_pin, 'ctrl_b': ctrlb_pin, 'clki': clki_pin, 'clko': clko_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin, 'clk_ib': clk_ib_pin, 'ns': ns_pin, 'ps': ps_pin})
            name_list.append('XCLKQ{}'.format(i))

        # IB path
        for i in range(quad_res):
            ctrl_pin = 'ctrl<{}>'.format(i + 2 * quad_res)
            ctrlb_pin = 'ctrlb<{}>'.format(i + 2 * quad_res)
            clki_pin = 'clk_ib'
            clko_pin = 'clko'
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            clk_ib_pin = 'clk_m{}'.format(4*i+3)
            ns_pin = 'ns_{}'.format(4*i+3)
            ps_pin = 'ps_{}'.format(4*i+3)
            term_list.append({'ctrl': ctrl_pin, 'ctrl_b': ctrlb_pin, 'clki': clki_pin, 'clko': clko_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin, 'clk_ib': clk_ib_pin, 'ns': ns_pin, 'ps': ps_pin})
            name_list.append('XCLKIB{}'.format(i))

        # QB path
        for i in range(quad_res):
            ctrl_pin = 'ctrl<{}>'.format(i + 3 * quad_res)
            ctrlb_pin = 'ctrlb<{}>'.format(i + 3 * quad_res)
            clki_pin = 'clk_qb'
            clko_pin = 'clko'
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            clk_ib_pin = 'clk_m{}'.format(4 * i + 4)
            ns_pin = 'ns_{}'.format(4 * i + 4)
            ps_pin = 'ps_{}'.format(4 * i + 4)
            term_list.append({'ctrl': ctrl_pin, 'ctrl_b': ctrlb_pin, 'clki': clki_pin, 'clko': clko_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin, 'clk_ib': clk_ib_pin, 'ns': ns_pin, 'ps': ps_pin})
            name_list.append('XCLKQB{}'.format(i))

        # generate clk_cell array
        self.array_instance('XCLK', name_list, term_list=term_list)
        for inst in self.instances['XCLK']:
            inst.design(lch=lch, wn=wn, wp=wp, nf_inv=nf_inv, nf_tinv0=nf_tinv0, nf_tinv1=nf_tinv1,
                        intent=intent)

        # dummy
        name_list = []
        term_list = []
        dum_list = [0, pi_res+1]
        for i in dum_list:
            ctrl_pin = 'VSS'
            ctrlb_pin = 'VDD'
            clki_pin = 'VSS'
            clko_pin = 'clkd<{}>'.format(i)
            vdd_pin = 'VDD'
            vss_pin = 'VSS'
            clk_ib_pin = 'clk_md{}'.format(i)
            ns_pin = 'ns_d_{}'.format(i)
            ps_pin = 'ps_d_{}'.format(i)
            term_list.append({'ctrl': ctrl_pin, 'ctrl_b': ctrlb_pin, 'clki': clki_pin, 'clko': clko_pin,
                              'VDD': vdd_pin, 'VSS': vss_pin, 'clk_ib': clk_ib_pin, 'ns': ns_pin, 'ps': ps_pin})
            name_list.append('XDUM{}'.format(i))
        # generate dummy
        self.array_instance('XDUM', name_list, term_list=term_list)
        for inst in self.instances['XDUM']:
            inst.design(lch=lch, wn=wn, wp=wp, nf_inv=nf_inv, nf_tinv0=nf_tinv0, nf_tinv1=nf_tinv1,
                        intent=intent)

        # rename pins
        self.rename_pin('ctrl', 'ctrl<{}:0>'.format(pi_res - 1))
        self.rename_pin('ctrlb', 'ctrlb<{}:0>'.format(pi_res - 1))

        # dummy
        self.design_dummy_transistors(dum_info, 'MOSDUM', 'VDD', 'VSS')

