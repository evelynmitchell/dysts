"""
Metrics for comparing two time series. These metrics are included to faciliate
benchmarking of the algorithms in this package while reducing dependencies.

For more exhaustive sets of metrics, use the external `tslearn`, `darts`, or `sktime`
libraries.
"""

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import (
    kendalltau,
    multivariate_normal,
    pearsonr,
    spearmanr,
)

from .utils import has_module

if has_module("sklearn"):
    from sklearn.feature_selection import mutual_info_regression


def are_broadcastable(shape1, shape2):
    """
    Check if two numpy arrays are broadcastable.
    """
    # Reverse the shapes to align dimensions from the end
    shape1, shape2 = shape1[::-1], shape2[::-1]
    # Iterate over the dimensions
    for dim1, dim2 in zip(shape1, shape2):
        if dim1 != dim2 and dim1 != 1 and dim2 != 1:
            return False
    return True


def calculate_season_error(y_past, m, time_dim=-1):
    """
    Calculate the mean absolute error between the forward and backward slices of the
    past data.
    """
    assert (
        0 < m < y_past.shape[time_dim]
    ), "Season length must be less than the length of the training data"
    yt_forward = np.take(y_past, range(m, y_past.shape[time_dim]), axis=time_dim)
    yt_backward = np.take(y_past, range(y_past.shape[time_dim] - m), axis=time_dim)
    return np.mean(np.abs(yt_forward - yt_backward))


def dtw(y_true, y_pred):
    """
    Compute the Dynamic Time Warping (DTW) distance between two time series.

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The DTW distance
    """

    y_true, y_pred = np.array(y_true), np.array(y_pred)

    # check inputs
    if np.ndim(y_true) > 2:
        raise ValueError("y_true must be at most 2 dimensional.")
    if np.ndim(y_pred) > 2:
        raise ValueError("y_pred must be at most dimensional.")

    if np.ndim(y_true) == 1:
        y_true = y_true[:, None]
    if np.ndim(y_pred) == 1:
        y_pred = y_pred[:, None]

    # get lengths of each series
    n, m = len(y_true), len(y_pred)

    # allocate cost matrix
    D = np.zeros((n + 1, m + 1))
    D[0, 1:] = np.inf
    D[1:, 0] = np.inf

    # compute cost matrix
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i, j] = cdist([y_true[i - 1]], [y_pred[j - 1]], metric="euclidean")
            D[i, j] += min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])

    # compute DTW
    cost = D[-1, -1] / sum(D.shape)
    #  compute aligned series
    i, j = np.array(D.shape) - 1
    p, q = [i], [j]
    while (i > 0) and (j > 0):
        tb = np.argmin((D[i, j - 1], D[i - 1, j], D[i - 1, j - 1]))
        if tb == 0:
            i = i
            j = j - 1
        elif tb == 1:
            i = i - 1
            j = j
        else:
            i = i - 1
            j = j - 1
        p.insert(0, i)
        q.insert(0, j)

    return cost, D, p, q


def wape(y_true, y_pred):
    """
    Weighted Absolute Percentage Error

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The WAPE
    """
    return 100 * np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))


def mse(y_true, y_pred):
    """
    Mean Squared Error

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The MSE
    """
    return np.mean(np.square(y_true - y_pred))


def rmse(x, y):
    """
    Root Mean Squared Error

    Args:
        x (np.ndarray): The true values
        y (np.ndarray): The predicted values

    Returns:
        float: The RMSE
    """
    return np.sqrt(mse(x, y))


def mae(y_true, y_pred):
    """
    Mean Absolute Error

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The MAE
    """
    return np.mean(np.abs(y_true - y_pred))


def coefficient_of_variation(y_true, y_pred):
    """
    Coefficient of Variation of the root mean squared error relative to the mean
    of the true values

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The Coefficient of Variation
    """
    return 100 * np.std(y_true - y_pred) / np.mean(y_true)


