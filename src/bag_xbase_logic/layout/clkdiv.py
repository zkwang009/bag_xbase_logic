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
from bag_xbase_logic.layout.dff_strst import DFFStRst
from bag_xbase_logic.layout.buffer import Buffer
from bag_xbase_logic.layout.xor import XOR


class ClkDiv(TemplateBase):
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
            dff_nf_inv0='inv0 finger number',
            dff_nf_inv1='inv1 finger number',
            dff_nf_inv2='inv2 finger number',
            dff_nf_inv3='inv3 finger number',
            dff_nf_tinv0_0='tinv0 NMOS finger number',
            dff_nf_tinv0_1='tinv0 NMOS finger number',
            dff_nf_tinv1_0='tinv1 switch NMOS finger number',
            dff_nf_tinv1_1='tinv0 NMOS finger number',
            dff_nfn_nand0='nand0 NMOS finger number',
            dff_nfp_nand0='nand0 PMOS finger number',
            dff_nfn_nand1='nand1 NMOS finger number',
            dff_nfp_nand1='nand1 PMOS finger number',
            dff_nfn_nand2='nand2 NMOS finger number',
            dff_nfp_nand2='nand2 PMOS finger number',
            dff_nfn_nand3='nand3 NMOS finger number',
            dff_nfp_nand3='nand3 PMOS finger number',
            dff_nf_tgate0='tgate0 MOS finger number',
            dff_nf_tgate1='tgate1 MOS finger number',
            buf_nf_inv0='buffer inv0 size',
            buf_nf_inv1='buffer inv1 size',

            intent='transistor threshold',
            ndum='dummy finger number between different transistors',
            ndum_side='dummy finger number between different transistors',
            div_ratio='divider ratio',
            clock_track='clock track width',
            clk_rst_sp='clk rst space in tracks',
            rst_list='rst list for each dff',
            out_list='output list for dffs',

            ptap_w='NMOS substrate width, in meters/number of fins.',
            ntap_w='PMOS substrate width, in meters/number of fins.',
            g_width_ntr='gate track width in number of tracks.',
            ds_width_ntr='source/drain track width in number of tracks.',
            power_width_ntr='power width in number of tracks',
            show_pins='True to draw pins.',
            debug='True in debug mode',
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
            rst_list=None,
            clk_rst_sp=2,
            out_list=None,
            power_width_ntr=None,
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, lch, wn, wp, dff_nf_inv0, dff_nf_inv1, dff_nf_inv2, dff_nf_inv3,
                            dff_nf_tinv0_0, dff_nf_tinv0_1, dff_nf_tinv1_0, dff_nf_tinv1_1, dff_nfn_nand0,
                            dff_nfp_nand0, dff_nfn_nand1, dff_nfp_nand1, dff_nfn_nand2, dff_nfp_nand2,
                            dff_nfn_nand3, dff_nfp_nand3, dff_nf_tgate0, dff_nf_tgate1,
                            buf_nf_inv0, buf_nf_inv1, ptap_w, ntap_w,
                            g_width_ntr, ds_width_ntr, intent, ndum, ndum_side, show_pins, power_width_ntr,
                            div_ratio, rst_list, clk_rst_sp, clock_track, out_list, debug, **kwargs):
        """Draw the layout of a transistor for characterization.
        Notes
        -------
        The number of fingers are for only half (or one side) of the tank.
        Total number should be 2x
        """

        # get resolution
        res = self.grid.resolution

        # get rst_list
        if rst_list is None:
            rst_list = []
            for i in range(div_ratio):
                if i < div_ratio//2:
                    rst_list.append(1)
                else:
                    rst_list.append(0)

        if out_list is None:
            out_list = [div_ratio-1]
        out_list = sorted(out_list)
        # print(out_list)

        for i in out_list:
            if i not in list(range(div_ratio)):
                raise ValueError("out_list have value out of bound")

        # get dff
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
            nfn_nand0=dff_nfn_nand0,
            nfp_nand0=dff_nfp_nand0,
            nfn_nand1=dff_nfn_nand1,
            nfp_nand1=dff_nfp_nand1,
            nfn_nand2=dff_nfn_nand2,
            nfp_nand2=dff_nfp_nand2,
            nfn_nand3=dff_nfn_nand3,
            nfp_nand3=dff_nfp_nand3,
            nf_tgate0=dff_nf_tgate0,
            nf_tgate1=dff_nf_tgate1,
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

        dff_master = self.new_template(params=dff_params, temp_cls=DFFStRst, debug=True)

        # get mux size
        dff_toplay, dff_w, dff_h = dff_master.size
        w_pitch_dff, h_pitch_dff = self.grid.get_size_pitch(dff_toplay, unit_mode=True)
        dff_width = dff_w * w_pitch_dff
        dff_height = dff_h * h_pitch_dff

        # get buffer
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
            g_space=2,
            ds_space=2,
            power_width_ntr=power_width_ntr,
        )

        buf_master = self.new_template(params=buf_params, temp_cls=Buffer, debug=True)
        
        # get buf size
        buf_toplay, buf_w, buf_h = buf_master.size
        w_pitch_buf, h_pitch_buf = self.grid.get_size_pitch(buf_toplay, unit_mode=True)
        buf_width = buf_w * w_pitch_buf
        buf_height = buf_h * h_pitch_buf

        # get instances
        rstbuf_inst = self.add_instance(buf_master, inst_name='RSTBUF', loc=(0, 0))
        clkbuf_inst = self.add_instance(buf_master, inst_name='CLKBUF', loc=(buf_width, 0),
                                        unit_mode=True)
        dff_inst = []
        # place all stages
        # import pdb
        # pdb.set_trace()

        for i in range(div_ratio):
            if i%2 == 0:
                dff_inst.append(self.add_instance(dff_master, inst_name='DFF{}'.format(i),
                                                  loc=(buf_width*2+dff_width*i, 0), orient='R0',
                                                  unit_mode=True))
            else:
                dff_inst.append(self.add_instance(dff_master, inst_name='DFF{}'.format(i),
                                                  loc=(buf_width*2+dff_width * (i+1), 0), orient='MY',
                                                  unit_mode=True))

        # connect clock
        clk_i = clkbuf_inst.get_all_port_pins('data_o')[0]
        clk_idx = self.grid.coord_to_nearest_track(clk_i.layer_id + 1, clk_i.get_bbox_array(self.grid).top_unit,
                                                   unit_mode=True)
        tid = TrackID(clk_i.layer_id + 1, clk_idx, width=clock_track)
        clk_warr = [clk_i]
        for i in range(div_ratio):
            clk_warr.append(dff_inst[i].get_all_port_pins('CLK')[0])
        clk_i = self.connect_to_tracks(clk_warr, tid)
        clk = clkbuf_inst.get_all_port_pins('data')

        # connect dff input and output, also connect rst/st
        rst_warr = []
        out_warr = []
        if div_ratio % 2 == 0:
            # connect between different ffs
            for i in range(div_ratio):
                if 2 * (i+1) < div_ratio:
                    dff_o = dff_inst[2*i].get_all_port_pins('O', layer=dff_toplay)[0]
                    dff_i = dff_inst[2*(i+1)].get_all_port_pins('I')[0]
                    idx = self.grid.coord_to_nearest_track(dff_o.layer_id+1, dff_o.get_bbox_array(self.grid)
                                                           .top_unit, unit_mode=True)
                    tid = TrackID(dff_o.layer_id+1, idx)
                    self.connect_to_tracks([dff_o, dff_i], tid)

                    # get rst/st vss
                    rst = dff_inst[2*i].get_all_port_pins('RST')[0]
                    st = dff_inst[2*i].get_all_port_pins('ST')[0]
                    vss = dff_inst[2*i].get_all_port_pins('VSS')[0]

                elif 2 * (i+1) == div_ratio:
                    dff_o = dff_inst[2*i].get_all_port_pins('O', layer=dff_toplay)[0]
                    dff_i = dff_inst[2*i+1].get_all_port_pins('I')[0]
                    idx = self.grid.coord_to_nearest_track(dff_o.layer_id + 1, dff_o.get_bbox_array(self.grid)
                                                           .top_unit, unit_mode=True)
                    tid = TrackID(dff_o.layer_id + 1, idx)
                    self.connect_to_tracks([dff_o, dff_i], tid)

                    # get rst/st vss
                    rst = dff_inst[2 * i].get_all_port_pins('RST')[0]
                    st = dff_inst[2 * i].get_all_port_pins('ST')[0]
                    vss = dff_inst[2 * i].get_all_port_pins('VSS')[0]
                else:
                    if i != div_ratio-1:
                        idx1 = 2 * div_ratio - 3 - 2 * i
                    else:
                        idx1 = 0
                    idx0 = 2*div_ratio-1-2*i
                    dff_o = dff_inst[idx0].get_all_port_pins('O', layer=dff_toplay)[0]
                    dff_i = dff_inst[idx1].get_all_port_pins('I')[0]
                    idx = self.grid.coord_to_nearest_track(dff_o.layer_id + 1, dff_o.get_bbox_array(self.grid)
                                                           .top_unit, unit_mode=True)
                    tid = TrackID(dff_o.layer_id + 1, idx-1)
                    self.connect_to_tracks([dff_o, dff_i], tid)

                    # get rst/st vss
                    rst = dff_inst[2*div_ratio-1-2*i].get_all_port_pins('RST')[0]
                    st = dff_inst[2*div_ratio-1-2*i].get_all_port_pins('ST')[0]
                    vss = dff_inst[2*div_ratio-1-2*i].get_all_port_pins('VSS')[0]

                # rst/st connection
                if rst_list[i] == 1:
                    rst_warr.append(st)
                    self.connect_to_tracks(vss, rst.track_id, track_upper=rst.get_bbox_array(self.grid).top_unit,
                                           unit_mode=True)
                else:
                    rst_warr.append(rst)
                    self.connect_to_tracks(vss, st.track_id, track_upper=st.get_bbox_array(self.grid).top_unit,
                                           unit_mode=True)
                # get output
                for j in out_list:
                    if j == i:
                        out_warr.append(dff_o)

        else:
            for i in range(div_ratio):
                if 2*i < div_ratio-1:
                    dff_o = dff_inst[2*i].get_all_port_pins('O', layer=dff_toplay)[0]
                    dff_i = dff_inst[2*(i+1)].get_all_port_pins('I')[0]
                    idx = self.grid.coord_to_nearest_track(dff_o.layer_id+1, dff_o.get_bbox_array(self.grid)
                                                           .top_unit, unit_mode=True)
                    tid = TrackID(dff_o.layer_id+1, idx)
                    self.connect_to_tracks([dff_o, dff_i], tid)

                    # get rst/st vss
                    rst = dff_inst[2 * i].get_all_port_pins('RST')[0]
                    st = dff_inst[2 * i].get_all_port_pins('ST')[0]
                    vss = dff_inst[2 * i].get_all_port_pins('VSS')[0]

                elif 2*i == div_ratio-1:
                    idx0 = 2*(div_ratio-1)-2*i
                    idx1 = 2*(div_ratio-1)-2*i-1
                    dff_o = dff_inst[idx0].get_all_port_pins('O', layer=dff_toplay)[0]
                    dff_i = dff_inst[idx1].get_all_port_pins('I')[0]
                    idx = self.grid.coord_to_nearest_track(dff_o.layer_id + 1, dff_o.get_bbox_array(self.grid)
                                                           .top_unit, unit_mode=True)
                    tid = TrackID(dff_o.layer_id + 1, idx-1)
                    self.connect_to_tracks([dff_o, dff_i], tid)

                    # get rst/st vss
                    rst = dff_inst[2*(div_ratio-1)-2*i].get_all_port_pins('RST')[0]
                    st = dff_inst[2*(div_ratio-1)-2*i].get_all_port_pins('ST')[0]
                    vss = dff_inst[2*(div_ratio-1)-2*i].get_all_port_pins('VSS')[0]
                else:
                    if i != div_ratio-1:
                        idx1 = 2 * div_ratio - 2 * (i + 1) - 1
                    else:
                        idx1 = 0
                    idx0 = 2*div_ratio-2*i-1
                    dff_o = dff_inst[idx0].get_all_port_pins('O', layer=dff_toplay)[0]
                    dff_i = dff_inst[idx1].get_all_port_pins('I')[0]
                    idx = self.grid.coord_to_nearest_track(dff_o.layer_id + 1, dff_o.get_bbox_array(self.grid)
                                                           .top_unit, unit_mode=True)
                    tid = TrackID(dff_o.layer_id + 1, idx-1)
                    self.connect_to_tracks([dff_o, dff_i], tid)

                    # get rst/st vss
                    rst = dff_inst[2*div_ratio-2*i-1].get_all_port_pins('RST')[0]
                    st = dff_inst[2*div_ratio-2*i-1].get_all_port_pins('ST')[0]
                    vss = dff_inst[2*div_ratio-2*i-1].get_all_port_pins('VSS')[0]

                # rst/st connection
                if rst_list[i] == 1:
                    rst_warr.append(st)
                    self.connect_to_tracks(vss, rst.track_id, track_upper=rst.get_bbox_array(self.grid).top_unit,
                                           unit_mode=True)
                else:
                    rst_warr.append(rst)
                    self.connect_to_tracks(vss, st.track_id, track_upper=st.get_bbox_array(self.grid).top_unit,
                                           unit_mode=True)
                # get output
                for j in out_list:
                    if j == i:
                        out_warr.append(dff_o)

        # connect to rst
        tid = TrackID(st.layer_id + 1, clk_idx - clk_rst_sp - clock_track)
        rst_warr.append(rstbuf_inst.get_all_port_pins('data_o')[0])
        self.connect_to_tracks(rst_warr, tid)
        rst = rstbuf_inst.get_all_port_pins('data')[0]

        # connect VDD/VSS
        vdd_warr = rstbuf_inst.get_all_port_pins('VDD')
        vss_warr = rstbuf_inst.get_all_port_pins('VSS')
        vdd_warr.append(clkbuf_inst.get_all_port_pins('VDD')[0])
        vss_warr.append(clkbuf_inst.get_all_port_pins('VSS')[0])
        for i in range(div_ratio):
            vdd_warr.append(dff_inst[i].get_all_port_pins('VDD')[0])
            vss_warr.append(dff_inst[i].get_all_port_pins('VSS')[0])
        vdd_wire = self.connect_wires(vdd_warr)
        vss_wire = self.connect_wires(vss_warr)

        # add pins
        self.add_pin('VDD', vdd_wire, show=show_pins)
        self.add_pin('VSS', vss_wire, show=show_pins)
        self.add_pin('clk', clk, show=show_pins)
        self.add_pin('rst', rst, show=show_pins)
        if len(out_warr) != 1:
            for i, o in enumerate(out_warr):
                self.add_pin('o<{}>'.format(i), o, show=show_pins)
        else:
            self.add_pin('o', out_warr[0], show=show_pins)
        if debug is True:
            self.add_pin('clk_i', clk_i, show=show_pins)

        # get size
        # get size and array box
        width = dff_width*div_ratio+buf_width*2
        # width = buf_width
        height = dff_height
        top_layer = dff_toplay+1
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
            div_ratio=div_ratio,
            rst_list=rst_list,
            out_list=out_list,
            debug=debug,
        )
