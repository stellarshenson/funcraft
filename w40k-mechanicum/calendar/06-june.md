# Cult Mechanicus Liturgical Calendar - June

## June 1 - Rite of the Initial Weights

**Purpose** - Scaling the initial weights to the layer width.

**Context** - Weights that start too large make the activations explode. Weights that start too small make the signal fade to nothing. Use an initialisation scaled to the width of each layer. It keeps the variance steady from input to output. The machine spirit needs a steady start.

## June 2 - Feast of the Majority Vote

**Purpose** - Combining models that make different errors.

**Context** - An ensemble works when its members err in different ways, because their average errs less than they do. Five copies of the same mistake remain one mistake, voted five times. The Magos wants diverse members.

## June 3 - Observance of the Covariance Matrix

**Purpose** - Reading what a covariance matrix holds.

**Context** - The covariance matrix holds the variance of each feature on its diagonal and the covariance of each pair elsewhere. It is symmetric. With collinear features, or with fewer samples than features, it cannot be inverted. The enginseers check that before inverting it.

## June 4 - Vigil of the Out-of-Fold Encoding

**Purpose** - Computing target encoding out of fold.

**Context** - Target encoding replaces a category with the mean of the target for that category. Computed on the rows it will be used on, it leaks the target into the feature. Compute it out of fold: for each row, from the other folds only. The Magos calls such a leak tech-heresy.

## June 5 - Commemoration of Saint Shapela the Dimensioned

**Purpose** - Remembering the saint who printed every tensor shape.

**Context** - Saint Shapela printed the shape of every tensor before she trusted it. Broadcasting silently turns a column minus a row into a full matrix. In her memory the enginseers assert the shapes they expect.

## June 6 - Rite of the Pseudo-Random

**Purpose** - Setting the seed to repeat a random experiment.

**Context** - The cogitator's random numbers are a deterministic sequence that only looks random. The seed selects the sequence. Count this a blessing, because it lets an experiment that involves chance be repeated exactly.

## June 7 - Feast of the Cosine Similarity

**Purpose** - Comparing vectors by direction with cosine similarity.

**Context** - Cosine similarity compares the direction of two vectors and ignores their length. If your embeddings are normalised to unit length, it equals the dot product. The dot product is cheaper to compute, and the servitors prefer cheap work.

## June 8 - Observance of the Labelled Pixel

**Purpose** - Choosing between semantic and instance segmentation.

**Context** - Semantic segmentation gives every pixel a class, so two cars side by side form one 'car' region. Instance segmentation also separates the individual objects. Choose by whether the objects must be counted. The Magos asks first whether anything must be counted.

## June 9 - Vigil of the Dead Unit

**Purpose** - Recognising dead ReLU units.

**Context** - A ReLU unit whose input is negative for every example outputs zero and receives zero gradient, so it never recovers. If many units have fallen silent, lower the learning rate or use a leaky variant. Enginseers call such units dead.

## June 10 - Feast of the Three Transformers

**Purpose** - Telling encoder, decoder and encoder-decoder models apart.

**Context** - An encoder-only transformer reads the whole text in both directions and suits classification and embeddings. A decoder-only transformer predicts the next token and suits generation. An encoder-decoder transformer reads one sequence and writes another, as in translation. The cult keeps all three.

## June 11 - Feast of the Law of Large Numbers

**Purpose** - Honouring the law of large numbers.

**Context** - As the sample grows, its average converges on the true mean. The law promises nothing about small samples. Ten coin flips owe you no particular number of heads. The tech-priests hold a feast for this law.

## June 12 - Commemoration of Saint Secreta the Unspoken

**Purpose** - Keeping passwords and tokens out of notebooks.

**Context** - Saint Secreta never typed a password or a token into a notebook cell. She kept them in the environment or in a secrets store. Nothing she committed ever had to be revoked in a hurry. The tech-priests follow her.

## June 13 - Observance of the Chunked Document

**Purpose** - Testing chunk size for document retrieval.

**Context** - Documents are cut into chunks before they are embedded for retrieval. Too small, and a passage loses its meaning. Too large, and one vector must stand for many topics. Test the size against real questions, as the adepts do.

## June 14 - Rite of the Class Weight

**Purpose** - Weighting the rare class in the loss.

**Context** - When the rare class matters most, weight its errors more heavily in the loss, or resample the training set. Resample the training partition only. Validation and test must keep the true proportions. The Magos checks this.

## June 15 - Vigil of the Held-Out Calibration

**Purpose** - Fitting a calibrator on data the model has not seen.

**Context** - Fit a calibrator on data the model was not trained on. On its training data the model looks better than it is, so a calibrator fitted there learns the wrong correction. Check the calibration again when the input data shifts, as the tech-priests do.

## June 16 - Feast of the Logistic Curve

