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


class XNOR(AnalogBase):
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
            nf_inv='inv finger number',
            nf_xnor='xnor finger number',
            intent='transistor threshold',
            ndum='dummy finger number between different transistors',
            ndum_side='dummy finger number between different transistors',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            g_space='gate space in nubmer of tracks',
            ds_space='drain souce space in number of tracks',
            show_pins='True to draw pins.',
            debug='True to see inner nodes',
            power_width_ntr='power width in number of tracks',
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
            debug=True,
            g_space=0,
            ds_space=0,
            power_width_ntr=None,
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, lch, wn, wp, nf_inv, nf_xnor, ptap_w, ntap_w,
                            g_width_ntr, ds_width_ntr, intent, ndum, ndum_side,
                            g_space, ds_space, show_pins,
                            power_width_ntr,
                            debug, **kwargs):
        """Draw the layout of a transistor for characterization.
        Notes
        -------
        The number of fingers are for only half (or one side) of the tank.
        Total number should be 2x
        """

        # TODO: assumption1 -- all nmos/pmos have same finger number
        # TODO: assumption2 -- all nmos/pmos finger number are even

        # get resolution
        res = self.grid.resolution

        # make sure all fingers are even number
        if nf_inv%2 != 0 or nf_xnor%2 != 0:
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        fg_tot = ndum_side*2 + ndum*5 + nf_inv*2 + nf_xnor*4

        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr * 3 + g_sp_ntr + g_space]
        pg_tracks = [g_width_ntr * 3 + g_sp_ntr + g_space]
        nds_tracks = [ds_width_ntr*2 + ds_space]
        pds_tracks = [ds_width_ntr*2 + ds_space]
        n_orientation = ['R0']
        p_orientation = ['MX']

        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list,
                       nth_list, pw_list, pth_list,
                       ng_tracks=ng_tracks, nds_tracks=nds_tracks,
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       n_orientations=n_orientation, p_orientations=p_orientation,
                       )

        # get gate and drain index
        a_id = self.make_track_id('nch', 0, 'g', 0, width=1)
        ab_id = self.make_track_id('nch', 0, 'g', 1, width=1)
        b_id = self.make_track_id('pch', 0, 'g', 0, width=1)
        bb_id = self.make_track_id('pch', 0, 'g', 1, width=1)
        ngate_id = self.make_track_id('nch', 0, 'g', 2, width=1)
        pgate_id = self.make_track_id('pch', 0, 'g', 2, width=1)
        nout_id = self.make_track_id('nch', 0, 'ds', 0, width=1)
        pout_id = self.make_track_id('pch', 0, 'ds', 0, width=1)
        out_id = self.make_track_id('nch', 0, 'ds', 1, width=1)

        # Step1: connect inverter
        # group transistors
        # inv0
        inv0_n_ports = self.draw_mos_conn('nch', 0, ndum_side, nf_inv, 1, 1,
                                          s_net='VSS', d_net='a_b')
        inv0_p_ports = self.draw_mos_conn('pch', 0, ndum_side, nf_inv, 1, 1,
                                          s_net='VDD', d_net='a_b')
        # inv1
        inv1_n_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum+nf_inv,
                                          nf_inv, 1, 1, s_net='VSS', d_net='b_b')
        inv1_p_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum+nf_inv,
                                          nf_inv, 1, 1, s_net='VDD', d_net='b_b')
        # xnor logic
        xnor0_n_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum*2+nf_inv*2,
                                          nf_xnor, 1, 1, s_net='VSS', d_net='ns0')
        xnor0_p_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum*2+nf_inv*2,
                                          nf_xnor, 1, 1, s_net='VDD', d_net='ps0')
        xnor1_n_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum*3+nf_inv*2+nf_xnor,
                                          nf_xnor, 1, 1, s_net='ns0', d_net='o')
        xnor1_p_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum*3+nf_inv*2+nf_xnor,
                                          nf_xnor, 1, 1, s_net='ps0', d_net='o')
        xnor2_n_ports = self.draw_mos_conn('nch', 0, ndum_side + ndum * 4 + nf_inv * 2 + nf_xnor * 2,
                                          nf_xnor, 1, 1, s_net='VSS', d_net='ns1')
        xnor2_p_ports = self.draw_mos_conn('pch', 0, ndum_side + ndum * 4 + nf_inv * 2 + nf_xnor * 2,
                                          nf_xnor, 1, 1, s_net='VDD', d_net='ps1')
        xnor3_n_ports = self.draw_mos_conn('nch', 0, ndum_side + ndum * 5 + nf_inv * 2 + nf_xnor * 3,
                                          nf_xnor, 1, 1, s_net='ns1', d_net='o')
        xnor3_p_ports = self.draw_mos_conn('pch', 0, ndum_side + ndum * 5 + nf_inv * 2 + nf_xnor * 3,
                                          nf_xnor, 1, 1, s_net='ps1', d_net='o')

        # connect inv2, inv3 (clock buffers)
        # inv0
        inv0_gn_warr = self.connect_to_tracks(inv0_n_ports['g'], ngate_id, min_len_mode=0)
        inv0_gp_warr = self.connect_to_tracks(inv0_p_ports['g'], pgate_id, min_len_mode=0)
        inv0_g_idx = self.grid.coord_to_nearest_track(inv0_gn_warr.layer_id + 1, inv0_gn_warr.lower)
        inv0_g_tid = TrackID(inv0_gn_warr.layer_id + 1, inv0_g_idx)
        a = self.connect_to_tracks([inv0_gn_warr, inv0_gp_warr], inv0_g_tid)

        inv0_dn_warr = self.connect_to_tracks(inv0_n_ports['d'], nout_id, min_len_mode=0)
        inv0_dp_warr = self.connect_to_tracks(inv0_p_ports['d'], pout_id, min_len_mode=0)
        inv0_d_idx = self.grid.coord_to_nearest_track(inv0_dn_warr.layer_id + 1, inv0_dn_warr.upper)
        inv0_d_tid = TrackID(inv0_dn_warr.layer_id + 1, inv0_d_idx)
        a_b = self.connect_to_tracks([inv0_dn_warr, inv0_dp_warr], inv0_d_tid)
        
        self.connect_to_substrate('ptap', inv0_n_ports['s'])
        self.connect_to_substrate('ntap', inv0_p_ports['s'])

        # inv1
        inv1_gn_warr = self.connect_to_tracks(inv1_n_ports['g'], ngate_id, min_len_mode=0)
        inv1_gp_warr = self.connect_to_tracks(inv1_p_ports['g'], pgate_id, min_len_mode=0)
        inv1_g_idx = self.grid.coord_to_nearest_track(inv1_gn_warr.layer_id + 1, inv1_gn_warr.lower)
        inv1_g_tid = TrackID(inv1_gn_warr.layer_id + 1, inv1_g_idx)
        b = self.connect_to_tracks([inv1_gn_warr, inv1_gp_warr], inv1_g_tid)

        inv1_dn_warr = self.connect_to_tracks(inv1_n_ports['d'], nout_id, min_len_mode=0)
        inv1_dp_warr = self.connect_to_tracks(inv1_p_ports['d'], pout_id, min_len_mode=0)
        inv1_d_idx = self.grid.coord_to_nearest_track(inv1_dn_warr.layer_id + 1, inv1_dn_warr.upper)
        inv1_d_tid = TrackID(inv1_dn_warr.layer_id + 1, inv1_d_idx)
        b_b = self.connect_to_tracks([inv1_dn_warr, inv1_dp_warr], inv1_d_tid)

        self.connect_to_substrate('ptap', inv1_n_ports['s'])
        self.connect_to_substrate('ntap', inv1_p_ports['s'])

        # xnor MOSs
        xnor0_gn_warr = self.connect_to_tracks(xnor0_n_ports['g'], ngate_id, min_len_mode=0)
        xnor0_gn_idx = self.grid.coord_to_nearest_track(xnor0_gn_warr.layer_id + 1, xnor0_gn_warr.lower)
        xnor0_gn_tid = TrackID(xnor0_gn_warr.layer_id + 1, xnor0_gn_idx)
        xnor0_n = self.connect_to_tracks(xnor0_gn_warr, xnor0_gn_tid)
        
        xnor0_gp_warr = self.connect_to_tracks(xnor0_p_ports['g'], pgate_id, min_len_mode=0)
        xnor0_gp_idx = self.grid.coord_to_nearest_track(xnor0_gp_warr.layer_id + 1, xnor0_gp_warr.upper)
        xnor0_gp_tid = TrackID(xnor0_gp_warr.layer_id + 1, xnor0_gp_idx)
        xnor0_p = self.connect_to_tracks(xnor0_gp_warr, xnor0_gp_tid)
        
        xnor1_gn_warr = self.connect_to_tracks(xnor1_n_ports['g'], ngate_id, min_len_mode=0)
        xnor1_gn_idx = self.grid.coord_to_nearest_track(xnor1_gn_warr.layer_id + 1, xnor1_gn_warr.lower)
        xnor1_gn_tid = TrackID(xnor1_gn_warr.layer_id + 1, xnor1_gn_idx)
        xnor1_n = self.connect_to_tracks(xnor1_gn_warr, xnor1_gn_tid)
        
        xnor1_gp_warr = self.connect_to_tracks(xnor1_p_ports['g'], pgate_id, min_len_mode=0)
        xnor1_gp_idx = self.grid.coord_to_nearest_track(xnor1_gp_warr.layer_id + 1, xnor1_gp_warr.upper)
        xnor1_gp_tid = TrackID(xnor1_gp_warr.layer_id + 1, xnor1_gp_idx)
        xnor1_p = self.connect_to_tracks(xnor1_gp_warr, xnor1_gp_tid)
        
        xnor2_gn_warr = self.connect_to_tracks(xnor2_n_ports['g'], ngate_id, min_len_mode=0)
        xnor2_gn_idx = self.grid.coord_to_nearest_track(xnor2_gn_warr.layer_id + 1, xnor2_gn_warr.lower)
        xnor2_gn_tid = TrackID(xnor2_gn_warr.layer_id + 1, xnor2_gn_idx)
        xnor2_n = self.connect_to_tracks(xnor2_gn_warr, xnor2_gn_tid)
        
        xnor2_gp_warr = self.connect_to_tracks(xnor2_p_ports['g'], pgate_id, min_len_mode=0)
        xnor2_gp_idx = self.grid.coord_to_nearest_track(xnor2_gp_warr.layer_id + 1, xnor2_gp_warr.upper)
        xnor2_gp_tid = TrackID(xnor2_gp_warr.layer_id + 1, xnor2_gp_idx)
        xnor2_p = self.connect_to_tracks(xnor2_gp_warr, xnor2_gp_tid)
        
        xnor3_gn_warr = self.connect_to_tracks(xnor3_n_ports['g'], ngate_id, min_len_mode=0)
        xnor3_gn_idx = self.grid.coord_to_nearest_track(xnor3_gn_warr.layer_id + 1, xnor3_gn_warr.lower)
        xnor3_gn_tid = TrackID(xnor3_gn_warr.layer_id + 1, xnor3_gn_idx)
        xnor3_n = self.connect_to_tracks(xnor3_gn_warr, xnor3_gn_tid)
        
        xnor3_gp_warr = self.connect_to_tracks(xnor3_p_ports['g'], pgate_id, min_len_mode=0)
        xnor3_gp_idx = self.grid.coord_to_nearest_track(xnor3_gp_warr.layer_id + 1, xnor3_gp_warr.upper)
        xnor3_gp_tid = TrackID(xnor3_gp_warr.layer_id + 1, xnor3_gp_idx)
        xnor3_p = self.connect_to_tracks(xnor3_gp_warr, xnor3_gp_tid)

        # connect a, a_b, b, b_b
        self.connect_to_tracks([a, xnor0_p, xnor2_n], a_id)
        self.connect_to_tracks([a_b, xnor1_n, xnor2_p], ab_id)
        self.connect_to_tracks([b, xnor1_p, xnor0_n], b_id)
        self.connect_to_tracks([b_b, xnor3_p, xnor3_n], bb_id)

        self.connect_to_tracks([xnor0_n_ports['d'], xnor1_n_ports['s']], nout_id)
        self.connect_to_tracks([xnor0_p_ports['d'], xnor1_p_ports['s']], pout_id)
        self.connect_to_tracks([xnor2_n_ports['d'], xnor3_n_ports['s']], nout_id)
        self.connect_to_tracks([xnor2_p_ports['d'], xnor3_p_ports['s']], pout_id)

        o = self.connect_to_tracks([xnor1_n_ports['d'], xnor1_p_ports['d'], xnor3_n_ports['d'],
                                    xnor3_p_ports['d']], out_id)

        self.connect_to_substrate('ptap', [xnor0_n_ports['s'], xnor2_n_ports['s']])
        self.connect_to_substrate('ntap', [xnor0_p_ports['s'], xnor2_p_ports['s']])

        # add pins
        self.add_pin('A', a, show=show_pins)
        self.add_pin('B', b, show=show_pins)
        self.add_pin('O', o, show=show_pins)

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy(vdd_width=power_width_ntr, vss_width=power_width_ntr)

        # export supplies
        self.add_pin(self.get_pin_name('VSS'), ptap_wire_arrs, show=show_pins)
        self.add_pin(self.get_pin_name('VDD'), ntap_wire_arrs, show=show_pins)

        # get size
        self.size = self.grid.get_size_tuple(m5v_layer, width=self.bound_box.width, height=self.bound_box.height,
                                             round_up=True)

        # get schematic parameters
        dum_info = self.get_sch_dummy_info()

        self._sch_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv=nf_inv,
            nf_xnor=nf_xnor,
            intent=intent,
            dum_info=dum_info,
            debug=debug,
        )