def marre(y_true, y_pred):
    """
    Mean Absolute Ranged Relative Error

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The MARRE
    """
    return 100 * np.mean(np.abs(y_true - y_pred) / (np.max(y_true) - np.min(y_true)))


def ope(y_true, y_pred):
    """
    Optimality Percentage Error

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The OPE
    """
    return np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true - np.mean(y_true)))


def rmsle(y_true, y_pred):
    """
    Root Mean Squared Log Error. In case of negative values, the series is shifted
    to the positive domain.

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The RMSLE
    """
    y_true = y_true - np.min(y_true, axis=0, keepdims=True) + 1e-8
    y_pred = y_pred - np.min(y_pred, axis=0, keepdims=True) + 1e-8
    return np.sqrt(np.mean(np.square(np.log(y_pred + 1) - np.log(y_true + 1))))


def r2_score(y_true, y_pred):
    """
    The R2 Score

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The R2 Score
    """
    return 1 - np.sum(np.square(y_true - y_pred)) / np.sum(
        np.square(y_true - np.mean(y_true))
    )


def mape(y_true, y_pred):
    """
    The Mean Absolute Percentage Error

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values

    Returns:
        float: The MAPE
    """
    return 100 * np.mean(np.abs(y_true - y_pred) / y_true)


def smape(x, y):
    """Symmetric mean absolute percentage error"""
    return 100 * np.mean(np.abs(x - y) / (np.abs(x) + np.abs(y))) * 2


def mase(y, yhat, y_train=None, m=1, time_dim=-1):
    """
    The mean absolute scaled error.

    Adapted from tensorflow-probability and
    https://en.wikipedia.org/wiki/Mean_absolute_scaled_error

    Args:
        y (ndarray): The true values.
        yhat (ndarray): The predicted values.
        y_train (ndarray): The training values.
        m (int): The season length, which is the number of time steps that are
            skipped when computing the denominator. Default is 1.
        time_dim (int): The dimension of the time series. Default is -1.

    Returns:
        mase_val (float): The MASE error
    """
    if y_train is None:
        y_train = y.copy()

    assert are_broadcastable(yhat.shape, y_train.shape)
    assert are_broadcastable(y.shape, y_train.shape)

    season_error = calculate_season_error(y_train, m, time_dim)
    return np.mean(np.abs(y - yhat)) / season_error


def msis(y, yhat_lower, yhat_upper, y_obs, m, time_dim=-1, a=0.05):
    """The mean scaled interval score.

    Adapted from tensorflow-probability and
    https://www.uber.com/blog/m4-forecasting-competition/

    Args:
      y (np.ndarray): An array containing the true values.
      yhat_lower: An array containing the a% quantile of the predicted
        distribution.
      yhat_upper: An array containing the (1-a)% quantile of the
        predicted distribution.
      y_obs: An array containing the training values.
      m: The season length.
      a: A scalar in [0, 1] specifying the quantile window to evaluate.

    Returns:
      The scalar MSIS.
    """
    assert are_broadcastable(yhat_lower.shape, y.shape)
    assert are_broadcastable(yhat_upper.shape, y.shape)

    numer = np.mean(
        (yhat_upper - yhat_lower)
        + (2 / a) * (yhat_lower - y) * (y < yhat_lower)
        + (2 / a) * (y - yhat_upper) * (yhat_upper < y)
    )
    season_error = calculate_season_error(y_obs, m, time_dim)
    return numer / season_error


def spearman(y_true, y_pred):
    """
    Spearman Correlation. Returns dimensionwise mean for multivariate time series of
    shape (T, D)
    """
    y_true, y_pred = np.array(y_true).squeeze(), np.array(y_pred).squeeze()
    if y_true.ndim != y_pred.ndim:
        raise ValueError("y_true and y_pred must have the same number of dimensions")

    if y_true.ndim == 1:
        return spearmanr(y_true, y_pred)[0]

    else:
        all_vals = []
        for i in range(y_true.shape[1]):
            all_vals.append(spearmanr(y_true[:, i], y_pred[:, i])[0])
        return np.mean(all_vals)


