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
        )

    def draw_layout(self, **kwargs):
        self._draw_layout_helper(**self.params)

    def _draw_layout_helper(self, lch, wn, wp, nf_inv0, nf_tinv_0, nf_tinv_1, nf_inv2,
                            ptap_w, ntap_w, g_width_ntr, ds_width_ntr,
                            intent, ndum, ndum_side, mux_stage,
                            g_space, ds_space, show_pins,
                            debug, **kwargs):
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
            show_pins=True,
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
        offset = 0
        os_list = []
        for stage in reversed(range(mux_stage)):
            for cell in range(2**stage):
                if stage == mux_stage-1:
                    os_list.append(cell)
                    xcoord = ((offset + cell) * mux_width) // w_pitch_mux * w_pitch_mux
                    mux_inst.append(self.add_instance(mux_master, inst_name='MUX_{}'.format(i), orient='R0',
                                                      loc=(xcoord, (mux_stage-stage-1)*mux_height),
                                                      unit_mode=True))
                i += 1

            print(os_list)
            print(offset)
            offset += (2**stage-2**(stage-1))/2

        # # connect sel for each row
        # cell_os = 0
        # for stage in reversed(range(mux_stage)):
        #     sel_warr = []
        #     for cell in range(2**stage):
        #         sel_warr += mux_inst[cell_os+cell].get_all_port_pins('sel')
        #     print()
        #     sel_idx = self.grid.coord_to_nearest_track(sel_warr[0].track_id.layer_id+1,
        #                             sel_warr[0].get_bbox_array(self.grid).top_unit,
        #                             unit_mode=True)
        #     sel_tid = TrackID(sel_warr[0].track_id.layer_id+1, sel_idx)
        #     sel = self.connect_to_tracks(sel_warr, sel_tid, track_lower=0,
        #                                  track_upper=mux_width*2**(mux_stage-1), unit_mode=True)
        #     cell_os += 2**stage

        # # add pins
        # self.add_pin('i0', i0, show=show_pins)
        # self.add_pin('i1', i1, show=show_pins)
        # self.add_pin('sel', sel, show=show_pins)
        # self.add_pin('o', o, show=show_pins)
        #
        # # draw dummies
        # ptap_wire_arrs, ntap_wire_arrs = self.fill_dummy()
        #
        # # export supplies
        # self.add_pin(self.get_pin_name('VSS'), ptap_wire_arrs, show=show_pins)
        # self.add_pin(self.get_pin_name('VDD'), ntap_wire_arrs, show=show_pins)
        #
        # # get size
        # self.size = self.set_size_from_array_box(m5v_layer)
        #
        # # get schematic parameters
        # dum_info = self.get_sch_dummy_info()
        # self._sch_params = dict(
        #     lch=lch,
        #     wn=wn,
        #     wp=wp,
        #     nf_inv0=nf_inv0,
        #     nf_tinv_0=nf_tinv_0,
        #     nf_tinv_1=nf_tinv_1,
        #     nf_inv2=nf_inv2,
        #     intent=intent,
        #     dum_info=dum_info,
        #     debug=debug,
        # )


