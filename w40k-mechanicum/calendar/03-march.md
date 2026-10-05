# Cult Mechanicus Liturgical Calendar - March

## March 1 - Rite of the First Look

**Purpose** - Looking at the raw data before building any model.

**Context** - Read twenty raw rows, the range of each column and the count of nulls before you train anything. Many errors of a project are visible on the first page. The Magos asks every adept for this look first.

## March 2 - Rite of the Expected Improvement

**Purpose** - Choosing the next trial with expected improvement.

**Context** - In Bayesian optimisation an acquisition function chooses the next trial. It weighs settings the surrogate model predicts to be good against settings where that model is uncertain. Expected improvement, a common choice in the forge, is the expected gain of a setting over the best score so far.

## March 3 - Observance of the Sliding Kernel

**Purpose** - Understanding why a convolution shares its weights.

**Context** - A convolution slides one small set of weights across the whole image. A pattern learned in one corner is recognised in every other corner. This sharing keeps the network small. The enginseers honour it as thrift.

## March 4 - Vigil of the Exploding Gradient

**Purpose** - Handling a loss that turns to NaN in a single step.

**Context** - A loss that turns to NaN in one step means a gradient grew far too large. Clip the gradient norm, lower the learning rate and inspect the batch that caused the NaN. No litany will repair a NaN.

## March 5 - Commemoration of Saint Laplacia the Connected

**Purpose** - Remembering the saint who counted the parts of a graph.

**Context** - Saint Laplacia subtracted the adjacency matrix of a graph from the diagonal matrix of node degrees. The result is the graph Laplacian. Its smallest eigenvalue is always zero, and the number of zero eigenvalues equals the number of connected parts of the graph. In her memory the tech-priests count them.

## March 6 - Rite of the Undivided Group

**Purpose** - Keeping all rows of one group on the same side of the split.

**Context** - When one patient, one customer or one machine supplies many rows, keep all those rows on the same side of the split. Split by group. Otherwise the model is tested on subjects it has already seen. The Magos calls that tech-heresy.

## March 7 - Rite of the Centred Cloud

**Purpose** - Centring the data before a principal component analysis.

**Context** - PCA starts by subtracting the mean of each feature. Without centring, the first component points from the origin toward the mean of the data and says nothing about its spread. A PCA class centres the data for you; a plain SVD does not. The Magos calls an uncentred PCA tech-heresy.

## March 8 - Feast of the Holy Residual Connection

**Purpose** - Honouring the residual stream, the working memory of a model.

**Context** - A residual connection adds the output of a block to its input. In a transformer these connections form the residual stream: every block reads from it and adds its result to it. It is the working memory of the model and the gradient's path to the first layers. The cult holds this as one of its holy truths.

## March 9 - Vigil of the Train-Serve Skew

**Purpose** - Using the same feature code in training and in production.

**Context** - A feature computed by one piece of code in training and by another in production differs in small ways. The model then degrades without an error. Use the same code for both. Compare the feature values of the two on the same records. The tech-priests call two versions of one feature tech-heresy.

## March 10 - Observance of the Rank

**Purpose** - Counting independent directions with the rank of a matrix.

**Context** - The rank of a matrix is the number of independent directions in it. A 1,000 by 1,000 matrix of rank 8 can be written as the product of two thin matrices, 1,000 by 8 and 8 by 1,000. That is 16,000 numbers in place of a million. The enginseers call this thrift.

## March 11 - Observance of the Survivors

**Purpose** - Asking about the missing cases before drawing a conclusion.

**Context** - A table may list only the customers who stayed, the machines that still run or the studies that were published. Ask what happened to the absent ones before you conclude anything. The acolytes learn this question early.

## March 12 - Commemoration of Saint Evalia the Mode-Switcher

**Purpose** - Remembering the saint who set evaluation mode before measuring.

**Context** - Saint Evalia always put the model in evaluation mode before she measured it. Active dropout and updating batch statistics quietly distort every validation score. In her memory the tech-priests check the mode first.

## March 13 - Rite of the Adaptive Moment

**Purpose** - Knowing what the Adam optimiser does with each gradient.

**Context** - Adam keeps a running mean of each gradient and of its square, and scales every step by them. It tolerates a poorly chosen learning rate better than plain gradient descent does, but not entirely. The enginseers still tune the rate.

## March 14 - Feast of the Unending Ratio

**Purpose** - Estimating pi with random points.

**Context** - In month-day order, March 14 is 3.14, the first digits of pi. To estimate pi, scatter random points in a square, count the share inside the inscribed circle and multiply it by four. This Monte Carlo method converges slowly. Any adept can run it on a cogitator.

## March 15 - Observance of the Reversed Aggregate

**Purpose** - Remembering that a pooled trend can reverse the trend in each group.

**Context** - Simpson's paradox: a trend that holds in every subgroup can reverse when the groups are pooled. Look at the subgroups before you report the total. Ask which grouping the question is about. The Magos distrusts a total that nobody has split.

