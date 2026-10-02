# Cult Mechanicus Liturgical Calendar - July

## July 1 - Feast of the Evaluation Set

**Purpose** - Keeping the evaluation set the same for every model.

**Context** - An evaluation set defines what 'good' means. Build it from real cases, then keep it unchanged and version it. Do not change it only because the model finds it hard. The Magos judges every model by the same set.

## July 2 - Rite of the Momentum

**Purpose** - Understanding how momentum smooths gradient descent.

**Context** - Momentum keeps a running average of past gradients and moves the weights along that average. The optimiser then passes over small bumps in the loss surface and moves down its narrow valleys. The enginseers call momentum a blessing for gradient descent.

## July 3 - Vigil of the Underfitted Model

**Purpose** - Recognising a model that is too simple.

**Context** - If the training score is poor, more data and more regularisation will not help. The model is too simple or has trained too little. Add capacity or better features, and watch whether the training loss falls. The adepts check the training loss first.

## July 4 - Observance of the Independent Sample

**Purpose** - Checking that observations are independent.

**Context** - Most statistical tests assume independent observations. Ten readings from one sensor within one minute are not ten independent observations. Treating them as ten makes every confidence interval too narrow. The Magos calls that tech-heresy.

## July 5 - Commemoration of Saint Errata the Inspector

**Purpose** - Remembering the saint who read her model's errors.

**Context** - Saint Errata read a hundred wrong answers of her model by eye before she changed any hyperparameter. Half of them shared one cause. That one fix was worth more than a month of tuning. In her memory the tech-priests read the errors first.

## July 6 - Feast of the Positional Encoding

**Purpose** - Understanding why attention needs positional encodings.

**Context** - Attention alone cannot distinguish the first word from the last. Positional encodings give each token its place in the sequence. Without them, a sentence is only a bag of words to the model. The machine spirit needs the order.

## July 7 - Feast of the Pooled Window

**Purpose** - Understanding what max pooling does to a feature map.

**Context** - Max pooling keeps the largest value in each small window of a feature map. A 2 by 2 window with stride 2 halves the height and the width. The output then tolerates small shifts of the input. The machine spirit stays calm when the picture moves a little.

## July 8 - Rite of the Named Index

**Purpose** - Writing tensor operations with einsum.

**Context** - einsum describes a tensor operation by naming its indices. 'ij,jk->ik' is matrix multiplication: the repeated index j is summed over, and the indices after the arrow remain. One line of einsum replaces a chain of transposes and reshapes. The adepts approve.

## July 9 - Vigil of the Stale Benchmark

**Purpose** - Doubting scores on public benchmarks.

**Context** - A public benchmark published before a model's training cut-off may be inside its training data. A high score there may come from memorised answers, not from reasoning. The tech-priests keep a private set that the model can never have read.

## July 10 - Feast of the Nearest Neighbour

**Purpose** - Understanding the nearest-neighbour method.

**Context** - The nearest-neighbour method does no training. It stores the data and predicts by finding the closest examples. It is slow at prediction, and features on different scales mislead it. Its machine spirit is simple but easy to fool.

## July 11 - Feast of the Many Heads

**Purpose** - Understanding multi-head attention.

**Context** - Multi-head attention runs several attention heads side by side. Each head has its own projections of the queries, keys and values and can follow a different relation between tokens. One linear layer joins and mixes their outputs. The enginseers hold a feast for this design.

## July 12 - Saint Quantila of the Ninety-Ninth Percentile

**Purpose** - Remembering the saint who measured the slowest requests.

**Context** - Saint Quantila measured latency by its 99th percentile, because the mean hides the slow requests that users remember. In her memory the tech-priests report the median and the 99th percentile together.

## July 13 - Observance of the Residual Plot

**Purpose** - Reading a plot of the residuals.

**Context** - Plot the residuals against the fitted values. A shapeless cloud of points is the mark of a valid regression. A funnel or a curve means the model has left structure in its errors. The adepts look at this plot early.

## July 14 - Vigil of the Agent's Leash

**Purpose** - Limiting what an AI agent may do.

**Context** - A servitor obeys every command, and so does an agent. An agent that can run commands can run the wrong ones. Give each tool the narrowest permission that completes the task. Require a human for anything that cannot be undone.

## July 15 - Feast of the Softmax

**Purpose** - Remembering that a confident output is not proof.

**Context** - Softmax turns a vector of scores into positive numbers that sum to one, and it exaggerates the largest score. A confident output is a property of the function. By itself it is not evidence of a correct answer. The machine spirit sounds sure even when it is wrong.

## July 16 - Observance of the Failed Reconstruction

**Purpose** - Finding anomalies by the error of a reconstruction.

**Context** - Fit PCA or an autoencoder on normal data only. It learns to rebuild normal inputs well. An input that it rebuilds badly is unlike the normal data, so the reconstruction error serves as the anomaly score. The adepts read a bad rebuild as a warning.

