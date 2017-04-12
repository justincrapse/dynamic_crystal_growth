"""
Still working on a final solution for variable names as there is a lot to do with trehsholds
Currently, I'd like threshold rounds to refer to the ordered set of rounds, which is an organized list of dictionaries of
the threshold dictionaries based on thier placement values

"""

from math import sqrt
import hou
import operator

import toolutils

thresh_states = {}
thresh = toolutils.createModuleFromSection('threshold_module', kwargs['type'], 'threshold_module')


def thresh_dicts():
    for key, value in thresh.thresh_dict_old.iteritems():
        print 'Key: {}, Value: {}'.format(key, value)
    print '\n'
    for key, value in thresh.thresh_dict.iteritems():
        print 'Key: {}, Value: {}'.format(key, value)
        
        
def generate_geometry(flag=None):
    global gtc  # global threshold count
    global thresh_states  # this will be the dictionary for the thresh round dictionaries holding that round's node and other info
    
    if flag == 'thresholds':
        thresh.set_thresholds()  # if the thresh count changes, we have to go set up the threshold UI tab. 
    elif not thresh.gtc:
        thresh.set_thresholds()  # if no thresh count, run this for first population of thresh UI tab (can't run on node creation for some odd reason)
    if flag == 'thresh_values':
        thresh.set_thresh_dictionary()  # this will update the thresh values and old values as applicable
    
    # now that thresholds are set, lets set a dictionary of all their values and a dictionary of old values
    thresh_dict = thresh.thresh_dict
    thresh_dict_old = thresh.thresh_dict_old

    # pull in some variables
    new_maturity = hou.pwd().parm('maturity').eval()
        
    # set main cube size and rotation
    set_main_geometry(maturity=new_maturity)
    
    # we now create a sorted list of the dictionary values based on threshold placement. We want to go through each threshold in that order
    sorted_thresh = sorted(thresh_dict.items(), key=lambda x: x[1]['placement'])
    
    for thresh_round, thresh_def in enumerate(sorted_thresh):
        thresh_round += 1
        thresh_key = thresh_def[0]
        # tdd stands for thresh_def_dict and tddo stands for thresh_def_dict_old
        tdd = thresh_dict[thresh_key]           
        new_placement = tdd['placement']
        new_count = tdd['count']
        new_rotation = tdd['rotation']
        new_growth_rate = tdd['growth_rate']
        new_rate_variance = tdd['rate_variance']
        
        old_thresh_exist = thresh_key in thresh_dict_old
        if old_thresh_exist:
            tddo = thresh_dict_old[thresh_key]
            old_placement = tddo['placement']
            old_count = tddo['count']
            old_rotation = tddo['rotation']
            old_growth_rate = tddo['growth_rate']
            old_rate_variance = tddo['rate_variance']
        
        # set up a bunch of thesh round variables from dictionary
        thresh_states_key = 'thresh_round_{}'.format(thresh_round)
        thresh_state_exist = thresh_states_key in thresh_states
        if thresh_state_exist: 
            thresh_round_dict = thresh_states[thresh_states_key]
            thresh_round_nodes = thresh_round_dict['node_names']
            thresh_round_state = thresh_round_dict['thresh_state']
            thresh_round_placement = thresh_round_dict['placement']
            old_maturity = thresh_round_dict['maturity']
            print 'maturity {} and old maturity: {}'.format(new_maturity, old_maturity)
        
        if new_placement > new_maturity and thresh_state_exist and thresh_round_state != 'set':
            print 'level 0'
            pass
        elif new_placement > new_maturity and thresh_state_exist and thresh_round_state == 'set':
            print 'level 1'
            delete_thresh_round_nodes(thresh_round_dict)
            
        elif (old_thresh_exist and (new_count != old_count or new_rotation != old_rotation or new_growth_rate != old_growth_rate or
                new_rate_variance != old_rate_variance or new_placement != old_placement) and thresh_state_exist and thresh_round_state == 'set'):
            print 'level 2'
            for i in range(thresh_round - 1, len(sorted_thresh)):
                if 'thresh_round_{}'.format(i + 1) in thresh_states:
                    delete_thresh_round_nodes(thresh_states['thresh_round_{}'.format(i + 1)])
            generate_geometry()
            
        elif (thresh_state_exist and thresh_round_state != 'set') or not thresh_state_exist and new_placement < new_maturity:
            print 'level 3'
            # bring main maturity to threshold maturity, create a scatter node, then create the new instances and set the maturity back
            set_main_geometry(maturity=new_placement)
            print 'scatter node created at {} maturity'.format(new_placement)
        
            # create the bool node and attatch to previous round's output
            if thresh_round != 1:
                print 'thresh round: {}'.format(thresh_round)
                bool_node = hou.pwd().createNode('cookie', 'boolean_round_{}'.format(thresh_round))
                bool_node_name = bool_node.name()
                prev_bool_node_name = thresh_states['thresh_round_{}'.format(thresh_round - 1)]['node_names']['bool_node']
                prev_bool_node = hou.pwd().node(prev_bool_node_name)
                bool_node.setInput(0, prev_bool_node)
            
            scatter_node = hou.pwd().createNode('scatter', 'scatter_{}'.format(thresh_key))
            scatter_node_name = scatter_node.name()
            scatter_node.parm('npts').set(new_count)
  
            # now connect the scatter node to the transform node of the previous round. Round one will connect to the main scatter node
            if thresh_round == 1:
                prev_end_node = hou.pwd().node('transform1')
                scatter_node.setInput(0, prev_end_node)
                prev_bool_node = None
            else:
                prev_end_node = prev_bool_node
                scatter_node.setInput(0, prev_end_node)
                
            scatter_points_tup = scatter_node.geometry().points()
                           
            # create a parent node for the geometry:
            subnet_name = 'subnet_round_{}'.format(thresh_round)
            subnet_node = hou.pwd().createNode('subnet', subnet_name)
            subnet_node_real_name = subnet_node.name()
            
            # create merge node for all your geometries:
            merge_node = subnet_node.createNode('merge', 'merge_round_{}'.format(thresh_round))
            merge_node_name = merge_node.name()
            
            transform_nodes = []
            for point in scatter_points_tup:
                point_tuple = tuple(point.position())
                box_node = subnet_node.createNode('box')
                scalar = 5
                thresh_round_maturity = new_placement
                new_scale = scalar * sqrt(new_maturity - thresh_round_maturity)
                box_node.parmTuple('size').set((0.1, 0.1, 0.1))
                
                box_node.parm('vertexnormals').set(True)
                transform_node = subnet_node.createNode('xform')
                transform_node.parmTuple('t').set(point_tuple)
                
                transform_node_name = transform_node.name()
                transform_node.setInput(0, box_node)
                transform_node.parmTuple('s').set((new_scale, new_scale, new_scale))
                transform_nodes.append(transform_node)
                merge_node.setNextInput(transform_node)
                
            # set the merge and subnet node flags so we can see it all   
            merge_node.setDisplayFlag(True)
            merge_node.setRenderFlag(True)
            
            bool_node = hou.pwd().createNode('cookie')
            bool_name = bool_node.name()
            bool_node.setInput(0, prev_end_node)
            bool_node.setInput(1, subnet_node)
            bool_node.parm('boolop').set(0)
            bool_node.parm('insidetest').set(False)
            bool_node.setDisplayFlag(True)
            bool_node.setRenderFlag(True)

            # set maturity back to its real value
            set_main_geometry(maturity=new_maturity)
            
            # update the thresh_round_status
            print 'scatter node: {}'.format(scatter_node_name)
            thresh_states['thresh_round_{}'.format(thresh_round)] = {
                'thresh_def_key': 'round{}'.format(thresh_def),
                'thresh_state': 'set', 
                'deleted': False, 
                'node_names': {'scatter_node': scatter_node_name, 'subnet_node': subnet_node_real_name, 'bool_node': bool_name},
                'placement': new_placement,
                'transform_nodes': transform_nodes,
                'maturity': new_maturity}
        elif (thresh_state_exist and new_maturity != old_maturity and new_placement == old_placement and new_count == old_count and 
                new_rotation == old_rotation and new_growth_rate == old_growth_rate and new_rate_variance == old_rate_variance):
            print 'level 4'
            update_geometry(thresh_round_dict, tdd, new_maturity)
                

