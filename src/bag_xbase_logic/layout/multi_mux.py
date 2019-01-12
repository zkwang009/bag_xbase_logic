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
from bag_xbase_logic.layout.mux import MUX


class MultiMUX(TemplateBase):
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
            nf_inv0='inv0 finger number',
            nf_tinv_0='tinv MOS0 finger number',
            nf_tinv_1='tinv MOS1 finger number',
            nf_inv2='inv2 finger number',
            intent='transistor threshold',
            ndum='dummy finger number between different transistors',
            ndum_side='dummy finger number between different transistors',
            mux_stage='number of multi-stage mux',

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
                            intent, ndum, ndum_side, mux_stage,
                            g_space, ds_space, show_pins, power_width_ntr,
                            **kwargs):
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

        mux_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv0=nf_inv0,
            nf_tinv_0=nf_tinv_0,
            nf_tinv_1=nf_tinv_1,
            nf_inv2=nf_inv2,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            intent=intent,
            ndum=ndum,
            ndum_side=ndum_side,
            g_space=g_space,
            ds_space=ds_space,
            power_width_ntr=power_width_ntr,
            show_pins=False,
            debug=False,
        )

        mux_master = self.new_template(params=mux_params, temp_cls=MUX, debug=True)

        # get mux size
        mux_toplay, mux_w, mux_h = mux_master.size
        w_pitch_mux, h_pitch_mux = self.grid.get_size_pitch(mux_toplay, unit_mode=True)
        mux_width = mux_w * w_pitch_mux
        mux_height = mux_h * h_pitch_mux

        mux_inst = []
        i = 0
        j = 0
        n_dum = 0
        for stage in reversed(range(mux_stage)):
            mux_inst_row = []
            for cell in range(2**stage):
                if stage == mux_stage-1:
                    xcoord = cell * mux_width
                    mux_inst_row.append(self.add_instance(mux_master, inst_name='MUX_{}'.format(i), orient='R0',
                                                          loc=(xcoord, (mux_stage-stage-1)*mux_height),
                                                          unit_mode=True))
                    os_list_new = list(range(2**(mux_stage-1)))
                else:
                    os = (os_list[cell*2] + os_list[cell*2+1])/2
                    xcoord = os * mux_width // w_pitch_mux * w_pitch_mux
                    os_list_new.append(os)
                    mux_inst_row.append(self.add_instance(mux_master, inst_name='MUX_{}'.format(i), orient='R0',
                                                          loc=(xcoord, (mux_stage - stage - 1) * mux_height),
                                                          unit_mode=True))
                    if cell != 2**stage-1 and stage != 0:
                        dum_coord = xcoord + mux_width
                        self.add_instance(mux_master, inst_name='DUM_{}'.format(j), orient='R0',
                                          loc=(dum_coord, (mux_stage-stage-1) * mux_height),
                                          nx=2**(mux_stage-1-stage)-1, spx=mux_width, unit_mode=True)
                        n_dum += 1
                    i += 1  # index for useful cell
                    j += 1  # index for dummy cell
            os_list = os_list_new
            os_list_new = []
            mux_inst.append(mux_inst_row)

        # connect sel for each row, connect VDD and VSS
        mux_inst.reverse()
        vdd_warr = []
        vss_warr = []
        for stage in reversed(range(mux_stage)):
            sel_list = []
            vdd_list = []
            vss_list = []
            for cell in range(2**stage):
                sel_list += mux_inst[stage][cell].get_all_port_pins('sel')
                vdd_list += mux_inst[stage][cell].get_all_port_pins('VDD')
                vss_list += mux_inst[stage][cell].get_all_port_pins('VSS')

            sel_idx = self.grid.coord_to_nearest_track(sel_list[0].track_id.layer_id+1,
                                    sel_list[0].get_bbox_array(self.grid).top_unit,
                                    unit_mode=True)
            sel_tid = TrackID(sel_list[0].track_id.layer_id+1, sel_idx)
            sel = self.connect_to_tracks(sel_list, sel_tid, unit_mode=True, min_len_mode=0)
            # sel = self.connect_to_tracks(sel_list, sel_tid, track_lower=0,
            #                              track_upper=mux_width * 2 ** (mux_stage - 1), unit_mode=True)
            vdd_warr += self.connect_wires(vdd_list, unit_mode=True)
            # vdd_warr += self.connect_wires(vdd_list, lower=0, upper=mux_width*2**(mux_stage-1), unit_mode=True)
            vss_warr += self.connect_wires(vss_list, unit_mode=True)
            # vss_warr += self.connect_wires(vss_list, lower=0, upper=mux_width*2**(mux_stage-1), unit_mode=True)
            self.add_pin('sel<{}>'.format(stage), sel, show=show_pins)

        # connect output and input between different stages
        for stage in reversed(range(mux_stage)):
            if stage == 0:
                self.reexport(mux_inst[stage][0].get_port('o'), 'o', show=show_pins)
                continue
            if stage == mux_stage-1:
                for i in range(2**stage):
                    self.reexport(mux_inst[stage][i].get_port('i0'), 'i<{}>'.format(i*2), show=show_pins)
                    self.reexport(mux_inst[stage][i].get_port('i1'), 'i<{}>'.format(i*2+1), show=show_pins)
            for i in range(2**(stage-1)):
                out0 = mux_inst[stage][i*2].get_all_port_pins('o')[0]
                out1 = mux_inst[stage][i*2+1].get_all_port_pins('o')[0]
                # connect out0/1 to higher level
                # out0 = self.draw_wire_stack(out0, out0.layer_id+1, tr_list=[1])
                # out1 = self.draw_wire_stack(out1, out1.layer_id+1, tr_list=[1])
                idx = self.grid.coord_to_nearest_track(out0.layer_id+1, out0.upper)
                tid = TrackID(out0.layer_id+1, idx+1)
                out0 = self.connect_to_tracks(out0, tid)
                idx = self.grid.coord_to_nearest_track(out1.layer_id + 1, out1.upper)
                tid = TrackID(out1.layer_id + 1, idx+1)
                out1 = self.connect_to_tracks(out1, tid)  # input wire

                # get inputs
                in0 = mux_inst[stage-1][i].get_all_port_pins('i0')[0]
                in1 = mux_inst[stage-1][i].get_all_port_pins('i1')[0]
                coord_y = (mux_stage - stage) * mux_height
                idx = self.grid.coord_to_nearest_track(in0.layer_id-1, coord_y, unit_mode=True)
                tid = TrackID(in0.layer_id-1, idx)
                # connect inputs and outputs
                self.connect_to_tracks([out0, in0], tid, min_len_mode=0)
                self.connect_to_tracks([out1, in1], tid, min_len_mode=0)

        # add pins
        self.add_pin('VDD', vdd_warr, label='VDD:', show=show_pins)
        self.add_pin('VSS', vss_warr, label='VSS:', show=show_pins)

        # get size
        # get size and array box
        width = mux_width*2**(mux_stage-1)
        height = mux_stage * mux_height
        top_layer = mux_toplay
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
        mux_sch_params = mux_master.sch_params
        self._sch_params = dict(
            **mux_sch_params,
            mux_stage=mux_stage,
            n_dum=n_dum,
        )
