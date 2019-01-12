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


class DFF(AnalogBase):
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
            nf_inv0='inv0 finger number',
            nf_inv1='inv1 finger number',
            nf_inv2='inv2 finger number',
            nf_inv3='inv3 finger number',
            nf_tinv0_0='tinv0 NMOS finger number',
            nf_tinv0_1='tinv0 NMOS finger number',
            nf_tinv1_0='tinv1 switch NMOS finger number',
            nf_tinv1_1='tinv0 NMOS finger number',
            nf_tinv2_0='tinv2 switch NMOS finger number',
            nf_tinv2_1='tinv0 NMOS finger number',
            nf_tinv3_0='tinv3 switch NMOS finger number',
            nf_tinv3_1='tinv0 NMOS finger number',
            intent='transistor threshold',
            ndum='dummy finger number between different transistors',
            ndum_side='dummy finger number between different transistors',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            show_pins='True to draw pins.',
            debug='True to see inner nodes',
            g_space='gate space in nubmer of tracks',
            ds_space='drain souce space in number of tracks',
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

    def _draw_layout_helper(self, lch, wn, wp, nf_inv0, nf_inv1, nf_inv2, nf_inv3,
                            nf_tinv0_0, nf_tinv0_1, nf_tinv1_0, nf_tinv1_1, nf_tinv2_0,
                            nf_tinv2_1, nf_tinv3_0, nf_tinv3_1, ptap_w, ntap_w,
                            g_width_ntr, ds_width_ntr, intent, ndum, ndum_side, show_pins,
                            g_space, ds_space, power_width_ntr,
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
        if nf_inv0%2 != 0 or nf_inv1%2 != 0 or nf_inv2%2 != 0 or nf_inv3%2 != 0 or \
            nf_tinv0_0%2 != 0 or nf_tinv1_0%2 != 0 or nf_tinv2_0%2 != 0 or nf_tinv3_0%2 != 0 or \
            nf_tinv0_1%2 != 0 or nf_tinv1_1%2 != 0 or nf_tinv2_1%2 != 0 or nf_tinv3_1%2 != 0:
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        fg_tot = ndum_side*2 + ndum*11 + nf_inv0 + nf_inv1 + nf_inv2 + nf_inv3 + \
                 nf_tinv0_0 + nf_tinv1_0 + nf_tinv2_0 + nf_tinv3_0 + \
                 nf_tinv0_1 + nf_tinv1_1 + nf_tinv2_1 + nf_tinv3_1 + 2

        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr * 2 + g_sp_ntr + g_space]
        pg_tracks = [g_width_ntr * 2 + g_sp_ntr + g_space]
        nds_tracks = [ds_width_ntr * 2 + ds_sp_ntr + ds_space]
        pds_tracks = [ds_width_ntr * 2 + ds_sp_ntr + ds_space]
        n_orientation = ['R0']
        p_orientation = ['MX']

        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list,
                       nth_list, pw_list, pth_list,
                       ng_tracks=ng_tracks, nds_tracks=nds_tracks,
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       n_orientations=n_orientation, p_orientations=p_orientation,
                       )

        # get gate and drain index
        ck_id = self.make_track_id('nch', 0, 'g', 0, width=1)
        ckb_id = self.make_track_id('pch', 0, 'g', 0, width=1)
        ngate_id = self.make_track_id('nch', 0, 'g', 1, width=1)
        pgate_id = self.make_track_id('pch', 0, 'g', 1, width=1)
        nout_id = self.make_track_id('nch', 0, 'ds', 1, width=1)
        pout_id = self.make_track_id('pch', 0, 'ds', 1, width=1)
        ndrain_id = self.make_track_id('nch', 0, 'ds', 0, width=1)
        pdrain_id = self.make_track_id('pch', 0, 'ds', 0, width=1)

        # Step1: connect inverter
        # group transistors
        # inv2
        inv2_n_ports = self.draw_mos_conn('nch', 0, ndum_side, nf_inv2, 1, 1,
                                          s_net='VSS', d_net='iclkb')
        inv2_p_ports = self.draw_mos_conn('pch', 0, ndum_side, nf_inv2, 1, 1,
                                          s_net='VDD', d_net='iclkb')
        # inv3
        inv3_n_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum+nf_inv2,
                                          nf_inv3, 1, 1, s_net='VSS', d_net='iclk')
        inv3_p_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum+nf_inv2,
                                          nf_inv3, 1, 1, s_net='VDD', d_net='iclk')
        # tinv0
        tinv0_n0_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum*2+nf_inv2+nf_inv3,
                                            nf_tinv0_0, 1, 1, s_net='VSS', d_net='tinv0_ns')
        tinv0_p0_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum*2+nf_inv2+nf_inv3,
                                            nf_tinv0_0, 1, 1, s_net='VDD', d_net='tinv0_ps')
        col_idx = ndum_side + ndum * 3 + nf_inv2 + nf_inv3 + nf_tinv0_0 + 2
        tinv0_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv0_1, 1, 1,
                                            s_net='tinv0_ns', d_net='mem1')
        tinv0_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv0_1, 1, 1,
                                            s_net='tinv0_ps', d_net='mem1')
        # inv0
        col_idx = ndum_side + ndum * 4 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + 2
        inv0_n_ports = self.draw_mos_conn('nch', 0, col_idx, nf_inv0, 1, 1,
                                            s_net='VSS', d_net='latch')
        inv0_p_ports = self.draw_mos_conn('pch', 0, col_idx, nf_inv0, 1, 1,
                                          s_net='VDD', d_net='latch')
        # tinv1
        col_idx = ndum_side + ndum * 5 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + nf_inv0 + 2
        tinv1_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv1_0, 1, 1,
                                          s_net='VSS', d_net='tinv1_ns')
        tinv1_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv1_0, 1, 1,
                                          s_net='VDD', d_net='tinv1_ps')
        col_idx = ndum_side + ndum * 6 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + nf_inv0 +\
                  nf_tinv1_0 + 2
        tinv1_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv1_1, 1, 1,
                                          s_net='tinv1_ns', d_net='mem1')
        tinv1_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv1_1, 1, 1,
                                          s_net='tinv1_ps', d_net='mem1')
        # tinv2
        col_idx = ndum_side + ndum * 7 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + nf_inv0 + \
                  nf_tinv1_0 + nf_tinv1_1 + 2
        tinv2_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv2_0, 1, 1,
                                           s_net='VSS', d_net='tinv2_ns')
        tinv2_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv2_0, 1, 1,
                                           s_net='VDD', d_net='tinv2_ps')
        col_idx = ndum_side + ndum * 8 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + nf_inv0 + \
                  nf_tinv1_0 + nf_tinv1_1 + nf_tinv2_0 + 2
        tinv2_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv2_1, 1, 1,
                                          s_net='tinv2_ns', d_net='mem2')
        tinv2_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv2_1, 1, 1,
                                          s_net='tinv2_ps', d_net='mem2')
        # inv1
        col_idx = ndum_side + ndum * 9 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + nf_inv0 + \
                  nf_tinv1_0 + nf_tinv1_1 + nf_tinv2_0 + nf_tinv2_1 + 2
        inv1_n_ports = self.draw_mos_conn('nch', 0, col_idx, nf_inv1, 1, 1,
                                          s_net='VSS', d_net='o')
        inv1_p_ports = self.draw_mos_conn('pch', 0, col_idx, nf_inv1, 1, 1,
                                          s_net='VDD', d_net='o')
        # tinv3
        col_idx = ndum_side + ndum * 10 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + nf_inv0 + \
                  nf_tinv1_0 + nf_tinv1_1 + nf_tinv2_0 + nf_tinv2_1 + nf_inv1 + 2
        tinv3_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv3_0, 1, 1,
                                            s_net='VSS', d_net='tinv3_ns')
        tinv3_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv3_0, 1, 1,
                                            s_net='VDD', d_net='tinv3_ps')
        col_idx = ndum_side + ndum * 11 + nf_inv2 + nf_inv3 + nf_tinv0_0 + nf_tinv0_1 + nf_inv0 + \
                  nf_tinv1_0 + nf_tinv1_1 + nf_tinv2_0 + nf_tinv2_1 + nf_inv1 + nf_tinv3_0 + 2
        tinv3_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv3_1, 1, 1,
                                            s_net='tinv3_ns', d_net='mem2')
        tinv3_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv3_1, 1, 1,
                                            s_net='tinv3_ps', d_net='mem2')

        # connect inv2, inv3 (clock buffers)
        # inv2
        inv2_n_warr = self.connect_to_tracks(inv2_n_ports['g'], ngate_id, min_len_mode=0)
        inv2_p_warr = self.connect_to_tracks(inv2_p_ports['g'], pgate_id, min_len_mode=0)
        inv2_idx = self.grid.coord_to_nearest_track(inv2_n_warr.layer_id + 1, inv2_n_warr.middle)
        inv2_tid = TrackID(inv2_n_warr.layer_id + 1, inv2_idx)
        clk = self.connect_to_tracks([inv2_n_warr, inv2_p_warr], inv2_tid)
        
        self.connect_to_substrate('ptap', inv2_n_ports['s'])
        self.connect_to_substrate('ntap', inv2_p_ports['s'])

        # inv3
        inv3_n_warr = self.connect_to_tracks(inv3_n_ports['g'], ngate_id, min_len_mode=0)
        inv3_p_warr = self.connect_to_tracks(inv3_p_ports['g'], pgate_id, min_len_mode=0)
        inv3_idx = self.grid.coord_to_nearest_track(inv3_n_warr.layer_id + 1, inv3_n_warr.middle)
        inv3_tid = TrackID(inv3_n_warr.layer_id + 1, inv3_idx)
        inv3_g_wire = self.connect_to_tracks([inv3_n_warr, inv3_p_warr], inv3_tid)
        self.connect_to_tracks([inv2_n_ports['d'], inv2_p_ports['d'], inv3_g_wire], pout_id)
        iclkb = inv3_g_wire

        self.connect_to_substrate('ptap', inv3_n_ports['s'])
        self.connect_to_substrate('ntap', inv3_p_ports['s'])

        inv3_d_wire = self.connect_to_tracks([inv3_n_ports['d'], inv3_p_ports['d']], nout_id, min_len_mode=0)
        iclk_idx = self.grid.coord_to_nearest_track(inv3_d_wire.layer_id+1, inv3_d_wire.lower)
        iclk_tid = TrackID(inv3_d_wire.layer_id+1, iclk_idx)
        iclk = self.connect_to_tracks(inv3_d_wire, iclk_tid)

        # tinv0
        i_n_warr = self.connect_to_tracks(tinv0_n0_ports['g'], ngate_id, min_len_mode=0)
        i_p_warr = self.connect_to_tracks(tinv0_p0_ports['g'], pgate_id, min_len_mode=0)
        i_idx = self.grid.coord_to_nearest_track(i_n_warr.layer_id + 1, i_n_warr.middle)
        i_tid = TrackID(i_n_warr.layer_id + 1, i_idx)
        i = self.connect_to_tracks([i_n_warr, i_p_warr], i_tid)
        
        self.connect_to_substrate('ptap', tinv0_n0_ports['s'])
        self.connect_to_substrate('ntap', tinv0_p0_ports['s'])

        self.connect_to_tracks([tinv0_n0_ports['d'], tinv0_n1_ports['s']], ndrain_id)
        self.connect_to_tracks([tinv0_p0_ports['d'], tinv0_p1_ports['s']], pdrain_id)

        # inv0
        inv0_gn_warr = self.connect_to_tracks(inv0_n_ports['g'], ngate_id, min_len_mode=0)
        inv0_gp_warr = self.connect_to_tracks(inv0_p_ports['g'], pgate_id, min_len_mode=0)
        inv0_g_idx = self.grid.coord_to_nearest_track(inv0_gn_warr.layer_id + 1, inv0_gn_warr.middle)
        inv0_g_tid = TrackID(inv0_gn_warr.layer_id + 1, inv0_g_idx)
        inv0_g = self.connect_to_tracks([inv0_gn_warr, inv0_gp_warr], inv0_g_tid)
        # mem1 = self.connect_to_tracks([tinv0_n1_ports['d'], tinv0_p1_ports['d'], inv0_g], nout_id)

        self.connect_to_substrate('ptap', inv0_n_ports['s'])
        self.connect_to_substrate('ntap', inv0_p_ports['s'])

        # tinv1
        tinv1_gn_warr = self.connect_to_tracks(tinv1_n0_ports['g'], ngate_id, min_len_mode=0)
        tinv1_gp_warr = self.connect_to_tracks(tinv1_p0_ports['g'], pgate_id, min_len_mode=0)
        tinv1_g_idx = self.grid.coord_to_nearest_track(tinv1_gn_warr.layer_id + 1, tinv1_gn_warr.middle)
        tinv1_g_tid = TrackID(tinv1_gn_warr.layer_id + 1, tinv1_g_idx)
        tinv1_g = self.connect_to_tracks([tinv1_gn_warr, tinv1_gp_warr], tinv1_g_tid)
        # latch = self.connect_to_tracks([inv0_n_ports['d'], inv0_p_ports['d'], tinv1_g], nout_id)

        self.connect_to_tracks([tinv1_n0_ports['d'], tinv1_n1_ports['s']], ndrain_id)
        self.connect_to_tracks([tinv1_p0_ports['d'], tinv1_p1_ports['s']], pdrain_id)

        self.connect_to_substrate('ptap', tinv1_n0_ports['s'])
        self.connect_to_substrate('ntap', tinv1_p0_ports['s'])

        mem1 = self.connect_to_tracks([tinv0_n1_ports['d'], tinv0_p1_ports['d'], inv0_g,
                                       tinv1_n1_ports['d'], tinv1_p1_ports['d']], pout_id)
        
        # tinv2
        tinv2_gn_warr = self.connect_to_tracks(tinv2_n0_ports['g'], ngate_id, min_len_mode=0)
        tinv2_gp_warr = self.connect_to_tracks(tinv2_p0_ports['g'], pgate_id, min_len_mode=0)
        tinv2_g_idx = self.grid.coord_to_nearest_track(tinv2_gn_warr.layer_id + 1, tinv2_gn_warr.middle)
        tinv2_g_tid = TrackID(tinv2_gn_warr.layer_id + 1, tinv2_g_idx)
        tinv2_g = self.connect_to_tracks([tinv2_gn_warr, tinv2_gp_warr], tinv2_g_tid)
        latch = self.connect_to_tracks([inv0_n_ports['d'], inv0_p_ports['d'], tinv1_g, tinv2_g], nout_id)

        self.connect_to_substrate('ptap', tinv2_n0_ports['s'])
        self.connect_to_substrate('ntap', tinv2_p0_ports['s'])

        self.connect_to_tracks([tinv2_n0_ports['d'], tinv2_n1_ports['s']], ndrain_id)
        self.connect_to_tracks([tinv2_p0_ports['d'], tinv2_p1_ports['s']], pdrain_id)
        
        # inv1
        inv1_gn_warr = self.connect_to_tracks(inv1_n_ports['g'], ngate_id, min_len_mode=0)
        inv1_gp_warr = self.connect_to_tracks(inv1_p_ports['g'], pgate_id, min_len_mode=0)
        inv1_g_idx = self.grid.coord_to_nearest_track(inv1_gn_warr.layer_id + 1, inv1_gn_warr.middle)
        inv1_g_tid = TrackID(inv1_gn_warr.layer_id + 1, inv1_g_idx)
        inv1_g = self.connect_to_tracks([inv1_gn_warr, inv1_gp_warr], inv1_g_tid)

        self.connect_to_substrate('ptap', inv1_n_ports['s'])
        self.connect_to_substrate('ntap', inv1_p_ports['s'])

        # tinv3
        tinv3_gn_warr = self.connect_to_tracks(tinv3_n0_ports['g'], ngate_id, min_len_mode=0)
        tinv3_gp_warr = self.connect_to_tracks(tinv3_p0_ports['g'], pgate_id, min_len_mode=0)
        tinv3_g_idx = self.grid.coord_to_nearest_track(tinv3_gn_warr.layer_id + 1, tinv3_gn_warr.middle)
        tinv3_g_tid = TrackID(tinv3_gn_warr.layer_id + 1, tinv3_g_idx)
        tinv3_g = self.connect_to_tracks([tinv3_gn_warr, tinv3_gp_warr], tinv3_g_tid)
        self.connect_to_tracks([inv1_n_ports['d'], inv1_p_ports['d'], tinv3_g], nout_id)
        o = tinv3_g

        self.connect_to_tracks([tinv3_n0_ports['d'], tinv3_n1_ports['s']], ndrain_id)
        self.connect_to_tracks([tinv3_p0_ports['d'], tinv3_p1_ports['s']], pdrain_id)

        self.connect_to_substrate('ptap', tinv3_n0_ports['s'])
        self.connect_to_substrate('ntap', tinv3_p0_ports['s'])

        mem2 = self.connect_to_tracks([tinv2_n1_ports['d'], tinv2_p1_ports['d'], inv1_g,
                                       tinv3_n1_ports['d'], tinv3_p1_ports['d']], pout_id)

        # connect iclk, iclkb
        tinv0_gn1 = self.connect_to_tracks(tinv0_n1_ports['g'], ngate_id, min_len_mode=0)
        tinv0_gn1_idx = self.grid.coord_to_nearest_track(tinv0_gn1.layer_id+1, tinv0_gn1.lower)
        tinv0_gn1_tid = TrackID(tinv0_gn1.layer_id+1, tinv0_gn1_idx)
        tinv0_gn1 = self.connect_to_tracks(tinv0_gn1, tinv0_gn1_tid)

        tinv0_gp1 = self.connect_to_tracks(tinv0_p1_ports['g'], pgate_id, min_len_mode=0)
        tinv0_gp1_idx = self.grid.coord_to_nearest_track(tinv0_gp1.layer_id+1, tinv0_gp1.upper)
        tinv0_gp1_tid = TrackID(tinv0_gp1.layer_id+1, tinv0_gp1_idx)
        tinv0_gp1 = self.connect_to_tracks(tinv0_gp1, tinv0_gp1_tid)

        tinv1_gn1 = self.connect_to_tracks(tinv1_n1_ports['g'], ngate_id, min_len_mode=0)
        tinv1_gn1_idx = self.grid.coord_to_nearest_track(tinv1_gn1.layer_id + 1, tinv1_gn1.middle)
        tinv1_gn1_tid = TrackID(tinv1_gn1.layer_id + 1, tinv1_gn1_idx)
        tinv1_gn1 = self.connect_to_tracks(tinv1_gn1, tinv1_gn1_tid)

        tinv1_gp1 = self.connect_to_tracks(tinv1_p1_ports['g'], pgate_id, min_len_mode=0)
        tinv1_gp1_idx = self.grid.coord_to_nearest_track(tinv1_gp1.layer_id + 1, tinv1_gp1.upper)
        tinv1_gp1_tid = TrackID(tinv1_gp1.layer_id + 1, tinv1_gp1_idx)
        tinv1_gp1 = self.connect_to_tracks(tinv1_gp1, tinv1_gp1_tid)

        tinv2_gn1 = self.connect_to_tracks(tinv2_n1_ports['g'], ngate_id, min_len_mode=0)
        tinv2_gn1_idx = self.grid.coord_to_nearest_track(tinv2_gn1.layer_id + 1, tinv2_gn1.middle)
        tinv2_gn1_tid = TrackID(tinv2_gn1.layer_id + 1, tinv2_gn1_idx)
        tinv2_gn1 = self.connect_to_tracks(tinv2_gn1, tinv2_gn1_tid)

        tinv2_gp1 = self.connect_to_tracks(tinv2_p1_ports['g'], pgate_id, min_len_mode=0)
        tinv2_gp1_idx = self.grid.coord_to_nearest_track(tinv2_gp1.layer_id + 1, tinv2_gp1.upper)
        tinv2_gp1_tid = TrackID(tinv2_gp1.layer_id + 1, tinv2_gp1_idx)
        tinv2_gp1 = self.connect_to_tracks(tinv2_gp1, tinv2_gp1_tid)

        tinv3_gn1 = self.connect_to_tracks(tinv3_n1_ports['g'], ngate_id, min_len_mode=0)
        tinv3_gn1_idx = self.grid.coord_to_nearest_track(tinv3_gn1.layer_id + 1, tinv3_gn1.middle)
        tinv3_gn1_tid = TrackID(tinv3_gn1.layer_id + 1, tinv3_gn1_idx)
        tinv3_gn1 = self.connect_to_tracks(tinv3_gn1, tinv3_gn1_tid)

        tinv3_gp1 = self.connect_to_tracks(tinv3_p1_ports['g'], pgate_id, min_len_mode=0)
        tinv3_gp1_idx = self.grid.coord_to_nearest_track(tinv3_gp1.layer_id + 1, tinv3_gp1.upper)
        tinv3_gp1_tid = TrackID(tinv3_gp1.layer_id + 1, tinv3_gp1_idx+1) # to avoid short
        tinv3_gp1 = self.connect_to_tracks(tinv3_gp1, tinv3_gp1_tid)

        self.connect_to_tracks([tinv0_gp1, tinv1_gn1, tinv2_gn1, tinv3_gp1, iclk], ck_id)
        self.connect_to_tracks([tinv0_gn1, tinv1_gp1, tinv2_gp1, tinv3_gn1, iclkb], ckb_id)

        # add pins
        self.add_pin('CLK', clk, show=show_pins)
        self.add_pin('I', i, show=show_pins)
        self.add_pin('O', o, show=show_pins)
        if debug is True:
            self.add_pin('latch', latch, show=show_pins)
            self.add_pin('iclk', iclk, show=show_pins)
            self.add_pin('iclkb', iclkb, show=show_pins)
            self.add_pin('mem1', mem1, show=show_pins)
            self.add_pin('mem2', mem2, show=show_pins)

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
            nf_inv0=nf_inv0,
            nf_inv1=nf_inv1,
            nf_inv2=nf_inv2,
            nf_inv3=nf_inv3,
            nf_tinv0_0=nf_tinv0_0,
            nf_tinv0_1=nf_tinv0_1,
            nf_tinv1_0=nf_tinv1_0,
            nf_tinv1_1=nf_tinv1_1,
            nf_tinv2_0=nf_tinv2_0,
            nf_tinv2_1=nf_tinv2_1,
            nf_tinv3_0=nf_tinv3_0,
            nf_tinv3_1=nf_tinv3_1,
            intent=intent,
            dum_info=dum_info,
            debug=debug,
        )


