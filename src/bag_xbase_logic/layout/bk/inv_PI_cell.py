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


class InvPICell(AnalogBase):
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
        self._fg_tot = None
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
            wn='inverter0 NMOS width',
            wp='inverter0 PMOS width',
            nfn_inv0_clk='clk cell inverter0 NMOS finger number',
            nfp_inv0_clk='clk cell inverter0 PMOS finger number',
            nfn_inv1_clk='clk cell inverter1 NMOS finger number',
            nfp_inv1_clk='clk cell inverter1 PMOS finger number',
            intent='transistor threshold',
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

    def _draw_layout_helper(self, cbuf_params, clk_params):
        """Draw the layout of a transistor for characterization.
        Notes
        -------
        The number of fingers are for only half (or one side) of the tank.
        Total number should be 2x
        """

        # get resolution
        res = self.grid.resolution

        # get parameters
        lch = cbuf_params['lch']
        wn = cbuf_params['w']
        wp = cbuf_params['nfn']
        intent = cbuf_params['intent']
        ptap_w = cbuf_params['ptap_w']
        ntap_w = cbuf_params['ntap_w']
        g_width_ntr = cbuf_params['g_width_ntr']
        ds_width_ntr = cbuf_params['ds_width_ntr']
        # ndum
        # show_pins

        # buffer fingers
        nfn_inv0_buf = cbuf_params['nfn_inv0']
        nfn_inv1_buf = cbuf_params['nfn_inv1']
        nfp_inv0_buf = cbuf_params['nfp_inv0']
        nfp_inv1_buf = cbuf_params['nfp_inv1']

        # clk_cell fingers
        nfn_inv_clk = clk_params['nfn_inv']
        nfp_inv_clk = clk_params['nfp_inv']
        nfn_tinv0_clk = clk_params['nfn_tinv0']
        nfn_tinv1_clk = clk_params['nfn_tinv1']
        nfp_tinv0_clk = clk_params['nfp_tinv0']
        nfp_tinv1_clk = clk_params['nfp_tinv1']


        # get layer separation space
        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)
        m4h_layer = layout_info.mconn_port_layer + 1
        m5v_layer = layout_info.mconn_port_layer + 2
        g_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, g_width_ntr)
        ds_sp_ntr = self.grid.get_num_space_tracks(m4h_layer, ds_width_ntr)

        fg_tot = round(self.find_fg_tot(res, lch, width) / 4) * 4
        print(fg_tot)

        # some constant
        wm5_unit = 16

        # check nfn
        if nfn % 4 != 0:
            raise ValueError("To guarantee even finger number, need 'nfn' being divisible by 4!")
        nfn_cal = int(nfn/2)    # divide finger number by 2, as we will have even/odd rows
        
        # calculate row number and fingers per row
        fg_eff = int((fg_tot - ndum_min*2 - ndum_cen*2) / 2)    # max effective finger numbers in a row
        row = math.ceil(nfn_cal/fg_eff)     # row number
        avg = math.ceil(nfn_cal/row)   # avg number per row
        if avg % 2 != 0:
            avg += 1
        rem = nfn_cal - (row-1) * avg   # finger number in last row
        ndum1 = int((fg_tot - avg*2 - ndum_cen*2) / 2)  # dummy finger number except last row
        ndum2 = int((fg_tot - rem*2 - ndum_cen*2) / 2)  # dummy finger number for last row

        # draw transistor rows
        nw_list = [w, w] * row
        pw_list = []
        nth_list = [intent, intent] * row
        pth_list = []
        num_track_sep = 1
        ng_tracks = [g_width_ntr+g_sp_ntr, 0] * row
        # ng_tracks = [g_width_ntr, 0] * row
        pg_tracks = []
        # need have some gap for drain/source connection
        # also we try to share tracks for different row to make area smaller
        if row == 1:
            nds_tracks = [ds_width_ntr*2 + ds_sp_ntr, ds_width_ntr*2 + ds_sp_ntr]
        elif row == 2:
            nds_tracks = [ds_width_ntr*2 + ds_sp_ntr, ds_width_ntr,
                          ds_width_ntr, ds_width_ntr*2 + ds_sp_ntr]
        else:
            nds_tracks = [ds_width_ntr*2 + ds_sp_ntr, ds_width_ntr+ds_sp_ntr] + \
                         [ds_width_ntr, ds_width_ntr+ds_sp_ntr] * (row-2) + \
                         [ds_width_ntr, ds_width_ntr*2 + ds_sp_ntr]
        pds_tracks = []
        n_orientation = ['MX', 'R0'] * row
        self.draw_base(lch, fg_tot, ptap_w, ntap_w, nw_list,
                       nth_list, pw_list, pth_list, num_track_sep,
                       ng_tracks=ng_tracks, nds_tracks=nds_tracks,
                       pg_tracks=pg_tracks, pds_tracks=pds_tracks,
                       n_orientations=n_orientation, p_orientations=[],
                       )

        # initial some list for metals
        gleft_warr = []
        gright_warr = []
        deven_warr = []
        dodd_warr = []
        seven_warr = []
        sodd_warr = []

        # vertical M5 width
        wm5 = math.ceil(min(avg, rem)/wm5_unit)

        for i in range(row):
            # get gate track ID
            gate_id = self.make_track_id('nch', 2*i, 'g', 0, width=g_width_ntr)
            # get output track ID
            if i == 0:
                if row == 1:
                    deven_id = self.make_track_id('nch', 0, 'ds', 0, width=ds_width_ntr)
                    seven_id = self.make_track_id('nch', 0, 'ds', 1, width=ds_width_ntr)
                    dodd_id = self.make_track_id('nch', 1, 'ds', 0, width=ds_width_ntr)
                    sodd_id = self.make_track_id('nch', 1, 'ds', 1, width=ds_width_ntr)
                else:
                    deven_id = self.make_track_id('nch', 0, 'ds', 0, width=ds_width_ntr)
                    seven_id = self.make_track_id('nch', 0, 'ds', 1, width=ds_width_ntr)
                    dodd_id = self.make_track_id('nch', 1, 'ds', 0, width=ds_width_ntr)
                    sodd_id = self.make_track_id('nch', 2, 'ds', 0, width=ds_width_ntr)
            elif i == row-1:
                deven_id = self.make_track_id('nch', 2*i-1, 'ds', 0, width=ds_width_ntr)
                seven_id = self.make_track_id('nch', 2*i, 'ds', 0, width=ds_width_ntr)
                dodd_id = self.make_track_id('nch', 2*i+1, 'ds', 0, width=ds_width_ntr)
                sodd_id = self.make_track_id('nch', 2*i+1, 'ds', 1, width=ds_width_ntr)
            else:
                deven_id = self.make_track_id('nch', 2*i-1, 'ds', 0, width=ds_width_ntr)
                seven_id = self.make_track_id('nch', 2*i, 'ds', 0, width=ds_width_ntr)
                dodd_id = self.make_track_id('nch', 2*i+1, 'ds', 0, width=ds_width_ntr)
                sodd_id = self.make_track_id('nch', 2*i+2, 'ds', 0, width=ds_width_ntr)

            if i == row-1:
                # get ports
                leven_ports = self.draw_mos_conn('nch', 2*i, ndum2, rem, 1, 1)
                reven_ports = self.draw_mos_conn('nch', 2*i, ndum2+rem+ndum_cen*2, rem, 1, 1)
                lodd_ports = self.draw_mos_conn('nch', 2*i+1, ndum2, rem, 1, 1)
                rodd_ports = self.draw_mos_conn('nch', 2*i+1, ndum2+rem+ndum_cen*2, rem, 1, 1)
            else:
                # get ports
                leven_ports = self.draw_mos_conn('nch', 2*i, ndum1, avg, 1, 1)
                reven_ports = self.draw_mos_conn('nch', 2*i, ndum1+avg+ndum_cen*2, avg, 1, 1)
                lodd_ports = self.draw_mos_conn('nch', 2*i+1, ndum1, avg, 1, 1)
                rodd_ports = self.draw_mos_conn('nch', 2*i+1, ndum1+avg+ndum_cen*2, avg, 1, 1)

            # connect gates on both side
            gright_warr.append(self.connect_to_tracks([reven_ports['g']] + [rodd_ports['g']],
                                                     gate_id))
            gleft_warr.append(self.connect_to_tracks([leven_ports['g']] + [lodd_ports['g']],
                                                      gate_id))

            # connect drain/source
            deven_warr.append(self.connect_to_tracks([leven_ports['d'], reven_ports['d']], deven_id))
            seven_warr.append(self.connect_to_tracks([leven_ports['s'], reven_ports['s']], seven_id))
            dodd_warr.append(self.connect_to_tracks([lodd_ports['d'], rodd_ports['d']], dodd_id))
            sodd_warr.append(self.connect_to_tracks([lodd_ports['s'], rodd_ports['s']], sodd_id))

        # connect all vctrl vertically
        vctrl_idx = self.grid.coord_to_nearest_track(m5v_layer, self.bound_box.xc, half_track=True)
        vctrl_tid = TrackID(m5v_layer, vctrl_idx, width=1)
        # vctrl = self.connect_to_tracks(seven_warr, vctrl_tid)
        vctrl = self.connect_to_tracks(deven_warr+seven_warr+dodd_warr+sodd_warr, vctrl_tid)
        self.add_pin(self.get_pin_name('VCTRL'), vctrl, show=show_pins)

        # connect all output vertically for left side
        out_idx_left = self.grid.coord_to_nearest_track(m5v_layer, gleft_warr[-1].middle,
                                                        half_track=True)
        out_tid_left = TrackID(m5v_layer, out_idx_left, width=wm5)
        out_left = self.connect_to_tracks(gleft_warr, out_tid_left)
        self.add_pin(self.get_pin_name('OUTP'), out_left, show=show_pins)

        # right side
        out_idx_right = self.grid.coord_to_nearest_track(m5v_layer, gright_warr[-1].middle,
                                                         half_track=True)
        out_tid_right = TrackID(m5v_layer, out_idx_right, width=wm5)
        out_right = self.connect_to_tracks(gright_warr, out_tid_right)
        self.add_pin(self.get_pin_name('OUTN'), out_right, show=show_pins)

        # draw dummies
        ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy(vdd_width=power_width_ntr, vss_width=power_width_ntr)

        # export supplies
        self.add_pin(self.get_pin_name('VSS'), ptap_wire_arrs, show=show_pins)
        self.add_pin(self.get_pin_name('VDD'), ntap_wire_arrs, show=show_pins)

        # get size of block in resolution
        blk_w = self.bound_box.width_unit
        blk_h = self.bound_box.top_unit
        # blk_w, blk_h = self.grid.get_size_dimension(self.size, unit_mode=True)

        # get pitch of top 2 layers
        w_pitch, h_pitch = self.grid.get_size_pitch(m5v_layer, unit_mode=True)
        # print([w_pitch, h_pitch])

        # get size rounded to top 2 layers pitch
        blk_w_new = -(-blk_w // w_pitch)
        blk_h_new = -(-blk_h // h_pitch)

        # get size and array box
        self.size = m5v_layer, blk_w_new, blk_h_new
        self.array_box = BBox(0, 0, blk_w, blk_h, res, unit_mode=True)

        # get fg_tot
        self._fg_tot = fg_tot

        self._sch_params = dict(
            lch=self.params['lch'],
            w=self.params['w'],
            nfn=self.params['nfn'],
            fg_wid=self._fg_tot,
            ndum_min=self.params['ndum_min'],
            ndum_cen=self.params['ndum_cen'],
            intent=self.params['intent'],
        )

    def find_fg_tot(self, res, lch, width, larger_mode=False, unit_mode=True):
        # type: (float, float, Union[float, int], bool, bool) -> int
        """
        find track width just larger than given width
        will be done by eric in future
        Parameters
        -------------
        res: float
            the layout grid resolution.
        layer: int
            metal layer id
        width: float
            width of metal layer
        larger_mode: bool
            find larger track or smaller track
        unit_mode: bool
            True if width and points are given as resolution units instead of layout units.

        Return
        -------------
            track width
        """

        layout_info = AnalogBaseInfo(self.grid.copy(), lch, 0)

        if unit_mode is False:
            width = round(width / res)

        width_try = 0
        i = 0
        while width >= width_try:
            i += 1
            width_try = layout_info.get_total_width(i)

        if larger_mode is True:
            return i
        else:
            return i-1

