"""Export the vocabulary to standard RDF formats and WebVOWL JSON.

The database is the truth; these serializations are deterministic renders of it,
the same discipline as ``graph()`` and ``sync``. What is not in the vocabulary
is absent rather than invented.

Turtle and RDF/XML use SKOS for terms, OWL for structure and relations, and a
``monty:`` annotation namespace for gates the standards do not model (routes,
rulings, tests). WebVOWL JSON is emitted for the canvas viewer — the format
WebVOWL reads natively, without a separate converter.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

NS = "https://montology.dev/ns#"
ONTOLOGY = "https://montology.dev/ontology"
PREFIXES = {
    "monty": NS,
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


def _iri(local: str) -> str:
    return f"{NS}{local}"


def _esc(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def _collect(root_name: str) -> dict:
    from montology_ontology import (collisions, doctrines, exceptions, genera,
                                    overloads, questions, relations, renames,
                                    routes, words)

    return {
        "workspace": root_name,
        "words": words(),
        "genera": genera(),
        "relations": relations(),
        "routes": routes(),
        "renames": renames(),
        "overloads": overloads(),
        "collisions": collisions(),
        "exceptions": exceptions(),
        "doctrines": doctrines(),
        "questions": questions(),
    }


def _prefix_block() -> str:
    lines = ["@prefix monty: <{}> .".format(NS)]
    lines += [f"@prefix {p}: <{iri}> ." for p, iri in PREFIXES.items() if p != "monty"]
    return "\n".join(lines)


def turtle(*, root_name: str | None = None) -> str:
    """SKOS + OWL Turtle for the vocabulary."""
    from montology_core import workspace_root

    root = workspace_root()
    name = root_name or (root.name if root else "workspace")
    d = _collect(name)
    live = {w["name"] for w in d["words"]}
    by_name = {w["name"]: w for w in d["words"]}

    out = [_prefix_block(), ""]
    out.append(f"<{ONTOLOGY}> a owl:Ontology, skos:ConceptScheme ;")
    out.append(f'  rdfs:label "Montology — {name}"@en ;')
    out.append(f'  rdfs:comment "Vocabulary exported from .monty/ontology.db"@en .')
    out.append("")

    for w in sorted(d["words"], key=lambda x: x["name"]):
        local = w["name"]
        out.append(f"monty:{local} a skos:Concept, owl:Class ;")
        out.append(f"  skos:prefLabel {_esc(w['name'])}@en ;")
        if w.get("definition"):
            out.append(f"  skos:definition {_esc(w['definition'])}@en ;")
        if w.get("test"):
            out.append(f"  monty:test {_esc(w['test'])}@en ;")
        if w.get("code"):
            out.append(f"  monty:code {_esc(w['code'])} ;")
        if w.get("kind"):
            out.append(f"  monty:wordKind {_esc(w['kind'])} ;")
        if w.get("pos"):
            out.append(f"  monty:pos {_esc(w['pos'])} ;")
        if w.get("origin"):
            out.append(f"  monty:origin {_esc(w['origin'])} ;")
        if w.get("owner") and w["owner"] in live:
            out.append(f"  skos:broader monty:{w['owner']} ;")
        out.append(f"  skos:inScheme <{ONTOLOGY}> .")
        out.append("")

    for g in d["genera"]:
        if g["word_name"] in live and g["genus_name"] in live:
            out.append(f"monty:{g['word_name']} rdfs:subClassOf monty:{g['genus_name']} .")
            if g.get("why"):
                out.append(f"monty:{g['word_name']} rdfs:comment {_esc(g['why'])}@en .")
    if d["genera"]:
        out.append("")

    verbs: dict[str, list[tuple[str, str, str | None]]] = {}
    for r in d["relations"]:
        subj = r["subject"]
        obj = r["object"]
        if subj not in live or obj not in live:
            continue
        verbs.setdefault(r["verb"], []).append((subj, obj, r.get("why")))

    for verb, triples in sorted(verbs.items()):
        prop = _verb_property(verb)
        out.append(f"monty:{prop} a owl:ObjectProperty ;")
        out.append(f"  rdfs:label {_esc(verb)}@en .")
        for subj, obj, _why in triples:
            out.append(f"monty:{subj} monty:{prop} monty:{obj} .")
        out.append("")

    for r in d["renames"]:
        if r["was"] not in live and r["now"] in live:
            out.append(f"monty:{r['was']} a owl:Class ;")
            out.append("  owl:deprecated true ;")
            out.append(f"  skos:prefLabel {_esc(r['was'])}@en ;")
            out.append(f"  monty:supersededBy monty:{r['now']} .")
            if r.get("why"):
                out.append(f"monty:{r['was']} rdfs:comment {_esc(r['why'])}@en .")
            out.append("")

    for o in d["overloads"]:
        if o["say"] in live:
            out.append(f"monty:{o['dont_say']} a owl:Class ;")
            out.append("  owl:deprecated true ;")
            out.append(f"  skos:prefLabel {_esc(o['dont_say'])}@en ;")
            out.append(f"  monty:useInstead monty:{o['say']} .")
            if o.get("why"):
                out.append(f"monty:{o['dont_say']} rdfs:comment {_esc(o['why'])}@en .")
            out.append("")

    for r in d["routes"]:
        if r["to_word"] not in live:
            continue
        term = r["from_term"]
        if term not in live:
            out.append(f"monty:{term} a owl:Class ;")
            out.append("  owl:deprecated true ;")
            out.append(f"  skos:prefLabel {_esc(term)}@en ;")
            out.append(f"  monty:useInstead monty:{r['to_word']} ;")
        else:
            out.append(f"monty:{term} monty:useInstead monty:{r['to_word']} ;")
        out.append(f"  monty:register {_esc(r['register'])} ;")
        if r.get("scope"):
            out.append(f"  monty:scope {_esc(r['scope'])} ;")
        if r.get("why"):
            out.append(f"  rdfs:comment {_esc(r['why'])}@en ;")
        out.append("  .")
        out.append("")

    for c in d["collisions"]:
        if c["term"] in live:
            out.append(f"monty:{c['term']} monty:collisionWith {_esc(c['theirs'])} ;")
            out.append(f"  monty:theirMeaning {_esc(c['their_meaning'])}@en ;")
            out.append(f"  monty:ruling {_esc(c['ruling'])}@en .")
            out.append("")

    for e in d["exceptions"]:
        if e["word"] in live:
            out.append(f"monty:{e['word']} monty:exceptionScope {_esc(e['scope'])} ;")
            out.append(f"  monty:exceptionWhy {_esc(e['why'])}@en .")
            out.append("")

    for doc in d["doctrines"]:
        safe = _slug(doc["title"])
        out.append(f"monty:doctrine-{safe} a monty:Doctrine ;")
        out.append(f"  rdfs:label {_esc(doc['title'])}@en ;")
        out.append(f"  rdfs:comment {_esc(doc['body'])}@en .")
        out.append("")

    for q in d["questions"]:
        qid = q["id"]
        out.append(f"monty:question-{qid} a monty:Question ;")
        out.append(f"  rdfs:label {_esc(q['text'])}@en .")
        for w in q["answered_by"]:
            if w in live:
                out.append(f"monty:question-{qid} monty:answeredBy monty:{w} .")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def _verb_property(verb: str) -> str:
    safe = _slug(verb)
    return f"rel-{safe}" if safe else "rel"


def _slug(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in "-_":
            out.append("-")
        elif ch.isspace():
            out.append("-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "term"


def rdfxml(*, root_name: str | None = None) -> str:
    """RDF/XML serialization of the same vocabulary."""
    RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    ET.register_namespace("rdf", RDF)
    for p, iri in PREFIXES.items():
        ET.register_namespace(p, iri)

    root = ET.Element(f"{{{RDF}}}RDF")

    def desc(uri: str) -> ET.Element:
        el = ET.SubElement(root, f"{{{RDF}}}Description")
        el.set(f"{{{RDF}}}about", uri)
        return el

    def lit(parent: ET.Element, pred: str, value: str, lang: str = "en") -> None:
        child = ET.SubElement(parent, pred)
        if lang:
            child.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
        child.text = value

    def ref(parent: ET.Element, pred: str, target: str) -> None:
        child = ET.SubElement(parent, pred)
        child.set(f"{{{RDF}}}resource", target)

    def typ(parent: ET.Element, cls: str) -> None:
        ET.SubElement(parent, f"{{{RDF}}}type").set(f"{{{RDF}}}resource", cls)

    from montology_core import workspace_root

    root_ws = workspace_root()
    name = root_name or (root_ws.name if root_ws else "workspace")
    d = _collect(name)
    live = {w["name"] for w in d["words"]}

    onto = desc(ONTOLOGY)
    typ(onto, f"{PREFIXES['owl']}Ontology")
    typ(onto, f"{PREFIXES['skos']}ConceptScheme")
    lit(onto, f"{PREFIXES['rdfs']}label", f"Montology — {name}")

    for w in sorted(d["words"], key=lambda x: x["name"]):
        el = desc(_iri(w["name"]))
        typ(el, f"{PREFIXES['skos']}Concept")
        typ(el, f"{PREFIXES['owl']}Class")
        lit(el, f"{PREFIXES['skos']}prefLabel", w["name"])
        if w.get("definition"):
            lit(el, f"{PREFIXES['skos']}definition", w["definition"])
        if w.get("test"):
            lit(el, f"{NS}test", w["test"])
        if w.get("owner") and w["owner"] in live:
            ref(el, f"{PREFIXES['skos']}broader", _iri(w["owner"]))
        ref(el, f"{PREFIXES['skos']}inScheme", ONTOLOGY)

    for g in d["genera"]:
        if g["word_name"] in live and g["genus_name"] in live:
            el = desc(_iri(g["word_name"]))
            ref(el, f"{PREFIXES['rdfs']}subClassOf", _iri(g["genus_name"]))

    verbs: dict[str, list[tuple[str, str]]] = {}
    for r in d["relations"]:
        if r["subject"] in live and r["object"] in live:
            verbs.setdefault(r["verb"], []).append((r["subject"], r["object"]))

    for verb, pairs in sorted(verbs.items()):
        prop = _verb_property(verb)
        pel = desc(_iri(prop))
        typ(pel, f"{PREFIXES['owl']}ObjectProperty")
        lit(pel, f"{PREFIXES['rdfs']}label", verb)
        for subj, obj in pairs:
            el = desc(_iri(subj))
            ref(el, _iri(prop), _iri(obj))

    rough = ET.tostring(root, encoding="unicode", xml_declaration=True)
    return rough if rough.startswith("<?xml") else f'<?xml version="1.0" encoding="UTF-8"?>\n{rough}'


def vowl(*, root_name: str | None = None) -> dict:
    """WebVOWL JSON — the format the canvas viewer consumes."""
    from montology_core import workspace_root

    root = workspace_root()
    name = root_name or (root.name if root else "workspace")
    d = _collect(name)
    live = {w["name"] for w in d["words"]}

    classes: list[dict] = []
    class_attrs: list[dict] = []
    properties: list[dict] = []
    prop_attrs: list[dict] = []
    id_map: dict[str, str] = {}

    def cid(local: str) -> str:
        if local not in id_map:
            id_map[local] = str(len(id_map))
        return id_map[local]

    for w in sorted(d["words"], key=lambda x: x["name"]):
        i = cid(w["name"])
        attrs = ["external"] if w.get("origin") else []
        if w.get("kind") == "core":
            attrs.append("rdf")
        classes.append({"id": i, "type": "owl:Class"})
        ca: dict = {
            "id": i,
            "label": {"undefined": w["name"]},
            "iri": _iri(w["name"]),
            "comment": {"undefined": w.get("definition") or ""},
            "attributes": attrs,
            "individuals": [],
        }
        if w.get("test"):
            ca.setdefault("annotations", {})["monty:test"] = [{"identifier": "monty:test",
                "language": "undefined", "value": w["test"], "type": "label"}]
        class_attrs.append(ca)

    hierarchy: list[tuple[str, str]] = []
    for g in d["genera"]:
        if g["word_name"] in live and g["genus_name"] in live:
            hierarchy.append((cid(g["word_name"]), cid(g["genus_name"])))

    for w in d["words"]:
        if w.get("owner") and w["owner"] in live and w["name"] in live:
            hierarchy.append((cid(w["name"]), cid(w["owner"])))

    for sub_id, super_id in hierarchy:
        pi = str(len(properties))
        properties.append({"id": pi})
        prop_attrs.append({
            "id": pi,
            "label": {"undefined": "subClassOf"},
            "type": "rdfs:subClassOf",
            "comment": {"undefined": ""},
            "attributes": [],
            "domain": sub_id,
            "range": super_id,
        })

    verbs: dict[str, list[tuple[str, str]]] = {}
    for r in d["relations"]:
        if r["subject"] in live and r["object"] in live:
            verbs.setdefault(r["verb"], []).append((r["subject"], r["object"]))

    for verb, pairs in sorted(verbs.items()):
        for subj, obj in pairs:
            pi = str(len(properties))
            properties.append({"id": pi})
            prop_attrs.append({
                "id": pi,
                "label": {"undefined": verb},
                "type": "owl:objectProperty",
                "comment": {"undefined": ""},
                "attributes": ["object"],
                "domain": cid(subj),
                "range": cid(obj),
            })

    retired: set[str] = set()
    for r in d["renames"]:
        if r["was"] not in live:
            retired.add(r["was"])
    for o in d["overloads"]:
        retired.add(o["dont_say"])
    for r in d["routes"]:
        if r["from_term"] not in live:
            retired.add(r["from_term"])

    for term in sorted(retired):
        i = cid(term)
        classes.append({"id": i, "type": "owl:Class"})
        class_attrs.append({
            "id": i,
            "label": {"undefined": term},
            "iri": _iri(term),
            "comment": {"undefined": "retired term"},
            "attributes": ["deprecated", "external"],
            "individuals": [],
        })

    word_count = len([w for w in d["words"]])
    return {
        "namespace": [{"name": "monty", "iri": NS}],
        "header": {
            "languages": ["undefined"],
            "title": {"undefined": f"Montology — {name}"},
            "iri": ONTOLOGY,
            "version": "",
            "author": ["Montology"],
            "description": {"undefined": "Vocabulary exported from .monty/ontology.db"},
            "other": {},
        },
        "metrics": {
            "classCount": len(classes),
            "objectPropertyCount": len(properties),
            "propertyCount": len(properties),
            "nodeCount": len(classes) + len(properties),
            "individualCount": 0,
        },
        "class": classes,
        "classAttribute": class_attrs,
        "datatype": [],
        "datatypeAttribute": [],
        "property": properties,
        "propertyAttribute": prop_attrs,
    }


def export(fmt: str = "ttl", *, root_name: str | None = None) -> str:
    """Serialize the vocabulary. ``fmt``: ``ttl``, ``xml``, ``vowl``."""
    f = fmt.lower().removesuffix(".json")
    if f in ("ttl", "turtle"):
        return turtle(root_name=root_name)
    if f in ("xml", "rdf", "rdfxml"):
        return rdfxml(root_name=root_name)
    if f == "vowl":
        return json.dumps(vowl(root_name=root_name), indent=2, ensure_ascii=False) + "\n"
    raise ValueError(f"unknown export format {fmt!r} — use ttl, xml, or vowl")
