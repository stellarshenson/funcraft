# Cult Mechanicus liturgical calendar - writing brief

The calendar gives one entry for each of the 366 days of a leap year. Each entry is a feast, rite, vigil, observance or saint's day of the Cult Mechanicus of Warhammer 40,000, and it teaches one correct point of machine learning, statistics, data science, AI or the use of the workstation. It goes on the welcome page of the BEHEMOTH workstation, where a team of data scientists reads one entry a day. The model is `references/cult_mechanicus_calendar.pdf`: a title, a purpose, a context.

## 1. Reader

- **Who** - data scientists and engineers. English is not their first language. Most of them do not know Warhammer 40,000
- **What they must get** - the technical point, at first reading, without translating anything
- **What makes it fun** - the title, and a light touch of the cult in the text: a tech-priest does it, the Magos demands it, the cult calls the bad practice heresy

## 2. Files

- **Month files** - `calendar/01-january.md` to `calendar/12-december.md`, one per month
- **Day plan** - `references/calendar-plan.md`: the title and the fact of every day, month by month
- **Check** - `python3 src/liturgy.py 09 10` from `w40k-mechanicum/`, with the numbers of the months to check; it must end with `0 faults`
- **Whole year in one file** - `python3 src/liturgy.py` without numbers checks all months and, with 0 faults, writes `out/14-calendar.md`

## 3. Format

A month file starts with the month heading. Each day is a heading, a Purpose line and a Context line, each followed by one blank line. Nothing else goes in the file.

```markdown
# Cult Mechanicus Liturgical Calendar - January

## January 7 - Rite of Device Selection

**Purpose** - Choosing the GPU before the framework starts.

**Context** - Set CUDA_VISIBLE_DEVICES first and import the framework second. A framework started without this instruction takes the first GPU it finds, even if another adept is already working there. The enginseers call this the first courtesy of the forge.

```

- **Heading** - `## <Month> <day> - <title>`, day without a leading zero, the title exactly as given in the plan or the source
- **Purpose** - one plain line that says what the day is about, so that a reader who reads only this line knows the subject. 25 to 90 characters, ends with a full stop. It starts with an -ing word or a plain noun: Choosing, Checking, Remembering, Honouring, Counting, Testing
- **Context** - two to four short sentences, 150 to 300 characters. It states the technical fact plainly and adds one light touch of the cult
- **Characters** - ASCII only. Single straight quotes `'` for quoted words, no double quotes. No em dash, no en dash, no `--`, no `!!`. British spelling
- **Markup** - no code formatting, no bold or italics inside Purpose or Context, no lists. Commands and names are written plain: nvidia-smi, CUDA_VISIBLE_DEVICES, git status

## 4. Language

- **Plain modern English** - short sentences, at most 25 words each, common words, active voice. One fact per sentence. Direct instructions are welcome: "Halve the batch."
- **No old or literary words** - not lest, upon, kin, whereof, thereof, hath, ere, nor "that it may", nor "for" in the sense of "because"
- **Technical things keep their normal names** - GPU or card, memory, kernel, notebook, checkpoint, commit, log, test set, README, model, dataset. Never rename them: no engine, hold, data-slate, relic, reliquary, scroll, ledger, vault. A command is run, not intoned. A kernel is shut down, not laid to rest
- **Cult words, a short list only** - tech-priest, Magos, enginseer, adept, acolyte, servitor, servo-skull, cogitator, machine spirit, Omnissiah, Machine God, the forge, litany, rite, incense, purity seal, sacred, holy, blessing, heresy, tech-heresy, scrap-code, binary chant. No other cult vocabulary: not lexmechanic, logis, transmechanic, datasmith, noosphere, auspex, binharic, canticle, catechism, unguent, augury, omen, penance, congregation
- **One or two cult touches per entry, not more** - who does the thing, or how the cult judges it. The rest of the entry is plain technical English
- **Saints** - a saint's day says in the past tense what the saint did, then what the tech-priests do in her or his memory. The saints are invented; the name is a pun on the practice

