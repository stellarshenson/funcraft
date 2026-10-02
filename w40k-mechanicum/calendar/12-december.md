# Cult Mechanicus Liturgical Calendar - December

## December 1 - Feast of the Averaged Weights

**Purpose** - Averaging weights over the end of training.

**Context** - Averaging the weights of a model over the last part of training often gives a model that generalises better than the final step. Two methods are the exponential moving average and stochastic weight averaging. The enginseers keep the average.

## December 2 - Rite of the Merged Pair

**Purpose** - Building a tokeniser vocabulary by merging pairs.

**Context** - Byte-pair encoding builds a vocabulary by merging, again and again, the most frequent adjacent pair of symbols. Common words end as one token and rare words as several pieces. Each merge is a small rite.

## December 3 - Observance of the Unfree Lunch

**Purpose** - Remembering that no algorithm wins on every problem.

**Context** - The no-free-lunch theorem says that, averaged over all possible problems, no learning algorithm outperforms any other. An algorithm wins on your problem because its assumptions fit your problem. The Magos asks what it assumes.

## December 4 - Vigil of the Imperceptible Change

**Purpose** - Testing a classifier against tiny changes to an image.

**Context** - An adversarial example is a change to an image too small for the eye to see. It can make a classifier give a different answer with high confidence. Accuracy on a clean test set says nothing about this. The machine spirit sees what the adept cannot.

## December 5 - Commemoration of Saint Synthetica the Wary

**Purpose** - Remembering the saint who kept real data in training.

**Context** - Synthetica saw that models trained on the outputs of models lose the rare cases a little more with each generation. She kept real data in every training set and marked the synthetic rows as synthetic.

## December 6 - Feast of the Thousand Dice

**Purpose** - Counting the trials of a Monte Carlo estimate.

**Context** - Monte Carlo estimation answers a question by simulating many random trials. The error falls with the square root of the number of trials. A hundred times the trials buys one more digit. The cogitator throws the dice.

## December 7 - Feast of the Moving Pixel

**Purpose** - Understanding what optical flow measures.

**Context** - Optical flow estimates, for every pixel, how far and in which direction it moved between two frames of a video. It shows motion without recognising any object. The machine spirit sees the movement and names nothing.

## December 8 - Feast of the Spectral Norm

**Purpose** - Limiting a layer with the spectral norm of its weights.

**Context** - The spectral norm of a matrix is its largest singular value: the most the matrix can stretch any vector. Spectral normalisation divides the weights of a layer by this value. This limits how much the layer can amplify its input and steadies the training of a GAN discriminator. The cult counts it a blessing.

## December 9 - Feast of the Unitless Number

**Purpose** - Preferring correlation to covariance across units.

**Context** - Covariance depends on the units: change one variable from metres to millimetres and it grows a thousandfold. Correlation divides the covariance by both standard deviations, has no unit and always lies between minus 1 and 1. The enginseers prize a number without a unit.

## December 10 - Observance of the Smoothed Neighbourhood

**Purpose** - Avoiding over-smoothing in graph convolution layers.

**Context** - A graph convolution layer replaces the features of each node with a weighted average over the node and its neighbours. This smooths the features along the edges. With too many layers all nodes of a connected graph come to look alike. The Magos calls this over-smoothing.

## December 11 - Feast of the Joined Image and Word

**Purpose** - Classifying an image with no training, using CLIP.

**Context** - A model such as CLIP places images and texts in one shared embedding space. To classify an image with no training, compare it with the texts 'a photo of a cat' and 'a photo of a dog'. Take the nearest. The acolytes call this a small miracle.

## December 12 - Commemoration of Saint Centrala the Well-Connected

**Purpose** - Remembering the saint who measured the centrality of nodes.

**Context** - Saint Centrala measured node importance in several ways, called centrality. Degree counts its edges. Betweenness counts the shortest paths through it. Closeness measures its nearness to all others. Eigenvector centrality counts links to important nodes. In her memory the adepts ask what each one answers.

## December 13 - Feast of the Chosen Basis

**Purpose** - Seeing PCA and the Fourier transform as changes of basis.

**Context** - The same vector has different coordinates in different bases. PCA, the Fourier transform and wavelets are all changes of basis, chosen so that the data needs few large coordinates. The tech-priests choose the basis that suits the data.

## December 14 - Rite of the Crossed Attention

**Purpose** - Understanding cross-attention between two sequences.

**Context** - In cross-attention the queries come from one sequence and the keys and values from another. This is how a decoder reads the output of an encoder, and how an image diffusion model reads the text prompt. The machine spirit looks at two sequences at once.

## December 15 - Feast of the Joint Effect

**Purpose** - Understanding the interaction between two features.

**Context** - An interaction means the effect of one feature depends on the value of another. A linear model without an interaction term cannot represent it. A tree-based model can. The tech-priests add the term or choose the trees.

## December 16 - Rite of the Scaled Dot Product

**Purpose** - Knowing why attention divides by the square root of the dimension.

