#!/usr/bin/env python3
"""Entity Guard: inject named entities as standalone memories before mem0 ingestion.

Root cause: mem0's ADDITIVE_EXTRACTION LLM generalizes specific entity names into
category descriptions ("Under Armour" → "a renowned outdoor gear company"), causing
open-domain questions to fail (54.3% vs 74-82% for other categories).

Fix: extract named entities from each chunk via regex NER and add them as standalone
memories in the format "{Speaker} mentioned {entity} in context of {brief_context}".
This ensures the exact entity name is always retrievable, regardless of mem0's
extraction quality.

Usage:
    python3 entity_guard.py --conversation 4 --user-id locomo_4_full01 \
        --server http://localhost:8888 --dry-run
"""

import argparse
import json
import re
import sys
import urllib.request
import time


def extract_entities(text):
    """Extract named entities using regex heuristics.
    
    Targets: CamelCase words, multi-word proper nouns, single proper nouns
    that mem0's extraction LLM tends to drop or generalize.
    """
    entities = set()

    # 1. CamelCase (MinaLima, iPhone, TikTok)
    for m in re.findall(r'\b([a-zA-Z]*[a-z][A-Z][a-zA-Z]*)\b', text):
        if len(m) >= 4:
            entities.add(m)

    # 2. Proper noun phrases (mid-sentence + sentence-start with coordinator)
    for m in re.finditer(
        r'(?<=\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})(?=\s|$|[,.!?;:])', text
    ):
        phrase = m.group(1)
        start = m.start()
        before = text[:start].rstrip()

        is_sentence_start = (start == 0) or (before and before[-1] in '.!?')

        if is_sentence_start:
            after = text[m.end():m.end() + 25]
            if re.match(r'^\s+(and|or)\s+(I|we|you|he|she|they|my|our|the)', after):
                entities.add(phrase)
            continue

        stop_phrases = {
            'the following', 'in the', 'at the', 'on the', 'for the',
            'thank you', 'good morning', 'of course', 'no problem',
        }
        if phrase.lower() in stop_phrases:
            continue
        if ' ' not in phrase:
            common_single = {
                'The', 'A', 'An', 'I', 'He', 'She', 'It', 'We', 'You',
                'They', 'This', 'That', 'These', 'Those', 'But', 'And',
                'Or', 'So', 'Yet', 'Nor', 'For', 'However', 'Therefore',
                'Thanks', 'Yeah', 'Oh', 'Well', 'Right', 'Sure', 'Okay',
                'Maybe', 'Probably', 'Definitely', 'Absolutely', 'Totally',
                'Really', 'Very', 'Much', 'More', 'Most', 'Some', 'Any',
                'All', 'Each', 'Every', 'Both', 'Few', 'Many', 'Other',
                'Another', 'Such', 'Same', 'One', 'Two', 'Three', 'Four',
                'Five', 'First', 'Second', 'Third', 'Last', 'Next',
                'New', 'Old', 'Big', 'Small', 'Good', 'Bad', 'Great',
                'Nice', 'Cool', 'Awesome', 'Amazing', 'Happy', 'Sad',
                'Angry', 'Tired', 'Excited', 'Because', 'Before', 'After',
                'During', 'Without', 'Through', 'Until', 'Between',
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                'Saturday', 'Sunday', 'January', 'February', 'March',
                'April', 'May', 'June', 'July', 'August', 'September',
                'October', 'November', 'December',
            }
            if phrase in common_single:
                continue
        entities.add(phrase)

    return entities


def get_brief_context(text, entity, max_len=80):
    """Get a brief context snippet around the entity mention."""
    idx = text.lower().find(entity.lower())
    if idx < 0:
        return text[:max_len]
    start = max(0, idx - 30)
    end = min(len(text), idx + len(entity) + 30)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'
    return snippet[:max_len]


