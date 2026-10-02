# Cult Mechanicus Liturgical Calendar - October

## October 1 - Feast of the First Convergence

**Purpose** - Synchronising the repository and removing stale branches.

**Context** - On this day the tech-priests make every copy agree. Fetch, pull and push to synchronise the local repository with the remote. Remove stale branches and files that can be rebuilt.

## October 2 - Rite of the Motive Force

**Purpose** - Reading the power draw of each GPU.

**Context** - Today the enginseers watch the power of their machines. nvidia-smi reports the power draw of each card in watts beside its limit. A card whose draw stays low during training is idle part of the time.

## October 3 - Commemoration of Saint Land the Finder

**Purpose** - Searching for existing code and models before writing new ones.

**Context** - The Finder taught that what is needed already exists. Before writing a new function or training a new model, search the standard library, the project and the published pretrained models. The tech-priests search first, because most of what they need already exists.

## October 4 - The Day of the Sixteen Laws

**Purpose** - Remembering what a language model is: a predictor of the next token.

**Context** - Today the tech-priests recite the sixteen laws of the cult, and sixteen is 2 to the power 4. One law forbids thinking machines. So the tech-priests remind everyone that a language model only predicts the next token from the statistics of its training text.

## October 5 - Ascent of the Binaric Living Conduit

**Purpose** - Upgrading one dependency at a time.

**Context** - The enginseers honour upgrades today. Upgrade one dependency at a time, inside the virtual environment of the project, and run the tests after each. An upgrade of everything at once hides which change broke the code.

## October 6 - Rite of the Called Tool

**Purpose** - Knowing that a model only writes the tool call.

**Context** - When a language model calls a tool, it only writes a request: a tool name and arguments. Your code performs the call. Validate the arguments first, and let the model call a calculator for arithmetic. The Magos trusts no unchecked request.

## October 7 - Vigil of the Collider

**Purpose** - Avoiding false links created by selecting cases.

**Context** - Selecting cases by a common effect creates a false link between its causes. Suppose machines are sent for repair when they are either hot or loud. Then among the repaired machines heat and noise appear negatively related, though unrelated in the whole forge.

## October 8 - Observance of the Shuffled Column

**Purpose** - Measuring feature importance by shuffling a feature.

**Context** - Permutation importance: shuffle the values of one feature in the validation data and measure how far the score falls. When one of two correlated features is shuffled, the other still gives the model similar information, so each can look unimportant. Acolytes shuffle one column at a time.

## October 9 - Commemoration of Saint Permuta the Shuffler

**Purpose** - Remembering the saint who tested a difference by shuffling labels.

**Context** - Permuta shuffled the group labels a few thousand times and recomputed the difference between the two groups each time. The share of shuffles with a difference at least as large as the observed one is the p-value. The test assumes no particular distribution. The tech-priests use it in her memory.

## October 10 - Feast of the Binary Ten

**Purpose** - Reading 1010 as the binary number ten.

**Context** - On the tenth of October the date reads 1010. Read as binary, that is ten: one eight plus one two. The cogitator counts with two digits only, 0 and 1. The tech-priests call this the binary chant.

## October 11 - Rite of the Nested Fold

**Purpose** - Estimating performance with nested cross-validation.

**Context** - Tuning hyperparameters and estimating performance on the same folds gives a score that is too high. Nested cross-validation tunes in an inner loop and estimates in an outer loop the tuning never saw. The Magos rejects the inflated score.

## October 12 - Observance of the Rare Event

**Purpose** - Expecting fault-free months by chance alone.

**Context** - Counts of rare independent events in a fixed interval follow the Poisson distribution, whose variance equals its mean. A servitor that faults twice a month on average will pass about one month in seven with no fault at all, by chance alone.

## October 13 - Vigil of the Judging Model

**Purpose** - Checking a judge model against human grades.

**Context** - Using one language model to grade the answers of another scales well. But the judge has biases of its own, such as a liking for longer answers. Compare the judge with human grades on a sample before you trust it. The Magos trusts no judge unchecked.

## October 14 - Feast of the Maximum Likelihood

**Purpose** - Choosing parameters by maximum likelihood.

**Context** - Maximum likelihood chooses the parameters under which the observed data would have been most probable. Least squares is the same method under normally distributed errors. The tech-priests keep a feast for this link.

## October 15 - Rite of the Adversarial Validation

**Purpose** - Checking whether the test data differs from the training data.

**Context** - The enginseers train a classifier to tell the test data from the training data. An area under the ROC curve near 0.5 means the two look alike. A high value means a shift, and the most important features of that classifier show where.

## October 16 - Commemoration of Saint Contrasta the Pairwise

**Purpose** - Training embeddings with matching and non-matching pairs.

**Context** - Contrasta trained an encoder to draw the embeddings of matching pairs together and to push non-matching pairs apart. The model learned most from the hard negatives, the non-matches that look alike. The adepts honour her by training with hard negatives.

## October 17 - Observance of the Three Anomalies