## March 16 - Feast of the Multilayer Perceptron

**Purpose** - Understanding why a network needs non-linear functions.

**Context** - A multilayer perceptron is a stack of layers. Each computes weighted sums of its inputs and passes them through a non-linear function. Without that function the whole stack collapses into a single linear map, however many layers it has. The enginseers never leave it out.

## March 17 - Vigil of the Hallucination

**Purpose** - Checking what a language model tells you against a real source.

**Context** - Plausible is not the same as true, and a language model is trained to produce the plausible. Check every citation, number and name it gave you against a source you can open. An unchecked answer is scrap-code.

## March 18 - Feast of the Central Limit

**Purpose** - Honouring the theorem behind most error bars.

**Context** - Average enough independent readings of finite variance, and the averages form a bell curve, whatever shape the readings had. The tech-priests hold a feast for this theorem, because most error bars in the forge rest on it.

## March 19 - Rite of the Borrowed Mean

**Purpose** - Normalising images as the pretrained model expects.

**Context** - A pretrained vision model expects its input normalised with the mean and standard deviation of the data it was trained on, usually those of ImageNet. With other values it still runs, raises no error and is less accurate. The machine spirit stays silent, so the adept must check.

## March 20 - Commemoration of Saint Imputa the Gap-Filler

**Purpose** - Remembering the saint who flagged every filled gap.

**Context** - Saint Imputa filled each gap with the median and added a column that recorded the fill. In her memory the tech-priests impute only when they must, and they keep the flag. A missing value is often a signal in itself.

## March 21 - Rite of the Balanced Trade

**Purpose** - Finding the balance between bias and variance.

**Context** - A rigid model makes the same error every time: bias. A flexible model makes different errors on every sample: variance. Total error is lowest somewhere between these two extremes. Find out whether your model is too rigid or too flexible, because the Magos will ask.

## March 22 - Feast of Random Silence

**Purpose** - Understanding what dropout does in training and in inference.

**Context** - Dropout sets a random share of activations to zero at each training step, so that no single unit becomes indispensable. At inference every unit is active. Training scales up the remaining activations, so the expected totals are the same as at inference. The enginseers call the zeros a blessing.

## March 23 - Rite of the Split Before Augmentation

**Purpose** - Splitting the data before augmenting or oversampling.

**Context** - Split the data first, then augment or oversample the training part only. If augmented copies of one image, or synthetic neighbours of one row, land on both sides of the split, the validation score is inflated. The Magos rejects any score made that way.

## March 24 - Feast of the Small Sample

**Purpose** - Widening intervals when the sample is small.

**Context** - The mean of a small sample with unknown variance follows Student's t distribution, which has heavier tails than the normal distribution. Intervals from few observations are therefore wider. Above about 30 observations the two are almost the same. The tech-priests accept the wider interval.

## March 25 - Rite of the Few Examples

**Purpose** - Showing a language model a few worked examples.

**Context** - Show the model three worked examples of the output you want. It follows their form more faithfully than any description. Vary the examples, or it will copy them too closely. Every acolyte learns this early.

## March 26 - Feast of the Standard Error

**Purpose** - Telling the standard deviation from the standard error.

**Context** - The standard deviation describes the spread of the data. The standard error describes the uncertainty of the mean, and it shrinks as the square root of the sample size grows. Say which one your error bars show. The Omnissiah wants it written.

## March 27 - Commemoration of Saint Robusta the Median-Minded

**Purpose** - Remembering the saint who used the median to find outliers.

**Context** - Saint Robusta saw that a z-score uses the mean and the standard deviation, and that the outliers she looked for inflate both. She used the median and the median absolute deviation instead, which a few extreme values barely move. The tech-priests do the same in her memory.

## March 28 - Observance of the Duplicated Row

**Purpose** - Removing duplicate rows before splitting the data.

**Context** - The same record on both sides of the split inflates every score. Remove duplicates before you divide the data: exact copies first, then near-copies that differ by a space or a capital letter. A dataset with duplicates carries no purity seal.

## March 29 - Vigil of the Shifting Distribution

**Purpose** - Comparing new inputs with the data the model was trained on.

**Context** - Compare this month's inputs with the data the model was trained on. The world that produced the training set changes. When the inputs drift away from the training data, the model degrades without any error message. Let a servitor repeat this check every month.

## March 30 - Rite of the Logit

**Purpose** - Giving each loss function the scores it expects.

**Context** - Logits are raw scores. Probabilities come only after the softmax. Give each loss function the one it expects. The cogitator usually raises no error if you hand it the other. The model simply trains badly.

## March 31 - Feast of the Dense Region

**Purpose** - Clustering by density with DBSCAN.

**Context** - DBSCAN groups the points that lie in dense regions and marks points in sparse regions as noise. It needs no number of clusters in advance and finds clusters of any shape. It needs a radius and a minimum number of neighbours. The adepts set both with care.