def pearson(y_true, y_pred):
    """
    Pearson Correlation. Returns dimensionwise mean for multivariate time series of
    shape (T, D)
    """
    y_true, y_pred = np.array(y_true).squeeze(), np.array(y_pred).squeeze()
    if y_true.ndim != y_pred.ndim:
        raise ValueError("y_true and y_pred must have the same number of dimensions")

    if y_true.ndim == 1:
        return spearmanr(y_true, y_pred)[0]

    else:
        all_vals = []
        for i in range(y_true.shape[1]):
            all_vals.append(pearsonr(y_true[:, i], y_pred[:, i])[0])
        return np.mean(all_vals)


def kendall(y_true, y_pred):
    """
    Kendall-Tau Correlation. Returns dimensionwise mean for multivariate time series of
    shape (T, D)
    """
    y_true, y_pred = np.array(y_true).squeeze(), np.array(y_pred).squeeze()
    if y_true.ndim != y_pred.ndim:
        raise ValueError("y_true and y_pred must have the same number of dimensions")

    if y_true.ndim == 1:
        return kendalltau(y_true, y_pred)[0]

    else:
        all_vals = []
        for i in range(y_true.shape[1]):
            all_vals.append(kendalltau(y_true[:, i], y_pred[:, i])[0])
        return np.mean(all_vals)


def mutual_information(y_true, y_pred):
    """
    Mutual Information. Returns dimensionwise mean for multivariate time series of
    shape (T, D). Computes the mutual information separately for each dimension and
    returns the mean.
    """
    if not has_module("sklearn"):
        raise ImportError("Sklearn is required for mutual information")
    mi = np.zeros(y_true.shape[1])
    for i in range(y_true.shape[1]):
        mi[i] = mutual_info_regression(
            y_true[:, i].reshape(-1, 1), y_pred[:, i].ravel()
        )
    return np.mean(mi)


def nrmse(y_true, y_pred, eps=1e-8, scale=None):
    """
    Normalized Root Mean Squared Error

    Args:
        y_true (np.ndarray): True values of shape (T, D)
        y_pred (np.ndarray): Predicted values of shape (T, D)
        eps (float): Small value to avoid division by zero
        scale (np.ndarray): Standard deviation of the true values of shape (D,). If None,
            the standard deviation is computed from the true values.

    Returns:
        float: NRMSE
    """
    if scale is None:
        sigma = np.std(y_true, axis=0)  # D
    else:
        sigma = scale
    vals = (y_true - y_pred) ** 2 / (sigma**2 + eps)  # T x D
    return np.sqrt(np.mean(vals))  # Flatten along both dimensions


def horizoned_metric(y_true, y_pred, metric, *args, horizon=None, **kwargs):
    """
    Compute a metric over a range of horizons

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values
        metric (callable): The metric function
        *args: Additional arguments to pass to the metric function
        horizon (int): The maximum horizon to compute the metric over. If None, the
            horizon is set to the length of the time series
        **kwargs: Additional keyword arguments to pass to the metric function

    Returns:
        np.ndarray: The metric values at each horizon
    """
    if horizon is None:
        horizon = len(y_true)
    return [
        metric(y_true[: i + 1], y_pred[: i + 1], *args, **kwargs)
        for i in range(horizon)
    ]


