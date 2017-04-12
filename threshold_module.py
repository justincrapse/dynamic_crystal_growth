import hou
from time import sleep

gtc = None
thresh_dict = {}
thresh_dict_old = {}

def set_thresholds():
    global gtc  # global threshold count
    if not gtc:
        gtc = 0
    threshold_count = hou.pwd().parm('threshold_count').eval()
    maturity_max = hou.pwd().parm('maturity').parmTemplate().maxValue()
    
    # fist check to see if there are less or more thresholds than before
    if threshold_count > gtc:
        # just add the parameters per new threshold
        # if thresholds previously existed, bring back thier on-deletion parameter values
        new_rounds = threshold_count - gtc
        for round in range(gtc, gtc + new_rounds):
            round += 1
            parm_group = hou.pwd().parmTemplateGroup()
            default_placement = (maturity_max / threshold_count * round,)
            
            # set a label for each threshold round's parameters block
            parm_template = hou.LabelParmTemplate('round{}label'.format(round), 'Threshold {}'.format(round))
            parm_group.appendToFolder('Thresholds', parm_template)
            
            # placement (relative to maturity maximum)
            parm_template = hou.FloatParmTemplate('round{}placement'.format(round), 'T{} Placement'.format(round), 1, default_value=default_placement,
                                                  max=maturity_max, max_is_strict=True, 
                                                  script_callback="hou.pwd().hdaModule().generate_geometry(flag='thresh_values')", 
                                                  script_callback_language=hou.scriptLanguage.Python)
            parm_group.appendToFolder('Thresholds', parm_template)
            
            # scatter count per round
            parm_template = hou.FloatParmTemplate('round{}count'.format(round), 'T{} Count'.format(round), 1, max=1000, default_value=(100,),
                                                  script_callback="hou.pwd().hdaModule().generate_geometry(flag='thresh_values')", 
                                                  script_callback_language=hou.scriptLanguage.Python)
            parm_group.appendToFolder('Thresholds', parm_template)
            
            # round angle
            parm_template = hou.FloatParmTemplate('round{}rotation'.format(round), 'T{} Rotation'.format(round), 3,
                                                  script_callback="hou.pwd().hdaModule().generate_geometry(flag='thresh_values')", 
                                                  script_callback_language=hou.scriptLanguage.Python)
            parm_group.appendToFolder('Thresholds', parm_template)
            
            # growth rate sqrt multiplier
            parm_template = hou.FloatParmTemplate('round{}growth_rate'.format(round), 'T{} Growth Rate'.format(round), 1, max=1,
                                                  script_callback="hou.pwd().hdaModule().generate_geometry(flag='thresh_values')", 
                                                  script_callback_language=hou.scriptLanguage.Python)
            parm_group.appendToFolder('Thresholds', parm_template)
            
            # growth rate per-instance variance
            parm_template = hou.FloatParmTemplate('round{}rate_variance'.format(round), 'T{} Rate Variance'.format(round), 1, max=1,
                                                  script_callback="hou.pwd().hdaModule().generate_geometry(flag='thresh_values')", 
                                                  script_callback_language=hou.scriptLanguage.Python)
            parm_group.appendToFolder('Thresholds', parm_template)
            
            # separator
            parm_template = hou.SeparatorParmTemplate('round{}separator'.format(round))
            parm_group.appendToFolder('Thresholds', parm_template)
            
            hou.pwd().setParmTemplateGroup(parm_group)
        
        gtc = threshold_count
    elif threshold_count < gtc:
        # delete the extra ones
        # try to keep the values though
        rounds_to_delete = gtc - threshold_count
        
        for round in range(threshold_count, gtc):
            round += 1
            parm_group = hou.pwd().parmTemplateGroup()
            parm_group.remove('round{}placement'.format(round))
            parm_group.remove('round{}label'.format(round))
            parm_group.remove('round{}separator'.format(round))
            parm_group.remove('round{}count'.format(round))
            parm_group.remove('round{}rotation'.format(round))
            parm_group.remove('round{}growth_rate'.format(round))
            parm_group.remove('round{}rate_variance'.format(round))
            hou.pwd().setParmTemplateGroup(parm_group)
        
        gtc = threshold_count
        
    set_thresh_dictionary()
     
def set_thresh_dictionary():
    for round in range(1, gtc + 1):
        placement = hou.pwd().parm('round{}placement'.format(round)).eval()
        count = hou.pwd().parm('round{}count'.format(round)).eval()
        rotation = hou.pwd().parmTuple('round{}rotation'.format(round)).eval()
        growth_rate = hou.pwd().parm('round{}growth_rate'.format(round)).eval()
        rate_variance = hou.pwd().parm('round{}rate_variance'.format(round)).eval()
        dict_key = 'round{}'.format(round) 
        
        if dict_key in thresh_dict:
            thresh_dict_old[dict_key] = thresh_dict[dict_key]
        
        thresh_dict[dict_key] = {'placement': placement, 'count': count, 'rotation': rotation, 'growth_rate': growth_rate,
                                 'rate_variance': rate_variance}
        
        
        
