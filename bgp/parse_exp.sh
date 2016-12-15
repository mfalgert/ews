#!/bin/bash

python parse_bgp_updates.py --input dumps/rrc00/2016.03.09/ dumps/rrc00/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/00/ &
#python parse_bgp_updates.py --input dumps/rrc01/2016.03.09/ dumps/rrc01/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/01/ &
#python parse_bgp_updates.py --input dumps/rrc04/2016.03.09/ dumps/rrc04/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/04/ &
python parse_bgp_updates.py --input dumps/rrc05/2016.03.09/ dumps/rrc05/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/05/ &
python parse_bgp_updates.py --input dumps/rrc06/2016.03.09/ dumps/rrc06/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/06/ &
python parse_bgp_updates.py --input dumps/rrc07/2016.03.09/ dumps/rrc07/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/07/ &
python parse_bgp_updates.py --input dumps/rrc10/2016.03.09/ dumps/rrc10/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/10/ &
python parse_bgp_updates.py --input dumps/rrc11/2016.03.09/ dumps/rrc11/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/11/ &
#python parse_bgp_updates.py --input dumps/rrc12/2016.03.09/ dumps/rrc12/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/12/ &
python parse_bgp_updates.py --input dumps/rrc13/2016.03.09/ dumps/rrc13/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/13/ &
#python parse_bgp_updates.py --input dumps/rrc14/2016.03.09/ dumps/rrc14/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/14/ &
#python parse_bgp_updates.py --input dumps/rrc15/2016.03.09/ dumps/rrc15/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/15/ &
python parse_bgp_updates.py --input dumps/rrc16/2016.03.09/ dumps/rrc16/2016.03.10/ --start_date 16.3.9.15 --end_date 16.3.10.15 --at $1 --save_from at-$1/16/
