# Cult Mechanicus Liturgical Calendar - August

## August 1 - Feast of the Model Card

**Purpose** - Writing a model card for every released model.

**Context** - For every model you release, write what it was trained on, what it is for, how it was evaluated and where it fails. A model sent out without such a record will be used for the one thing it cannot do. The Magos asks to see the card.

## August 2 - Rite of the Threshold

**Purpose** - Choosing the decision threshold with care.

**Context** - A classifier returns a score. The threshold that turns the score into a decision is yours to set. Choose it on validation data, from the cost of each kind of error. 0.5 is a default, not a law of the Omnissiah.

## August 3 - Vigil of the Persistent Series

**Purpose** - Beating the 'same as yesterday' forecast.

**Context** - Today's value in a time series resembles yesterday's, so a forecast of 'the same as yesterday' is hard to beat. Make it your baseline. Distrust any model that cannot do better. The adepts call such a model scrap-code.

## August 4 - Observance of the Human Reviewer

**Purpose** - Reading what the model wrote before you send it.

**Context** - A model's draft is a draft. Whoever sends the report, merges the code or signs the analysis is its author in every way that matters. That person must have read it. The Magos names the human, not the model.

## August 5 - Commemoration of Saint Hypera the Random

**Purpose** - Remembering the saint of random search.

**Context** - Saint Hypera sampled her hyperparameters at random instead of on a grid, and so tried many more distinct values of the few that mattered. She sampled the learning rate on a logarithmic scale, so every order of magnitude was tried equally often. In her memory the tech-priests search as she did.

## August 6 - Observance of the Sparse Weight

**Purpose** - Choosing between an L1 and an L2 penalty.

**Context** - An L1 penalty drives the weights of weak features all the way to zero, while an L2 penalty only shrinks them. Use L1 when you want the model to keep a few features and discard the rest. The enginseers choose it for that job.

## August 7 - Feast of the Singular Value

**Purpose** - Computing PCA from the singular value decomposition.

**Context** - PCA is computed by the singular value decomposition of the centred data matrix. The right singular vectors are the principal directions. Each squared singular value, divided by n minus 1, is the variance along its direction. The cogitator does the whole decomposition in one call.

## August 8 - Feast of the Eight Bits

**Purpose** - Measuring the cost of 8-bit quantisation.

**Context** - Eighth day, eighth month, eight bits. Quantising weights from 32-bit floats to 8-bit integers cuts a model to a quarter of its size, at some cost in accuracy. Measure that cost and never assume it. The enginseers keep this feast.

## August 9 - Vigil of the Poisoned Pickle

**Purpose** - Loading weights in a safe format only.

**Context** - Loading a pickle file can run any code its author chose. That is scrap-code hidden in a data file. Accept weights from strangers only in a format that stores tensors and nothing else, such as safetensors.

## August 10 - Observance of the Planned Analysis

**Purpose** - Deciding the analysis plan before you see the results.

**Context** - Decide the hypothesis, the metric and the test before you look at the outcome, and lock the plan. Every choice made after seeing the data can steer the result toward the answer you hoped for, however honest you are. The Magos demands the plan first.

## August 11 - Rite of the Nucleus

**Purpose** - Understanding nucleus sampling.

**Context** - Nucleus sampling keeps the smallest set of tokens whose probabilities sum to p and draws only from those. It discards the long tail of unlikely tokens, where much of the nonsense is found. The tech-priests use it to keep the machine spirit sensible.

## August 12 - Feast of the Clustered Points

**Purpose** - Questioning the clusters that k-means finds.

**Context** - The machine spirit of k-means will find k clusters whether or not the data contains any. Try several values of k and several starting points. Look at the clusters before you give them names.

## August 13 - Commemoration of Saint Solitaria the Lonely

**Purpose** - Remembering the saint who found outliers by local density.

**Context** - Solitaria compared the density around each point with the density around its neighbours (the local outlier factor). A point in a much sparser place than its neighbours is an outlier, even where one global threshold would miss it. The tech-priests judge a point by its neighbours.

## August 14 - Vigil of the Monitored Model

**Purpose** - Monitoring a model after deployment.

**Context** - Deployment is the start of a model's service, not the end of the project. Log its inputs and predictions, and compare the predictions with the outcomes when the outcomes arrive. Set an alarm for the day the two differ. A servo-skull can watch the model.

## August 15 - Observance of the Stated Denominator

**Purpose** - Stating the denominator beside every rate.

**Context** - Every rate is a count divided by something, and the error usually hides in that something. Per user or per session, per day or per active day: state the denominator beside the number. The Magos always asks 'per what' of a number.

## August 16 - Rite of the No-Gradient Context

**Purpose** - Switching off gradient recording during inference.

**Context** - During inference the framework need not record operations for backpropagation. Wrap the forward pass in a no-gradient context. It uses less memory, runs faster and returns the same outputs. The enginseers do this for inference.

