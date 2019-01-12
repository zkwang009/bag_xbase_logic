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


class Buffer(AnalogBase):
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
            intent='transistor threshold',
            ndum='dummy finger number between different transistors',
            ndum_side='dummy finger number between different transistors',
            g_space='gate space in nubmer of tracks',
            ds_space='drain souce space in number of tracks',
            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            show_pins='True to draw pins.',
            out_M5='True to use M5 for output',
            out_n='True to put output wire at NMOS side',
            power_width_ntr='power width in number of tracks',
            invert='True to have 3 stages instead of 2',
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
            out_M5=True,
            out_n=True,
            power_width_ntr=None,
            invert=False,
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, lch, wn, wp, nf_inv0, nf_inv1, ptap_w, ntap_w,
                            g_width_ntr, ds_width_ntr, intent, ndum, ndum_side,
                            invert, show_pins,
                            g_space, ds_space, out_M5, out_n, power_width_ntr, **kwargs):
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
        if nf_inv0%2 != 0 or nf_inv1%2 != 0 :
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        if invert is False:
            fg_tot = ndum_side*2 + ndum*1 + nf_inv0 + nf_inv1
        else:
            fg_tot = ndum_side*2 + ndum*2 + nf_inv0 * 2 + nf_inv1


        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr + g_space]
        pg_tracks = [g_width_ntr + ds_space]
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
        ngate_id = self.make_track_id('nch', 0, 'g', g_space, width=1)
        pgate_id = self.make_track_id('pch', 0, 'g', g_space, width=1)
        nout_id = self.make_track_id('nch', 0, 'ds', 0, width=1)
        pout_id = self.make_track_id('pch', 0, 'ds', 0, width=1)

        # group transistors

        if invert:
            # invx
            invx_n_ports = self.draw_mos_conn('nch', 0, ndum_side, nf_inv0, 1, 1,
                                              s_net='VSS', d_net='data_x')
            invx_p_ports = self.draw_mos_conn('pch', 0, ndum_side, nf_inv0, 1, 1,
                                              s_net='VDD', d_net='data_x')
            # inv0
            inv0_n_ports = self.draw_mos_conn('nch', 0, ndum_side+nf_inv0+ndum,
                                              nf_inv0, 1, 1, s_net='VSS', d_net='data_ob')
            inv0_p_ports = self.draw_mos_conn('pch', 0, ndum_side+nf_inv0+ndum,
                                              nf_inv0, 1, 1, s_net='VDD', d_net='data_ob')
            # inv1
            inv1_n_ports = self.draw_mos_conn('nch', 0, ndum_side + ndum*2 + nf_inv0*2,
                                              nf_inv1, 1, 1, s_net='VSS', d_net='data_o')
            inv1_p_ports = self.draw_mos_conn('pch', 0, ndum_side + ndum*2 + nf_inv0*2,
                                              nf_inv1, 1, 1, s_net='VDD', d_net='data_o')
        else:
            # inv0
            inv0_n_ports = self.draw_mos_conn('nch', 0, ndum_side, nf_inv0, 1, 1,
                                              s_net='VSS', d_net='data_ob')
            inv0_p_ports = self.draw_mos_conn('pch', 0, ndum_side, nf_inv0, 1, 1,
                                              s_net='VDD', d_net='data_ob')
            # inv1
            inv1_n_ports = self.draw_mos_conn('nch', 0, ndum_side+ndum+nf_inv0,
                                              nf_inv1, 1, 1, s_net='VSS', d_net='data_o')
            inv1_p_ports = self.draw_mos_conn('pch', 0, ndum_side+ndum+nf_inv0,
                                              nf_inv1, 1, 1, s_net='VDD', d_net='data_o')




        # connect inv0, inv1
        if invert:
            # invx
            invx_n_warr = self.connect_to_tracks(invx_n_ports['g'], ngate_id, min_len_mode=0)
            invx_p_warr = self.connect_to_tracks(invx_p_ports['g'], pgate_id, min_len_mode=0)
            invx_idx = self.grid.coord_to_nearest_track(invx_n_warr.layer_id + 1, invx_n_warr.middle)
            invx_tid = TrackID(invx_n_warr.layer_id + 1, invx_idx)
            data = self.connect_to_tracks([invx_n_warr, invx_p_warr], invx_tid, min_len_mode=0)

            self.connect_to_substrate('ptap', invx_n_ports['s'])
            self.connect_to_substrate('ntap', invx_p_ports['s'])

        # inv0
        inv0_n_warr = self.connect_to_tracks(inv0_n_ports['g'], ngate_id, min_len_mode=0)
        inv0_p_warr = self.connect_to_tracks(inv0_p_ports['g'], pgate_id, min_len_mode=0)
        inv0_idx = self.grid.coord_to_nearest_track(inv0_n_warr.layer_id + 1, inv0_n_warr.middle)
        inv0_tid = TrackID(inv0_n_warr.layer_id + 1, inv0_idx)
        if invert:
            inv0_g_wire = self.connect_to_tracks([inv0_n_warr, inv0_p_warr], inv0_tid, min_len_mode=0)
            self.connect_to_tracks([invx_n_ports['d'], invx_p_ports['d'], inv0_g_wire], nout_id, min_len_mode=0)
        else:
            data = self.connect_to_tracks([inv0_n_warr, inv0_p_warr], inv0_tid, min_len_mode=0)

        self.connect_to_substrate('ptap', inv0_n_ports['s'])
        self.connect_to_substrate('ntap', inv0_p_ports['s'])

        # inv1
        inv1_n_warr = self.connect_to_tracks(inv1_n_ports['g'], ngate_id, min_len_mode=0)
        inv1_p_warr = self.connect_to_tracks(inv1_p_ports['g'], pgate_id, min_len_mode=0)
        inv1_idx = self.grid.coord_to_nearest_track(inv1_n_warr.layer_id + 1, inv1_n_warr.middle)
        inv1_tid = TrackID(inv1_n_warr.layer_id + 1, inv1_idx)
        inv1_g_wire = self.connect_to_tracks([inv1_n_warr, inv1_p_warr], inv1_tid, min_len_mode=0)
        self.connect_to_tracks([inv0_n_ports['d'], inv0_p_ports['d'], inv1_g_wire], pout_id, min_len_mode=0)
        data_ob = inv1_g_wire

        self.connect_to_substrate('ptap', inv1_n_ports['s'])
        self.connect_to_substrate('ntap', inv1_p_ports['s'])

        if out_n is True:
            out_id = nout_id
        else:
            out_id = pout_id

        data_o = self.connect_to_tracks([inv1_n_ports['d'], inv1_p_ports['d']], out_id, min_len_mode=0)

        if out_M5 is True:
            data_o_idx = self.grid.coord_to_nearest_track(data_o.layer_id+1, data_o.upper)
            data_o_tid = TrackID(data_o.layer_id+1, data_o_idx)
            data_o = self.connect_to_tracks(data_o, data_o_tid, min_len_mode=0)

        # add pins
        self.add_pin('data', data, show=show_pins)
        self.add_pin('data_ob', data_ob, show=show_pins)
        self.add_pin('data_o', data_o, show=show_pins)

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy(vdd_width=power_width_ntr, vss_width=power_width_ntr)

        # export supplies
        self.add_pin(self.get_pin_name('VSS'), ptap_wire_arrs, show=show_pins)
        self.add_pin(self.get_pin_name('VDD'), ntap_wire_arrs, show=show_pins)

        # get size
        self.size = self.grid.get_size_tuple(m5v_layer, width=self.bound_box.width, height=self.bound_box.height,
                                             round_up=True)
        # import pdb
        # pdb.set_trace()

        # get schematic parameters
        dum_info = self.get_sch_dummy_info()
        self._sch_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv0=nf_inv0,
            nf_inv1=nf_inv1,
            intent=intent,
            invert=invert,
            dum_info=dum_info,
        )