def update_geometry(thresh_round_dict, thresh_def_dict, new_maturity):
    print 'updating geometry'
    # get all the nodes of thresh round subnet
    transform_nodes = thresh_round_dict['transform_nodes']
    
    # get all of the new values of the thresh deffinition
    thresh_round_maturity = thresh_round_dict['placement']
    scalar = 5
    new_scale = scalar * sqrt(new_maturity - thresh_round_maturity)
    for transform in transform_nodes:
        transform.parmTuple('s').set((new_scale, new_scale, new_scale))
     
                    
def delete_thresh_round_nodes(thresh_round_dict):
    thresh_round_nodes = thresh_round_dict['node_names']
    print 'Deleting Threshold Round {} Nodes'.format(thresh_round_nodes)

    for key, node in thresh_round_nodes.iteritems():
        print 'node to destroy: {}'.format(node)
        if node is None: pass
        else:
            hou.pwd().node(node).destroy()
            thresh_round_dict['deleted'] = True
            thresh_round_dict['thresh_state'] = 'unset'
    thresh_round_dict['node_names'] = None
    
   
def set_main_geometry(maturity):
    main_rotation = hou.pwd().parmTuple('main_rotation').eval()
    main_cube_size = sqrt(maturity)
    hou.node('box1').parmTuple('size').set((main_cube_size, main_cube_size, main_cube_size))
    hou.node('transform1').parmTuple('r').set(main_rotation)