**Context** - Attention scores are dot products of query and key vectors, divided by the square root of their dimension. Without the division the scores grow with the dimension, the softmax saturates and the gradients become very small. The machine spirit demands the division.

## December 17 - Rite of the Rotated Position

**Purpose** - Understanding rotary position embeddings.

**Context** - Rotary position embeddings encode the position of a token by rotating its query and key vectors by an angle that grows with the position. The attention score between two tokens then depends on how far apart they are, not on where they stand in the text. Adepts call it a holy rotation.

## December 18 - Observance of the Two Uncertainties

**Purpose** - Telling noise in the data from what the model does not know.

**Context** - Aleatoric uncertainty is noise in the data itself; more data does not reduce it. Epistemic uncertainty is what the model does not yet know; more data reduces it. The Magos asks which one is large before the team collects more data.

## December 19 - Saint Hybrida of the Two Searches

**Purpose** - Remembering the saint who ran two searches together.

**Context** - Keyword search finds exact terms such as part numbers and names. Vector search finds passages with the same meaning in other words. Hybrida ran both and merged the results, which often retrieves better than either alone. In her memory the tech-priests run both.

## December 20 - Rite of the Counted Parameters

**Purpose** - Counting the parameters of a layer by hand.

**Context** - A linear layer from n inputs to m outputs has n times m weights and m biases. A convolution has a k by k kernel, c input channels and d output channels. It has k times k times c times d weights and d biases, whatever the image size. Count them once by hand, as the tech-priests do.

## December 21 - Feast of the Spectrogram

**Purpose** - Seeing how the frequencies of a signal change over time.

**Context** - A spectrogram shows how the frequency content of a signal changes over time: time on one axis, frequency on the other, strength as colour. Speech and audio models usually take a spectrogram as input, not the raw wave. The cogitator draws sound as a picture.

## December 22 - Feast of the Universal Approximator

**Purpose** - Knowing what the universal approximation theorem says.

**Context** - A network with one hidden layer, if wide enough, can approximate any continuous function on a bounded domain. The theorem does not say how wide, nor how to find the weights. The Magos reads it as permission, not as a method.

## December 23 - Rite of the Cut Tree

**Purpose** - Choosing the number of clusters after looking at the tree.

**Context** - Hierarchical clustering joins the two closest groups again and again and records the joins as a tree, the dendrogram. Cut the tree at a height to get clusters. The number of clusters is chosen after looking, not before. The adepts look first.

## December 24 - Commemoration of Saint Sigmoida the Curve-Fitter

**Purpose** - Remembering the saint who calibrated scores with Platt scaling.

**Context** - Sigmoida calibrated classifier scores by Platt scaling: a logistic regression on held-out data with one input, the score. It suits sigmoid-shaped distortions, as in support vector machines and boosted trees, and works with little calibration data. The tech-priests do the same in her memory.

## December 25 - Rite of the Learned Warp

**Purpose** - Learning a distortion-free view from a fisheye image.

**Context** - A network can learn a warp from a fisheye image of a flat target to a distortion-free, telecentric view. No lens formula is needed. In effect the network holds the full Jacobian of the transformation: how every small patch is stretched, turned and sheared. The enginseers let the machine spirit learn the lens.

## December 26 - Vigil of the Averaged Curve

**Purpose** - Remembering that the mean of a function is not the function of the mean.

**Context** - The average of a function is in general not the function of the average. The mean of the logarithms is not the logarithm of the mean, and the mean of ratios is not the ratio of means. The adepts decide which one the question asks for.

## December 27 - Feast of the Gated Memory

**Purpose** - Remembering how an LSTM gates its memory.

**Context** - The long short-term memory network carries a cell state through the sequence. Three gates decide what enters it, what is forgotten and what is output. It carried gradients across long sequences before attention took over. The cogitators remember it.

## December 28 - Rite of the Single Batch

**Purpose** - Training on one small batch before a long run.

**Context** - Before a long training run, train on one small batch alone. A sound model drives that loss close to zero. One that cannot has a fault in the model, the loss or the data pipeline. The enginseers test the machine spirit this way.

## December 29 - Vigil of the Batch-Averaged Metric

**Purpose** - Computing a metric once on all predictions, not per batch.

**Context** - The average of a metric computed per batch is not the metric of the whole set. A smaller last batch gets too much weight. The F1 or the AUC of the whole set is not the mean of batch values at all. The acolytes collect all predictions, then compute the metric once.

## December 30 - Commemoration of Saint Shrinka the Moderate

**Purpose** - Remembering the saint who shrank noisy group averages.

**Context** - The average of a small group is noisy. Shrinka pulled each group average toward the overall mean, the more so the smaller the group (partial pooling). Her estimates were better on average than the raw group means. The tech-priests shrink small groups in her memory.

## December 31 - Feast of the Final Checkpoint

**Purpose** - Saving the state of the work at the end of the year.

**Context** - The last checkpoint of the year: commit and push the work, save the state of whatever still runs, and write where to resume. Tomorrow the count begins again at epoch zero. The adepts end the year with this rite.