**Purpose** - Explaining a logistic regression through log-odds.

**Context** - Logistic regression passes a weighted sum through a sigmoid and returns a probability. Each coefficient is a change in log-odds. This makes it one of the few models you can explain line by line to a sceptical Magos.

## June 17 - Observance of the Repeated Run

**Purpose** - Training with several seeds and reporting the spread.

**Context** - One run is one draw from a distribution. Train with several seeds and report the mean and the spread. A gain smaller than the run-to-run variation is not yet a gain. No adept should celebrate it.

## June 18 - Rite of the Alert Budget

**Purpose** - Setting the alert threshold by what the team can inspect.

**Context** - An anomaly detector returns a score, and the threshold decides how many alerts are raised. Set it from the number of alerts the team can inspect each day. Then measure how many of the top alerts were real. The servo-skulls raise the alerts and the adepts inspect them.

## June 19 - Feast of the Distilled Model

**Purpose** - Distilling a large model into a small one.

**Context** - Train a small student to imitate the outputs of a large teacher, and it keeps much of the skill at a fraction of the cost. The teacher's full probability distribution teaches more than its top answer alone. The Magos teaches, the acolyte learns.

## June 20 - Feast of the Adjacency Matrix

**Purpose** - Writing a graph as an adjacency matrix.

**Context** - A graph of n nodes can be written as an n by n adjacency matrix. Entry i, j is 1 when an edge joins node i to node j. The k-th power of this matrix counts the walks of length k between every pair of nodes. The cogitators prefer graphs in this form.

## June 21 - Observance of the Honest Stopwatch

**Purpose** - Timing GPU code with warm-up and synchronisation.

**Context** - GPU operations are asynchronous, so a call returns before the work is done. To time them honestly, run a few warm-up iterations first. Then synchronise the device before you read the clock. Enginseers time no other way.

## June 22 - Commemoration of Saint Conditia the Well-Conditioned

**Purpose** - Remembering the saint who checked the condition number first.

**Context** - The condition number of a matrix is the ratio of its largest to its smallest singular value. Conditia computed it before solving: a large one turns small errors in the input into large errors in the answer. A condition number of 10 to the power 8 costs about 8 decimal digits. The tech-priests do likewise.

## June 23 - Rite of the Control Group

**Purpose** - Randomising subjects into treatment and control.

**Context** - Assign subjects to treatment and control by chance alone. Then every confounder, known or unknown, is balanced on average. No adjustment made afterwards gives the same guarantee. The Magos demands this rite.

## June 24 - Feast of the Low-Rank Adapter

**Purpose** - Training a low-rank adapter beside frozen weights.

**Context** - A low-rank adapter leaves the pretrained weights frozen and trains two small matrices beside them. It is a tiny fraction of the model's size. One base model can use many adapters in turn, and its machine spirit stays untouched.

## June 25 - Vigil of the Unread Log

**Purpose** - Reading the last lines of a long job's log.

**Context** - Tonight, read the last hundred lines of your longest-running job. A log that nobody reads is only a slow way of filling the disk. A warning you have learned to ignore is still a warning. The servo-skulls write it, so the adepts must read it.

## June 26 - Observance of the Skewed Column

**Purpose** - Taking the logarithm of a skewed column.

**Context** - Values that span several orders of magnitude crowd against one edge of a linear scale. Take the logarithm. Multiplicative structure becomes additive, the plot becomes readable and many models behave better. The tech-priests do this often.

## June 27 - Observance of the Curved Sheet

**Purpose** - Using a non-linear method for data on a curved surface.

**Context** - PCA finds straight directions only. Data that lies on a curved surface, such as a spiral, is not unrolled by it. Use a non-linear method there: kernel PCA, UMAP or an autoencoder. The Magos does not force a straight line on a curve.

## June 28 - Feast of the Full Turn

**Purpose** - Encoding hours and weekdays as sine and cosine.

**Context** - Sixth month, twenty-eighth day: 6.28, about two pi, the radians in one full turn. Encode hours, weekdays and months as the sine and cosine of their angle. Then 23:00 sits beside midnight, as the cogitator needs.

## June 29 - Rite of the Power Iteration

**Purpose** - Finding the dominant eigenvector by power iteration.

**Context** - Power iteration finds the dominant eigenvector of a matrix: multiply a vector by the matrix, normalise it and repeat. It converges fast when the largest eigenvalue is well separated from the second. It converges slowly when the two are close. The servitors repeat the multiplication like a litany.

## June 30 - Observance of the Silhouette

**Purpose** - Reading the silhouette score of each clustered point.

**Context** - The silhouette score compares, for each point, the distance to its own cluster with the distance to the nearest other cluster. Near 1 means well placed, near 0 means on a border, and negative means probably in the wrong cluster. The cogitator scores every point.
