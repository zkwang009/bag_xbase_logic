# -*- coding: utf-8 -*-
import bag.core

temp_lib = 'bag_xbase_logic'

if 'prj' not in locals():
    prj = bag.core.BagProject()

print('importing library: %s' % temp_lib)
prj.import_design_library(temp_lib)
print('finish importing library %s.' % temp_lib)
