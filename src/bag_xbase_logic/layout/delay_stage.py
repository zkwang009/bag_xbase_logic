# -*- coding: utf-8 -*-


from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# noinspection PyUnresolvedReferences,PyCompatibility
from builtins import *

import bag
import math

from bag.layout.routing import TrackID

from abs_templates_ec.analog_core import AnalogBase, AnalogBaseInfo
from bag.layout.template import TemplateBase, TemplateDB

from bag.layout.util import BBox
from typing import Union
from bag_xbase_logic.layout.dff import DFF
from bag_xbase_logic.layout.buffer import Buffer


class DelStage(TemplateBase):
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
        TemplateBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)
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
            dff_nf_inv0='dff inv0 finger number',
            dff_nf_inv1='dff inv1 finger number',
            dff_nf_inv2='dff inv2 finger number',
            dff_nf_inv3='dff inv3 finger number',
            dff_nf_tinv0_0='dff tinv0 NMOS finger number',
            dff_nf_tinv0_1='dff tinv0 NMOS finger number',
            dff_nf_tinv1_0='dff tinv1 switch NMOS finger number',
            dff_nf_tinv1_1='dff tinv0 NMOS finger number',
            dff_nf_tinv2_0='dff tinv2 switch NMOS finger number',
            dff_nf_tinv2_1='dff tinv0 NMOS finger number',
            dff_nf_tinv3_0='dff tinv3 switch NMOS finger number',
            dff_nf_tinv3_1='dff tinv0 NMOS finger number',
            buf_nf_inv0='buffer inv0 size',
            buf_nf_inv1='buffer inv1 size',
            intent='transistor threshold',
            ndum='dummy finger number between different transistors',
            ndum_side='dummy finger number between different transistors',
            stage='number of delay stages',
            clock_track='clock track width',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            show_pins='True to draw pins.',
            debug='True in debug mode',
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
            debug=False,
            clock_track=1,
            power_width_ntr=None,

        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, lch, wn, wp, dff_nf_inv0, dff_nf_inv1, dff_nf_inv2, dff_nf_inv3,
                            dff_nf_tinv0_0, dff_nf_tinv0_1, dff_nf_tinv1_0, dff_nf_tinv1_1, dff_nf_tinv2_0,
                            dff_nf_tinv2_1, dff_nf_tinv3_0, dff_nf_tinv3_1,
                            buf_nf_inv0, buf_nf_inv1, ptap_w, ntap_w,
                            g_width_ntr, ds_width_ntr, intent, ndum, ndum_side, show_pins,
                            stage, clock_track, power_width_ntr, debug, **kwargs):
        """Draw the layout of a transistor for characterization.
        Notes
        -------
        The number of fingers are for only half (or one side) of the tank.
        Total number should be 2x
        """

        # get resolution
        res = self.grid.resolution

        dff_params = dict(
            lch=lch, 
            wn=wn, 
            wp=wp, 
            nf_inv0=dff_nf_inv0,
            nf_inv1=dff_nf_inv1,
            nf_inv2=dff_nf_inv2,
            nf_inv3=dff_nf_inv3,
            nf_tinv0_0=dff_nf_tinv0_0,
            nf_tinv0_1=dff_nf_tinv0_1,
            nf_tinv1_0=dff_nf_tinv1_0,
            nf_tinv1_1=dff_nf_tinv1_1,
            nf_tinv2_0=dff_nf_tinv2_0,
            nf_tinv2_1=dff_nf_tinv2_1,
            nf_tinv3_0=dff_nf_tinv3_0,
            nf_tinv3_1=dff_nf_tinv3_1,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            intent=intent,
            ndum=ndum,
            ndum_side=ndum_side,
            show_pins=False,
            debug=False,
            power_width_ntr=power_width_ntr,
        )

        dff_master = self.new_template(params=dff_params, temp_cls=DFF, debug=True)

        # get mux size
        dff_toplay, dff_w, dff_h = dff_master.size
        w_pitch_dff, h_pitch_dff = self.grid.get_size_pitch(dff_toplay, unit_mode=True)
        dff_width = dff_w * w_pitch_dff
        dff_height = dff_h * h_pitch_dff

        buf_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv0=buf_nf_inv0,
            nf_inv1=buf_nf_inv1,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            intent=intent,
            ndum=ndum,
            ndum_side=ndum_side,
            show_pins=False,
            out_M5=False,
            g_space=1,
            ds_space=1,
            power_width_ntr=power_width_ntr,
        )

        buf_master = self.new_template(params=buf_params, temp_cls=Buffer, debug=True)
        
        # get buf size
        buf_toplay, buf_w, buf_h = buf_master.size
        w_pitch_buf, h_pitch_buf = self.grid.get_size_pitch(buf_toplay, unit_mode=True)
        buf_width = buf_w * w_pitch_buf
        buf_height = buf_h * h_pitch_buf

        # get instances
        buf_inst = self.add_instance(buf_master, inst_name='BUF', loc=(0, 0))
        dff_inst = []
        for i in range(stage):
            dff_inst.append(self.add_instance(dff_master, inst_name='DFF{}'.format(i),
                                              loc=(buf_width+dff_width*i, 0), orient='R0',
                                              unit_mode=True))

        out_warr = []
        for i in range(stage):
            if i == 0:
                in_warr = dff_inst[i].get_all_port_pins('I')
            if i == stage-1:
                out_warr.append(dff_inst[i].get_all_port_pins('O'))
                continue

            dff_o = dff_inst[i].get_all_port_pins('O')[0]
            dff_i = dff_inst[i+1].get_all_port_pins('I')[0]

            idx = self.grid.coord_to_nearest_track(dff_o.layer_id+1, dff_o.get_bbox_array(self.grid)
                                                   .top_unit, unit_mode=True)
            tid = TrackID(dff_o.layer_id+1, idx)
            out_warr.append(self.connect_to_tracks([dff_o, dff_i], tid))

        # connect VDD/VSS
        vdd_warr = buf_inst.get_all_port_pins('VDD')
        vss_warr = buf_inst.get_all_port_pins('VSS')
        for i in range(stage):
            vdd_warr.append(dff_inst[i].get_all_port_pins('VDD')[0])
            vss_warr.append(dff_inst[i].get_all_port_pins('VSS')[0])

        self.connect_wires(vdd_warr)
        self.connect_wires(vss_warr)

        # connect clock
        clk_i = buf_inst.get_all_port_pins('data_o')[0]
        idx = self.grid.coord_to_nearest_track(clk_i.layer_id+1, clk_i.upper)
        tid = TrackID(clk_i.layer_id+1, idx+1)
        clk_i = self.connect_to_tracks(clk_i, tid, min_len_mode=0)
        idx = self.grid.coord_to_nearest_track(clk_i.layer_id+1, clk_i.get_bbox_array(self.grid).top_unit,
                                               unit_mode=True)
        tid = TrackID(clk_i.layer_id+1, idx, width=clock_track)
        clk_warr = [clk_i]
        for i in range(stage):
            clk_warr.append(dff_inst[i].get_all_port_pins('CLK')[0])
        clk_i = self.connect_to_tracks(clk_warr, tid)
        clk = buf_inst.get_all_port_pins('data')

        # add pins
        self.add_pin('VDD', vdd_warr, show=show_pins)
        self.add_pin('VSS', vss_warr, show=show_pins)
        self.add_pin('clk', clk, show=show_pins)
        self.add_pin('i', in_warr, show=show_pins)
        for i, out in enumerate(out_warr):
            self.add_pin('o<{}>'.format(i), out, show=show_pins)

        if debug is True:
            self.add_pin('clk_i', clk_i, show=show_pins)

        # get size
        # get size and array box
        width = dff_width*stage+buf_width
        height = dff_height
        top_layer = dff_toplay
        w_pitch, h_pitch = self.grid.get_size_pitch(top_layer, unit_mode=True)

        # get block size rounded by top 2 layers pitch
        blk_w = -(-1 * width // w_pitch) * w_pitch
        blk_h = -(-1 * height // h_pitch) * h_pitch

        # get block size based on top 2 layers
        blk_w_tr = blk_w // w_pitch
        blk_h_tr = blk_h // h_pitch

        # size and array box
        self.size = top_layer, blk_w_tr, blk_h_tr
        self.array_box = BBox(0, 0, blk_w, blk_h, res, unit_mode=True)

        # get schematic parameters
        buf_sch_params = buf_master.sch_params
        dff_sch_params = dff_master.sch_params

        self._sch_params = dict(
            buf_sch_params=buf_sch_params,
            dff_sch_params=dff_sch_params,
            stage=stage,
            debug=debug,
        )