**Purpose** - Telling point, contextual and collective anomalies apart.

**Context** - A point anomaly is odd by itself. A contextual anomaly is odd only in its context: 30 degrees is normal in summer and not in winter. A collective anomaly is a run of values that are odd only together. Every acolyte learns the three kinds.

## October 18 - Vigil of the Memorised Record

**Purpose** - Removing secrets and personal data before fine-tuning.

**Context** - Large models can reproduce rare training records word for word. Remove secrets and personal data before fine-tuning. Whatever the model was trained on, it may one day recite. The Magos calls leaked data tech-heresy.

## October 19 - Feast of the Hidden Frequencies

**Purpose** - Finding hidden cycles with the Fourier transform.

**Context** - The Fourier transform describes a signal as a sum of sine waves. A cycle hidden in the raw readings, such as the hum of a worn bearing, stands out as a peak in the spectrum. The servo-skulls report the peak.

## October 20 - Rite of the Twofold Sampling

**Purpose** - Sampling a signal fast enough to avoid aliasing.

**Context** - A signal must be sampled at more than twice its highest frequency. Sampled more slowly, the high frequencies appear as false low ones, which is called aliasing. Filter out the high frequencies before reducing the sampling rate. The cogitator cannot tell false from true.

## October 21 - Vigil of the Dragged Component

**Purpose** - Inspecting the outliers before running PCA.

**Context** - PCA looks for the direction of greatest variance, and a few extreme points carry a great deal of variance. They can turn the first component toward themselves. Inspect the outliers before the PCA, not after. The Magos asks to see them first.

## October 22 - Commemoration of Saint Colda the Newcomer

**Purpose** - Remembering the saint who served users with no history.

**Context** - A recommender has no history to use for a new user or a new item, because no interactions exist yet (the cold-start problem). Colda fell back on popularity and on the features of the item until enough interactions arrived. The tech-priests plan for the newcomer.

## October 23 - Feast of the Random Surfer

**Purpose** - Understanding PageRank as a random surfer.

**Context** - PageRank scores a page by the share of time a random surfer spends on it. The surfer follows a random link and sometimes jumps to a random page. The scores are the dominant eigenvector of the transition matrix and are computed by power iteration. The tech-priests picture the surfer as a servo-skull.

## October 24 - Feast of the Kibibyte

**Purpose** - Telling kibibytes, gibibytes and gigabytes apart.

**Context** - The date written 1024 is 2 to the power 10: the bytes in one kibibyte. A gigabyte is 10 to the power 9 bytes and a gibibyte 2 to the power 30, about 7 percent more. nvidia-smi reports MiB, and the 503 GiB of RAM in BEHEMOTH are about 540 GB. The cogitator counts in powers of two.

## October 25 - Rite of the Summed Logarithm

**Purpose** - Adding logarithms instead of multiplying probabilities.

**Context** - The product of many small probabilities underflows to zero in floating point. Add their logarithms instead, and use log-sum-exp where probabilities must be summed. The enginseers never multiply a long chain of probabilities.

## October 26 - Rite of the Separated Convolution

**Purpose** - Counting what a depthwise separable convolution saves.

**Context** - A depthwise separable convolution splits a convolution in two: one spatial filter per channel, then a 1 by 1 convolution that mixes the channels. It needs far fewer parameters and operations than a full convolution. The enginseers build networks for mobile devices on it.

## October 27 - Vigil of the Repeated Guess

**Purpose** - Estimating uncertainty with Monte Carlo dropout.

**Context** - In Monte Carlo dropout, dropout stays switched on at inference on purpose, and the same input is predicted many times. The spread of the predictions is a rough estimate of the model's uncertainty. The machine spirit answers differently each time, and the adepts read the spread.

## October 28 - Feast of the Two Encoders

**Purpose** - Choosing between a two-tower model and a cross-encoder.

**Context** - A two-tower model encodes query and item separately, so item vectors can be computed in advance and searched fast. A cross-encoder reads both together: more accurate, far slower. The tech-priests retrieve with the first and re-sort the best few with the second.

## October 29 - Observance of the Receptive Field

**Purpose** - Understanding what one convolutional unit can see.

**Context** - Each unit of a convolutional network sees only a patch of the input, called its receptive field, and the patch grows with depth. No unit sees the whole of an object larger than its receptive field. The adepts compare the receptive field with the size of the objects in their data.

## October 30 - Commemoration of Saint Distanta the Scaled

**Purpose** - Remembering the saint who measured distance in units of spread.

**Context** - Distanta used the Mahalanobis distance: how far a point lies from the centre of the data in units of the data's own spread, with correlations taken into account. She found points that were ordinary in every single feature and odd in their combination. The adepts measure as she did.

## October 31 - Feast of the Two Adversaries

**Purpose** - Knowing that GAN training is unstable.

**Context** - A generative adversarial network trains two networks against each other: a generator that makes fake samples and a discriminator that distinguishes fake from real. Training is unstable, and the generator may collapse to a few outputs. The adepts watch both networks.

