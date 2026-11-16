"""Disposable opening-contract fixtures; no human or actual media acceptance."""
import copy
import json
from pathlib import Path
from opening_alignment_guard import opening_context_sha256, REVIEW_ITEMS
from stage_checks import file_digest


def attach_opening_fixture(data, root, duration=1.0):
    root = Path(root)
    qa = data.setdefault("qa", {})
    topic = qa.setdefault("topic_alignment", {})
    required = {"video", "cover_3_4", "cover_4_3"}
    if not required <= set(data.get("deliverables", {})) or not required <= set(qa.get("reviewed_sha256", {})):
        # G4 intentionally has no release-cover requirement. Do not invent a
        # final opening pass for that fixture; G5 will still reject it.
        topic["opening_alignment"] = dict(status="pending", evidence=dict(file="", sha256=""))
        return None
    heard = topic.setdefault("opening_voiceover", {})
    heard.setdefault("heard_question", "Synthetic specific opening question; no spoken media claim")
    heard.setdefault("heard_answer_route", "Synthetic concise answer; no spoken media claim")
    review = json.loads((Path(__file__).resolve().parents[2] / "assets/opening-review-template.json").read_text())
    statement = "Synthetic contract fixture only: specific cover question, heard question and route, and continuous visual entry reviewed; no actual viewing occurred."
    source = root / "synthetic-opening-source.txt"
    source.write_text(statement)
    review.update(status="pass", review_scope="final_export", context_sha256=opening_context_sha256(data),
                  viewed_range_s=[0, duration], question_range_s=[0, duration * .4],
                  answer_route_range_s=[duration * .4, duration * .8],
                  question_relation="specific_equivalent", question_comparison="Synthetic comparison of the same specific question, not an actual semantic verdict")
    review["sources"] = [dict(status="pass", actually_watched=True, actually_heard=True,
                            method="normal_speed_continuous_av", range_s=[0, duration], kind="editor", reviewer="synthetic reviewer", reference="synthetic-source-only",
                            statement=statement, reviewed_items=sorted(REVIEW_ITEMS),
                            evidence=dict(file=source.name, sha256=file_digest(source)))]
    review["video"] = dict(file=data["deliverables"]["video"], sha256=qa["reviewed_sha256"]["video"])
    review["answer_route_review"] = dict(status="pass", observation="Synthetic concise answer follows the actual question in this contract fixture only")
    review["covers"] = {key: dict(status="pass", file=data["deliverables"][key], sha256=qa["reviewed_sha256"][key],
                         observed_title="Synthetic specific question", core_question="Synthetic same specific question", subject="Synthetic sky subject",
                         question_relation="specific_equivalent", comparison="Synthetic cover and spoken question retain the same promised relation")
                         for key in ("cover_3_4", "cover_4_3")}
    review["visual_handoff"] = dict(status="pass", mode="motivated_transition", range_s=[0, duration],
                                    opening_subject="Synthetic sky observer", relationship="Synthetic cover sky to observed sky",
                                    observation="Synthetic continuous-entry observation, no real visual result")
    # Content-addressed fixture records keep copied test packets independent.
    from opening_alignment_guard import digest
    path = root / ("synthetic-opening-review-" + digest(review) + ".json")
    path.write_text(json.dumps(review, ensure_ascii=False))
    topic["opening_alignment"] = dict(status="pass", evidence=dict(file=path.name, sha256=file_digest(path)))
    return review
