# Cult Mechanicus Liturgical Calendar - January

## January 1 - Feast of the Zeroth Epoch

**Purpose** - Starting the year with a clean and repeatable setup.

**Context** - Cogitators count time from the first second of 1 January 1970, and every training run counts from epoch zero. Start the year the way the tech-priests do: a clean environment, a fresh seed, and the seed written down.

## January 2 - Rite of the Three Partitions

**Purpose** - Splitting the data into train, tune and final test parts.

**Context** - Divide the data in three before any other step: one part to train, one to tune and one kept sealed until the end. A split made after you have studied the data is already shaped by what you saw. The Magos calls that tech-heresy.

## January 3 - Vigil of the Idle Kernel

**Purpose** - Shutting down the notebook kernels you no longer use.

**Context** - An idle kernel still holds every gigabyte it was given. Before you leave tonight, shut down the kernels you no longer use. Then the other adepts can use that memory.

## January 4 - Commemoration of Saint Holdout the Untouched

**Purpose** - Remembering the saint who opened the test set only once.

**Context** - Saint Holdout kept the test set sealed for the whole project and opened it once, at the end. The tech-priests follow this example. Each extra look at the test data turns it into one more validation set.

## January 5 - Observance of the Honest Baseline

**Purpose** - Fitting the simplest possible model before the deep one.

**Context** - Before you train the deep model, fit the simplest one: predict the mean, or the majority class. No score means anything until you know what the simplest method achieves. The Magos asks for this baseline first.

## January 6 - Feast of the Descending Gradient

**Purpose** - Honouring gradient descent and its small steps downhill.

**Context** - Gradient descent finds its way downhill by small steps against the slope. Thank the Omnissiah when the loss falls, but remember that a low training loss was never the goal. The goal is a model that works on new data.

## January 7 - Rite of Device Selection

**Purpose** - Choosing the GPU before the framework starts.

**Context** - Set CUDA_VISIBLE_DEVICES first and import the framework second. A framework started without this instruction takes the first GPU it finds, even if another adept is already working there. The enginseers call this the first courtesy of the forge.

## January 8 - Litany Against Leakage

**Purpose** - Keeping test data out of every training step.

**Context** - Say this litany before every fit: no statistic from the test rows may touch the training. Scalers, imputers and encoders learn from the training partition alone and are then applied to the rest.

## January 9 - Vigil of the Learning Rate

**Purpose** - Testing three learning rates before trusting one.

**Context** - A learning rate that is too high makes the loss jump around. One that is too low makes it crawl. Tonight, try three rates, each a factor of ten apart, before you trust any one of them. The servitors do not tire, so run all three.

## January 10 - Feast of the Dot Product

**Purpose** - Understanding the dot product behind every linear layer.

**Context** - The dot product multiplies two vectors component by component and adds the results. It equals the product of their lengths and the cosine of the angle between them. Each output of a linear layer is one dot product of the input with a row of weights, plus a bias. The adepts honour it.

## January 11 - Feast of the Blessed Checkpoint

**Purpose** - Saving the full training state, not only the weights.

**Context** - A run that saves no checkpoint loses all its hours when it stops. Save the weights, the optimiser state and the step count together. A model resumed without its optimiser state does not continue the same run. The tech-priests count this a blessing.

## January 12 - Commemoration of Saint Seedra the Repeatable

**Purpose** - Remembering the saint who fixed every random seed.

**Context** - Saint Seedra fixed the seed of every generator: Python's, the array library's and the framework's. Her results came back unchanged every morning. In her memory the tech-priests seed all three, because one unseeded generator is enough to undo the others.

## January 13 - Observance of the Steady and the Boastful

**Purpose** - Checking whether a model's probabilities can be trusted.

**Context** - Logistic regression is usually well calibrated, because it is trained on the log loss. Deep networks are often overconfident: they say 99 percent and are right far less often. Check the calibration before a probability drives a decision, as the tech-priests do.

## January 14 - Observance of the Added Variances

**Purpose** - Adding variances, not standard deviations.

**Context** - For independent quantities the variances add; the standard deviations do not. Two independent errors with standard deviations 3 and 4 combine to 5, not 7. An enginseer who adds the standard deviations commits tech-heresy.

## January 15 - Feast of the Mean and the Median

**Purpose** - Reporting both mean and median when the data is skewed.

**Context** - Two servitors measure the centre of the same data and disagree. When a few very large values pull the mean far from the median, report both. Then the reader can see the skew.

## January 16 - Vigil of the Vanishing Gradient

**Purpose** - Spotting gradients that shrink in a deep network.

