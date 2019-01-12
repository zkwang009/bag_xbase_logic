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


class MUX(AnalogBase):
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
        self._upper_idx = None

    @property
    def sch_params(self):
        return self._sch_params

    @property
    def upper_idx(self):
        return self._upper_idx

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
            nf_tinv_0='tinv MOS0 finger number',
            nf_tinv_1='tinv MOS1 finger number',
            nf_inv2='inv2 finger number',
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

    def _draw_layout_helper(self, lch, wn, wp, nf_inv0, nf_tinv_0, nf_tinv_1, nf_inv2,
                            ptap_w, ntap_w, g_width_ntr, ds_width_ntr,
                            intent, ndum, ndum_side,
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
        if nf_inv0%2 != 0 or nf_tinv_0%2 != 0 or nf_tinv_1%2 != 0 or nf_inv2%2 != 0:
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        fg_tot = ndum_side*2 + ndum*6 + nf_inv0*2 + nf_tinv_0*2 + nf_tinv_1*2 + nf_inv2 + 2

        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr*2 + g_space]
        pg_tracks = [g_width_ntr*2 + g_space]
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
        seli_id = self.make_track_id('nch', 0, 'g', 0, width=1)
        selib_id = self.make_track_id('pch', 0, 'g', 0, width=1)
        ngate_id = self.make_track_id('nch', 0, 'g', 1, width=1)
        pgate_id = self.make_track_id('pch', 0, 'g', 1, width=1)
        nout_id = self.make_track_id('nch', 0, 'ds', 1, width=1)
        pout_id = self.make_track_id('pch', 0, 'ds', 1, width=1)
        ndrain_id = self.make_track_id('nch', 0, 'ds', 0, width=1)
        pdrain_id = self.make_track_id('pch', 0, 'ds', 0, width=1)

        # Step1: connect inverter
        # group transistors
        # inv0
        inv0_n_ports = self.draw_mos_conn('nch', 0, ndum_side, nf_inv0, 1, 1,
                                          s_net='VSS', d_net='sel_ib')
        inv0_p_ports = self.draw_mos_conn('pch', 0, ndum_side, nf_inv0, 1, 1,
                                          s_net='VDD', d_net='sel_ib')
        # inv1
        inv1_n_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum+nf_inv0,
                                          nf_inv0, 1, 1, s_net='VSS', d_net='sel_i')
        inv1_p_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum+nf_inv0,
                                          nf_inv0, 1, 1, s_net='VDD', d_net='sel_i')
        # xor logic
        tinv0_n0_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum*2+nf_inv0*2,
                                            nf_tinv_0, 1, 1, s_net='VSS', d_net='tinv0_ns')
        tinv0_p0_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum*2+nf_inv0*2,
                                            nf_tinv_0, 1, 1, s_net='VDD', d_net='tinv0_ps')
        tinv0_n1_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum*3+nf_inv0*2+nf_tinv_0,
                                            nf_tinv_1, 1, 1, s_net='tinv0_ns', d_net='mux_b')
        tinv0_p1_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum*3+nf_inv0*2+nf_tinv_0,
                                            nf_tinv_1, 1, 1, s_net='tinv0_ps', d_net='mxu_b')
        col_idx = ndum_side + ndum * 4 + nf_inv0 * 2 + nf_tinv_0 + nf_tinv_1
        tinv1_n0_ports = self.draw_mos_conn('nch', 0, col_idx,
                                            nf_tinv_0, 1, 1, s_net='VSS', d_net='tinv1_ns')
        tinv1_p0_ports = self.draw_mos_conn('pch', 0, col_idx,
                                            nf_tinv_1, 1, 1, s_net='VDD', d_net='tinv1_ps')
        col_idx = ndum_side + ndum * 5 + nf_inv0 * 2 + nf_tinv_0*2 + nf_tinv_1 + 2  # 1 to pass drc
        tinv1_n1_ports = self.draw_mos_conn('nch', 0, col_idx,
                                            nf_tinv_1, 1, 1, s_net='tinv1_ns', d_net='mux_b')
        tinv1_p1_ports = self.draw_mos_conn('pch', 0, col_idx,
                                            nf_tinv_1, 1, 1, s_net='tinv1_ps', d_net='mux_b')
        col_idx = ndum_side + ndum * 6 + nf_inv0 * 2 + nf_tinv_0 * 2 + nf_tinv_1 * 2 + 2
        inv2_n_ports = self.draw_mos_conn('nch', 0, col_idx,
                                          nf_inv2, 1, 1, s_net='VSS', d_net='o')
        inv2_p_ports = self.draw_mos_conn('pch', 0, col_idx,
                                          nf_inv2, 1, 1, s_net='VDD', d_net='o')

        # connect inv0, inv1 (buffers)
        # inv0
        inv0_gn_warr = self.connect_to_tracks(inv0_n_ports['g'], ngate_id, min_len_mode=0)
        inv0_gp_warr = self.connect_to_tracks(inv0_p_ports['g'], pgate_id, min_len_mode=0)
        inv0_g_idx = self.grid.coord_to_nearest_track(inv0_gn_warr.layer_id + 1, inv0_gn_warr.lower)
        inv0_g_tid = TrackID(inv0_gn_warr.layer_id + 1, inv0_g_idx)
        sel = self.connect_to_tracks([inv0_gn_warr, inv0_gp_warr], inv0_g_tid)
        # inv0 drain
        sel_ib = self.connect_to_tracks([inv0_n_ports['d'], inv0_p_ports['d']], nout_id)
        # inv0 source
        self.connect_to_substrate('ptap', inv0_n_ports['s'])
        self.connect_to_substrate('ntap', inv0_p_ports['s'])

        # inv1
        inv1_gn_warr = self.connect_to_tracks(inv1_n_ports['g'], ngate_id, min_len_mode=0)
        inv1_gp_warr = self.connect_to_tracks(inv1_p_ports['g'], pgate_id, min_len_mode=0)
        inv1_g_idx = self.grid.coord_to_nearest_track(inv1_gn_warr.layer_id + 1, inv1_gn_warr.middle)
        inv1_g_tid = TrackID(inv1_gn_warr.layer_id + 1, inv1_g_idx)
        # inv0 drain, inv1 gate
        sel_ib = self.connect_to_tracks([inv1_gn_warr, inv1_gp_warr, sel_ib], inv1_g_tid)
        # inv1 source
        self.connect_to_substrate('ptap', inv1_n_ports['s'])
        self.connect_to_substrate('ntap', inv1_p_ports['s'])
        # inv1 drain
        sel_i = self.connect_to_tracks([inv1_n_ports['d'], inv1_p_ports['d']], pout_id, min_len_mode=0)
        sel_i_idx = self.grid.coord_to_nearest_track(sel_i.layer_id + 1, sel_i.upper)
        sel_i_tid = TrackID(sel_i.layer_id + 1, sel_i_idx+1)
        sel_i = self.connect_to_tracks(sel_i, sel_i_tid)

        # tinv0 MOSs
        # tinv0_0 gate
        tinv0_gn0_warr = self.connect_to_tracks(tinv0_n0_ports['g'], ngate_id, min_len_mode=0)
        tinv0_gp0_warr = self.connect_to_tracks(tinv0_p0_ports['g'], pgate_id, min_len_mode=0)
        tinv0_g0_idx = self.grid.coord_to_nearest_track(tinv0_gn0_warr.layer_id + 1, tinv0_gn0_warr.middle)
        tinv0_g0_tid = TrackID(tinv0_gn0_warr.layer_id + 1, tinv0_g0_idx)
        i0 = self.connect_to_tracks([tinv0_gn0_warr, tinv0_gp0_warr], tinv0_g0_tid)
        # tinv0_1 NMOS gate
        tinv0_gn1_warr = self.connect_to_tracks(tinv0_n1_ports['g'], ngate_id, min_len_mode=0)
        tinv0_gn1_idx = self.grid.coord_to_nearest_track(tinv0_gn1_warr.layer_id + 1, tinv0_gn1_warr.middle)
        tinv0_gn1_tid = TrackID(tinv0_gn1_warr.layer_id + 1, tinv0_gn1_idx)
        tinv0_gn1 = self.connect_to_tracks(tinv0_gn1_warr, tinv0_gn1_tid)
        # tinv0_1 PMOS gate
        tinv0_gp1_warr = self.connect_to_tracks(tinv0_p1_ports['g'], pgate_id, min_len_mode=0)
        tinv0_gp1_idx = self.grid.coord_to_nearest_track(tinv0_gp1_warr.layer_id + 1, tinv0_gp1_warr.upper)
        tinv0_gp1_tid = TrackID(tinv0_gp1_warr.layer_id + 1, tinv0_gp1_idx)
        tinv0_gp1 = self.connect_to_tracks(tinv0_gp1_warr, tinv0_gp1_tid)
        # tinv0_0 source
        self.connect_to_substrate('ptap', tinv0_n0_ports['s'])
        self.connect_to_substrate('ntap', tinv0_p0_ports['s'])
        # tinv0_0 drain and tinv0_1 source
        self.connect_to_tracks([tinv0_n0_ports['d'], tinv0_n1_ports['s']], ndrain_id)
        self.connect_to_tracks([tinv0_p0_ports['d'], tinv0_p1_ports['s']], pdrain_id)
        # tinv0 output
        tinv0_d = self.connect_to_tracks([tinv0_n1_ports['d'], tinv0_p1_ports['d']], nout_id)

        # tinv1 MOSs
        tinv1_gn0_warr = self.connect_to_tracks(tinv1_n0_ports['g'], ngate_id, min_len_mode=0)
        tinv1_gp0_warr = self.connect_to_tracks(tinv1_p0_ports['g'], pgate_id, min_len_mode=0)
        tinv1_g0_idx = self.grid.coord_to_nearest_track(tinv1_gn0_warr.layer_id + 1, tinv1_gn0_warr.middle)
        tinv1_g0_tid = TrackID(tinv1_gn0_warr.layer_id + 1, tinv1_g0_idx)
        i1 = self.connect_to_tracks([tinv1_gn0_warr, tinv1_gp0_warr], tinv1_g0_tid)
        # tinv1_1 NMOS gate
        tinv1_gn1_warr = self.connect_to_tracks(tinv1_n1_ports['g'], ngate_id, min_len_mode=0)
        tinv1_gn1_idx = self.grid.coord_to_nearest_track(tinv1_gn1_warr.layer_id + 1, tinv1_gn1_warr.lower)
        tinv1_gn1_tid = TrackID(tinv1_gn1_warr.layer_id + 1, tinv1_gn1_idx)
        tinv1_gn1 = self.connect_to_tracks(tinv1_gn1_warr, tinv1_gn1_tid)
        # tinv1_1 PMOS gate
        tinv1_gp1_warr = self.connect_to_tracks(tinv1_p1_ports['g'], pgate_id, min_len_mode=0)
        tinv1_gp1_idx = self.grid.coord_to_nearest_track(tinv1_gp1_warr.layer_id + 1, tinv1_gp1_warr.upper)
        tinv1_gp1_tid = TrackID(tinv1_gp1_warr.layer_id + 1, tinv1_gp1_idx)
        tinv1_gp1 = self.connect_to_tracks(tinv1_gp1_warr, tinv1_gp1_tid)
        # tinv1_0 source
        self.connect_to_substrate('ptap', tinv1_n0_ports['s'])
        self.connect_to_substrate('ntap', tinv1_p0_ports['s'])
        # tinv1_0 drain and tinv1_1 source
        self.connect_to_tracks([tinv1_n0_ports['d'], tinv1_n1_ports['s']], ndrain_id)
        self.connect_to_tracks([tinv1_p0_ports['d'], tinv1_p1_ports['s']], pdrain_id)
        # tinv1 output
        tinv1_d = self.connect_to_tracks([tinv1_n1_ports['d'], tinv1_p1_ports['d']], nout_id)

        # inv2
        inv2_gn_warr = self.connect_to_tracks(inv2_n_ports['g'], ngate_id, min_len_mode=0)
        inv2_gp_warr = self.connect_to_tracks(inv2_p_ports['g'], pgate_id, min_len_mode=0)
        inv2_g_idx = self.grid.coord_to_nearest_track(inv2_gn_warr.layer_id + 1, inv2_gn_warr.middle)
        inv2_g_tid = TrackID(inv2_gn_warr.layer_id + 1, inv2_g_idx)
        mux_b = self.connect_to_tracks([inv2_gn_warr, inv2_gp_warr, tinv0_d, tinv1_d], inv2_g_tid)
        # inv2 source
        self.connect_to_substrate('ptap', inv2_n_ports['s'])
        self.connect_to_substrate('ntap', inv2_p_ports['s'])
        # inv2 drain
        o = self.connect_to_tracks([inv2_n_ports['d'], inv2_p_ports['d']], pout_id, min_len_mode=1)

        # connect mux control
        sel_i = self.connect_to_tracks([sel_i, tinv0_gp1, tinv1_gn1], selib_id)
        sel_ib = self.connect_to_tracks([sel_ib, tinv0_gn1, tinv1_gp1], seli_id)

        # # get upper metal index
        # self._upper_idx = seli_id.base_index

        # add pins
        self.add_pin('i0', i0, show=show_pins)
        self.add_pin('i1', i1, show=show_pins)
        self.add_pin('sel', sel, show=show_pins)
        self.add_pin('o', o, show=show_pins)

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
            nf_tinv_0=nf_tinv_0,
            nf_tinv_1=nf_tinv_1,
            nf_inv2=nf_inv2,
            intent=intent,
            dum_info=dum_info,
            debug=debug,
        )


