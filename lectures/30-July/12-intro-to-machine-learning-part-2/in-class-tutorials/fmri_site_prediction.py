# # Predicting site from fMRI: cross-validation and dimensionality reduction.
#
# Here we consider the same data and prediction task as in the tutorial of
# Machine Learning part 1 of the QLS course.
#
# We have some fMRI time series, that we use to compute a connectivity matrix
# for each participant. We use the connectivity matrix values as our input
# features to predict to which site the participant belongs.
#
# As in Part 1, we classify participants using a logistic regression. However
# we make several additions.
#
# ## Pipeline
#
# We use scikit-learn's `sklearn.pipeline.Pipeline`, that enables chaining
# several transformations into a single scikit-learn estimator (an object with
# a `fit` method). This avoids dealing with the connectivity feature extraction
# separately and ensures everything is fitted on the training data only --
# which is crucial here because we will add a dimensionality reduction step
# with Principal Component Analysis.
#
# ## Dimensionality Reduction
#
# We also consider a pipeline that reduces the dimension of input features with
# PCA, and compare it to the baseline logistic regrssion. One advantage is that
# the pipeline that uses PCA can be fitted much faster.
#
# ## Cross-validation
#
# In part 1 we fitted one model and evaluated it on a held-out test set. Here,
# we will use scikit-learn's `cross_validate` to perform K-Fold
# cross-validation and get a better estimate of our model's generalization
# performance. This allows comparing logistic regression with and without PCA,
# as well as a naive baseline.
#
# Moreover, instead of the plain `LogisticRegression`, we use scikit-learn's
# `LogisticRegressionCV`, which automatically performs a nested
# cross-validation loop on the training data to select the best hyperparameter.
#
# We therefore obtain a typical supervised learning experiment, with learning
# pipelines that involve chained transformations, hyperparameter selection, a
# cross-validation, and comparison of several models and a baseline.
#
# ## Exercises
#
# Read, understand and run this script. `load_connectivity_data` loads the data
# and returns the matrices `X` and `y`. `prepare_pipelines` returns a
# dictionary whose values are scikit-learn estimators and whose keys are names
# for each estimator. All estimators are instances of scikit-learn's
# `Pipeline`, and the first step is always connectivity feature extraction with
# nilearn's `ConnectivityMeasure`.
#
# At the moment `prepare_pipelines` only returns 2 estimators: the logistic
# regression and a dummy estimator. Add a third estimator in the returned
# dictionary, which contains a dimensionality reduction step: a PCA with 20
# components. To do so, add a `sklearn.decomposition.PCA` as the second step of
# the pipeline.
#
# Once we have compared our 3 models (logistic, logistic with PCA and
# baseline), we can select the one that performs best according to our
# cross-validation. Is its cross-validation score a good estimate of how it
# would perform on new data?
#
# There are 111 regions in the atlas we use to compute region-region
# connectivity matrices: the output of the `ConnectivityMeasure` has
# 111 * (111 # + 1) / 2 = 6216 columns.
# What is the size of the coefficients of the logistic regression? of the
# principal components? of the output of the PCA?
#
# As you can see, in this script we do not specify explicitly the metric
# functions that are used to evaluate models, but rely on scikit-learn's
# defaults instead. What metric is used in order to select the best
# hyperparameter? What metric is used to compute scores in `cross_validate`?
# Are these defaults appropriate for our particular situation? Try replacing
# the default metrics with other scoring functions from scikit-learn or
# functions that you write yourself. Does the relative performance of the
# models change?
#
# Add another estimator to the options returned by `prepare_pipelines`, that
# uses univariate feature selection instead of PCA.


from nilearn import datasets
from nilearn.connectome import ConnectivityMeasure

from sklearn import preprocessing
from sklearn.model_selection import cross_validate
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegressionCV
from sklearn.dummy import DummyClassifier

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns


def load_timeseries_and_site(n_subjects=100):
    """Load ABIDE timeseries and participants' site.

    Returns X, a list with one array of shape (n_samples, n_rois) per
    participant, and y, an array of length n_participants containing integers
    representing the site each participant belongs to.

    """
    data = datasets.fetch_abide_pcp(
        n_subjects=n_subjects, derivatives=["rois_ho"]
    )
    X = data["rois_ho"]
    y = preprocessing.LabelEncoder().fit_transform(
        data["phenotypic"]["SITE_ID"]
    )
    return X, y


def prepare_pipelines():
    """Prepare scikit-learn pipelines for fmri classification with connectivity.

    Returns a dictionary where each value is a scikit-learn estimator (a
    `Pipeline`) and the corresponding key is a descriptive string for that
    estimator.

    As an exercise you need to add a pipeline that performs dimensionality
    reduction with PCA.

    """
    logistic_reg = Pipeline(
        [
            (
                "feature_extraction",
                ConnectivityMeasure(kind="correlation", vectorize=True),
            ),
            ("logistic", LogisticRegressionCV(solver="liblinear")),
        ]
    )
    dummy = Pipeline(
        [
            (
                "feature_extraction",
                ConnectivityMeasure(kind="correlation", vectorize=True),
            ),
            ("classif", DummyClassifier()),
        ]
    )
    # TODO: add a pipeline with a PCA dimensionality reduction step to this
    # dictionary. You will need to import `sklearn.decomposition.PCA`.
    return {
        "Logistic no PCA": logistic_reg,
        "Dummy": dummy,
    }


def compute_cv_scores(models, X, y):
    """Compute cross-validation scores for all models

    `models` is a dictionary like the one returned by `prepare_pipelines`, ie
    of the form `{"model_name": estimator}`, where `estimator` is a
    scikit-learn estimator.

    `X` and `y` are the design matrix and the outputs to predict.

    Returns a `pd.DataFrame` with one row for each model and cross-validation
    fold. Columns include `test_score` and `fit_time`.

    """
    all_scores = []
    for model_name, model in models.items():
        print(f"Computing scores for model: '{model_name}'")
        model_scores = pd.DataFrame(cross_validate(model, X, y))
        model_scores["model"] = model_name
        all_scores.append(model_scores)
    all_scores = pd.concat(all_scores)
    return all_scores


if __name__ == "__main__":
    X, y = load_timeseries_and_site()
    models = prepare_pipelines()
    all_scores = compute_cv_scores(models, X, y)
    print(all_scores.groupby("model").mean())
    sns.stripplot(data=all_scores, x="test_score", y="model")
    plt.tight_layout()
    plt.show()