**Context** - In a deep network the gradient can shrink layer by layer until the earliest weights receive almost no signal. Residual connections, careful initialisation and normalisation help against this. The enginseers keep watch for it.

## January 17 - Observance of the Squared Coefficient

**Purpose** - Squaring a correlation to see how much it explains.

**Context** - A correlation of 0.5 sounds strong, but squared it is 0.25. In a linear fit, one variable then explains a quarter of the variance of the other. Square the coefficient before you judge. The Magos squares every coefficient before nodding.

## January 18 - Saint Pinnia, Martyr of Unpinned Dependencies

**Purpose** - Remembering the adept who asked for the 'latest' version.

**Context** - Pinnia installed the latest version of everything, and one morning nothing ran. In her memory the tech-priests pin every dependency to an exact version and commit the lock file beside the code.

## January 19 - Observance of the Confidence Interval

**Purpose** - Reporting an interval beside every estimate.

**Context** - A single number without an interval hides how uncertain it is. A 95 percent interval comes from a procedure that captures the true value in about 95 of 100 repetitions. The Magos wants one beside every estimate.

## January 20 - Feast of the Sacred Embedding

**Purpose** - Honouring embeddings and knowing which ones can be compared.

**Context** - An embedding turns words into vectors, so that nearness in space stands for nearness in meaning. Compare only vectors made by the same model, because two models share no common space. Mixing them is tech-heresy.

## January 21 - Rite of the Morning Census

**Purpose** - Checking who uses the GPUs before you start work.

**Context** - Begin the shift with nvidia-smi. It lists the three GPUs of BEHEMOTH, the memory each one has in use and the processes holding it. Know who works where before you add your own load. The enginseers do this every morning.

## January 22 - Vigil of the Lone Outlier

**Purpose** - Investigating an outlier before deleting it.

**Context** - One reading stands far from the rest. Do not delete it at once. First find out whether it is a broken sensor, a typing error or the most important observation in the whole set. The servo-skulls cannot tell you which.

## January 23 - Rite of the Ordered Product

**Purpose** - Reading the shapes before multiplying matrices.

**Context** - Matrix multiplication depends on the order: A times B is in general not B times A. The shapes must chain: a matrix of m by n times one of n by p gives m by p. Read the shapes before multiplying. Every adept repeats this rite before a product.

## January 24 - Feast of the Attentive Head

**Purpose** - Remembering what attention costs as sequences grow.

**Context** - Attention lets every token weigh every other token in the sequence. The cost grows with the square of the sequence length. Be sparing with what you place in the context. The acolytes learn this before they learn anything else about transformers.

## January 25 - Rite of the Channel Order

**Purpose** - Checking the shape and colour order of images before training.

**Context** - Most image libraries hold an image as height, width, channels, but PyTorch models expect channels first. OpenCV loads colour as BGR, not RGB. Check the shape and the channel order before training, because swapped colours raise no error. The servo-skulls cannot see the swap.

## January 26 - Commemoration of Saint Nulla the Sceptic

**Purpose** - Remembering what a p-value does and does not say.

**Context** - Saint Nulla taught that a p-value is the chance of data at least this extreme if the null hypothesis holds, and nothing more. It is not the probability that your hypothesis is true. The tech-priests repeat this when a colleague misreads one.

## January 27 - Observance of the Scaled Feature

**Purpose** - Scaling features before methods that use distances or gradients.

**Context** - A column in millimetres outweighs a column in kilometres. Scale the features before any method that relies on distances or on gradient descent. The machine spirit hears only the loudest column.

## January 28 - Vigil of the Full Disk

**Purpose** - Checking the free disk space before a long job.

**Context** - The enginseers run df -h before every long job. A run that dies at hour nine because the disk is full is a preventable loss. So is a disk full of checkpoints that nobody will ever load, which the tech-priests count as hoarding.

## January 29 - Feast of the Batch

**Purpose** - Choosing a batch size that the card can hold.

**Context** - Larger batches give smoother gradient estimates and fill more memory. Smaller batches are noisier and often generalise as well. Choose the size the card can hold, then tune the learning rate to match. The adepts who skip that step regret it.

## January 30 - Rite of the Tokeniser

**Purpose** - Using the tokeniser that the model was trained with.

**Context** - The model never reads your words, only the tokens the tokeniser cuts them into. Use the tokeniser the model was trained with. Any other one feeds the model scrap-code that it has never seen.

## January 31 - Vigil of the Rare Fault

**Purpose** - Learning what normal looks like when anomalies are rare.

**Context** - Anomalies are rare, and labelled anomalies are rarer. So anomaly detection often learns what normal looks like from normal data alone, and flags what does not fit. The servitors learn the normal and report the rest.

