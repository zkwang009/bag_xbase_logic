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


class CtrlBufArr(AnalogBase):
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
            nf_inv0='inv0 NMOS finger number',
            nf_inv1='inv1 NMOS finger number',
            intent='transistor threshold',
            ndum_side='dummy finger number at side',
            ndum='dummy finger number between transistors',
            ndum_cell='dummy finger number between cells',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            show_pins='True to draw pins.',
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
            ndum_cell=None,
            power_width_ntr=None,
            g_space=0,
            ds_space=0,
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
        global ngate_id, pgate_id, out_id, outp_id
        global ndum, ndum_side, ndum_cell, nf_inv0, nf_inv1
        global m4h_layer, m5v_layer
        global fg_cell

        # get parameters
        pi_res = self.params['pi_res']
        lch = self.params['lch']
        wn = self.params['wn']
        wp = self.params['wp']
        nf_inv0 = self.params['nf_inv0']
        nf_inv1 = self.params['nf_inv1']
        ndum = self.params['ndum']
        ndum_side = self.params['ndum_side']
        ndum_cell = self.params['ndum_cell']
        intent = self.params['intent']
        ptap_w = self.params['ptap_w']
        ntap_w = self.params['ntap_w']
        g_width_ntr = self.params['g_width_ntr']
        ds_width_ntr = self.params['ds_width_ntr']
        show_pins = self.params['show_pins']
        power_width_ntr = self.params['power_width_ntr']
        g_space = self.params['g_space']
        ds_space = self.params['ds_space']

        if ndum_cell is None:
            ndum_cell = ndum

        # get resolution
        res = self.grid.resolution

        # finger number
        fg_cell = ndum + ndum_cell + nf_inv0 + nf_inv1
        fg_tot = ndum_side * 2 + fg_cell * (pi_res+2) + ndum*(pi_res+1)

        # make sure all fingers are even number
        if nf_inv0 % 2 != 0 or nf_inv1 % 2 != 0:
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
        ng_tracks = [g_width_ntr+g_space]
        pg_tracks = [g_width_ntr+g_space]
        nds_tracks = [ds_width_ntr+ds_space]
        pds_tracks = [ds_width_ntr+ds_space]
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
        pgate_id = self.make_track_id('pch', 0, 'g', 0, width=g_width_ntr)
        out_id = self.make_track_id('nch', 0, 'ds', 0, width=ds_width_ntr)
        outp_id = self.make_track_id('pch', 0, 'ds', 0, width=ds_width_ntr)

        # define wire array
        dum_in_arr = []
        ctrli_in_arr = []
        ctrlq_in_arr = []
        ctrlib_in_arr = []
        ctrlqb_in_arr = []
        ctrli_o_arr = []
        ctrlq_o_arr = []
        ctrlib_o_arr = []
        ctrlqb_o_arr = []
        ctrli_ob_arr = []
        ctrlq_ob_arr = []
        ctrlib_ob_arr = []
        ctrlqb_ob_arr = []

        # Step1: draw dummy cell
        inv0_in, inv0_out, inv1_out = self.draw_ctrl_buf(idx=0, dum=True)
        dum_in_arr.append(inv0_in)
        inv0_in, inv0_out, inv1_out = self.draw_ctrl_buf(idx=pi_res+1, dum=True)
        dum_in_arr.append(inv0_in)

        # Step2: draw cells
        for i in range(0, pi_res):
            inv0_in, inv0_out, inv1_out = self.draw_ctrl_buf(idx=i+1)
            if i % 4 == 0:
                ctrli_in_arr.append(inv0_in)
                ctrli_o_arr.append(inv1_out)
                ctrli_ob_arr.append(inv0_out)
            elif i % 4 == 1:
                ctrlq_in_arr.append(inv0_in)
                ctrlq_o_arr.append(inv1_out)
                ctrlq_ob_arr.append(inv0_out)
            elif i % 4 == 2:
                ctrlib_in_arr.append(inv0_in)
                ctrlib_o_arr.append(inv1_out)
                ctrlib_ob_arr.append(inv0_out)
            else:
                ctrlqb_in_arr.append(inv0_in)
                ctrlqb_o_arr.append(inv1_out)
                ctrlqb_ob_arr.append(inv0_out)

        ctrl_in_arr = ctrli_in_arr + ctrlq_in_arr + ctrlib_in_arr + ctrlqb_in_arr
        ctrl_o_arr = ctrli_o_arr + ctrlq_o_arr + ctrlib_o_arr + ctrlqb_o_arr
        ctrl_ob_arr = ctrli_ob_arr + ctrlq_ob_arr + ctrlib_ob_arr + ctrlqb_ob_arr

        # add pins
        for i, ctrl_in in enumerate(ctrl_in_arr):
            self.add_pin('ctrl<{}>'.format(i), ctrl_in, show=show_pins)
        for i, ctrl_o in enumerate(ctrl_o_arr):
            self.add_pin('ctrl_o<{}>'.format(i), ctrl_o, show=show_pins)
        for i, ctrl_ob in enumerate(ctrl_ob_arr):
            self.add_pin('ctrl_ob<{}>'.format(i), ctrl_ob, show=show_pins)

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy(vdd_width=power_width_ntr, vss_width=power_width_ntr)

        # connect dummy input to ground
        for dum_in in dum_in_arr:
            self.connect_to_tracks(ptap_wire_arrs, dum_in.track_id,
                                   track_upper=dum_in.get_bbox_array(self.grid).top_unit, unit_mode=True,
                                   min_len_mode=0)

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
            nf_inv0=self.params['nf_inv0'],
            nf_inv1=self.params['nf_inv1'],
            intent=self.params['intent'],
            dum_info=dum_info,
        )

    def draw_ctrl_buf(self, idx, dum=False):

        # Step1: connect inverter
        fg_base = ndum_side+(fg_cell+ndum)*idx
        # group transistors
        if dum is False:
            inv0_n_ports = self.draw_mos_conn('nch', 0, fg_base, nf_inv0, 1, 1, s_net='VSS',
                                              d_net='ctrl_ob<{}>'.format(idx-1))
            inv0_p_ports = self.draw_mos_conn('pch', 0, fg_base, nf_inv1, 1, 1, s_net='VDD',
                                              d_net='ctrl_ob<{}>'.format(idx-1))
        else:
            inv0_n_ports = self.draw_mos_conn('nch', 0, fg_base, nf_inv0, 1, 1, s_net='VSS',
                                              d_net='ctrl_db_{}'.format(idx))
            inv0_p_ports = self.draw_mos_conn('pch', 0, fg_base, nf_inv1, 1, 1, s_net='VDD',
                                              d_net='ctrl_db_{}'.format(idx))

        # connect gate
        ng_inv0_warr = self.connect_to_tracks(inv0_n_ports['g'], ngate_id, min_len_mode=0)
        pg_inv0_warr = self.connect_to_tracks(inv0_p_ports['g'], pgate_id, min_len_mode=0)
        # connect gate vertically
        vgate_idx = self.grid.coord_to_nearest_track(m5v_layer, ng_inv0_warr.middle)
        vgate_tid = TrackID(m5v_layer, vgate_idx)
        inv0_in = self.connect_to_tracks([ng_inv0_warr, pg_inv0_warr], vgate_tid, min_len_mode=0)  # input wire
        # connect drain
        inv0_d = self.connect_to_tracks([inv0_n_ports['d'], inv0_p_ports['d']], outp_id, min_len_mode=0)
        # connect gate
        self.connect_to_substrate('ptap', inv0_n_ports['s'])
        self.connect_to_substrate('ntap', inv0_p_ports['s'])

        # Step2: connect tri-inverter
        # group transistors
        if dum is False:
            inv1_n_ports = self.draw_mos_conn('nch', 0, fg_base + nf_inv0 + ndum, nf_inv1, 1, 1,
                                              s_net='VSS', d_net='ctrl_o<{}>'.format(idx-1))
            inv1_p_ports = self.draw_mos_conn('pch', 0, fg_base + nf_inv0 + ndum, nf_inv1, 1, 1,
                                              s_net='VDD', d_net='ctrl_o<{}>'.format(idx-1))
        else:
            inv1_n_ports = self.draw_mos_conn('nch', 0, fg_base + nf_inv0 + ndum, nf_inv1, 1, 1,
                                              s_net='VSS', d_net='ctrl_d_{}'.format(idx))
            inv1_p_ports = self.draw_mos_conn('pch', 0, fg_base + nf_inv0 + ndum, nf_inv1, 1, 1,
                                              s_net='VDD', d_net='ctrl_d_{}'.format(idx))

        # connect top/bottom MOSs
        # connect gate
        ng_inv1_warr = self.connect_to_tracks(inv1_n_ports['g'], ngate_id, min_len_mode=0)
        pg_inv1_warr = self.connect_to_tracks(inv1_p_ports['g'], pgate_id, min_len_mode=0)
        # connect gate vertically
        vgate_idx = self.grid.coord_to_nearest_track(m5v_layer, ng_inv1_warr.middle)
        vgate_tid = TrackID(m5v_layer, vgate_idx)
        # connect inv0 drain with inv1 gate
        inv0_out = self.connect_to_tracks([inv0_d, ng_inv1_warr, pg_inv1_warr], vgate_tid, min_len_mode=0)
        # inv1_d_warr
        inv1_out = self.connect_to_tracks([inv1_n_ports['d'], inv1_p_ports['d']], out_id, min_len_mode=2)  # output wire
        # connect source
        self.connect_to_substrate('ptap', inv1_n_ports['s'])
        self.connect_to_substrate('ntap', inv1_p_ports['s'])

        return inv0_in, inv0_out, inv1_out
