# -*- coding: utf-8 -*-


from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# noinspection PyUnresolvedReferences,PyCompatibility
from builtins import *

import bag
import math

from bag.layout.routing import TrackID

from abs_templates_ec.analog_core import AnalogBase, AnalogBaseInfo
from bag.layout.util import BBox
from typing import Union


class ClkCell(AnalogBase):
    """A differential NMOS passgate track-and-hold circuit with clock driver.

    This template is mainly used for ADC purposes.

    Parameters
    ----------
    temp_db : :class:`bag.layout.template.TemplateDB`
            the template database.
    lib_name : str
        the layout library name.
    params : dict[str, any]
        the parameter values.
    used_names : set[str]
        a set of already used cell names.
    kwargs : dict[str, any]
        dictionary of optional parameters.  See documentation of
        :class:`bag.layout.template.TemplateBase` for details.
    """

    def __init__(self, temp_db, lib_name, params, used_names, **kwargs):
        AnalogBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
        self._sch_params = None

    @property
    def sch_params(self):
        return self._sch_params

    @classmethod
    def get_params_info(cls):
        """Returns a dictionary containing parameter descriptions.

        Override this method to return a dictionary from parameter names to descriptions.

        Returns
        -------
        param_info : dict[str, str]
            dictionary from parameter name to description.
        """
        return dict(
            lch='transistor channel length',
            wn='NMOS width',
            wp='PMOS width',
            nfn_inv='inv NMOS finger number',
            nfp_inv='inv PMOS finger number',
            nfn_tinv0='tinv NMOS finger number',
            nfn_tinv1='tinv switch NMOS finger number',
            nfp_tinv0='tinv PMOS finger number',
            nfp_tinv1='tinv switch PMOS finger number',
            intent='transistor threshold',
            ndum='dummy finger number between different transistors',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            show_pins='True to draw pins.',
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
            rename_dict={},
            show_pins=False,
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper()

    def _draw_layout_helper(self, **kwargs):
        """Draw the layout of a transistor for characterization.
        Notes
        -------
        The number of fingers are for only half (or one side) of the tank.
        Total number should be 2x
        """

        lch = self.params['lch']
        wn = self.params['wn']
        wp = self.params['wp']
        nfn_inv = self.params['nfn_inv']
        nfp_inv = self.params['nfp_inv']
        nfn_tinv0 = self.params['nfn_tinv0']
        nfp_tinv0 = self.params['nfp_tinv0']
        nfn_tinv1 = self.params['nfn_tinv1']
        nfp_tinv1 = self.params['nfp_tinv1']
        ndum = self.params['ndum']
        intent = self.params['intent']
        ptap_w = self.params['ptap_w']
        ntap_w = self.params['ntap_w']
        g_width_ntr = self.params['g_width_ntr']
        ds_width_ntr = self.params['ds_width_ntr']
        show_pins = self.params['show_pins']

        # get resolution
        res = self.grid.resolution

        # make sure all fingers are even number
        if nfn_inv%2 != 0 or nfp_inv%2 != 0 or nfn_tinv0%2 != 0 or nfn_tinv1%2 != 0 or\
            nfp_tinv0%2 != 0 or nfp_tinv1%2 != 0:
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        fg_tot = ndum*4 + max(nfn_inv, nfp_inv) + max(nfn_tinv0, nfp_tinv0) + max(nfn_tinv1, nfp_tinv1)

        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr]
        pg_tracks = [g_width_ntr]
        nds_tracks = [ds_width_ntr*2]
        pds_tracks = [ds_width_ntr*2]
        n_orientation = ['R0']
        p_orientation = ['MX']

        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list,
                       nth_list, pw_list, pth_list,
                       ng_tracks=ng_tracks, nds_tracks=nds_tracks,
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       n_orientations=n_orientation, p_orientations=p_orientation,
                       )

        # get gate and drain index
        ngate_id = self.make_track_id('nch', 0, 'g', 0, width=g_width_ntr)
        pgate_id = self.make_track_id('pch', 0, 'g', 0, width=g_width_ntr)
        out_id = self.make_track_id('nch', 0, 'ds', 1, width=ds_width_ntr)
        ndrain_id = self.make_track_id('nch', 0, 'ds', 0, width=ds_width_ntr)
        pdrain_id = self.make_track_id('pch', 0, 'ds', 0, width=ds_width_ntr)

        # Step1: connect inverter
        # group transistors
        inv_n_ports = self.draw_mos_conn('nch', 0, ndum, nfn_inv, 1, 1)
        inv_p_ports = self.draw_mos_conn('pch', 0, ndum, nfp_inv, 1, 1)

        # connect gate
        ng_inv_warr = self.connect_to_tracks(inv_n_ports['g'], ngate_id)
        pg_inv_warr = self.connect_to_tracks(inv_p_ports['g'], pgate_id)
        # connect gate vertically
        vgate_idx = self.grid.coord_to_nearest_track(m5v_layer, ng_inv_warr.lower)
        vgate_tid = TrackID(m5v_layer, vgate_idx)
        inv_in_warr = self.connect_to_tracks([ng_inv_warr, pg_inv_warr], vgate_tid)
        # connect drain
        inv_d_warr = self.connect_to_tracks([inv_n_ports['d'], inv_p_ports['d']], out_id)
        # connect gate
        self.connect_to_substrate('ptap', inv_n_ports['s'])
        self.connect_to_substrate('ntap', inv_p_ports['s'])

        # Step2: connect tri-inverter
        nf_inv = max(nfn_inv, nfp_inv)
        nf_tinv0 = max(nfn_tinv0, nfp_tinv0)
        # group transistors
        tinv0_n_ports = self.draw_mos_conn('nch', 0, nf_inv+2*ndum, nfn_tinv0, 1, 1)
        tinv0_p_ports = self.draw_mos_conn('pch', 0, nf_inv+2*ndum, nfp_tinv0, 1, 1)
        tinv1_n_ports = self.draw_mos_conn('nch', 0, nf_tinv0+nf_inv+3*ndum, nfn_tinv1, 1, 1)
        tinv1_p_ports = self.draw_mos_conn('pch', 0, nf_tinv0+nf_inv+3*ndum, nfp_tinv1, 1, 1)

        # connect top/bottom MOSs
        # connect gate
        ng_tinv0_warr = self.connect_to_tracks(tinv0_n_ports['g'], ngate_id)
        pg_tinv0_warr = self.connect_to_tracks(tinv0_p_ports['g'], pgate_id)
        # connect gate vertically
        vgate_idx = self.grid.coord_to_nearest_track(m5v_layer, ng_tinv0_warr.lower)
        vgate_tid = TrackID(m5v_layer, vgate_idx)
        # also connect inverter drain
        tinv0_g_warr = self.connect_to_tracks([inv_d_warr, ng_tinv0_warr, pg_tinv0_warr], vgate_tid)

        # connect middle MOSs
        ng_tinv1_warr = self.connect_to_tracks(tinv1_n_ports['g'], ngate_id)
        pg_tinv1_warr = self.connect_to_tracks(tinv1_p_ports['g'], pgate_id)
        # connect source
        ns_tinv0_warr = self.connect_to_tracks([tinv0_n_ports['d'], tinv1_n_ports['s']], ndrain_id)
        ps_tinv0_warr = self.connect_to_tracks([tinv0_p_ports['d'], tinv1_p_ports['s']], pdrain_id)
        # connect drain
        tinv_out_warr = self.connect_to_tracks([tinv1_n_ports['d'], tinv1_p_ports['d']], out_id)
        # connect source
        self.connect_to_substrate('ptap', tinv0_n_ports['s'])
        self.connect_to_substrate('ntap', tinv0_p_ports['s'])

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy()

        # add pins
        self.add_pin('clk_i', inv_in_warr)
        self.add_pin('clk_o', tinv_out_warr)
        self.add_pin('ctrl', ng_tinv1_warr)
        self.add_pin('ctrl_b', pg_tinv1_warr)

        # export supplies
        self.add_pin(self.get_pin_name('VSS'), ptap_wire_arrs, show=show_pins)
        self.add_pin(self.get_pin_name('VDD'), ntap_wire_arrs, show=show_pins)

        # get size
        self.size = self.set_size_from_array_box(m5v_layer)

        # get schematic parameters
        dum_info = self.get_sch_dummy_info()
        dum_nmos = dum_info[0][1]
        dum_pmos = dum_info[1][1]
        print(dum_info)
        self._sch_params = dict(
            lch=self.params['lch'],
            wn=self.params['wn'],
            wp=self.params['wp'],
            nf_inv=self.params['nfn_inv'],
            nfp_inv=self.params['nfp_inv'],
            nfn_tinv0=self.params['nfn_tinv0'],
            nfp_tinv0=self.params['nfp_tinv0'],
            nfn_tinv1=self.params['nfn_tinv1'],
            nfp_tinv1=self.params['nfp_tinv1'],
            intent=self.params['intent'],
            dum_n0=dum_nmos-2,
            dum_n1=2,
            dum_p0=dum_pmos-2,
            dum_p1=2,
        )


