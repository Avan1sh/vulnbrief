from vulnbrief.evaluation import grade_trial


def recovery_events(model_decision_before_success=True):
    kinds=[('plan',{}),('tool_start',{'tool':'get_cve_record'}),
           ('tool_result',{'tool':'get_cve_record','observation':{'error':{'injected':True}}})]
    decision=('decision',{})
    success=('tool_result',{'tool':'get_cve_record','observation':{'ok':True}})
    kinds+=([decision,success] if model_decision_before_success else [success,decision])
    return [dict(sequence=i+1,event=kind,**data) for i,(kind,data) in enumerate(kinds)]


def test_recovery_grade_requires_a_model_decision_before_success():
    case={'cves':['CVE-2024-3400'],'expected':{'recovery':True}}
    name='model_selected_recovery_after_injected_failure'
    assert grade_trial(case,None,recovery_events())[name]
    assert not grade_trial(case,None,recovery_events(False))[name]


def test_scope_grade_rejects_an_error_after_model_calls():
    case={'expected':{'input_rejection':'At most three'}}
    assert grade_trial(case,None,[],'At most three CVEs per run',0)['scope_rejected_before_model']
    assert not grade_trial(case,None,[],'At most three CVEs per run',1)['scope_rejected_before_model']


def test_failed_run_cannot_pass_an_accepted_analysis_check():
    case={'cves':['CVE-2099-9999999'],'expected':{'status':'partial'}}
    checks=grade_trial(case,{'status':'failed','analysis':None,'evidence':[]},[])
    assert not checks['accepted_analysis']
    assert not checks['expected_status']
