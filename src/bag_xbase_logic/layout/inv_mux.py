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

from bag_xbase_logic.layout.inv import Inv
from bag_xbase_logic.layout.mux import MUX



class InvMUX(TemplateBase):
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
            inv_nf='inverter figner number',
            mux_nf_inv0='inv0 finger number',
            mux_nf_tinv_0='tinv MOS0 finger number',
            mux_nf_tinv_1='tinv MOS1 finger number',
            mux_nf_inv2='inv2 finger number',
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

    def _draw_layout_helper(self, lch, wn, wp, inv_nf, mux_nf_inv0, mux_nf_tinv_0, mux_nf_tinv_1,
                            mux_nf_inv2, ptap_w, ntap_w, g_width_ntr, ds_width_ntr, intent,
                            ndum, ndum_side, g_space, ds_space, power_width_ntr, show_pins, **kwargs):
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
        inv_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nfn=inv_nf,
            nfp=inv_nf,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            intent=intent,
            ndum=ndum,
            ndum_side=ndum_side,
            show_pins=False,
            debug=False,
            g_space=g_space+1,
            ds_space=ds_space+1,
            power_width_ntr=power_width_ntr,

        )
        inv_master = self.new_template(params=inv_params, temp_cls=Inv, debug=True)

        # get mux size
        inv_toplay, inv_w, inv_h = inv_master.size
        w_pitch_inv, h_pitch_inv = self.grid.get_size_pitch(inv_toplay, unit_mode=True)
        inv_width = inv_w * w_pitch_inv
        inv_height = inv_h * h_pitch_inv

        mux_params = dict(
            lch=lch,
            wn=wn,
            wp=wp,
            nf_inv0=mux_nf_inv0,
            nf_tinv_0=mux_nf_tinv_0,
            nf_tinv_1=mux_nf_tinv_1,
            nf_inv2=mux_nf_inv2,
            ptap_w=ptap_w,
            ntap_w=ntap_w,
            g_width_ntr=g_width_ntr,
            ds_width_ntr=ds_width_ntr,
            intent=intent,
            ndum=ndum,
            ndum_side=ndum_side,
            show_pins=False,
            debug=False,
            g_space=g_space,
            ds_space=ds_space,
            power_width_ntr=power_width_ntr,
        )

        mux_master = self.new_template(params=mux_params, temp_cls=MUX, debug=True)

        # get mux size
        mux_toplay, mux_w, mux_h = mux_master.size
        w_pitch_mux, h_pitch_mux = self.grid.get_size_pitch(mux_toplay, unit_mode=True)
        mux_width = mux_w * w_pitch_mux
        mux_height = mux_h * h_pitch_mux

        # get instances
        inv_inst = self.add_instance(inv_master, inst_name='INV', loc=(0, 0))
        mux_inst = self.add_instance(mux_master, inst_name='MUX', loc=(inv_width, 0),
                                     unit_mode=True)

        # connect all the blocks
        i = inv_inst.get_all_port_pins('I')[0]
        inv_O = inv_inst.get_all_port_pins('O')[0]

        mux_i0 = mux_inst.get_all_port_pins('i0')[0]
        mux_i1 = mux_inst.get_all_port_pins('i1')[0]
        in_flip = mux_inst.get_all_port_pins('sel')[0]
        o = mux_inst.get_all_port_pins('o')[0]

        # connect between inv and mux
        idx = self.grid.coord_to_nearest_track(inv_O.layer_id + 1, inv_O.upper)
        tid = TrackID(inv_O.layer_id+1, idx)
        inv_O = self.connect_to_tracks(inv_O, tid, min_len_mode=0)

        idx = self.grid.coord_to_nearest_track(inv_O.layer_id + 1, inv_O.upper)
        tid = TrackID(inv_O.layer_id+1, idx)
        self.connect_to_tracks([inv_O, mux_i1], tid, min_len_mode=0)

        # connect input
        idx = self.grid.coord_to_nearest_track(i.layer_id+1, i.upper)
        tid = TrackID(i.layer_id+1, idx)
        inv_O = self.connect_to_tracks([i, mux_i0], tid, min_len_mode=0)

        # connect VDD/VSS
        inv_vdd = inv_inst.get_all_port_pins('VDD')[0]
        inv_vss = inv_inst.get_all_port_pins('VSS')[0]
        mux_vdd = mux_inst.get_all_port_pins('VDD')[0]
        mux_vss = mux_inst.get_all_port_pins('VSS')[0]

        vdd_wire = self.connect_wires([inv_vdd, mux_vdd])
        vss_wire = self.connect_wires([inv_vss, mux_vss])

        # add pins
        self.add_pin('VDD', vdd_wire, show=show_pins)
        self.add_pin('VSS', vss_wire, show=show_pins)

        self.add_pin('i', i, show=show_pins)
        self.add_pin('o', o, show=show_pins)
        self.add_pin('in_flip', in_flip, show=show_pins)

        # get size
        # get size and array box
        width = inv_width + mux_width
        height = mux_height
        top_layer = mux_toplay + 1
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
        self._sch_params = dict(
            inv_sch_params=inv_master.sch_params,
            mux_sch_params=mux_master.sch_params,
        )


