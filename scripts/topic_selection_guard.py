"""Editorial selection evidence only. No prediction of audience interest or popularity."""
import hashlib
import json
from urllib.parse import urlparse
from datetime import date

LIMITS = "Topic checks verify a declared editorial decision and its inputs, not real audience interest, scientific truth or production approval."
DISQUALIFIERS = {"common_knowledge_only", "definition_only", "title_only_change", "asset_led", "unsupported_hook", "no_explanatory_payoff", "unvisualizable", "unfeasible", "specialist_only_hook", "no_viewer_entry"}


def obj(x):
    return x if isinstance(x, dict) else {}


def seq(x):
    return x if isinstance(x, list) else []


def meaningful(x):
    return isinstance(x, str) and x.strip().casefold() not in {"", "todo", "pending", "tbd", "unknown", "n/a", "none", "pass", "ok", "待定", "待补", "待审", "未审", "待验", "未验", "待核", "不适用", "未核实", "未完成", "无", "通过", "涨知识", "有趣", "提高兴趣"}


def selection_context_sha256(data):
    brief = obj(data.get("brief")); card = obj(brief.get("topic_selection"))
    refs = seq(card.get("source_ids"))
    payload = {"topic": obj(data.get("topic")).get("current"),
               "audience": brief.get("audience"), "prior_knowledge": obj(brief.get("audience_start")).get("assumed_knowledge"),
               "answer": brief.get("one_sentence_answer"), "payoff": obj(brief.get("understanding_targets")).get("transfer"),
               "card": {k: v for k, v in card.items() if k != "review"},
               "sources": [s for s in seq(data.get("sources")) if obj(s).get("id") in refs]}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_topic_selection(checks):
    """Require current selection before plan/G1/render; no legacy/render exemption."""
    data = checks.data; brief = obj(data.get("brief")); card = obj(brief.get("topic_selection"))
    need = lambda ok, text: checks.need(ok, "topic selection: " + text)
    need(bool(card), "editorial selection card required before production")
    need(card.get("audience_category") == "ordinary_adults" or (card.get("selection_origin") == "user_requested" and meaningful(card.get("audience_category"))), "default ordinary adult audience or explicit user-requested audience required")
    need(meaningful(brief.get("audience")), "specific adult audience context required")
    known = obj(brief.get("audience_start")).get("assumed_knowledge")
    need(isinstance(known, list) and bool(known) and all(meaningful(k) for k in known), "explicit audience prior knowledge required")
    need(meaningful(brief.get("one_sentence_answer")) and meaningful(obj(brief.get("understanding_targets")).get("transfer")), "concrete answer and explanatory payoff required")
    need(meaningful(obj(obj(data.get("topic")).get("current")).get("question")), "specific topic question required")
    for field in ("conflict_or_question", "adult_relevance", "knowledge_increment", "causal_visualization"):
        need(meaningful(card.get(field)), field + " must explain why this question merits production")
    feasibility = obj(card.get("feasibility"))
    for field in ("materials_and_rights_plan", "method", "constraints"):
        need(meaningful(feasibility.get(field)), "feasibility " + field + " required; existing assets are not a selection rationale")
    need(feasibility.get("blocking_gaps") == [], "unresolved feasibility gaps block production")
    reasons = card.get("disqualifiers")
    user_selected = card.get("selection_origin") == "user_requested"
    if user_selected:
        checks.evidence(card.get("user_request_evidence"), "topic selection original user request")
        need(meaningful(card.get("user_request_reference")) and meaningful(card.get("scope_reason")), "user-requested topic needs original scope and explanation rationale")
    preference_only = {"common_knowledge_only", "definition_only", "title_only_change", "specialist_only_hook", "no_viewer_entry"}
    valid_reasons = isinstance(reasons, list) and all(isinstance(x, str) and x in DISQUALIFIERS for x in reasons)
    need(valid_reasons and (not reasons or (user_selected and set(reasons) <= preference_only)), "declared factual/feasibility disqualifiers block selection; editorial taste alone cannot veto a user-requested topic")
    if not user_selected:
        alternatives = card.get("alternatives")
        need(isinstance(alternatives, list) and bool(alternatives), "editorial choice needs a feasible alternative question and comparison reason")
        question = obj(obj(data.get("topic")).get("current")).get("question")
        key = lambda value: "".join(c.casefold() for c in value if c.isalnum()) if isinstance(value, str) else ""
        seen = {key(question)}
        for raw in seq(alternatives):
            alternative = obj(raw); candidate = alternative.get("question")
            valid_question = meaningful(candidate) and bool(key(candidate))
            need(valid_question and key(candidate) not in seen, "alternative must be a distinct question, not the selected question or a duplicate")
            need(meaningful(alternative.get("not_selected_reason")), "alternative needs a concrete not_selected_reason comparing viewer entry, visual payoff or feasibility")
            if valid_question: seen.add(key(candidate))
    refs = card.get("source_ids"); sources = seq(data.get("sources"))
    valid = isinstance(refs, list) and bool(refs) and all(isinstance(i, str) and i for i in refs)
    need(valid and len(refs) == len(set(refs)) if valid else False, "unique factual main-source IDs required")
    for ident in refs if valid else []:
        matches = [obj(s) for s in sources if obj(s).get("id") == ident]
        if not need(len(matches) == 1, "factual main source missing/ambiguous: " + ident):
            continue
        source = matches[0]; url = source.get("url")
        try:
            parsed = urlparse(url) if isinstance(url, str) else None
        except ValueError:
            parsed = None
        need(parsed is not None and parsed.scheme in ("http", "https") and bool(parsed.netloc), "main source needs traceable URL")
        for field in ("title", "publisher", "scope_note"):
            need(meaningful(source.get(field)), "main source " + field + " required")
        try:
            checked = date.fromisoformat(source.get("accessed_on", "")); need(checked <= date.today(), "source check date cannot be in future")
        except (ValueError, TypeError):
            need(False, "actual main-source check date required")
    basis = card.get("interest_basis")
    need(basis in ("editorial_hypothesis", "observed_audience_evidence"), "interest basis must distinguish editorial hypothesis from actual audience evidence")
    evidence = card.get("audience_evidence")
    need(isinstance(evidence, list), "audience evidence must be explicit; [] is valid for an editorial hypothesis")
    if basis == "observed_audience_evidence":
        need(bool(seq(evidence)), "claimed observed audience interest requires real evidence")
    for item in seq(evidence):
        item = obj(item)
        checks.evidence(item, "topic selection actual audience evidence")
        for field in ("origin_reference", "observed_scope", "limitations"):
            need(meaningful(item.get(field)), "audience evidence " + field + " required")
    review = obj(card.get("review"))
    need(review.get("status") == "selected", "pending/revise/rejected editorial decision blocks production")
    need(meaningful(review.get("reviewer")) and meaningful(review.get("reason")), "actual editor and selection reason required; no automatic interest score")
    try:
        actual_context = selection_context_sha256(data)
    except (ValueError, TypeError):
        actual_context = None
        need(False, "selection inputs must be finite JSON data")
    need(actual_context is not None and review.get("context_sha256") == actual_context, "stale topic/audience/source/feasibility selection; re-review before production")
