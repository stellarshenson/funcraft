# Cult Mechanicus Liturgical Calendar - November

## November 1 - Feast of the Patched Image

**Purpose** - Seeing how a vision transformer reads an image.

**Context** - A vision transformer cuts an image into square patches and treats each patch as a token. An image of 224 by 224 pixels in patches of 16 by 16 becomes 196 tokens. The acolytes count the patches first.

## November 2 - Rite of the Paired Comparison

**Purpose** - Comparing two models on the same test examples.

**Context** - Run both models on the same test examples and analyse the difference example by example. Pairing removes the variation between examples, so smaller differences can be detected. The Magos asks for pairs.

## November 3 - Feast of the Embedding Table

**Purpose** - Understanding an embedding layer as a lookup table.

**Context** - An embedding layer is a lookup table with one learned vector per token identifier. Looking up row i gives the same result as multiplying a one-hot vector by the table, without the multiplication. The cogitator takes the cheaper way.

## November 4 - Vigil of the Chosen Champion

**Purpose** - Measuring the winner of many runs again.

**Context** - The best of fifty runs, chosen by its validation score, owes part of that score to luck. Measure the winner again on data that took no part in the choice. The Magos trusts only that second number.

## November 5 - Commemoration of Saint Recurra the Remembering

**Purpose** - Remembering the saint of the recurrent network.

**Context** - Saint Recurra applied the same weights at every step of a sequence and let a hidden state carry what was seen before. Her network cannot process the steps in parallel, and over long sequences its gradients vanish. Gated cells eased the second fault, and attention removed both.

## November 6 - Feast of the Passed Message

**Purpose** - Following messages between the nodes of a graph.

**Context** - In a graph neural network each node updates its state from the messages of its neighbours. After k rounds a node has heard from nodes up to k steps away. The servo-skulls carry one message a step.

## November 7 - Rite of the Recomputed Activation

**Purpose** - Trading time for memory with gradient checkpointing.

**Context** - Gradient checkpointing discards some activations in the forward pass and computes them again in the backward pass. It uses less memory and more time. It can fit a model the card could not otherwise hold. The enginseers try it first.

## November 8 - Observance of the Two Intervals

**Purpose** - Telling a confidence interval from a prediction interval.

**Context** - A confidence interval concerns the mean. A prediction interval concerns one new observation. The prediction interval is wider, and more data does not shrink it to nothing. The Magos asks which one you mean.

## November 9 - Observance of the Second Eigenvector

**Purpose** - Splitting a graph in two with the Fiedler vector.

**Context** - The eigenvector of the second-smallest eigenvalue of the graph Laplacian is called the Fiedler vector. The signs of its entries split a connected graph into two parts with few edges between them. It is the basis of spectral partitioning. The adepts read the signs.

## November 10 - Observance of the Determinant

**Purpose** - Reading what the determinant says about a matrix.

**Context** - The determinant of a square matrix is the factor by which the matrix scales volume. A determinant of zero means the matrix flattens space into fewer dimensions and cannot be inverted. The tech-priests do not try to invert such a matrix.

## November 11 - Feast of the Four Ones

**Purpose** - Reading 1111 as binary and as hexadecimal.

**Context** - The date written 1111 and read as binary is fifteen, F in hexadecimal. That is four bits, all set. Two hexadecimal digits write one byte. The cogitator keeps this feast with a binary chant.

## November 12 - Commemoration of Saint Steadia the Stationary

**Purpose** - Remembering the saint who made a series stationary.

**Context** - Many forecasting methods assume a stationary series, whose mean and variance do not change over time. Steadia removed a trend by differencing: she modelled the change from one step to the next. The enginseers still difference a series with a trend.

## November 13 - Observance of the Forgetful Chain

**Purpose** - Remembering that a Markov chain forgets the past.

**Context** - In a Markov chain the next state depends on the present state alone. An n-gram language model is one. It predicts the next word from the last n minus 1 words and nothing earlier. The machine spirit keeps no older memory.

## November 14 - Vigil of the Lossy Image

**Purpose** - Saving masks and labels in a lossless format.

**Context** - JPEG compression discards detail, and every new save discards more. A segmentation mask saved as JPEG gets wrong class values along its edges. Keep masks and labels in a lossless format such as PNG. The Magos calls a JPEG mask heresy.

## November 15 - Feast of the Many Experts

**Purpose** - Counting the memory a mixture-of-experts model needs.

**Context** - A mixture-of-experts model routes each token to a few of its many expert sub-networks. Only part of the parameters work on any one token, yet all of them must be held in memory. The enginseers plan for all of them.

## November 16 - Rite of the Batched Request

**Purpose** - Choosing a batch size for inference requests.

**Context** - A GPU processes many inputs in one pass. Batching inference requests raises throughput, and each request waits a little longer. Choose the batch size from the latency that is acceptable. The servitors follow that limit.

