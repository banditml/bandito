from sklearn.metrics import accuracy_score, log_loss, mean_squared_error, roc_auc_score
from sklearn.model_selection import train_test_split
from skorch import dataset, NeuralNetClassifier, NeuralNetRegressor
import torch

from utils import utils

logger = utils.get_logger(__name__)


def fit_custom_pytorch_module_w_skorch(
    reward_type, model, X, y, hyperparams, train_percent=0.8
):
    """Fit a custom PyTorch module using Skorch."""
    logger.info(f"Model input dimension: {model.layers[0].in_features}")

    if reward_type == "regression":
        skorch_func = NeuralNetRegressor
    else:
        skorch_func = NeuralNetClassifier
        # torch's nll_loss wants 1-dim tensors & long type tensors.
        y = y.long().squeeze()

    skorch_net = skorch_func(
        module=model,
        optimizer=torch.optim.Adam,
        lr=hyperparams["learning_rate"],
        optimizer__weight_decay=hyperparams["l2_decay"],
        max_epochs=hyperparams["max_epochs"],
        batch_size=hyperparams["batch_size"],
        iterator_train__shuffle=True,
        train_split=dataset.CVSplit(1 - train_percent),
    )

    skorch_net.fit(X, y)
    return skorch_net


def fit_sklearn_model(reward_type, model, X, y, train_percent=0.8):
    X = X["X_float"]
    logger.info(f"Model input dimension: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=(1 - train_percent)
    )
    model.fit(X_train, y_train)
    training_stats = {}

    if reward_type == "regression":
        mse_train = mean_squared_error(y_train, model.predict(X_train))
        mse_test = mean_squared_error(y_test, model.predict(X_test))
        logger.info(utils.color_text(f"Training MSE: {mse_train}", color="blue"))
        logger.info(utils.color_text(f"Test MSE: {mse_test}", color="green"))
        training_stats["mse_train"] = mse_train
        training_stats["mse_test"] = mse_test
    else:
        acc_train = accuracy_score(y_train, model.predict(X_train))
        acc_test = accuracy_score(y_test, model.predict(X_test))
        roc_train = roc_auc_score(y_train, model.predict(X_train))
        roc_test = roc_auc_score(y_test, model.predict(X_test))
        lloss_train = log_loss(y_train, model.predict_proba(X_train))
        lloss_test = log_loss(y_test, model.predict_proba(X_test))
        logger.info(utils.color_text(f"Training accuracy: {acc_train}", color="blue"))
        logger.info(utils.color_text(f"Test accuracy: {acc_test}", color="green"))
        logger.info(utils.color_text(f"Training log loss: {lloss_train}", color="blue"))
        logger.info(utils.color_text(f"Test log loss: {lloss_test}", color="green"))
        logger.info(utils.color_text(f"Train ROC AUC: {roc_train}", color="blue"))
        logger.info(utils.color_text(f"Test ROC AUC: {roc_test}", color="green"))
        training_stats["acc_train"] = acc_train
        training_stats["acc_test"] = acc_test
        training_stats["roc_train"] = roc_train
        training_stats["roc_test"] = roc_test
        training_stats["lloss_train"] = lloss_train
        training_stats["lloss_test"] = lloss_test

    return model, training_stats
