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


class ClkCellArr(AnalogBase):
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
            pi_res='phase interpolator resolution',
            lch='transistor channel length',
            wn='NMOS width',
            wp='PMOS width',
            nf_inv='inv NMOS finger number',
            nf_tinv0='tinv NMOS finger number',
            nf_tinv1='tinv switch NMOS finger number',
            intent='transistor threshold',
            ndum_side='dummy finger number at side',
            ndum='dummy finger number between cells',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            show_pins='True to draw pins.',
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
            power_width_ntr=None,
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

        # define some global variables
        global ngate_id, ngate1_id, pgate_id, out_id, outp_id, ndrain_id, pdrain_id
        global ndum, ndum_side, nf_inv, nf_tinv0, nf_tinv1
        global m4h_layer, m5v_layer
        global fg_cell

        # get parameters
        pi_res = self.params['pi_res']
        lch = self.params['lch']
        wn = self.params['wn']
        wp = self.params['wp']
        nf_inv = self.params['nf_inv']
        nf_inv = self.params['nf_inv']
        nf_tinv0 = self.params['nf_tinv0']
        nf_tinv0 = self.params['nf_tinv0']
        nf_tinv1 = self.params['nf_tinv1']
        nf_tinv1 = self.params['nf_tinv1']
        ndum = self.params['ndum']
        ndum_side = self.params['ndum_side']
        intent = self.params['intent']
        ptap_w = self.params['ptap_w']
        ntap_w = self.params['ntap_w']
        g_width_ntr = self.params['g_width_ntr']
        ds_width_ntr = self.params['ds_width_ntr']
        show_pins = self.params['show_pins']
        power_width_ntr = self.params['power_width_ntr']

        # get resolution
        res = self.grid.resolution

        # finger number
        fg_cell = ndum * 2 + max(nf_inv, nf_inv) + max(nf_tinv0, nf_tinv0) + max(nf_tinv1, nf_tinv1)
        fg_tot = ndum_side * 2 + fg_cell * (pi_res+2) + ndum*(pi_res+1)

        # make sure all fingers are even number
        if nf_inv % 2 != 0 or nf_inv % 2 != 0 or nf_tinv0 % 2 != 0 or nf_tinv1 % 2 != 0 or\
            nf_tinv0 % 2 != 0 or nf_tinv1 % 2 != 0:
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr*2]
        pg_tracks = [g_width_ntr*2]
        nds_tracks = [ds_width_ntr*2]
        pds_tracks = [ds_width_ntr*2]
        n_orientation = ['R0']
        p_orientation = ['MX']

        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list,
                       nth_list, pw_list, pth_list,
                       ng_tracks=ng_tracks, nds_tracks=nds_tracks,
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       n_orientations=n_orientation, p_orientations=p_orientation,
                       top_layer=m5v_layer)

        # get gate and draiin index
        ngate_id = self.make_track_id('nch', 0, 'g', 0, width=g_width_ntr)
        ngate1_id = self.make_track_id('nch', 0, 'g', 1, width=g_width_ntr)
        pgate_id = self.make_track_id('pch', 0, 'g', 0, width=g_width_ntr)
        out_id = self.make_track_id('nch', 0, 'ds', 1, width=ds_width_ntr)
        outp_id = self.make_track_id('pch', 0, 'ds', 1, width=ds_width_ntr)
        ndrain_id = self.make_track_id('nch', 0, 'ds', 0, width=ds_width_ntr)
        pdrain_id = self.make_track_id('pch', 0, 'ds', 0, width=ds_width_ntr)

        # define wire array
        dum_in_arr = []
        dum_ctrl_arr = []
        dum_ctrlb_arr = []
        clk_i_arr = []
        clk_q_arr = []
        clk_ib_arr = []
        clk_qb_arr = []
        clko_arr = []
        ctrli_arr = []
        ctrli_b_arr = []
        ctrlq_arr = []
        ctrlq_b_arr = []
        ctrlib_arr = []
        ctrlib_b_arr = []
        ctrlqb_arr = []
        ctrlqb_b_arr = []

        # draw dummy
        inv_in, ng_tinv1, pg_tinv1, tinv_out = self.draw_clk_cell(idx=0, dum=True)
        dum_in_arr.append(inv_in)
        dum_ctrl_arr.append(ng_tinv1)
        dum_ctrlb_arr.append(pg_tinv1)

        inv_in, ng_tinv1, pg_tinv1, tinv_out = self.draw_clk_cell(idx=pi_res+1, dum=True)
        dum_in_arr.append(inv_in)
        dum_ctrl_arr.append(ng_tinv1)
        dum_ctrlb_arr.append(pg_tinv1)

        for i in range(pi_res):
            # draw clk cell
            inv_in, ng_tinv1, pg_tinv1, tinv_out = self.draw_clk_cell(idx=i+1)      # 1 is for dummy
            if i % 4 == 0:
                clk_i_arr.append(inv_in)
                ctrli_arr.append(ng_tinv1)
                ctrli_b_arr.append(pg_tinv1)
                clko_arr.append(tinv_out)
            elif i % 4 == 1:
                clk_q_arr.append(inv_in)
                ctrlq_arr.append(ng_tinv1)
                ctrlq_b_arr.append(pg_tinv1)
                clko_arr.append(tinv_out)
            elif i % 4 == 2:
                clk_ib_arr.append(inv_in)
                ctrlib_arr.append(ng_tinv1)
                ctrlib_b_arr.append(pg_tinv1)
                clko_arr.append(tinv_out)
            else:
                clk_qb_arr.append(inv_in)
                ctrlqb_arr.append(ng_tinv1)
                ctrlqb_b_arr.append(pg_tinv1)
                clko_arr.append(tinv_out)

        ctrl_arr = ctrli_arr + ctrlq_arr + ctrlib_arr + ctrlqb_arr
        ctrlb_arr = ctrli_b_arr + ctrlq_b_arr + ctrlib_b_arr + ctrlqb_b_arr

        # connect all clk_i_arr
        idx = self.grid.coord_to_nearest_track(clk_i_arr[0].layer_id+1,
                                               clk_i_arr[0].get_bbox_array(self.grid).bottom_unit, unit_mode=True)
        tid_i = TrackID(clk_i_arr[0].layer_id+1, idx+1)
        tid_q = TrackID(clk_i_arr[0].layer_id+1, idx+2)
        tid_ib = TrackID(clk_i_arr[0].layer_id+1, idx+3)
        tid_qb = TrackID(clk_i_arr[0].layer_id+1, idx+4)

        clk_i = self.connect_to_tracks(clk_i_arr, tid_i, min_len_mode=0)
        clk_q = self.connect_to_tracks(clk_q_arr, tid_q, min_len_mode=0)
        clk_ib = self.connect_to_tracks(clk_ib_arr, tid_ib, min_len_mode=0)
        clk_qb = self.connect_to_tracks(clk_qb_arr, tid_qb, min_len_mode=0)

        # connect all clk_o
        idx = self.grid.coord_to_nearest_track(clko_arr[0].layer_id + 1,
                                               clk_i_arr[0].get_bbox_array(self.grid).top_unit, unit_mode=True)
        tid = TrackID(clko_arr[0].layer_id+1, idx+2)
        clko = self.connect_to_tracks(clko_arr, tid, min_len_mode=0)

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy(vdd_width=power_width_ntr, vss_width=power_width_ntr)

        # connect dummy
        for dum_in in dum_in_arr:
            self.connect_to_tracks(ptap_wire_arrs, dum_in.track_id,
                                   track_upper=dum_in.get_bbox_array(self.grid).top_unit,
                                   unit_mode=True, min_len_mode=0)
        for dum_ctrl in dum_ctrl_arr:
            idx = self.grid.coord_to_nearest_track(dum_ctrl.layer_id+1, dum_ctrl.middle)
            tid = TrackID(dum_ctrl.layer_id+1, idx)
            self.connect_to_tracks([ptap_wire_arrs[0], dum_ctrl], tid,
                                   track_lower=dum_ctrl.get_bbox_array(self.grid).top_unit, min_len_mode=0)
        for dum_ctrlb in dum_ctrlb_arr:
            idx = self.grid.coord_to_nearest_track(dum_ctrlb.layer_id + 1, dum_ctrlb.middle)
            tid = TrackID(dum_ctrlb.layer_id + 1, idx)
            self.connect_to_tracks([ntap_wire_arrs[0], dum_ctrlb], tid,
                                   track_lower=dum_ctrlb.get_bbox_array(self.grid).top_unit, min_len_mode=0)

        # add pins
        self.add_pin('clko', clko, show=show_pins)
        self.add_pin('clk_i', clk_i, show=show_pins)
        self.add_pin('clk_q', clk_q, show=show_pins)
        self.add_pin('clk_ib', clk_ib, show=show_pins)
        self.add_pin('clk_qb', clk_qb, show=show_pins)
        for i, ctrl in enumerate(ctrl_arr):
            self.add_pin('ctrl<{}>'.format(i), ctrl, show=show_pins)
        for i, ctrlb in enumerate(ctrlb_arr):
            self.add_pin('ctrlb<{}>'.format(i), ctrlb, show=show_pins)
        # export supplies
        self.add_pin(self.get_pin_name('VSS'), ptap_wire_arrs, show=show_pins)
        self.add_pin(self.get_pin_name('VDD'), ntap_wire_arrs, show=show_pins)

        # get schematic parameters
        dum_info = self.get_sch_dummy_info()
        self._sch_params = dict(
            pi_res=self.params['pi_res'],
            lch=self.params['lch'],
            wn=self.params['wn'],
            wp=self.params['wp'],
            nf_inv=self.params['nf_inv'],
            nf_tinv0=self.params['nf_tinv0'],
            nf_tinv1=self.params['nf_tinv1'],
            intent=self.params['intent'],
            dum_info=dum_info,
        )

    def draw_clk_cell(self, idx, dum=False):

        # Step1: connect inverter
        fg_base = ndum_side+(fg_cell+ndum)*idx
        # group transistors
        if dum is False:
            inv_n_ports = self.draw_mos_conn('nch', 0, fg_base, nf_inv, 1, 1, s_net='VSS', d_net='clk_m{}'.format(idx))
            inv_p_ports = self.draw_mos_conn('pch', 0, fg_base, nf_inv, 1, 1, s_net='VDD', d_net='clk_m{}'.format(idx))
        else:
            inv_n_ports = self.draw_mos_conn('nch', 0, fg_base, nf_inv, 1, 1, s_net='VSS', d_net='clk_md{}'.format(idx))
            inv_p_ports = self.draw_mos_conn('pch', 0, fg_base, nf_inv, 1, 1, s_net='VDD', d_net='clk_md{}'.format(idx))

        # connect gate
        ng_inv = self.connect_to_tracks(inv_n_ports['g'], ngate_id, min_len_mode=0)
        pg_inv = self.connect_to_tracks(inv_p_ports['g'], pgate_id, min_len_mode=0)
        # connect gate vertically
        vgate_idx = self.grid.coord_to_nearest_track(m5v_layer, ng_inv.middle)
        vgate_tid = TrackID(m5v_layer, vgate_idx)
        inv_in = self.connect_to_tracks([ng_inv, pg_inv], vgate_tid, min_len_mode=0)  # input wire
        # connect drain
        inv_d_warr = self.connect_to_tracks([inv_n_ports['d'], inv_p_ports['d']], out_id, min_len_mode=0)
        # connect gate
        self.connect_to_substrate('ptap', inv_n_ports['s'])
        self.connect_to_substrate('ntap', inv_p_ports['s'])

        # Step2: connect tri-inverter
        # group transistors
        if dum is False:
            tinv0_n_ports = self.draw_mos_conn('nch', 0, fg_base + nf_inv + ndum, nf_tinv0, 1, 1, s_net='VSS',
                                               d_net='ns_{}'.format(idx))
            tinv0_p_ports = self.draw_mos_conn('pch', 0, fg_base + nf_inv + ndum, nf_tinv0, 1, 1, s_net='VDD',
                                               d_net='ps_{}'.format(idx))
            tinv1_n_ports = self.draw_mos_conn('nch', 0, fg_base + nf_tinv0 + nf_inv + 2 * ndum, nf_tinv1, 1, 1,
                                               s_net='ns_{}'.format(idx), d_net='clko')
            tinv1_p_ports = self.draw_mos_conn('pch', 0, fg_base + nf_tinv0 + nf_inv + 2 * ndum, nf_tinv1, 1, 1,
                                               s_net='ps_{}'.format(idx), d_net='clko')
        else:
            tinv0_n_ports = self.draw_mos_conn('nch', 0, fg_base + nf_inv + ndum, nf_tinv0, 1, 1, s_net='VSS',
                                               d_net='ns_d_{}'.format(idx))
            tinv0_p_ports = self.draw_mos_conn('pch', 0, fg_base + nf_inv + ndum, nf_tinv0, 1, 1, s_net='VDD',
                                               d_net='ps_d_{}'.format(idx))
            tinv1_n_ports = self.draw_mos_conn('nch', 0, fg_base + nf_tinv0 + nf_inv + 2 * ndum, nf_tinv1, 1, 1,
                                               s_net='ns_d_{}'.format(idx))     # d_net is floating
            tinv1_p_ports = self.draw_mos_conn('pch', 0, fg_base + nf_tinv0 + nf_inv + 2 * ndum, nf_tinv1, 1, 1,
                                               s_net='ps_d_{}'.format(idx))     # d_net is floating

        # connect top/bottom MOSs
        # connect gate
        ng_tinv0 = self.connect_to_tracks(tinv0_n_ports['g'], ngate1_id, min_len_mode=0)
        pg_tinv0 = self.connect_to_tracks(tinv0_p_ports['g'], pgate_id, min_len_mode=0)
        # connect gate vertically
        vgate_idx = self.grid.coord_to_nearest_track(m5v_layer, ng_tinv0.middle)
        vgate_tid = TrackID(m5v_layer, vgate_idx)
        # also connect inverter drain
        tinv0_g = self.connect_to_tracks([inv_d_warr, ng_tinv0, pg_tinv0], vgate_tid, min_len_mode=0)

        # connect middle MOSs
        ng_tinv1 = self.connect_to_tracks(tinv1_n_ports['g'], ngate_id, min_len_mode=0)  # input wire
        pg_tinv1 = self.connect_to_tracks(tinv1_p_ports['g'], pgate_id, min_len_mode=0)  # input wire
        # connect source
        ns_tinv0 = self.connect_to_tracks([tinv0_n_ports['d'], tinv1_n_ports['s']], ndrain_id, min_len_mode=0)
        ps_tinv0 = self.connect_to_tracks([tinv0_p_ports['d'], tinv1_p_ports['s']], pdrain_id, min_len_mode=0)
        # connect drain
        tinv_out = self.connect_to_tracks([tinv1_n_ports['d'], tinv1_p_ports['d']], outp_id, min_len_mode=0)  # output wire
        # connect source
        self.connect_to_substrate('ptap', tinv0_n_ports['s'])
        self.connect_to_substrate('ntap', tinv0_p_ports['s'])
        # connect middl
        idx = self.grid.coord_to_nearest_track(tinv_out.layer_id+1, tinv_out.middle)
        tid = TrackID(tinv_out.layer_id+1, idx+1)
        tinv_out = self.connect_to_tracks(tinv_out, tid, min_len_mode=0)

        return inv_in, ng_tinv1, pg_tinv1, tinv_out