## November 17 - Observance of the Two-Dimensional Shadow

**Purpose** - Writing the explained variance on a PCA plot.

**Context** - A plot of the first two principal components shows only the share of the variance those two explain. If that share is 30 percent, 70 percent of the structure is not on the plot. Write the share on the axes. The tech-priests mistrust a shadow without its share.

## November 18 - Vigil of the Forgotten Task

**Purpose** - Guarding old skills while tuning a model for a new task.

**Context** - Fine-tuning a model on a new task can erase its skill on the old ones (catastrophic forgetting). Test the old tasks after tuning. Mix in old data, or train an adapter and leave the base weights frozen. The Magos tests the old tasks first.

## November 19 - Commemoration of Saint Isotona the Stepwise

**Purpose** - Remembering the saint who calibrated scores with isotonic regression.

**Context** - Isotona calibrated her scores with isotonic regression: a step function that never decreases, fitted from score to observed frequency on held-out data. It follows any monotonic distortion, where a fitted sigmoid cannot. It needs more calibration data and overfits a small set. The adepts give it plenty.

## November 20 - Feast of the Dilated Convolution

**Purpose** - Understanding how dilation widens the receptive field.

**Context** - A dilated convolution leaves gaps between the points of its kernel. Stacking layers whose dilation doubles each time makes the receptive field grow exponentially with depth, with no extra parameters per layer. The enginseers use it on long stretches of audio or of a time series.

## November 21 - Rite of the Guided Hand

**Purpose** - Understanding teacher forcing and its limit.

**Context** - With teacher forcing, a sequence model is given the true previous token at every step in training. In generation it is given its own output. Its early mistakes then compound in a way that training never showed it. The Magos expects them.

## November 22 - Vigil of the Transformed Target

**Purpose** - Correcting the predictions of a model trained on a logarithm.

**Context** - A model trained on the logarithm of the target predicts the mean of the logarithm. Transformed back with the exponential, that is closer to the median of the target than to its mean, and it underestimates totals. The adepts correct for it, or evaluate on the original scale.

## November 23 - Feast of the Summed Pair

**Purpose** - Remembering how memoisation tames a naive recursion.

**Context** - The date 11-23 gives 1, 1, 2, 3: each term is the sum of the two before it. Naive recursion makes the work grow exponentially. Store each term once computed (memoisation) and it grows linearly. The cogitator keeps what it computed.

## November 24 - Vigil of the Curved Bowl

**Purpose** - Understanding why gradient descent zigzags in a curved loss.

**Context** - The Hessian is the matrix of second derivatives of the loss, and its eigenvalues give the curvature in each direction. When the largest is far greater than the smallest, gradient descent zigzags across the steep direction and crawls along the flat one. The enginseers call it a curved bowl.

## November 25 - Feast of the Smoothed Histogram

**Purpose** - Choosing the bandwidth of a kernel density estimate.

**Context** - A kernel density estimate places a small smooth bump on every observation and adds the bumps. The bandwidth of the bump plays the role of the bin width of a histogram: too narrow gives noise, too wide hides the shape. The adepts set it with care.

## November 26 - Observance of the Attributed Credit

**Purpose** - Reading feature attributions for what they are.

**Context** - Feature attributions, such as SHAP values, describe what the model relies on, not what causes the outcome in the world. Between correlated features the credit is divided arbitrarily. Adepts do not call it proof of cause.

## November 27 - Commemoration of Saint Factora the Decomposer

**Purpose** - Remembering the saint who filled the empty cells of a table.

**Context** - Factora described every user and every item by a short vector (matrix factorisation). She predicted a rating as the dot product of the two vectors. So she filled the empty cells of a table in which most users had rated few items. The tech-priests factorise in her memory.

## November 28 - Vigil of the Checkerboard

**Purpose** - Avoiding the checkerboard pattern in generated images.

**Context** - A transposed convolution whose kernel size is not divisible by its stride paints some output pixels more often than others, and a checkerboard pattern appears. Use a kernel size divisible by the stride, or resize first and then apply an ordinary convolution. The tech-priests call the pattern scrap-code.

## November 29 - Feast of the Mean Average Precision

**Purpose** - Stating the overlap threshold with every mAP score.

**Context** - In object detection, average precision is the area under the precision-recall curve of one class. The mean over all classes is mAP. State the overlap threshold with it: mAP at 0.5 is more lenient than mAP averaged from 0.5 to 0.95. The Magos asks for it.

## November 30 - Rite of the Closed Loop

**Purpose** - Keeping random exposure in a system that ranks.

**Context** - A model that decides what users are shown is later trained on what they chose from what it showed, and so confirms itself. Keep a small share of random exposure to learn about what it never shows. The machine spirit cannot learn about what it hides.
