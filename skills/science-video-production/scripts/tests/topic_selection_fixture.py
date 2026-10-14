"""Fabricated software fixture. Never use as real topic/source/interest evidence."""
from topic_selection_guard import selection_context_sha256


def attach_topic_selection_fixture(data):
    brief=data.setdefault('brief',{});brief.setdefault('audience','Synthetic ordinary adult fixture')
    prior=brief.setdefault('audience_start',{})
    if not prior.get('assumed_knowledge'): prior['assumed_knowledge']=['Synthetic prior knowledge, no real audience research']
    if not brief.get('one_sentence_answer'): brief['one_sentence_answer']='Synthetic answer, no scientific claim'
    targets=brief.setdefault('understanding_targets',{})
    if not targets.get('transfer'): targets['transfer']='Synthetic comparison payoff'
    data.setdefault('topic',{}).setdefault('current',{}).setdefault('question','Synthetic topic question')
    ident='TOPIC_SELECTION_SYNTHETIC'
    sources=data.setdefault('sources',[])
    if not any(s.get('id')==ident for s in sources):
        sources.append({'id':ident,'url':'https://example.org/synthetic-topic-fixture','title':'Synthetic fixture only',
             'publisher':'Synthetic, not an actual publisher','accessed_on':'2026-01-01','note':'Fabricated software source only',
             'scope_note':'Fabricated traceability row, not real scientific support','supported_claim_ids':[]})
    brief['topic_selection']={'audience_category':'ordinary_adults','conflict_or_question':'Synthetic explainable difference',
        'adult_relevance':'Synthetic relevance, not real interest','knowledge_increment':'Synthetic mechanism beyond premise',
        'source_ids':[ident],'causal_visualization':'Synthetic objects visibly change under a controlled condition',
        'feasibility':{'materials_and_rights_plan':'Synthetic original drawing plan','method':'Synthetic layered 2D',
                       'constraints':'Synthetic scope limits; no real production','blocking_gaps':[]},
        'interest_basis':'editorial_hypothesis','audience_evidence':[],'disqualifiers':[],
        'review':{'status':'selected','reviewer':'synthetic editor, not a real review','reason':'Synthetic test of selection structure only'}}
    refresh_topic_selection_fixture(data)


def refresh_topic_selection_fixture(data):
    card=data.get('brief',{}).get('topic_selection')
    if isinstance(card,dict):card['review']['context_sha256']=selection_context_sha256(data)