## July 17 - Observance of the Explained Variance

**Purpose** - Judging R squared with care.

**Context** - R squared states what share of the variance the model explains on the data it was fitted to. It never falls when a feature is added, useful or not. Judge the model on held-out data instead. The Magos trusts only the score on held-out data.

## July 18 - Vigil of the Uneven Error

**Purpose** - Breaking every metric down by subgroup.

**Context** - An overall accuracy can hide a model that fails one group of people far more often than another. Break every metric down by subgroup, and look hardest at the smallest groups. The adepts keep this vigil tonight.

## July 19 - Observance of the Unequal Divergence

**Purpose** - Remembering that the KL divergence is not a distance.

**Context** - The Kullback-Leibler divergence measures how far one probability distribution is from another. It is zero only when the two are equal. It is not symmetric: the divergence from P to Q differs from that from Q to P. So it is not a distance, and the tech-priests never call it one.

## July 20 - Saint Calida of the Heat Map

**Purpose** - Remembering the saint who mapped which image regions a model uses.

**Context** - Calida used Grad-CAM to draw a heat map of the image regions that drove a prediction. With it she found a classifier that recognised wolves by the snow behind them. In her memory the tech-priests check which image regions a model uses.

## July 21 - Litany of the Three Decoders

**Purpose** - Recording which decoding method produced the text.

**Context** - Greedy decoding takes the likeliest token at each step. Beam search keeps several candidates alive, and sampling draws at random. The same model gives different text under each. The tech-priests record which one they used.

## July 22 - Feast of the Jacobian

**Purpose** - Understanding why backpropagation never builds the Jacobian.

**Context** - The Jacobian of a function holds the derivative of every output with respect to every input. Backpropagation never builds this matrix. It multiplies a vector by the Jacobian of each layer in turn, which is far cheaper. The machine spirit is spared the work.

## July 23 - Vigil of the Edge of the Range

**Purpose** - Widening a hyperparameter search range when the best value lies on its edge.

**Context** - When the best hyperparameter value of a search lies on the edge of the range, the true best may lie outside. Widen the range and search again. Search learning rates and regularisation strengths on a logarithmic scale. The acolytes watch the edges.

## July 24 - Feast of the Augmented Sample

**Purpose** - Augmenting data only with changes that keep the label.

**Context** - Flip, crop, shift and add noise to your training images, and the model sees more variety than you collected. Use only changes that leave the label true: an upside-down 6 has become a 9. The Magos rejects any other change.

## July 25 - Rite of the Paired Quantiles

**Purpose** - Reading a quantile-quantile plot against the normal distribution.

**Context** - A quantile-quantile plot sets the quantiles of the data against those of a normal distribution. Points on a straight line mean the data is close to normal. Ends that bend away mean heavier or lighter tails. The tech-priests judge the line by its ends.

## July 26 - Vigil of the Many-Valued Feature

**Purpose** - Distrusting impurity importance for features with many values.

**Context** - Impurity-based feature importance of tree models favours features with many distinct values, such as identifiers, even when they carry no signal. Check with permutation importance on held-out data, and remove identifiers from the features. The adepts do both.

## July 27 - Vigil of the Saddle Point

**Purpose** - Understanding why the loss stalls.

**Context** - In high dimensions the optimiser is far more often slowed by saddle points and flat plateaus than trapped in a poor local minimum. If the loss stalls, adjust the learning rate before you despair. The machine spirit is slow, not lost.

## July 28 - Saint Rara of the Uncommon Word

**Purpose** - Remembering the saint who weighted words by their rarity.

**Context** - Rara used TF-IDF, which weights a word by how often it occurs in a document and by how rare it is across all documents. Words found everywhere get a low weight. A word found in few documents marks what a document is about. In her memory the tech-priests weigh words.

## July 29 - Feast of the Well-Made Feature

**Purpose** - Building one good feature by hand.

**Context** - A ratio, a difference or a count over the last seven days is a feature built by hand. One well-chosen feature can give a simple model what a deep model would need a million rows to discover. The enginseers ask a domain expert what to compute.

## July 30 - Rite of the Chat Template

**Purpose** - Using the model's own chat template.

**Context** - Chat models expect each turn wrapped in the exact special tokens they were trained with. Apply the model's own chat template. A hand-built prompt with the wrong markers makes the answers worse and raises no error. The machine spirit gives no warning.

## July 31 - Rite of the Shortest Path

**Purpose** - Choosing a shortest-path algorithm for a graph.

**Context** - In a graph without edge weights, breadth-first search finds the shortest path. With non-negative weights, Dijkstra's algorithm finds it. With negative weights Dijkstra's algorithm can give a wrong answer, so use the Bellman-Ford algorithm there. The enginseers check the weights first.

