import os
import json
from spellchecker import SpellChecker
import re

folder_path = "D:\Study\Lab\Vitualization\Ink-Pulse\static\chi2022-coauthor-v1.0\coauthor-json"
spell = SpellChecker(language='en')
spell.word_frequency.add("shapeshifter")
spell.word_frequency.add("mana")
spell.word_frequency.add("mana's")
spell.word_frequency.add("iii")
spell.word_frequency.add("tv")
spell.word_frequency.add("vr")
spell.word_frequency.add("usa")
spell.word_frequency.add("etc")
spell.word_frequency.add("elon")
spell.word_frequency.add("snapchat")
spell.word_frequency.add("instagram")
spell.word_frequency.add("apps")
spell.word_frequency.add("im")
spell.word_frequency.add("wasnt")
spell.word_frequency.add("werent")
spell.word_frequency.add("dont")
spell.word_frequency.add("wouldnt")
spell.word_frequency.add("didnt")
spell.word_frequency.add("doesnt")
spell.word_frequency.add("hasnt")
spell.word_frequency.add("gps")
spell.word_frequency.add("ii")
spell.word_frequency.add("duolingo")
spell.word_frequency.add("gpa")
spell.word_frequency.add("app")
spell.word_frequency.add("texting")
spell.word_frequency.add("umm")
spell.word_frequency.add("hmm")
spell.word_frequency.add("iv")
spell.word_frequency.add("ipads")
spell.word_frequency.add("dna")
spell.word_frequency.add("fbi")
spell.word_frequency.add("tech")
spell.word_frequency.add("nasa")
spell.word_frequency.add("dvd")
spell.word_frequency.add("ptsd")
spell.word_frequency.add("smartphone")
spell.word_frequency.add("covid")
spell.word_frequency.add("shapeshift")
spell.word_frequency.add("pc")
spell.word_frequency.add("multiplayer")
spell.word_frequency.add("coronavirus")
spell.word_frequency.add("shapeshifted")
spell.word_frequency.add("hmmmm")
spell.word_frequency.add("shapeshifters")
spell.word_frequency.add("shapeshift")
spell.word_frequency.add("shapeshifting")
spell.word_frequency.add("thats")
spell.word_frequency.add("ufo")
spell.word_frequency.add("cia")
spell.word_frequency.add("afterall")
spell.word_frequency.add("mcdavis")
spell.word_frequency.add("ncaa")
spell.word_frequency.add("uh")

results = []
error_docs = {}
for file_name in os.listdir(folder_path):
    if file_name.endswith(".jsonl"):
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data["text"][0]
        # print(text)
        words = re.findall(r"[A-Za-z]+'?[A-Za-z]+", text)
        filtered_words = []
        for i, word in enumerate(words):
            if word.isupper():
                continue
            if word[0].isupper() and not (i == 0 or words[i-1].endswith(('.', '!', '?'))):
                continue
            filtered_words.append(word)
        misspelled = spell.unknown(filtered_words)

        if len(misspelled) > 2:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            error_sentences = [
                s for s in sentences 
                if any(re.search(rf"\b{re.escape(word)}\b", s, flags=re.IGNORECASE) 
                    for word in misspelled)
            ]
            
            results.append({
                "file": file_name,
                "errors": list(misspelled),
                "error_sentences": error_sentences
            })
            error_docs[file_name] = {
                "errors": list(misspelled),
                "error_sentences": error_sentences
            }

count = 0
for r in results:
    print(f"File: {r['file']}")
    print(f"Spell error: {', '.join(r['errors'])}")
    print("-" * 40)
    count += 1
with open("spell_errors_summary.json", "w", encoding="utf-8") as f:
    json.dump(error_docs, f, indent=4, ensure_ascii=False)

print(count)