class GaussianMixture:
    """
    A Gaussian Mixture Model class.

    Args:
        means (list): A list of means for each component of the GMM.
        covariances (list): A list of covariance matrices for each component of the GMM.
        weights (list): A list of weights for each component of the GMM.

    Attributes:
        means (np.ndarray): An array of means for each component of the GMM.
        covariances (np.ndarray): An array of covariance matrices for each component of the GMM.
        weights (np.ndarray): An array of weights for each component of the GMM.
        n_components (int): The number of components in the GMM.
        gaussians (list): A list of multivariate_normal objects, one for each component
    """

    def __init__(self, means, covariances, weights=None):
        self.means = np.array(means)
        self.covariances = np.array(covariances)
        self.n_components, self.ndim = self.means.shape

        ## If covariances is a single scaler, assume isotropic covariance constant
        ## Otherwise if covariances is a list of scalars, assume isotropic covariance
        if isinstance(covariances, (int, float)):
            self.covariances = (
                np.ones(self.n_components)[:, None, None] * np.eye(self.ndim)[None, ...]
            ) * covariances
        elif isinstance(covariances[0], (int, float)):
            self.covariances = covariances[:, None, None] * np.eye(self.ndim)[None, ...]
        else:
            self.covariances = np.array(covariances)

        # If no weights are provided, assume uniform weights
        if weights is None:
            self.weights = np.ones(self.n_components) / self.n_components
        else:
            self.weights = np.array(weights)

        self.gaussians = [
            multivariate_normal(mean=mean, cov=cov)
            for mean, cov in zip(self.means, self.covariances)
        ]

    def __call__(self, x):
        # Vectorized computation of the Gaussian mixture probability density
        x = np.array(x)
        probs = np.array([gaussian.pdf(x) for gaussian in self.gaussians])
        return np.dot(self.weights, probs)

    def sample(self, n_samples=1):
        """
        Draw samples from the Gaussian Mixture Model.

        Args:
            n_samples (int): The number of samples to draw.

        Returns:
            samples (np.ndarray): An array of shape (n_samples, ndim) containing the drawn samples.
        """
        component_indices = np.random.choice(
            self.n_components, size=n_samples, p=self.weights
        )
        samples = np.array([self.gaussians[i].rvs() for i in component_indices])
        return samples


def estimate_kl_divergence(true_orbit, generated_orbit, n_samples=300, sigma_scale=1.0):
    """
    Estimate KL divergence between observed and generated orbits using Gaussian Mixture
    Models (GMMs).

    Args:
        observed_orbit (np.ndarray): Observed orbit points, with shape (T, N) where T is
            the number of time steps and N is the dimensionality.
        generated_orbit (np.ndarray): Generated orbit points, with shape (T, N) where T is
            the number of time steps and N is the dimensionality.
        n_samples (int): Number of Monte Carlo samples.
        sigma_squared (float): Variance parameter for the GMMs.

    Returns:
        float: Estimated KL divergence

    References:
        Hess, Florian, et al. "Generalized teacher forcing for learning chaotic
        dynamics." Proceedings of the 40th International Conference on Machine Learning.
        2023.

        Hershey, John R., and Peder A. Olsen. "Approximating the Kullback Leibler
        divergence between Gaussian mixture models." 2007 IEEE International Conference
        on Acoustics, Speech and Signal Processing-ICASSP'07. Vol. 4. IEEE, 2007.

    Development:
        Rank-order (copula) transform each orbit coordinate, in order to reduce
        sensitivity to spacing among time series.
    """
    # if the orbits are 1D, add a dimension to make them 2D
    if true_orbit.ndim == 1:
        true_orbit = true_orbit.reshape(-1, 1)
    if generated_orbit.ndim == 1:
        generated_orbit = generated_orbit.reshape(-1, 1)

    if sigma_scale is None:
        sigma_scale = np.linalg.norm(np.diff(true_orbit, axis=0), axis=1) + 1e-8
        sigma_scale = np.hstack((sigma_scale, sigma_scale[-1]))
        p_hat = GaussianMixture(true_orbit, sigma_scale)
        sigma_scale = np.linalg.norm(np.diff(generated_orbit, axis=0), axis=1) + 1e-8
        sigma_scale = np.hstack((sigma_scale, sigma_scale[-1]))
        q_hat = GaussianMixture(generated_orbit, sigma_scale)
    else:
        p_hat = GaussianMixture(true_orbit, sigma_scale)
        q_hat = GaussianMixture(generated_orbit, sigma_scale)

    # Generate Monte Carlo samples from p_hat
    T, N = true_orbit.shape
    samples = p_hat.sample(n_samples=T)

    # Randomly select n_samples from the generated samples
    selected_samples = samples[np.random.choice(T, n_samples, replace=True)]
    log_ratios = np.log(p_hat(selected_samples) / q_hat(selected_samples))
    kl_estimate = np.mean(log_ratios)

    return -kl_estimate


