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

from bag_xbase_logic.layout.clk_cell_array import ClkCellArr
from bag_xbase_logic.layout.ctrl_buf_array import CtrlBufArr
from bag_xbase_logic.layout.buffer import Buffer
from bag_xbase_logic.layout.cload import Cload

class InvPI(AnalogBase):
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
            pi_res='phase interpolator resolution',
            lch='transistor channel length',
            wn='NMOS width',
            wp='PMOS width',
            ctrl_nf_inv0='ctrl array inv0 NMOS finger number',
            ctrl_nf_inv1='ctrl array inv1 NMOS finger number',
            clk_nf_inv='clock cell inv NMOS finger number',
            clk_nf_tinv0='clock cell tinv NMOS finger number',
            clk_nf_tinv1='clock cell tinv switch NMOS finger number',
            buf_nf_inv0='buffer inv0 NMOS finger number',
            buf_nf_inv1='buffer inv1 NMOS finger number',
            cload_nf='cload MOS finger number',
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
            power_width_ntr=None,
            show_pins=False,
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, pi_res, lch, wn, wp, ctrl_nf_inv0, ctrl_nf_inv1, clk_nf_inv,
                            clk_nf_tinv0, clk_nf_tinv1, buf_nf_inv0, buf_nf_inv1, cload_nf,
                            intent, ndum_side,
                            ndum, ptap_w, ntap_w, g_width_ntr, ds_width_ntr, power_width_ntr,
                            show_pins, **kwargs):
        """Draw the layout of a transistor for characterization.
        Notes
        -------
        The number of fingers are for only half (or one side) of the tank.
        Total number should be 2x
        """

        # get resolution
        res = self.grid.resolution

        # get ctrl_buf_array
        ctrl_ndum = clk_nf_inv + clk_nf_tinv0 + clk_nf_tinv1 - ctrl_nf_inv0 - ctrl_nf_inv1 + ndum
        ctrl_params = dict(
            pi_res=pi_res,
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv0=ctrl_nf_inv0,
            nf_inv1=ctrl_nf_inv1,
            intent=intent,
            ndum_side=ndum_side,
            ndum=ndum,
            ndum_cell= ctrl_ndum,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            power_width_ntr=power_width_ntr,
            show_pins=False,
            g_space=1,
            ds_space=1,
        )
        ctrl_master = self.new_template(params=ctrl_params, temp_cls=CtrlBufArr, debug=True)

        ctrl_toplay, ctrl_w, ctrl_h = ctrl_master.size
        w_pitch_ctrl, h_pitch_ctrl = self.grid.get_size_pitch(ctrl_toplay, unit_mode=True)
        ctrl_width = ctrl_w * w_pitch_ctrl
        ctrl_height = ctrl_h * h_pitch_ctrl

        # get clock_cell_array
        clk_params = dict(
            pi_res=pi_res,
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv=clk_nf_inv,
            nf_tinv0=clk_nf_tinv0,
            nf_tinv1=clk_nf_tinv1,
            intent=intent,
            ndum_side=ndum_side,
            ndum=ndum,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            power_width_ntr=power_width_ntr,
            show_pins=False,
        )
        clk_master = self.new_template(params=clk_params, temp_cls=ClkCellArr, debug=True)

        clk_toplay, clk_w, clk_h = clk_master.size
        w_pitch_clk, h_pitch_clk = self.grid.get_size_pitch(clk_toplay, unit_mode=True)
        clk_width = clk_w * w_pitch_clk
        clk_height = clk_h * h_pitch_clk

        # get clock buffer
        buf_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv0=buf_nf_inv0,
            nf_inv1=buf_nf_inv1,
            intent=intent,
            ndum_side=ndum_side,
            ndum=ndum,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            power_width_ntr=power_width_ntr,
            show_pins=False,
            out_M5=False,
        )
        buf_master = self.new_template(params=buf_params, temp_cls=Buffer, debug=True)

        buf_toplay, buf_w, buf_h = buf_master.size
        buf_width = buf_master.bound_box.right_unit
        buf_height = buf_master.bound_box.top_unit
        w_loc_buf, h_loc_buf = self.grid.get_size_pitch(buf_toplay, unit_mode=True)

        # get clock buffer
        cload_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nfn=cload_nf,
            nfp=cload_nf,
            intent=intent,
            ndum_side=ndum_side,
            ndum=ndum,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            power_width_ntr=power_width_ntr,
            show_pins=False,
        )
        cload_master = self.new_template(params=cload_params, temp_cls=Cload, debug=True)

        buf_toplay, buf_w, buf_h = buf_master.size
        buf_width = cload_master.bound_box.right_unit
        buf_height = cload_master.bound_box.top_unit

        # initiate ctrl and clock
        ctrl_inst = self.add_instance(ctrl_master, inst_name='CTRL', loc=(0, 0))
        clk_inst = self.add_instance(clk_master, inst_name='CLK', loc=(0, ctrl_height), unit_mode=True)
        buf_xcoord = (clk_width / 2) // w_loc_buf * w_loc_buf
        buf_inst = self.add_instance(buf_master, inst_name='BUF', loc=(buf_xcoord, ctrl_height + clk_height),
                                     unit_mode=True)
        cload_inst = self.add_instance(cload_master, inst_name='CLOAD', loc=(buf_xcoord, ctrl_height + clk_height),
                                     orient='MY', unit_mode=True)


        # connect ctrl signals
        clk_ctrl_arr = []
        clk_ctrlb_arr = []
        ctrl_o_arr = []
        ctrl_ob_arr = []
        ctrl_arr = []
        for i in range(pi_res):
            clk_ctrl_arr.append(clk_inst.get_all_port_pins('ctrl<{}>'.format(i))[0])
            clk_ctrlb_arr.append(clk_inst.get_all_port_pins('ctrlb<{}>'.format(i))[0])
            ctrl_o_arr.append(ctrl_inst.get_all_port_pins('ctrl_o<{}>'.format(i))[0])
            ctrl_ob_arr.append(ctrl_inst.get_all_port_pins('ctrl_ob<{}>'.format(i))[0])
            ctrl_arr.append(ctrl_inst.get_all_port_pins('ctrl<{}>'.format(i))[0])

        for i in range(pi_res):
            clk_ctrl = clk_ctrl_arr[i]
            clk_ctrlb = clk_ctrlb_arr[i]
            ctrl_o = ctrl_o_arr[i]
            ctrl_ob = ctrl_ob_arr[i]

            # get clk_ctrl track id
            idx0 = self.grid.coord_to_nearest_track(clk_ctrl.layer_id+1,
                                                    clk_ctrl.get_bbox_array(self.grid).left_unit, unit_mode=True)
            tid0 = TrackID(clk_ctrl.layer_id+1, idx0)
            idx1 = self.grid.coord_to_nearest_track(clk_ctrl.layer_id + 1,
                                                    clk_ctrl.get_bbox_array(self.grid).right_unit, unit_mode=True)
            tid1 = TrackID(clk_ctrl.layer_id+1, idx1)
            # draw clk_ctrl on higher layer
            clk_ctrl = self.connect_to_tracks(clk_ctrl, tid0, min_len_mode=0)
            clk_ctrlb = self.connect_to_tracks(clk_ctrlb, tid1, min_len_mode=0)

            # get ctrl_o
            idx2 = self.grid.coord_to_nearest_track(ctrl_o.layer_id + 1,
                                                    ctrl_o.get_bbox_array(self.grid).right_unit, unit_mode=True)
            tid2 = TrackID(ctrl_o.layer_id + 1, idx2)
            # draw clk_ctrl on higher layer
            ctrl_o = self.connect_to_tracks(ctrl_o, tid2, min_len_mode=0)

            # connect them
            idx = self.grid.coord_to_nearest_track(ctrl_o.layer_id-1, ctrl_height, unit_mode=True)
            tid0 = TrackID(ctrl_o.layer_id-1, idx+1)
            tid1 = TrackID(ctrl_o.layer_id-1, idx)
            self.connect_to_tracks([clk_ctrl, ctrl_o], tid0, min_len_mode=0)
            self.connect_to_tracks([clk_ctrlb, ctrl_ob], tid1, min_len_mode=0)

        # get clk
        clk_i = clk_inst.get_all_port_pins('clk_i')[0]
        clk_q = clk_inst.get_all_port_pins('clk_q')[0]
        clk_ib = clk_inst.get_all_port_pins('clk_ib')[0]
        clk_qb = clk_inst.get_all_port_pins('clk_qb')[0]

        # connect clki/q/ib/qb
        idx = self.grid.coord_to_nearest_track(clk_i.layer_id+1, clk_width/2,
                                               half_track=True, unit_mode=True)
        tid_i = TrackID(clk_i.layer_id+1, idx-1.5)
        tid_q = TrackID(clk_i.layer_id+1, idx-0.5)
        tid_ib = TrackID(clk_i.layer_id + 1, idx + 0.5)
        tid_qb = TrackID(clk_i.layer_id + 1, idx + 1.5)

        clk_i, clk_q, clk_ib, clk_qb = self.connect_matching_tracks([clk_i, clk_q, clk_ib, clk_qb], clk_i.layer_id+1,
                                                                    [idx-1.5, idx-0.5, idx+0.5, idx+1.5], track_lower=0)

        # get to output buffer
        outm = clk_inst.get_all_port_pins('clko')[0]
        data = buf_inst.get_all_port_pins('data')[0]
        cload_in = cload_inst.get_all_port_pins('I')[0]
        clk_m = self.connect_to_tracks(outm, data.track_id, track_upper=data.get_bbox_array(self.grid).top_unit,
                               unit_mode=True)
        idx = self.grid.coord_to_nearest_track(clk_m.layer_id+1, cload_in.middle)
        tid = TrackID(clk_m.layer_id+1, idx)
        self.connect_to_tracks([clk_m, cload_in], tid)

        # get ouput
        out = buf_inst.get_all_port_pins('data_o')[0]
        out_b = buf_inst.get_all_port_pins('data_ob')[0]

        # add_pin
        self.add_pin('clk_i', clk_i, show=show_pins)
        self.add_pin('clk_q', clk_q, show=show_pins)
        self.add_pin('clk_ib', clk_ib, show=show_pins)
        self.add_pin('clk_qb', clk_qb, show=show_pins)
        self.add_pin('clkm', outm, show=show_pins)
        self.add_pin('clko', out, show=show_pins)
        self.add_pin('clkob', out_b, show=show_pins)
        for i, ctrl in enumerate(ctrl_arr):
            self.add_pin('ctrl<{}>'.format(i), ctrl, show=show_pins)

        self.reexport(ctrl_inst.get_port('VSS'), 'VSS', label='VSS:', show=show_pins)
        self.reexport(clk_inst.get_port('VSS'), 'VSS', label='VSS:', show=show_pins)
        vss0 = self.connect_wires(buf_inst.get_all_port_pins('VSS')+cload_inst.get_all_port_pins('VSS'))
        self.add_pin('VSS', vss0, label='VSS:', show=show_pins)

        self.reexport(ctrl_inst.get_port('VDD'), 'VDD', label='VDD:', show=show_pins)
        self.reexport(clk_inst.get_port('VDD'), 'VDD', label='VDD:', show=show_pins)
        vdd0 = self.connect_wires(buf_inst.get_all_port_pins('VDD') + cload_inst.get_all_port_pins('VDD'))
        self.add_pin('VDD', vdd0, label='VDD:', show=show_pins)

        # get size
        # get size and array box
        width = max(buf_width, ctrl_width, clk_width)
        height = ctrl_height + clk_height + buf_height
        top_layer = clk_i.layer_id
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
        ctrl_sch_params = ctrl_master.sch_params
        clk_sch_params = clk_master.sch_params
        buf_sch_params = buf_master.sch_params
        cload_sch_params = cload_master.sch_params

        self._sch_params = dict(
            pi_res=pi_res,
            ctrl_sch_params=ctrl_sch_params,
            clk_sch_params=clk_sch_params,
            buf_sch_params=buf_sch_params,
            cload_sch_params=cload_sch_params,
        )







