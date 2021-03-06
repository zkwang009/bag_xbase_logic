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


class Inv(AnalogBase):
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
            nfn='inv finger number',
            nfp='inv finger number',
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
            out_M5='True to put out on M5',
            power_width_ntr='power width in number of tracks',
            out_n='True to put output wire at NMOS side',
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
            out_M5=False,
            power_width_ntr=None,
            out_n=True,
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, lch, wn, wp, nfn, nfp, g_space, ds_space, ptap_w, ntap_w,
                            g_width_ntr, ds_width_ntr, intent, ndum_side, show_pins, out_M5,
                            power_width_ntr, out_n,
                            **kwargs):
        """Draw the layout of a transistor for characterization.
        Notes
        -------
        The number of fingers are for only half (or one side) of the tank.
        Total number should be 2x
        """

        # get resolution
        res = self.grid.resolution

        # make sure all fingers are even number
        if nfn%2 != 0 or nfp%2 != 0:
            raise ValueError("Need all finger number to be even!")

        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        fg_tot = ndum_side * 2 + max(nfn, nfp)

        # draw transistor rows
        nw_list = [wn]
        pw_list = [wp]
        nth_list = [intent]
        pth_list = [intent]
        ng_tracks = [g_width_ntr + g_sp_ntr + g_space]
        pg_tracks = [g_width_ntr + g_sp_ntr + g_space]
        nds_tracks = [ds_width_ntr + ds_sp_ntr + ds_space]
        pds_tracks = [ds_width_ntr + ds_sp_ntr + ds_space]
        n_orientation = ['R0']
        p_orientation = ['MX']

        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list,
                       nth_list, pw_list, pth_list,
                       ng_tracks=ng_tracks, nds_tracks=nds_tracks,
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       n_orientations=n_orientation, p_orientations=p_orientation,
                       top_layer=m5v_layer)

        # get gate and drain index
        ngate_id = self.make_track_id('nch', 0, 'g', g_space, width=1)
        pgate_id = self.make_track_id('pch', 0, 'g', g_space, width=1)
        nout_id = self.make_track_id('nch', 0, 'ds', ds_space, width=1)
        pout_id = self.make_track_id('pch', 0, 'ds', ds_space, width=1)
        ndrain_id = self.make_track_id('nch', 0, 'ds', 0, width=1)
        pdrain_id = self.make_track_id('pch', 0, 'ds', 0, width=1)

        # nor
        inv_n_ports = self.draw_mos_conn('nch', 0, ndum_side, nfn, 1, 1,
                                         s_net='VSS', d_net='O')
        inv_p_ports = self.draw_mos_conn('pch', 0, ndum_side, nfp, 1, 1,
                                         s_net='VDD', d_net='O')

        # connect inv
        inv_gn_warr = self.connect_to_tracks(inv_n_ports['g'], ngate_id, min_len_mode=0)
        inv_gp_warr = self.connect_to_tracks(inv_p_ports['g'], pgate_id, min_len_mode=0)
        inv_g_idx = self.grid.coord_to_nearest_track(inv_gn_warr.layer_id + 1, inv_gn_warr.lower)
        inv_g_tid = TrackID(inv_gn_warr.layer_id + 1, inv_g_idx)
        inv_g = self.connect_to_tracks([inv_gn_warr, inv_gp_warr], inv_g_tid)
        # connect drain
        if out_n is True:
            o = self.connect_to_tracks([inv_n_ports['d'], inv_p_ports['d']], nout_id, min_len_mode=0)
        else:
            o = self.connect_to_tracks([inv_n_ports['d'], inv_p_ports['d']], pout_id, min_len_mode=0)

        if out_M5 is True:
            o_idx = self.grid.coord_to_nearest_track(o.layer_id+1, o.upper)
            o_tid = TrackID(o.layer_id+1, o_idx)
            o = self.connect_to_tracks(o, o_tid, min_len_mode=0)

        # connect source
        self.connect_to_substrate('ptap', inv_n_ports['s'])
        self.connect_to_substrate('ntap', inv_p_ports['s'])

        # add pins
        self.add_pin('I', inv_g, show=show_pins)
        self.add_pin('O', o, show=show_pins)

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy(vdd_width=power_width_ntr, vss_width=power_width_ntr)

        # export supplies
        self.add_pin(self.get_pin_name('VSS'), ptap_wire_arrs, show=show_pins)
        self.add_pin(self.get_pin_name('VDD'), ntap_wire_arrs, show=show_pins)

        # # get size
        # self.size = self.grid.get_size_tuple(m5v_layer, width=self.bound_box.width, height=self.bound_box.height,
        #                                      round_up=True)

        # get schematic parameters
        dum_info = self.get_sch_dummy_info()
        self._sch_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nfn=nfn,
            nfp=nfp,
            intent=intent,
            dum_info=dum_info,
        )


