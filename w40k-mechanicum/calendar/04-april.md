# Cult Mechanicus Liturgical Calendar - April

## April 1 - Observance of the Too-Good Score

**Purpose** - Doubting a validation score that looks too good.

**Context** - A validation accuracy of 99.9 percent on a hard problem is a symptom, not a triumph. Suspect leakage first, a duplicated row second and a fault in the metric third. Suspect your own brilliance last. The enginseers check in this order.

## April 2 - Rite of the Cosine Descent

**Purpose** - Decaying the learning rate during a run.

**Context** - Lower the learning rate slowly during a run, by steps or along a cosine curve. With a constant rate, the weights still jump around the minimum of the loss when the run ends. With a decayed rate, the weights settle in the minimum. The tech-priests call a run without decay unfinished.

## April 3 - Feast of the Good and Bad Trials

**Purpose** - Searching hyperparameters with the tree-structured Parzen estimator.

**Context** - The tree-structured Parzen estimator, the default sampler of Optuna, sorts the finished trials into a good group and a bad group, and models each. It proposes values likely in the good group and unlikely in the bad one. The enginseers like it for categorical and conditional hyperparameters.

## April 4 - Rite of All but the Top

**Purpose** - Cleaning word embeddings with the all-but-the-top method.

**Context** - Word embeddings share a common mean vector and a few dominant directions that mostly encode word frequency, not meaning. The acolytes apply the all-but-the-top method: subtract the mean, remove the top few principal components. Similarity between words then becomes more meaningful.

## April 5 - Commemoration of Saint Solva the Uninverting

**Purpose** - Remembering the saint who solved systems without inverting.

**Context** - To solve the system A x = b, Solva never computed the inverse of A. She called a solver, which is faster and loses less precision. In her memory the tech-priests write solve(A, b) in NumPy, not inv(A) times b.

## April 6 - Observance of the Sufficient Sample

**Purpose** - Estimating the sample size before an experiment.

**Context** - An experiment that is too small cannot detect the effect it seeks, and its samples are wasted. Estimate the sample size before you begin, from the smallest effect that would matter. The Magos blesses no experiment without it.

## April 7 - Rite of the Zeroed Gradient

**Purpose** - Clearing the gradients in every PyTorch training step.

**Context** - In PyTorch, gradients accumulate across backward passes until you clear them. Call zero_grad in every training step, before the backward pass. Otherwise the model is steered by the sum of the gradients of every batch it has seen. The call is a rite, and it is not optional.

## April 8 - Feast of the Retrieved Passage

**Purpose** - Evaluating the search step of a retrieval system.

**Context** - Retrieval lets a model answer from documents it was never trained on, by placing the relevant passages in its context. The answer is only as good as what was retrieved. So evaluate the search before you evaluate the answer. A servo-skull fetches the passages.

## April 9 - Rite of the Transformer Block

**Purpose** - Knowing the parts of a transformer block.

**Context** - The adepts build a transformer as a stack of identical blocks. In each block, a self-attention layer and a small feed-forward network are each wrapped in a residual connection with a layer normalisation. Attention moves information between tokens; the feed-forward network works on each token alone.

## April 10 - Observance of the Returning Mean

**Purpose** - Remembering that extreme values drift back toward the average.

**Context** - Last month's worst performers will tend to improve and its best performers will tend to decline, with no intervention at all. Before you say that your fix worked, ask whether extreme values were only drifting back toward the average. The tech-priests call this regression to the mean.

## April 11 - Rite of the Frozen Layers

**Purpose** - Freezing the pretrained layers when data is scarce.

**Context** - When data is scarce, freeze the pretrained body and train only the new head. Unfreeze the deeper layers later, with a smaller learning rate. Otherwise you may overwrite what the model learned at great cost. The adepts guard that knowledge.

## April 12 - Commemoration of Saint Lettera the Unsquashed

**Purpose** - Remembering the saint who kept the aspect ratio of images.

**Context** - Saint Lettera knew that resizing an image to a square without keeping its aspect ratio squashes every shape. She kept the ratio and padded the rest of the square, which is called letterboxing. She resized in the same way in training and in inference. The tech-priests do likewise in her memory.

## April 13 - Feast of the Random Forest

**Purpose** - Understanding why many trees vote better than one.

**Context** - A random forest grows many trees, each on a different bootstrap sample and a random subset of features. The trees vote together. Their errors are partly independent, so the forest is steadier than any single tree. The Magos prefers a forest to a lone tree.

## April 14 - Observance of the Peeked Result

**Purpose** - Not stopping an experiment the moment it looks significant.

**Context** - Checking a running experiment daily and stopping when it looks significant pushes the false-positive rate far above 5 percent. Fix the sample size in advance, or use a test designed for repeated looks. Peeking is tech-heresy.

## April 15 - Vigil of the Silent NaN

