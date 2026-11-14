"""Exchange of 12 October 2026: the sermons that gave the reader no practice to apply and no fact they are likely to
lack get a new Purpose, a new Context, a new plan fact and a new badge line. The titles stay.

    python3 src/calendar/exchange.py          # checks the new texts against the brief, changes nothing
    python3 src/calendar/exchange.py apply    # writes calendar/, references/calendar-plan.md and badges.md
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
CULT = re.compile(
    r"tech-priest|priest|magos|enginseer|adept|acolyte|servitor|servo-skull|cogitator|machine spirit|omnissiah"
    r"|machine god|\bforges?\b|litan|\brites?\b|ritual|incense|purity seal|sacred|holy|bless|heres|scrap-code"
    r"|binary chant|chant|\bsaint|\bcult\b|\bsins?\b|motive force|sixteen laws", re.I)

# day: (purpose, context, fact of the plan, what the badge shows)
NEW = {
    "01-10": (
        "Computing dot products in one call, not in a Python loop.",
        "A linear layer computes one dot product for each output: the input with one row of weights. Do not compute it in a Python loop over the components. One matrix product computes all outputs in compiled code and is many times faster. The enginseers remove every such loop from the forge.",
        "Each output of a linear layer is one dot product of the input with a row of weights, plus a bias. One matrix product computes all outputs in compiled code and is many times faster than a Python loop over the components",
        "one long straight gold arrow that passes through a coil of dark iron wire, and a small cog wheel at the tip of the arrow"),
    "02-07": (
        "Checking the first loss of a classifier against the logarithm of the class count.",
        "Second month, seventh day: 2.7, the first digits of e, the base of the logarithm in cross-entropy. An untrained classifier spreads its probability almost evenly, so its first loss is near the logarithm of the class count: 2.3 for ten classes. The acolytes check this in every run.",
        "Second month, seventh day: 2.7, the opening digits of e, the base of the logarithm in the cross-entropy loss. A classifier that spreads its probability evenly over n classes has a loss of ln n, about 2.3 for ten classes. A first loss far from that value points to a fault in the initialisation or in the labels",
        "a brass gauge with its needle on a gold mark, and below it a row of small candles of exactly equal height"),
    "02-23": (
        "Calling the symmetric solver for the eigenvectors of a covariance matrix.",
        "An eigenvector is a vector that a matrix only stretches and does not turn. A covariance matrix is symmetric, so call eigh in NumPy, not eig. It is faster and returns real eigenvalues sorted from smallest to largest. The general eig sorts nothing. The enginseers call eigh for every symmetric matrix.",
        "An eigenvector of a matrix is a vector that the matrix only stretches and does not turn. For a symmetric matrix, such as a covariance matrix, eigh in NumPy is faster than eig and returns real eigenvalues in ascending order; eig returns them in no particular order",
        "a round mirror in a gold frame with a gold arrow that crosses it and continues straight on the other side, and a row of three beads below it, small, medium and large"),
    "03-03": (
        "Letting a convolutional network accept images of other sizes.",
        "A convolution slides one small set of weights across the image, so one layer works on images of different sizes. A flatten layer before the classifier fixes the input size. Put global average pooling in its place, and the network accepts other sizes. The enginseers call the sliding kernel thrift.",
        "A convolution slides one small set of weights across the whole image, so the layer works on images of different sizes. A flatten layer before the classifier fixes the input size; global average pooling in its place lets the network accept other sizes",
        "a large brass funnel that gathers a wide grid of small squares into one gold drop"),
    "03-14": (
        "Passing angles in radians to the sine and the cosine.",
        "In month-day order, March 14 is 3.14, the first digits of pi: half a turn in radians. The sine and cosine of NumPy and PyTorch expect radians. Pass 90 for a right angle and the sine is 0.89, not 1, with no error. The adepts convert degrees with deg2rad first.",
        "Third month, fourteenth day: 3.14, the first digits of pi, half a turn in radians. The trigonometric functions of NumPy and PyTorch expect radians: the sine of 90 is 0.89, not 1, and no error is raised. deg2rad converts degrees",
        "a brass protractor in the shape of a half circle with a gold pointer that stands upright at a right angle, and a small cog wheel at its centre"),
    "03-16": (
        "Checking that no activation is missing between two layers.",
        "A multilayer perceptron passes each weighted sum through a non-linear function. Without that function, two layers collapse into a single linear map. A forgotten activation raises no error: the network trains and remains a linear model. The enginseers read the forward pass line by line to find it.",
        "A multilayer perceptron passes each weighted sum through a non-linear function. Without it two layers collapse into a single linear map. A forgotten activation raises no error; the network trains and remains a linear model",
        "two iron plates joined by a bent gold bar, and beside them two iron plates with an empty gap between them, a mechanical finger that points at the gap"),
    "04-09": (
        "Placing the layer normalisation before each part of a block.",
        "The adepts build a transformer as a stack of identical blocks: self-attention, then a small feed-forward network, each inside a residual connection. Place the layer normalisation before each of the two, not after. Deep stacks then usually train more stably and depend less on warm-up.",
        "A transformer block holds a self-attention layer and a small feed-forward network, each inside a residual connection. With the layer normalisation placed before each of the two (pre-norm), deep stacks usually train more stably and depend less on warm-up than with the normalisation placed after (post-norm)",
        "a tower of two stacked machine blocks, a small gold balance scale in front of the door of each block, and a cable that runs past both blocks"),
    "04-13": (
        "Reading the out-of-bag score of a random forest.",
        "A random forest grows each tree on a bootstrap sample, which leaves out about 37 percent of the rows. Score every row with the trees that never saw it. This out-of-bag score estimates the error on new data without a separate validation set. The Magos reads it first.",
        "A random forest grows each tree on a bootstrap sample, which leaves out about 37 percent of the rows. Scoring every row with the trees that never saw it gives the out-of-bag score, an estimate of the error on new data without a separate validation set",
        "a grove of small bare trees of gold wire, and on the ground beside them an open cloth sack with a few bone white beads that lie outside it"),
    "05-01": (
        "Checking a hand-written gradient against a numerical one.",
        "Backpropagation is the chain rule applied from the loss back to the first layer. The framework applies it for you. If you write a gradient by hand, compare it with a numerical gradient: gradcheck in PyTorch does this in double precision. The tech-priests trust no unchecked derivative.",
        "Backpropagation is the chain rule of calculus applied from the loss back to the first layer. A gradient written by hand for a custom function is checked against a numerical gradient; gradcheck in PyTorch does this in double precision",
        "a chain of large iron links with one small gold arrow that points backwards along it, and a pair of calipers that measures one of the links"),
    "05-29": (
        "Undoing a rotation with the transpose, not with an inverse.",
        "An orthogonal matrix turns or mirrors vectors and keeps their lengths and angles. Its inverse is its transpose. So undo a rotation by transposing the matrix: no inverse is computed and no precision is lost. The tech-priests call such a turn pure.",
        "An orthogonal matrix turns or mirrors vectors without changing their lengths or the angles between them. Its inverse is its transpose, so a rotation is undone by transposing the matrix, without computing an inverse",
        "a gold square frame that stands on one of its corners like a diamond, a curved gold arrow that circles around it, and a small cog wheel at its centre"),
    "06-06": (
        "Passing a seeded generator instead of setting a global seed.",
        "The cogitator's random numbers are a fixed sequence chosen by the seed. np.random.seed sets one hidden generator shared by every call in the program, so one added call shifts all numbers after it. Create a generator with default_rng and a seed, and pass it to each function that needs chance.",
        "The random numbers of a computer are a deterministic sequence chosen by the seed. np.random.seed sets one global generator shared by every call in the program, so one added call shifts all numbers after it. A generator created with default_rng and a seed, and passed to each function that needs it, keeps the sequences apart",
        "a mechanical hand that passes a small open iron box with a pair of dice inside it to a second mechanical hand"),
    "07-02": (
        "Lowering the learning rate when you raise the momentum.",
        "Momentum adds a share of the previous step to each new step. In the usual form of SGD, along a steady gradient, a momentum of 0.9 multiplies the long-run step by ten, and 0.99 by a hundred. So lower the learning rate when you raise the momentum. The enginseers tune the two together.",
        "Momentum adds a share of the previous step to each new step. In the usual form of SGD with momentum, along a steady gradient, a momentum of 0.9 multiplies the long-run step by ten and 0.99 by a hundred, so the learning rate is lowered when the momentum is raised",
        "a heavy iron ball that rolls down a slope with speed lines behind it, and a mechanical hand that pulls a brake lever beside the slope"),
    "07-06": (
        "Checking the longest input that a model's positions allow.",
        "Attention alone cannot tell the first word from the last, so each token receives a position. A learned table of positions has a fixed length: 512 in BERT. A tokeniser with truncation switched on cuts off longer text with no warning. The adepts decide which part to cut, or they split the text.",
        "Attention alone cannot distinguish the first word from the last, so each token is given a position. A model with a learned table of positions has a fixed number of them, 512 in BERT; a tokeniser with truncation switched on cuts off longer text with no warning",
        "a long parchment ribbon laid along a brass measuring rod, and iron shears that cut the ribbon at the end of the rod"),
    "07-07": (
        "Making the image size a multiple of the total pooling factor.",
        "Max pooling keeps the largest value in each window. A 2 by 2 window with stride 2 halves each side, so five such stages divide it by 32. Pad or crop the image to a multiple of 32. Otherwise the skip connections of a U-shaped network can meet maps of different sizes. The enginseers pad first.",
        "Max pooling keeps the largest value in each small window. A 2 by 2 window with stride 2 halves the height and the width, so five such stages divide each side by 32. With a side that is not a multiple of 32, the skip connections of a U-shaped network can meet feature maps of different sizes",
        "a staircase of four gold squares, each half the size of the one before it, and around the largest square an added border of plain dark cloth"),
    "07-11": (
        "Remembering that more heads make each head narrower.",
        "Multi-head attention splits the width of the model among its heads: 768 dimensions and 12 heads give 64 per head. The width must be divisible by the number of heads. More heads add no parameters and leave each head fewer dimensions. The enginseers keep enough dimensions in every head.",
        "Multi-head attention splits the width of the model among its heads: 768 dimensions and 12 heads give 64 per head, and the width must be divisible by the number of heads. More heads add no parameters and leave each head fewer dimensions",
        "one hooded figure in a crimson cowl with several small skulls around its head, and below them a row of short plain gold rods of equal length"),
    "07-28": (
        "Remembering the saint who tried word weights before a deep model.",
        "Rara weighted each word by how often it occurs in a document and by how rare it is across all documents (TF-IDF). She trained a linear classifier on these weights before any transformer, and it was often hard to beat. In her memory the tech-priests fit this baseline first for every text task.",
        "TF-IDF weights a word by how often it occurs in a document and by how rare it is across all documents. A linear classifier on these weights is often a strong baseline for text classification and is fitted before any transformer",
        "a skull-faced saint in a crimson cowl who weighs one gold bead against a heap of grey beads on a small balance scale"),
    "09-05": (
        "Remembering the saint who tuned the penalty C of a support vector machine.",
        "Marginia drew the boundary with the widest margin between the classes, as a support vector machine does. For overlapping classes she tuned the penalty C: a small C keeps the margin wide and tolerates points inside it, a large C narrows it. She searched C on a logarithmic scale, as the adepts do.",
        "A support vector machine draws the boundary with the widest margin between the classes. Where the classes overlap, the penalty C decides: a small C keeps the margin wide and tolerates points inside it, a large C narrows it. C is searched on a logarithmic scale",
        "a skull-faced saint in a crimson cowl who turns a brass dial, on a road between a group of red dots and a group of white dots, with one red dot on the road"),
    "09-06": (
        "Reading a rising validation loss beside a rising accuracy.",
        "Cross-entropy is the negative logarithm of the probability given to the correct class. A confident wrong answer costs far more than a hesitant one. So the validation loss can rise while the accuracy improves: the model grows overconfident. The tech-priests plot both and check the calibration.",
        "Cross-entropy loss is the negative logarithm of the probability the model gave to the correct class, so a confident wrong answer costs far more than a hesitant one. The validation loss can therefore rise while the accuracy still improves, when the model grows overconfident",
        "a crowned skull on a tall narrow pedestal between two gold arrows that rise side by side, one on each side of the pedestal"),
    "09-10": (
        "Comparing an autoencoder with PCA of the same size.",
        "An autoencoder squeezes its input through a narrow middle layer and rebuilds it on the other side. With linear layers only, it finds the same subspace as PCA. So compare its reconstruction error with that of PCA with the same number of components. If it is no better, the Magos keeps the PCA.",
        "An autoencoder squeezes its input through a narrow middle layer and rebuilds it. With linear layers only and a squared error it finds the same subspace as PCA, so its reconstruction error is compared with that of PCA with the same number of components",
        "a small balance scale with an hourglass on one pan and a straight gold rod on the other pan"),
    "09-13": (
        "Converting 8-bit images to a wider type before arithmetic.",
        "Day 256 of a common year is September 13, and 256 is the number of values one byte can hold, 0 to 255. A pixel stored as uint8 is one byte. Add two such images in NumPy and a sum above 255 wraps around: 200 plus 100 gives 44, with no error. The enginseers convert to a wider type first.",
        "Day 256 of a common year is September 13; 256 is 2 to the power 8, the number of values one byte can hold, 0 to 255. Arithmetic on uint8 arrays in NumPy wraps around above 255 without an error: 200 plus 100 gives 44. Images are converted to a wider type first",
        "a brass cup filled to its rim with molten gold that spills over the edge, inside a frame of cog teeth"),
    "09-15": (
        "Continuing masked training on your own unlabelled text.",
        "In masked language modelling some tokens are hidden, and the model predicts them from the words on both sides. The text supplies its own labels. So continue this training on unlabelled text of your own domain before you fine-tune. It often improves the result. The servitors do the hiding.",
        "In masked language modelling some tokens of a text are hidden and the model predicts them from the words on both sides, so the text supplies its own labels. Continuing this training on unlabelled text of the target domain before fine-tuning often improves the result",
        "a black mask with two eye holes that lies on a pile of stacked parchment sheets, and a quill that lies beside the pile"),
    "09-18": (
        "Counting what each denoising step of a diffusion model costs.",
        "A diffusion model starts from pure noise and removes a little of it at every step. Each step is at least one full pass of the network, so fifty steps cost at least fifty passes. Halve the number of steps and compare the images. Often little is lost, and the servitors finish in half the time.",
        "A diffusion model generates by starting from pure noise and removing noise step by step. Each step is at least one full pass of the network, so the time grows with the number of steps; halving the steps often loses little quality",
        "a row of three panels in which a cloud of random specks becomes a clear skull, and a large hourglass that stands beside the row"),
    "10-10": (
        "Reading long identifiers as text, not as numbers.",
        "On the tenth of October the date reads 1010, the binary number ten. A 64-bit float keeps 53 binary digits, so a whole number above 2 to the power 53 may lose its last digits with no error. pandas reads an integer column with one missing value as floats. The adepts read identifiers as text.",
        "The date written 1010 and read as binary is ten. A 64-bit float keeps 53 binary digits, so a whole number above 2 to the power 53, about 9 times 10 to the power 15, may lose its last digits with no error. pandas reads an integer column with a missing value as floats; identifiers are read as text",
        "a long iron chain whose last links are broken off and lie apart from it, and beside the chain a quill and a parchment tag on a cord"),
    "11-03": (
        "Resizing the embedding table after adding tokens.",
        "An embedding layer is a lookup table with one learned vector per token identifier. Add a token to the tokeniser, and its identifier points beyond the last row. On a GPU the run then stops with a device-side assert that does not name the cause. The enginseers resize the table first.",
        "An embedding layer is a lookup table with one learned vector per token identifier. A token added to the tokeniser has an identifier beyond the last row; on a GPU the lookup then stops with a device-side assert. The table is resized to the new vocabulary first",
        "a cabinet of many small dark drawers, and a mechanical hand that pushes one new gold drawer into its side"),
    "11-10": (
        "Computing the logarithm of a determinant without underflow.",
        "The determinant is the factor by which a square matrix scales volume. For a large matrix it leaves the range of floating point: a thousand diagonal entries of 0.1 give a determinant stored as zero. If you need its logarithm, call slogdet in NumPy. The tech-priests never take the logarithm of det.",
        "The determinant of a square matrix is the factor by which the matrix scales volume. For a large matrix it overflows or underflows in floating point: a diagonal matrix of a thousand entries of 0.1 has the determinant 10 to the power minus 1000, stored as zero. slogdet in NumPy returns the logarithm directly",
        "a slanted four-sided gold frame that shrinks in three steps to a tiny gold dot, and a magnifying lens held over the dot"),
    "11-11": (
        "Recording the hash of the data file with every run.",
        "The date written 1111 and read as binary is fifteen, F in hexadecimal: one digit for four bits. A SHA-256 hash is 64 such digits. Compute it for your data file with sha256sum and record it with every run. Two runs with the same hash used the same data. The cogitator recites them as a binary chant.",
        "The date written 1111 and read as binary is fifteen, F in hexadecimal: one hexadecimal digit writes four bits. A SHA-256 hash is 64 hexadecimal digits, 256 bits. The hash of the data file, computed with sha256sum and recorded with every run, shows whether two runs used the same data",
        "a closed iron chest with a red wax seal on its lid, and beside it a second identical red wax seal that hangs on a short crimson ribbon"),
    "11-13": (
        "Smoothing the counts of a Markov chain.",
        "In a Markov chain the next state depends on the present state alone. Its probabilities are estimated from counts, so a transition never observed gets probability zero. One zero makes every sequence that contains it impossible. Add a small count to every transition, as the tech-priests do.",
        "In a Markov chain the next state depends on the present state alone; an n-gram language model is one. Probabilities estimated from counts are zero for a transition never observed, and one zero makes every sequence that contains it impossible. Smoothing adds a small count to every transition",
        "a chain of iron links with one gap where a link is missing, and a mechanical hand that sets a small gold link into the gap"),
    "12-27": (
        "Starting an LSTM with its forget gate open.",
        "An LSTM carries a cell state through the sequence, and a forget gate decides how much of it survives each step. Set the bias of that gate to 1 at the start. The cell then keeps its memory until it learns what to forget. Keras does this by default; PyTorch does not, so the enginseers set it by hand.",
        "The long short-term memory network carries a cell state through the sequence, and a forget gate decides how much of it survives each step. A forget-gate bias of 1 at the start lets the cell keep its memory until it learns what to forget. Keras sets it by default; PyTorch does not",
        "a conveyor of small chests that passes through one iron gate that stands wide open, and a gold weight on a chain that holds the gate up"),
}


def check():
    """The faults of the new texts against the brief: lengths, sentences, characters, a cult word."""
    faults = []
    for day, (purpose, context, fact, shows) in NEW.items():
        text = purpose + context + fact + shows
        if not text.isascii() or '"' in text or "--" in text or "|" in text:
            faults.append(f"{day}: character outside the allowed set")
        if not 25 <= len(purpose) <= 90:
            faults.append(f"{day}: Purpose of {len(purpose)} characters")
        if not 150 <= len(context) <= 300:
            faults.append(f"{day}: Context of {len(context)} characters")
        longest = max(len(x.split()) for x in re.split(r"(?<=[.:;]) ", context))
        if longest > 25:
            faults.append(f"{day}: a sentence of {longest} words")
        if not CULT.search(purpose + " " + context):
            faults.append(f"{day}: no cult word")
        if fact.endswith(".") or shows.endswith("."):
            faults.append(f"{day}: plan fact or badge line ends with a full stop")
        print(f"{day}  Purpose {len(purpose):2d}  Context {len(context):3d}  longest sentence {longest:2d} words")
    return faults


def apply():
    plan = (ROOT / "references/calendar-plan.md").read_text()
    badges = (ROOT / "badges.md").read_text()
    for day, (purpose, context, fact, shows) in NEW.items():
        m, d = int(day[:2]), int(day[3:])
        path = ROOT / f"calendar/{m:02d}-{MONTHS[m - 1].lower()}.md"
        text = path.read_text()
        entry = re.compile(rf"(^## {MONTHS[m - 1]} {d} - (.+)\n\n)\*\*Purpose\*\* - .+\n\n\*\*Context\*\* - .+$", re.M)
        hit = entry.search(text)
        title = hit[2]
        text, n = entry.subn(lambda h: f"{h[1]}**Purpose** - {purpose}\n\n**Context** - {context}", text)
        assert n == 1, day
        path.write_text(text)
        # the plan: the row of this day under the heading of its month
        start = plan.index(f"## {MONTHS[m - 1]}\n")
        end = plan.find("\n## ", start + 1)
        end = len(plan) if end < 0 else end
        row = re.compile(rf"^\| {d} \| {re.escape(title)} \| .+ \|$", re.M)
        part, n = row.subn(lambda h: f"| {d} | {title} | {fact} |", plan[start:end])
        assert n == 1, f"{day}: no plan row with the title {title}"
        plan = plan[:start] + part + plan[end:]
        badges, n = re.subn(rf"^- \*\*{day}\*\* - .+$", lambda h: f"- **{day}** - {shows}", badges, flags=re.M)
        assert n == 1, day
    (ROOT / "references/calendar-plan.md").write_text(plan)
    (ROOT / "badges.md").write_text(badges)
    print(f"wrote {len(NEW)} entries to calendar/, references/calendar-plan.md and badges.md")


if __name__ == "__main__":
    found = check()
    for x in found:
        print("FAULT", x)
    print(len(NEW), "days,", len(found), "faults")
    if not found and sys.argv[1:] == ["apply"]:
        apply()