Entries at the standard to reach:

```markdown
## January 28 - Vigil of the Full Disk

**Purpose** - Checking the free disk space before a long job.

**Context** - The enginseers run df -h before every long job. A run that dies at hour nine because the disk is full is a preventable loss. So is a disk full of checkpoints that nobody will ever load, which the tech-priests count as hoarding.

## February 3 - Vigil of the Exhausted Memory

**Purpose** - Dealing with 'CUDA out of memory'.

**Context** - 'CUDA out of memory' means the card has no more memory to give, and no litany will change that. Halve the batch, shorten the sequences or switch to mixed precision. Only then ask the Magos for a bigger GPU.

## March 18 - Feast of the Central Limit

**Purpose** - Honouring the theorem behind most error bars.

**Context** - Average enough independent readings of finite variance, and the averages form a bell curve, whatever shape the readings had. The tech-priests hold a feast for this theorem, because most error bars in the forge rest on it.

## May 17 - Observance of the Floating Point

**Purpose** - Remembering that floating-point numbers are not exact.

**Context** - The cogitator cannot store one tenth exactly in binary, so 0.1 plus 0.2 is not equal to 0.3. Compare floats within a tolerance, never with strict equality. The tech-priests count money as integers of its smallest unit.

## January 18 - Saint Pinnia, Martyr of Unpinned Dependencies

**Purpose** - Remembering the adept who asked for the 'latest' version.

**Context** - Pinnia installed the latest version of everything, and one morning nothing ran. In her memory the tech-priests pin every dependency to an exact version and commit the lock file beside the code.

## September 16 - Vigil of the Three Doors

**Purpose** - Testing intuition against a famous puzzle of probability.

**Context** - There are three doors and one prize. An adept picks a door. The Magos, who knows where the prize is, opens an empty door of the other two. Switching wins two times in three. An adept who doubts it should simulate it on the cogitator.

```

Two ways to fail:

- **Too heavy** - "In the choir of features a column chanted in millimetres drowns one chanted in kilometres, and the datasmiths anoint every column to a common scale." The reader must translate it. Write: "A column in millimetres outweighs a column in kilometres. Scale the features before any method that relies on distances or on gradient descent. The machine spirit hears only the loudest column."
- **No cult at all** - an entry with no tech-priest, Magos, machine spirit, heresy or other word of the short list. Every entry has at least one

## 5. Limits

- **Correctness** - every technical statement is true as written. Keep the fact of the plan or the source; do not add numbers, version numbers or claims that are not given there. Where a fact holds "often" or "usually", keep that word
- **People** - no real person. No named Warhammer character: not the Emperor, no primarch, no named magos. The title "Commemoration of Saint Land the Finder" comes from the PDF and stays; its Context speaks of "the Finder" only
- **Excluded** - war, battle, weapons, killing, enemies; real-world religion and its words (amen, gospel, bible, hallelujah, the names of real saints and gods); politics
- **Original text** - no sentence copied from the PDF or from any Games Workshop text
- **Variety** - no two entries in a month open with the same three words; "The tech-priests" opens at most four entries in a month

## 6. Workstation facts

Use these wherever an entry speaks of the machine. Do not invent others.

- **Name** - BEHEMOTH
- **GPUs, by nvidia-smi index** - index 0 RTX PRO 4000 Blackwell 24 GB; index 1 RTX PRO 6000 Blackwell 96 GB; index 2 RTX 5000 Ada 32 GB; 152 GB in all
- **CPU and memory** - 64 threads, 503 GiB of RAM
- **Volumes** - @volumes/shared is read by every user; @volumes/personal is the user's own
- **Practice** - set CUDA_VISIBLE_DEVICES before importing a framework; nvidia-smi shows memory, utilisation, temperature, power and the processes on each card