def hellinger_distance(p, q, axis=0):
    """Compute the Hellinger distance between two distributions."""
    return np.sqrt(1 - np.sum(np.sqrt(p * q), axis=axis))


def average_hellinger_distance(
    ts_true: np.ndarray, ts_gen: np.ndarray, num_freq_bins: int = 100
):
    """
    Compute the average Hellinger distance between power spectra of two multivariate
    time series.

    Args:
        ts_true (np.ndarray): True time series, shape (n_samples, n_dimensions).
        ts_gen (np.ndarray): Generated time series, shape (n_samples, n_dimensions).
        num_freq_bins (int): Number of frequency bins to use in FFT for power spectrum.

    Returns:
        avg_dh (np.ndarray): Average Hellinger distance across all dimensions.

    References:
        Mikhaeil et al. Advances in Neural Information Processing Systems, 35:
            11297–11312, December 2022.
    """
    d = ts_true.shape[1]
    all_dh = list()

    for i in range(d):
        f_true = np.abs(np.fft.fft(ts_true[:, i])) ** 2
        f_gen = np.abs(np.fft.fft(ts_gen[:, i])) ** 2
        f_true /= np.sum(f_true)
        f_gen /= np.sum(f_gen)
        all_dh.append(hellinger_distance(f_true[:num_freq_bins], f_gen[:num_freq_bins]))
    all_dh = np.array(all_dh)

    avg_dh = np.mean(all_dh, axis=0)

    return avg_dh


def compute_metrics(
    y_true, y_pred, time_dim=0, standardize=False, verbose=False, include=None
):
    """
    Compute multiple time series metrics

    Args:
        y_true (np.ndarray): The true values
        y_pred (np.ndarray): The predicted values
        time_dim (int): The dimension of the time axis. Default is 0.
        standardize (bool): Whether to standardize the time series before computing the
            metrics. Default is False.
        verbose (bool): Whether to print the computed metrics. Default is False.
        include (optional, list): The metrics to include. Default is None, which
            computes all metrics. Otherwise, specify a list of metrics to compute.

    Returns:
        dict: A dictionary containing the computed metrics
    """
    if standardize:
        scale_true, scale_pred = (
            np.std(y_true, axis=time_dim, keepdims=True),
            np.std(y_pred, axis=time_dim, keepdims=True),
        )
        if np.all(scale_true == 0):
            scale_true = 1
        if np.all(scale_pred == 0):
            scale_pred = 1
        y_true = (y_true - np.mean(y_true, axis=time_dim, keepdims=True)) / scale_true
        y_pred = (y_pred - np.mean(y_pred, axis=time_dim, keepdims=True)) / scale_pred

    assert are_broadcastable(
        y_true.shape, y_pred.shape
    ), "y_true and y_pred must have broadcastable shapes"

    metric_functions = {
        "mse": mse,
        "mae": mae,
        "rmse": rmse,
        "nrmse": nrmse,
        "marre": marre,
        "r2_score": r2_score,
        "rmsle": rmsle,
        "smape": smape,
        "mape": mape,
        "wape": wape,
        "spearman": spearman,
        "pearson": pearson,
        "kendall": kendall,
        "coefficient_of_variation": coefficient_of_variation,
        "mutual_information": mutual_information,
        "kl_divergence": estimate_kl_divergence,
        "hellinger_distance": hellinger_distance,
    }

    if include is None:
        include = list(metric_functions.keys())

    assert all(
        metric in metric_functions for metric in include
    ), f"Invalid metrics specified. Must be one of {list(metric_functions.keys())}"

    metrics = {
        metric: func(y_true, y_pred)
        for metric, func in metric_functions.items()
        if metric in include
    }

    if verbose:
        for key, value in metrics.items():
            print(f"{key}: {value:.4f}")

    return metrics
