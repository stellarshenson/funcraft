"""Applies the rewrites of the review for internal logic to calendar/*.md and writes wip/calendar-logic/changes.md.

    python3 src/calendar-logic/apply.py            # report only: the length and the longest sentence of every rewrite
    python3 src/calendar-logic/apply.py --write    # also changes the month files

An entry is found by its heading. Run `python3 src/liturgy.py` afterwards.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
# id: (the gap in the logic of the entry, the new Context)
REWRITES = {
    "01-01": ("The entry does not say why counting from zero leads to a clean setup.",
              "Cogitators count time from the first second of 1 January 1970, and every training run counts from epoch zero. "
              "Today the year starts its own count at zero. The tech-priests start it as they start a run: a clean "
              "environment, a fresh seed, and the seed written down."),
    "03-14": ("The entry never says that the method estimates pi.",
              "In month-day order, March 14 is 3.14, the first digits of pi. To estimate pi, scatter random points in a "
              "square, count the share inside the inscribed circle and multiply it by four. This Monte Carlo method "
              "converges slowly. Any adept can run it on a cogitator."),
    "05-05": ("'so five folds': a date does not cause a method.",
              "On the fifth day of the fifth month the adepts honour cross-validation with five folds. Train five times, "
              "each time holding out a different fifth of the data. Report the mean and the spread of the five scores, "
              "not only the best one."),
    "07-23": ("The sentence on the logarithmic scale has no link to the edge of the range.",
              "When the best hyperparameter value of a search lies on the edge of the range, the true best may lie "
              "outside. Widen the range and search again. Widen learning rates and regularisation strengths by factors "
              "of ten, because they are searched on a logarithmic scale. The acolytes watch the edges."),
    "08-05": ("The saint searched at random, but in her memory the tech-priests do another thing.",
              "Saint Hypera sampled her hyperparameters at random instead of on a grid, and so tried many more distinct "
              "values of the few that mattered. She sampled the learning rate on a logarithmic scale, so every order of "
              "magnitude was tried equally often. In her memory the tech-priests search as she did."),
    "10-04": ("'sixteen is 2 to the power 4' is used by nothing, and the step from the law to the language model is not stated.",
              "Today the tech-priests recite the sixteen laws of the cult. One law forbids thinking machines. The cult "
              "does not count a language model as one, because it only predicts the next token from the statistics of "
              "its training text. The tech-priests remind every adept of this today."),
    "10-06": ("The calculator is named without a reason and without a link to the request.",
              "When a language model calls a tool, it only writes a request: a tool name and arguments. Your code performs "
              "the call, so validate the arguments in your code first. The Magos trusts no unchecked request. For "
              "arithmetic, give the model a calculator: it computes, and the model only predicts."),
    "10-08": ("The last sentence does not answer the problem of the correlated features.",
              "Permutation importance: shuffle the values of one feature in the validation data and measure how far the "
              "score falls. When one of two correlated features is shuffled, the other still gives the model similar "
              "information, so each can look unimportant. Acolytes judge no feature by this score alone."),
    "10-12": ("'whose variance equals its mean' is not used by the example.",
              "Counts of rare independent events in a fixed interval follow the Poisson distribution. Its variance equals "
              "its mean, so counts with a small mean scatter widely around it. A servitor that faults twice a month on "
              "average will pass about one month in seven with no fault at all, by chance alone."),
    "11-11": ("The step from four bits to one byte is not stated.",
              "The date written 1111 and read as binary is fifteen, F in hexadecimal. One hexadecimal digit writes four "
              "bits, and here all four are set to 1. A byte has eight bits, so two hexadecimal digits write one byte. "
              "The cogitator celebrates this feast with a binary chant."),
    "11-23": ("The step from the sequence to the recursion and its repeated work is not stated.",
              "The date 11-23 gives 1, 1, 2, 3: each term is the sum of the two before it. A function that calls itself "
              "for both earlier terms computes the same terms many times, so its work grows exponentially. Let the "
              "cogitator store each term once it is computed (memoisation), and the work grows linearly."),
}

texts = {m: (ROOT / f"calendar/{m:02d}-{name}.md").read_text() for m, name in enumerate(MONTHS, 1)}
lines, bad = ["# Calendar review for internal logic - rewrites", ""], 0
for key, (gap, new) in REWRITES.items():
    month, day = int(key[:2]), int(key[3:])
    hit = re.search(rf"^## {MONTHS[month - 1].capitalize()} {day} - (.+)\n\n\*\*Purpose\*\* - (.+)\n\n\*\*Context\*\* - (.+)$", texts[month], flags=re.M)
    title, old = hit[1], hit[3]
    longest = max(len(x.split()) for x in re.split(r"(?<=[.:;]) ", new))
    ok = 150 <= len(new) <= 300 and longest <= 25 and new.isascii() and '"' not in new and new.endswith(".")
    bad += not ok
    print(f"{key} {len(new):3d} characters, longest sentence {longest:2d} words {'' if ok else '  <-- OUTSIDE THE RULES'}{'' if old != new else '  (already applied)'}")
    lines += [f"## {key} - {title}", "", f"Gap: {gap}", "", f"- before: {old}", f"- after: {new}", ""]
    texts[month] = texts[month].replace("**Context** - " + old + "\n", "**Context** - " + new + "\n")
(ROOT / "wip" / "calendar-logic" / "changes.md").write_text("\n".join(lines))
if "--write" in sys.argv and not bad:
    for m, name in enumerate(MONTHS, 1):
        (ROOT / f"calendar/{m:02d}-{name}.md").write_text(texts[m])
    print("wrote the month files")