def build_entity_memories(conversation, speaker_a, speaker_b):
    """Build entity memory strings from a LoCoMo conversation.
    
    Returns list of (memory_text, source_turn) tuples.
    Format: "FACT: {Speaker} mentioned '{entity}' — {context}"
    This phrasing encourages mem0 to store it as a verbatim fact.
    """
    entity_mems = []
    seen_entities = set()  # dedupe: only first mention per entity
    
    for session_key, turns in conversation.items():
        if not isinstance(turns, list):
            continue
        for turn_idx, turn in enumerate(turns):
            speaker = turn.get('speaker', '?')
            text = turn.get('text', '')
            if not text:
                continue
            
            entities = extract_entities(text)
            for entity in sorted(entities):
                key = f"{speaker}:{entity.lower()}"
                if key in seen_entities:
                    continue
                seen_entities.add(key)
                
                context = get_brief_context(text, entity)
                mem_text = (
                    f"FACT: {speaker} mentioned '{entity}' — {context}"
                )
                entity_mems.append((mem_text, f"{session_key}[{turn_idx}]"))
    
    return entity_mems


def add_memory(server, user_id, memory_text, dry_run=False):
    """Add a single memory to the mem0 server with entity-preservation instructions."""
    if dry_run:
        return True
    
    payload = json.dumps({
        "messages": [{"role": "user", "content": memory_text}],
        "user_id": user_id,
        "custom_instructions": (
            "Store this fact exactly as stated. Preserve all proper nouns, brand names, "
            "person names, and entity names verbatim. Do not generalize, paraphrase, or "
            "replace specific names with category descriptions."
        ),
    }).encode()
    
    req = urllib.request.Request(
        f"{server}/memories",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return True
    except Exception as e:
        print(f"  ERROR adding memory: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Entity Guard for LoCoMo benchmark")
    parser.add_argument("--conversation", type=int, required=True, help="Conversation index (0-9)")
    parser.add_argument("--user-id", required=True, help="mem0 user_id")
    parser.add_argument("--server", default="http://localhost:8888", help="mem0 server URL")
    parser.add_argument("--dataset", default="datasets/locomo/locomo10.json", help="LoCoMo dataset path")
    parser.add_argument("--dry-run", action="store_true", help="Print entities without adding")
    parser.add_argument("--output", help="Save entity list to JSON file")
    args = parser.parse_args()

    # Load dataset
    with open(args.dataset) as f:
        data = json.load(f)
    
    conv = data[args.conversation]
    conversation = conv['conversation']
    speaker_a = conversation.get('speaker_a', 'Speaker A')
    speaker_b = conversation.get('speaker_b', 'Speaker B')
    
    print(f"Conversation {args.conversation}: {speaker_a} & {speaker_b}")
    
    # Build entity memories
    entity_mems = build_entity_memories(conversation, speaker_a, speaker_b)
    print(f"Extracted {len(entity_mems)} unique entity mentions")
    
    # Show summary by entity type
    entity_names = [m.split("'")[1] for m, _ in entity_mems if "'" in m]
    print(f"Unique entities: {len(set(entity_names))}")
    print(f"Sample entities: {sorted(set(entity_names))[:20]}")
    
    if args.dry_run:
        print("\n--- DRY RUN: First 20 entity memories ---")
        for mem, src in entity_mems[:20]:
            print(f"  [{src}] {mem[:120]}")
        if len(entity_mems) > 20:
            print(f"  ... and {len(entity_mems) - 20} more")
    else:
        print(f"\nAdding {len(entity_mems)} entity memories to {args.server}...")
        success = 0
        failed = 0
        for i, (mem, src) in enumerate(entity_mems):
            ok = add_memory(args.server, args.user_id, mem)
            if ok:
                success += 1
            else:
                failed += 1
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(entity_mems)} ({success} ok, {failed} failed)")
            time.sleep(0.1)  # Rate limit
        
        print(f"\nDone: {success} added, {failed} failed out of {len(entity_mems)}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(
                [{"memory": m, "source": s} for m, s in entity_mems],
                f, indent=2, ensure_ascii=False,
            )
        print(f"Saved entity list to {args.output}")


if __name__ == '__main__':
    main()