## August 17 - Feast of the Great Inventory

**Purpose** - Matching each job to the smallest GPU that fits it.

**Context** - Three GPUs serve BEHEMOTH: 24 GB at index 0, 96 GB at index 1 and 32 GB at index 2, 152 GB in all. Give each job the smallest GPU that can fit it. The tech-priests give thanks to the Machine God.

## August 18 - Vigil of the Projected Mirage

**Purpose** - Trusting t-SNE and UMAP plots only a little.

**Context** - In a t-SNE or UMAP plot, the sizes of clusters and the distances between them are not reliable. Only local neighbourhoods are roughly preserved. Admire the picture, then prove any claim by another method. The Magos wants that second method.

## August 19 - Observance of the Rounded Figure

**Purpose** - Rounding results to what the sample supports.

**Context** - An accuracy of 87.3462 percent measured on 200 examples claims more precision than it has. Each example is worth half a percentage point. Round to what the sample size can support. The tech-priests write 'about 87 percent'.

## August 20 - Feast of the Truncated Sum

**Purpose** - Approximating a matrix with its largest singular values.

**Context** - The singular value decomposition writes a matrix as a sum of simple rank-one pieces, ordered by their singular values. Keeping the k largest pieces gives the best approximation of rank k in the least-squares sense. The tech-priests keep the pieces that matter.

## August 21 - Commemoration of Saint Entropa the Surprised

**Purpose** - Remembering the saint who measured surprise as entropy.

**Context** - Saint Entropa measured surprise, and her measure is called entropy. An outcome that is sure to happen carries no information, and a fair coin carries one bit. Perplexity is the entropy exponentiated, roughly the number of choices the model is unsure between. The tech-priests honour her for it.

## August 22 - Feast of the Pruned Network

**Purpose** - Knowing when pruning makes a model faster.

**Context** - Many weights in a trained network can be set to zero with little loss of accuracy. The model becomes sparse. It becomes faster only if the hardware and the library can use that sparsity. The adepts measure the speed.

## August 23 - Vigil of the Noisy Objective

**Purpose** - Running the best trials of a search again with other seeds.

**Context** - The score of one trial depends on the random seed. A search over hundreds of trials can pick a setting that was only lucky. Run the best few settings again with other seeds before believing the winner. The Magos does not bless a lucky score.

## August 24 - Observance of the Two Errors

**Purpose** - Choosing between mean absolute error and RMSE.

**Context** - Mean absolute error treats every unit of error alike. Root mean squared error punishes large misses far more. Choose the one that matches what a large miss costs you, and report both when in doubt. The Magos asks which miss costs more.

## August 25 - Rite of the Softened Choice

**Purpose** - Making a discrete choice differentiable with Gumbel-softmax.

**Context** - A choice among discrete options has no gradient. The tech-priests add Gumbel noise to the logits and apply a softmax with a temperature (the Gumbel-softmax trick). The result is a differentiable, approximate sample. A lower temperature brings it closer to a choice of exactly one option.

## August 26 - Rite of the Spectral Clustering

**Purpose** - Clustering points by how they are connected.

**Context** - Spectral clustering describes each point by the eigenvectors of the graph Laplacian with the smallest eigenvalues and runs k-means on those coordinates. It groups points by connection, not by compactness, so it separates two rings that k-means would cut in half. The enginseers use it on such rings.

## August 27 - Observance of the Alarm and the Miss

**Purpose** - Telling a false alarm from a miss in a statistical test.

**Context** - A type I error is a false alarm: the test reports an effect that is not there. A type II error is a miss: a real effect goes undetected. Power is the chance of detecting a real effect. At a fixed sample size, fewer false alarms mean more misses. The tech-priests weigh both errors.

## August 28 - Observance of the First Layer's Edges

**Purpose** - Knowing what the layers of a vision network respond to.

**Context** - The first layers of a trained vision network respond to edges and blobs of colour. Later layers respond to textures, parts and whole objects. This is why the early layers transfer well to a new task. The tech-priests value these layers highly.

## August 29 - Commemoration of Saint Profila the Timekeeper

**Purpose** - Remembering the saint who timed before optimising.

**Context** - Saint Profila never optimised a line she had not timed. The profiler showed nine-tenths of the run in one function, and it was not the function she suspected. In her memory the enginseers profile first.

## August 30 - Rite of the Softened Label

**Purpose** - Understanding label smoothing.

**Context** - Label smoothing replaces the hard target of 1 with a slightly softer one, such as 0.9, and spreads the remainder over the other classes. The model grows less overconfident and is often better calibrated. The machine spirit learns humility.

## August 31 - Rite of the Rolling Origin

**Purpose** - Evaluating a forecast at many points in time.

**Context** - Train on the data up to a date, called the origin, then predict the next period and score it. Move the origin forward and repeat. The average score over many origins is a better estimate than one split. The Magos distrusts a forecast that was scored only once.