**Purpose** - Checking that the features and the loss are finite.

**Context** - One NaN turns every sum and mean that contains it into NaN, and NaN is not even equal to itself. Assert that your features and your loss are finite. Do it before the corruption spreads through the whole dataset. A pipeline that hides NaN is scrap-code.

## April 16 - Rite of the Suppressed Twin

**Purpose** - Removing duplicate boxes with non-maximum suppression.

**Context** - An object detector proposes many overlapping boxes for one object. Non-maximum suppression keeps the box with the highest score and removes the others that overlap it more than a threshold. The servo-skulls clear the twins away.

## April 17 - Feast of the Bootstrap

**Purpose** - Estimating uncertainty by resampling with replacement.

**Context** - Resample your data with replacement a thousand times and recompute the statistic each time. The spread of the results estimates its uncertainty. No formula is needed, only patience and a willing cogitator.

## April 18 - Observance of the Encoded Category

**Purpose** - Not coding categories as plain numbers.

**Context** - If you code red, green and blue as 1, 2 and 3, a linear model concludes that blue is three times red. Where no order exists, use one-hot columns or a learned embedding. The tech-priests call the numbered colours a small heresy.

## April 19 - Commemoration of Saint Annota the Consistent

**Purpose** - Remembering the saint who wrote the guideline before the labels.

**Context** - Saint Annota wrote the labelling guideline before the first label and measured how often two annotators agreed. Where they disagreed, she amended the guideline, never the annotators. The tech-priests keep her order of work.

## April 20 - Rite of the Accumulated Step

**Purpose** - Simulating a large batch with gradient accumulation.

**Context** - If the batch you want does not fit in memory, run several small batches. Step the optimiser only after their gradients have accumulated. The update approximates the large batch at the memory cost of the small one. Every adept should know this litany.

## April 21 - Vigil of the Small-Batch Norm

**Purpose** - Choosing a normalisation that suits small batches.

**Context** - Batch normalisation estimates the mean and the variance from the batch. With very small batches those estimates are noisy and training suffers. The enginseers use group normalisation or layer normalisation there; these two methods do not depend on the batch size.

## April 22 - Feast of the Principal Component

**Purpose** - Standardising features before a principal component analysis.

**Context** - Principal components are the directions of greatest variance, each orthogonal to the last. Standardise the features first. Otherwise the leading component only points at the column whose unit gives the largest variance. The Magos calls that a measurement of the units, not of the data.

## April 23 - Observance of the Weighted Average

**Purpose** - Weighting group means by group size.

**Context** - The mean of group means is not the overall mean unless the groups have the same size. Weight each group by its count. Otherwise a group of three counts as much as a group of three thousand. The enginseers weigh every mean.

## April 24 - Rite of the Structured Reply

**Purpose** - Validating the JSON reply of a language model in code.

**Context** - When a language model must return JSON, state the schema, show an example and validate the reply in code before anything uses it. Trust the parser, never the look of the text. Unvalidated output is tech-heresy.

## April 25 - Vigil of the Arrow of Time

**Purpose** - Splitting time-ordered data by time, never at random.

**Context** - For data ordered in time, train on the past and validate on the future, never the reverse. A random shuffle puts data from the future into the training set, and the forecast scores become false. The Machine God accepts no forecast from a model trained on the future.

## April 26 - Feast of the Variational Autoencoder

**Purpose** - Understanding how a variational autoencoder generates new data.

**Context** - A variational autoencoder encodes each input as a mean and a variance, not as one point, and decodes a sample drawn from them. Its loss adds the reconstruction error and a term that keeps the codes close to a standard normal. The tech-priests decode random normal vectors to make new data.

## April 27 - Commemoration of Saint Loada the Interpreter

**Purpose** - Remembering the saint who read the loadings of a component.

**Context** - Each principal component is a weighted mix of the original features, and the weights are the loadings. Saint Loada read them to learn which features drive a component. She knew that the sign of a component is arbitrary: the whole component may be flipped. The acolytes read loadings in her memory.

## April 28 - Observance of the Effect Size

**Purpose** - Reporting how large an effect is, not only that it is significant.

**Context** - With enough data, a difference too small to matter becomes statistically significant. Report how large the effect is, with its interval, and whether it is worth acting on. A p-value alone does not impress the Magos.

## April 29 - Rite of the Padding Mask

**Purpose** - Passing the attention mask together with padded sequences.

**Context** - Sequences in a batch are padded to equal length, and the padding means nothing. Pass the attention mask with them. Otherwise the model attends to the padding and mixes it into the answer. Without the mask, the machine spirit cannot see which positions are padding.

## April 30 - Vigil of the Personal Reliquary

**Purpose** - Keeping your own files in your personal volume.

**Context** - Your own work belongs in @volumes/personal, under your own name and in your own order. Tonight, move the stray files from temporary folders to your personal volume. The enginseers do the same.
