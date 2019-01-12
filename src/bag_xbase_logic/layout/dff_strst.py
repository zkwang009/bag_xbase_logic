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


class DFFStRst(AnalogBase):
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
            nfn_nand0='nand0 NMOS finger number',
            nfp_nand0='nand0 PMOS finger number',
            nfn_nand1='nand1 NMOS finger number',
            nfp_nand1='nand1 PMOS finger number',
            nfn_nand2='nand2 NMOS finger number',
            nfp_nand2='nand2 PMOS finger number',
            nfn_nand3='nand3 NMOS finger number',
            nfp_nand3='nand3 PMOS finger number',
            nf_tgate0='tgate0 MOS finger number',
            nf_tgate1='tgate1 MOS finger number',
            intent='transistor threshold',
            ndum='dummy finger number between different transistors',
            ndum_side='dummy finger number between different transistors',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            show_pins='True to draw pins.',
            debug='True to show inner pins',
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
            power_width_ntr=None,
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, lch, wn, wp, nf_inv0, nf_inv1, nf_inv2, nf_inv3,
                            nf_tinv0_0, nf_tinv0_1, nf_tinv1_0, nf_tinv1_1, nfn_nand0,
                            nfp_nand0, nfn_nand1, nfp_nand1, nfn_nand2, nfp_nand2,
                            nfn_nand3, nfp_nand3, nf_tgate0, nf_tgate1,
                            ptap_w, ntap_w,
                            g_width_ntr, ds_width_ntr, intent, ndum, ndum_side, show_pins,
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
        if nf_inv0%2 != 0 or nf_inv1%2 != 0 or nf_inv2%2 != 0 or nf_inv3%2 != 0 or \
            nf_tinv0_0%2 != 0 or nf_tinv1_0%2 != 0 or nf_tinv0_1%2 != 0 or nf_tinv1_1%2 != 0 or\
            nfn_nand0%2 != 0 or nfp_nand0%2 != 0 or nfn_nand1%2 != 0 or nfp_nand1%2 != 0 or\
            nfn_nand2%2 != 0 or nfp_nand2%2 != 0 or nfn_nand3%2 != 0 or nfp_nand3%2 != 0 or\
            nf_tgate0%2 != 0 or nf_tgate1%2 != 0:
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        fg_tot = ndum_side*2 + ndum*17 + nf_inv0 + nf_inv1 + nf_inv2 + nf_inv3 + \
                 nf_tinv0_0 + nf_tinv0_1 + nf_tinv1_0 + nf_tinv1_1 + \
                 max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                 max(nfn_nand2, nfp_nand2) * 2 + max(nfn_nand3, nfp_nand3) * 2 + \
                 nf_tgate0 + nf_tgate1 + 2

        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr * 3 + g_sp_ntr * 2]
        pg_tracks = [g_width_ntr * 3 + g_sp_ntr * 2]
        nds_tracks = [ds_width_ntr * 2 + ds_sp_ntr]
        pds_tracks = [ds_width_ntr * 2 + ds_sp_ntr]
        n_orientation = ['R0']
        p_orientation = ['MX']

        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list,
                       nth_list, pw_list, pth_list,
                       ng_tracks=ng_tracks, nds_tracks=nds_tracks,
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       n_orientations=n_orientation, p_orientations=p_orientation,
                       )

        # get gate and drain index
        ck_id = self.make_track_id('nch', 0, 'g', 1, width=1)
        ckb_id = self.make_track_id('pch', 0, 'g', 1, width=1)
        ngate_id = self.make_track_id('nch', 0, 'g', 2, width=1)
        pgate_id = self.make_track_id('pch', 0, 'g', 2, width=1)
        nout_id = self.make_track_id('nch', 0, 'ds', 1, width=1)
        pout_id = self.make_track_id('pch', 0, 'ds', 1, width=1)
        ndrain_id = self.make_track_id('nch', 0, 'ds', 0, width=1)
        pdrain_id = self.make_track_id('pch', 0, 'ds', 0, width=1)
        st_id = self.make_track_id('nch', 0, 'g', 0, width=1)
        rst_id = self.make_track_id('pch', 0, 'g', 0, width=1)

        # Step1: connect inverter
        # group transistors
        # inv2
        inv2_n_ports = self.draw_mos_conn('nch', 0, ndum_side, nf_inv2, 1, 1,
                                          s_net='VSS', d_net='stb')
        inv2_p_ports = self.draw_mos_conn('pch', 0, ndum_side, nf_inv2, 1, 1,
                                          s_net='VDD', d_net='stb')
        # inv3
        inv3_n_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum+nf_inv2,
                                          nf_inv3, 1, 1, s_net='VSS', d_net='rstb')
        inv3_p_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum+nf_inv2,
                                          nf_inv3, 1, 1, s_net='VDD', d_net='rstb')
        # inv0
        col_idx = ndum_side+ndum*2+nf_inv2+nf_inv3
        inv0_n_ports = self.draw_mos_conn('nch', 0, col_idx, nf_inv0, 1, 1,
                                          s_net='VSS', d_net='iclkb')
        inv0_p_ports = self.draw_mos_conn('pch', 0, col_idx, nf_inv0, 1, 1,
                                          s_net='VDD', d_net='iclkb')
        # inv1
        col_idx = ndum_side+ndum*3+nf_inv2+nf_inv3+nf_inv0
        inv1_n_ports = self.draw_mos_conn('nch', 0, col_idx, nf_inv1, 1, 1,
                                          s_net='VSS', d_net='iclk')
        inv1_p_ports = self.draw_mos_conn('pch', 0, col_idx, nf_inv1, 1, 1,
                                          s_net='VDD', d_net='iclk')
        # tinv0
        col_idx = ndum_side + ndum * 4 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1
        tinv0_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv0_0, 1, 1, 
                                            s_net='VSS', d_net='tinv0_ns')
        tinv0_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv0_0, 1, 1, 
                                            s_net='VDD', d_net='tinv0_ps')
        col_idx = ndum_side + ndum * 5 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + 2 # for drc
        tinv0_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv0_1, 1, 1,
                                            s_net='tinv0_ns', d_net='mem1')
        tinv0_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv0_1, 1, 1,
                                            s_net='tinv0_ps', d_net='mem1')
        # nand0
        col_idx = ndum_side + ndum * 6 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + 2
        nand0_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand0, 1, 1, 
                                            s_net='VSS', d_net='nand0_ns')
        nand0_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand0, 1, 1, 
                                            s_net='VDD', d_net='latch')
        col_idx = ndum_side + ndum * 7 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) + 2
        nand0_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand0, 1, 1,
                                            s_net='nand0_ns', d_net='latch')
        nand0_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand0, 1, 1,
                                            s_net='VDD', d_net='latch')
        # nand1
        col_idx = ndum_side + ndum * 8 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + 2
        nand1_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand1, 1, 1, 
                                            s_net='VSS', d_net='nand1_ns')
        nand1_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand1, 1, 1, 
                                            s_net='VDD', d_net='rstm1')
        col_idx = ndum_side + ndum * 9 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) + 2
        nand1_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand1, 1, 1,
                                            s_net='nand1_ns', d_net='rstm1')
        nand1_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand1, 1, 1,
                                            s_net='VDD', d_net='rstm1')
        # tgate0
        col_idx = ndum_side + ndum * 10 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + 2
        tgate0_n_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tgate0, 1, 1,
                                            s_net='rstm1', d_net='mem1')
        tgate0_p_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tgate0, 1, 1,
                                            s_net='rstm1', d_net='mem1')

        # tinv1
        col_idx = ndum_side + ndum * 11 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                  nf_tgate0 + 2
        tinv1_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv1_0, 1, 1,
                                            s_net='VSS', d_net='tinv1_ns')
        tinv1_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv1_0, 1, 1,
                                            s_net='VDD', d_net='tinv1_ps')
        col_idx = ndum_side + ndum * 12 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                  nf_tgate0 + nf_tinv1_0 + 2
        tinv1_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tinv1_1, 1, 1,
                                            s_net='tinv1_ns', d_net='mem2')
        tinv1_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tinv1_1, 1, 1,
                                            s_net='tinv1_ps', d_net='mem2')
        # nand2
        col_idx = ndum_side + ndum * 13 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                  nf_tgate0 + nf_tinv1_0 + nf_tinv1_1 + 2
        nand2_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand2, 1, 1,
                                            s_net='VSS', d_net='nand2_ns')
        nand2_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand2, 1, 1,
                                            s_net='VDD', d_net='O')
        col_idx = ndum_side + ndum * 14 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                  nf_tgate0 + nf_tinv1_0 + nf_tinv1_1 + max(nfn_nand2, nfp_nand2) + 2
        nand2_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand2, 1, 1,
                                            s_net='nand2_ns', d_net='O')
        nand2_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand2, 1, 1,
                                            s_net='VDD', d_net='O')
        # nand3
        col_idx = ndum_side + ndum * 15 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                  nf_tgate0 + nf_tinv1_0 + nf_tinv1_1 + max(nfn_nand2, nfp_nand2) * 2 + 2
        nand3_n0_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand3, 1, 1,
                                            s_net='VSS', d_net='nand3_ns')
        nand3_p0_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand3, 1, 1,
                                            s_net='VDD', d_net='rstm2')
        col_idx = ndum_side + ndum * 16 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                  nf_tgate0 + nf_tinv1_0 + nf_tinv1_1 + max(nfn_nand2, nfp_nand2) * 2 +\
                  max(nfn_nand3, nfp_nand3) + 2
        nand3_n1_ports = self.draw_mos_conn('nch', 0, col_idx, nfn_nand3, 1, 1,
                                            s_net='nand3_ns', d_net='rstm2')
        nand3_p1_ports = self.draw_mos_conn('pch', 0, col_idx, nfp_nand3, 1, 1,
                                            s_net='VDD', d_net='rstm2')
        # tgate1
        col_idx = ndum_side + ndum * 17 + nf_inv2 + nf_inv3 + nf_inv0 + nf_inv1 + nf_tinv0_0 + \
                  nf_tinv0_1 + max(nfn_nand0, nfp_nand0) * 2 + max(nfn_nand1, nfp_nand1) * 2 + \
                  nf_tgate0 + nf_tinv1_0 + nf_tinv1_1 + max(nfn_nand2, nfp_nand2) * 2 + \
                  max(nfn_nand3, nfp_nand3) * 2 + 2
        tgate1_n_ports = self.draw_mos_conn('nch', 0, col_idx, nf_tgate1, 1, 1,
                                            s_net='rstm2', d_net='mem2')
        tgate1_p_ports = self.draw_mos_conn('pch', 0, col_idx, nf_tgate1, 1, 1,
                                            s_net='rstm2', d_net='mem2')
        
        # connect inv2, inv3 (rst, st buffers)
        # inv2
        inv2_n_warr = self.connect_to_tracks(inv2_n_ports['g'], ngate_id, min_len_mode=0)
        inv2_p_warr = self.connect_to_tracks(inv2_p_ports['g'], pgate_id, min_len_mode=0)
        inv2_idx = self.grid.coord_to_nearest_track(inv2_n_warr.layer_id + 1, inv2_n_warr.middle)
        inv2_tid = TrackID(inv2_n_warr.layer_id + 1, inv2_idx)
        st = self.connect_to_tracks([inv2_n_warr, inv2_p_warr], inv2_tid)

        self.connect_to_substrate('ptap', inv2_n_ports['s'])
        self.connect_to_substrate('ntap', inv2_p_ports['s'])

        inv2_d_wire = self.connect_to_tracks([inv2_n_ports['d'], inv2_p_ports['d']], nout_id, min_len_mode=0)
        stb_idx = self.grid.coord_to_nearest_track(inv2_d_wire.layer_id + 1, inv2_d_wire.lower)
        stb_tid = TrackID(inv2_d_wire.layer_id + 1, stb_idx)
        stb = self.connect_to_tracks(inv2_d_wire, stb_tid, min_len_mode=0)

        # inv3
        inv3_n_warr = self.connect_to_tracks(inv3_n_ports['g'], ngate_id, min_len_mode=0)
        inv3_p_warr = self.connect_to_tracks(inv3_p_ports['g'], pgate_id, min_len_mode=0)
        inv3_idx = self.grid.coord_to_nearest_track(inv3_n_warr.layer_id + 1, inv3_n_warr.middle)
        inv3_tid = TrackID(inv3_n_warr.layer_id + 1, inv3_idx)
        rst = self.connect_to_tracks([inv3_n_warr, inv3_p_warr], inv3_tid)

        self.connect_to_substrate('ptap', inv3_n_ports['s'])
        self.connect_to_substrate('ntap', inv3_p_ports['s'])

        inv3_d_wire = self.connect_to_tracks([inv3_n_ports['d'], inv3_p_ports['d']], nout_id)
        rstb_idx = self.grid.coord_to_nearest_track(inv3_d_wire.layer_id + 1, inv3_d_wire.upper)
        rstb_tid = TrackID(inv3_d_wire.layer_id + 1, rstb_idx+1)
        rstb = self.connect_to_tracks(inv3_d_wire, rstb_tid)

        # connect inv0, inv1 (clock buffer)
        # inv0
        inv0_n_warr = self.connect_to_tracks(inv0_n_ports['g'], ngate_id, min_len_mode=0)
        inv0_p_warr = self.connect_to_tracks(inv0_p_ports['g'], pgate_id, min_len_mode=0)
        inv0_idx = self.grid.coord_to_nearest_track(inv0_n_warr.layer_id + 1, inv0_n_warr.middle)
        inv0_tid = TrackID(inv0_n_warr.layer_id + 1, inv0_idx)
        clk = self.connect_to_tracks([inv0_n_warr, inv0_p_warr], inv0_tid)

        self.connect_to_substrate('ptap', inv0_n_ports['s'])
        self.connect_to_substrate('ntap', inv0_p_ports['s'])

        # inv1
        inv1_n_warr = self.connect_to_tracks(inv1_n_ports['g'], ngate_id, min_len_mode=0)
        inv1_p_warr = self.connect_to_tracks(inv1_p_ports['g'], pgate_id, min_len_mode=0)
        inv1_idx = self.grid.coord_to_nearest_track(inv1_n_warr.layer_id + 1, inv1_n_warr.middle)
        inv1_tid = TrackID(inv1_n_warr.layer_id + 1, inv1_idx)
        inv1_g_wire = self.connect_to_tracks([inv1_n_warr, inv1_p_warr], inv1_tid)
        self.connect_to_tracks([inv0_n_ports['d'], inv0_p_ports['d'], inv1_g_wire], pout_id)
        iclkb = inv1_g_wire

        self.connect_to_substrate('ptap', inv1_n_ports['s'])
        self.connect_to_substrate('ntap', inv1_p_ports['s'])

        inv1_d_wire = self.connect_to_tracks([inv1_n_ports['d'], inv1_p_ports['d']], nout_id)
        iclk_idx = self.grid.coord_to_nearest_track(inv1_d_wire.layer_id+1, inv1_d_wire.upper)
        iclk_tid = TrackID(inv1_d_wire.layer_id+1, iclk_idx+1)
        iclk = self.connect_to_tracks(inv1_d_wire, iclk_tid)

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

        # nand0
        nand0_gn0_warr = self.connect_to_tracks(nand0_n0_ports['g'], ngate_id, min_len_mode=0)
        nand0_gp0_warr = self.connect_to_tracks(nand0_p0_ports['g'], pgate_id, min_len_mode=0)
        nand0_g0_idx = self.grid.coord_to_nearest_track(nand0_gn0_warr.layer_id + 1, nand0_gn0_warr.middle)
        nand0_g0_tid = TrackID(nand0_gn0_warr.layer_id + 1, nand0_g0_idx)
        nand0_g0 = self.connect_to_tracks([nand0_gn0_warr, nand0_gp0_warr], nand0_g0_tid)

        # # connect nand0_g0
        # self.connect_to_tracks([tinv0_n1_ports['d'], tinv0_p1_ports['d'], nand0_g0], nout_id)
        # connect nand_n0 and nand_n1
        self.connect_to_tracks([nand0_n0_ports['d'], nand0_n1_ports['s']], ndrain_id)

        self.connect_to_substrate('ptap', nand0_n0_ports['s'])
        self.connect_to_substrate('ntap', [nand0_p0_ports['s'], nand0_p1_ports['s']])

        # # connect drain to output
        # self.connect_to_tracks([nand0_p0_ports['d'], nand0_p1_ports['d'], nand0_n1_ports['d']], nout_id)
        
        # nand1 
        nand1_gn0_warr = self.connect_to_tracks(nand1_n0_ports['g'], ngate_id, min_len_mode=0)
        nand1_gp0_warr = self.connect_to_tracks(nand1_p0_ports['g'], pgate_id, min_len_mode=0)
        nand1_g0_idx = self.grid.coord_to_nearest_track(nand1_gn0_warr.layer_id + 1, nand1_gn0_warr.middle)
        nand1_g0_tid = TrackID(nand1_gn0_warr.layer_id + 1, nand1_g0_idx)
        nand1_g0 = self.connect_to_tracks([nand1_gn0_warr, nand1_gp0_warr], nand1_g0_tid)
        # connect nand_n0 and nand_n1
        self.connect_to_tracks([nand1_n0_ports['d'], nand1_n1_ports['s']], ndrain_id)

        self.connect_to_substrate('ptap', nand1_n0_ports['s'])
        self.connect_to_substrate('ntap', [nand1_p0_ports['s'], nand1_p1_ports['s']])

        # tgate0
        # connect nand1 drain to tgage drain
        rstm1 = self.connect_to_tracks([nand1_p0_ports['d'], nand1_p1_ports['d'], nand1_n1_ports['d'],
                                        tgate0_n_ports['s'], tgate0_p_ports['s']], pdrain_id)

        # connect tgate0 drain, tinv0_n1/p1 drain and nand
        mem1 = self.connect_to_tracks([tgate0_n_ports['d'], tgate0_p_ports['d'], tinv0_n1_ports['d'],
                                       tinv0_p1_ports['d'], nand0_g0], nout_id)

        # tinv1
        tinv1_ng0_warr = self.connect_to_tracks(tinv1_n0_ports['g'], ngate_id, min_len_mode=0)
        tinv1_pg0_warr = self.connect_to_tracks(tinv1_p0_ports['g'], pgate_id, min_len_mode=0)
        tinv1_g0_idx = self.grid.coord_to_nearest_track(tinv1_ng0_warr.layer_id + 1, tinv1_ng0_warr.middle)
        tinv1_g0_tid = TrackID(tinv1_ng0_warr.layer_id + 1, tinv1_g0_idx)
        tinv1_g0 = self.connect_to_tracks([tinv1_ng0_warr, tinv1_pg0_warr], tinv1_g0_tid)
        latch = self.connect_to_tracks([nand0_n1_ports['d'], nand0_p0_ports['d'], nand0_p1_ports['d'],
                                       nand1_g0, tinv1_g0], pout_id)

        self.connect_to_substrate('ptap', tinv1_n0_ports['s'])
        self.connect_to_substrate('ntap', tinv1_p0_ports['s'])

        self.connect_to_tracks([tinv1_n0_ports['d'], tinv1_n1_ports['s']], ndrain_id)
        self.connect_to_tracks([tinv1_p0_ports['d'], tinv1_p1_ports['s']], pdrain_id)

        # nand2
        nand2_gn0_warr = self.connect_to_tracks(nand2_n0_ports['g'], ngate_id, min_len_mode=0)
        nand2_gp0_warr = self.connect_to_tracks(nand2_p0_ports['g'], pgate_id, min_len_mode=0)
        nand2_g0_idx = self.grid.coord_to_nearest_track(nand2_gn0_warr.layer_id + 1, nand2_gn0_warr.middle)
        nand2_g0_tid = TrackID(nand2_gn0_warr.layer_id + 1, nand2_g0_idx)
        nand2_g0 = self.connect_to_tracks([nand2_gn0_warr, nand2_gp0_warr], nand2_g0_tid)

        # # connect nand2_g0
        # self.connect_to_tracks([tinv0_n1_ports['d'], tinv0_p1_ports['d'], nand2_g0], nout_id)
        # connect nand_n0 and nand_n1
        self.connect_to_tracks([nand2_n0_ports['d'], nand2_n1_ports['s']], ndrain_id)

        self.connect_to_substrate('ptap', nand2_n0_ports['s'])
        self.connect_to_substrate('ntap', [nand2_p0_ports['s'], nand2_p1_ports['s']])

        # # connect drain to output
        # self.connect_to_tracks([nand0_p0_ports['d'], nand0_p1_ports['d'], nand0_n1_ports['d']], nout_id)

        # nand3
        nand3_gn0_warr = self.connect_to_tracks(nand3_n0_ports['g'], ngate_id, min_len_mode=0)
        nand3_gp0_warr = self.connect_to_tracks(nand3_p0_ports['g'], pgate_id, min_len_mode=0)
        nand3_g0_idx = self.grid.coord_to_nearest_track(nand3_gn0_warr.layer_id + 1, nand3_gn0_warr.middle)
        nand3_g0_tid = TrackID(nand3_gn0_warr.layer_id + 1, nand3_g0_idx)
        nand3_g0 = self.connect_to_tracks([nand3_gn0_warr, nand3_gp0_warr], nand3_g0_tid)

        # connect nand3_n0 and nand3_n1
        self.connect_to_tracks([nand3_n0_ports['d'], nand3_n1_ports['s']], ndrain_id)

        self.connect_to_substrate('ptap', nand3_n0_ports['s'])
        self.connect_to_substrate('ntap', [nand3_p0_ports['s'], nand3_p1_ports['s']])

        # tgate1
        # connect nand3 drain to tgate drain
        rstm2 = self.connect_to_tracks([nand3_p0_ports['d'], nand3_p1_ports['d'], nand3_n1_ports['d'],
                                        tgate1_n_ports['s'], tgate1_p_ports['s']], pdrain_id)

        # connect tgate1 drain, tinv1_n1/p1 drain and nand2 gate
        mem2 = self.connect_to_tracks([tgate1_n_ports['d'], tgate1_p_ports['d'], tinv1_n1_ports['d'],
                                       tinv1_p1_ports['d'], nand2_g0], nout_id)

        # connect nand2 drain and nand3 gate
        o = self.connect_to_tracks([nand2_n1_ports['d'], nand2_p0_ports['d'], nand2_p1_ports['d'],
                                    nand3_g0], pout_id)
        
        # connect stb, rstb
        nand0_gn1_warr = self.connect_to_tracks(nand0_n1_ports['g'], ngate_id, min_len_mode=0)
        nand0_gp1_warr = self.connect_to_tracks(nand0_p1_ports['g'], pgate_id, min_len_mode=0)
        nand0_g1_idx = self.grid.coord_to_nearest_track(nand0_gn1_warr.layer_id + 1, nand0_gn1_warr.middle)
        nand0_g1_tid = TrackID(nand0_gn1_warr.layer_id + 1, nand0_g1_idx)
        nand0_g1 = self.connect_to_tracks([nand0_gn1_warr, nand0_gp1_warr], nand0_g1_tid, min_len_mode=0)

        nand1_gn1_warr = self.connect_to_tracks(nand1_n1_ports['g'], ngate_id, min_len_mode=0)
        nand1_gp1_warr = self.connect_to_tracks(nand1_p1_ports['g'], pgate_id, min_len_mode=0)
        nand1_g1_idx = self.grid.coord_to_nearest_track(nand1_gn1_warr.layer_id + 1, nand1_gn1_warr.middle)
        nand1_g1_tid = TrackID(nand1_gn1_warr.layer_id + 1, nand1_g1_idx)
        nand1_g1 = self.connect_to_tracks([nand1_gn1_warr, nand1_gp1_warr], nand1_g1_tid, min_len_mode=0)

        nand2_gn1_warr = self.connect_to_tracks(nand2_n1_ports['g'], ngate_id, min_len_mode=0)
        nand2_gp1_warr = self.connect_to_tracks(nand2_p1_ports['g'], pgate_id, min_len_mode=0)
        nand2_g1_idx = self.grid.coord_to_nearest_track(nand2_gn1_warr.layer_id + 1, nand2_gn1_warr.middle)
        nand2_g1_tid = TrackID(nand2_gn1_warr.layer_id + 1, nand2_g1_idx)
        nand2_g1 = self.connect_to_tracks([nand2_gn1_warr, nand2_gp1_warr], nand2_g1_tid, min_len_mode=0)

        nand3_gn1_warr = self.connect_to_tracks(nand3_n1_ports['g'], ngate_id, min_len_mode=0)
        nand3_gp1_warr = self.connect_to_tracks(nand3_p1_ports['g'], pgate_id, min_len_mode=0)
        nand3_g1_idx = self.grid.coord_to_nearest_track(nand3_gn1_warr.layer_id + 1, nand3_gn1_warr.middle)
        nand3_g1_tid = TrackID(nand3_gn1_warr.layer_id + 1, nand3_g1_idx)
        nand3_g1 = self.connect_to_tracks([nand3_gn1_warr, nand3_gp1_warr], nand3_g1_tid, min_len_mode=0)

        stb = self.connect_to_tracks([nand0_g1, nand2_g1, stb], st_id)
        rstb = self.connect_to_tracks([nand1_g1, nand3_g1, rstb], rst_id)

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

        # tgate0
        tgate0_gn = self.connect_to_tracks(tgate0_n_ports['g'], ngate_id, min_len_mode=0)
        tgate0_gn_idx = self.grid.coord_to_nearest_track(tgate0_gn.layer_id + 1, tgate0_gn.middle)
        tgate0_gn_tid = TrackID(tgate0_gn.layer_id + 1, tgate0_gn_idx)
        tgate0_n = self.connect_to_tracks(tgate0_gn, tgate0_gn_tid)
        tgate0_gp = self.connect_to_tracks(tgate0_p_ports['g'], pgate_id, min_len_mode=0)
        tgate0_gp_idx = self.grid.coord_to_nearest_track(tgate0_gp.layer_id + 1, tgate0_gp.upper)
        tgate0_gp_tid = TrackID(tgate0_gp.layer_id + 1, tgate0_gp_idx)
        tgate0_p = self.connect_to_tracks(tgate0_gp, tgate0_gp_tid)

        # tgate1
        tgate1_gn = self.connect_to_tracks([tgate1_n_ports['g']], ngate_id, min_len_mode=0)
        tgate1_gn_idx = self.grid.coord_to_nearest_track(tgate1_gn.layer_id + 1, tgate1_gn.middle)
        tgate1_gn_tid = TrackID(tgate1_gn.layer_id + 1, tgate1_gn_idx)
        tgate1_n = self.connect_to_tracks(tgate1_gn, tgate1_gn_tid)
        tgate1_gp = self.connect_to_tracks([tgate1_p_ports['g']], pgate_id, min_len_mode=0)
        tgate1_gp_idx = self.grid.coord_to_nearest_track(tgate1_gp.layer_id + 1, tgate1_gp.upper)
        tgate1_gp_tid = TrackID(tgate1_gp.layer_id + 1, tgate1_gp_idx+1)
        tgate1_p = self.connect_to_tracks(tgate1_gp, tgate1_gp_tid)

        self.connect_to_tracks([tinv0_gp1, tinv1_gn1, tgate0_n, tgate1_p, iclk], ck_id)
        self.connect_to_tracks([tinv0_gn1, tinv1_gp1, tgate0_p, tgate1_n, iclkb], ckb_id)

        # add pins
        self.add_pin('CLK', clk, show=show_pins)
        self.add_pin('ST', st, show=show_pins)
        self.add_pin('RST', rst, show=show_pins)
        self.add_pin('I', i, show=show_pins)
        self.add_pin('O', [o, nand3_g0], show=show_pins)
        if debug is True:
            # test signals
            self.add_pin('latch', latch, show=show_pins)
            self.add_pin('mem1', mem1, show=show_pins)
            self.add_pin('mem2', mem2, show=show_pins)
            self.add_pin('rstm1', rstm1, show=show_pins)
            self.add_pin('rstm2', rstm2, show=show_pins)
            self.add_pin('iclk', iclk, show=show_pins)
            self.add_pin('iclkb', iclkb, show=show_pins)
            self.add_pin('stb', stb, show=show_pins)
            self.add_pin('rstb', rstb, show=show_pins)

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
            nf_inv2=nf_inv3,
            nf_inv3=nf_inv3,
            nf_tinv0_0=nf_tinv0_0,
            nf_tinv0_1=nf_tinv0_1,
            nf_tinv1_0=nf_tinv1_0,
            nf_tinv1_1=nf_tinv1_1,
            nfn_nand0=nfn_nand0,
            nfp_nand0=nfp_nand0,
            nfn_nand1=nfn_nand1,
            nfp_nand1=nfp_nand1,
            nfn_nand2=nfn_nand2,
            nfp_nand2=nfp_nand2,
            nfn_nand3=nfn_nand3,
            nfp_nand3=nfp_nand3,
            nf_tgate0=nf_tgate0,
            nf_tgate1=nf_tgate1,
            intent=intent,
            dum_info=dum_info,
            debug=debug,
        )


