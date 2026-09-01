"""
ARE ML Trainer -- Learning from Every Trade
=============================================
Every trade outcome is recorded. ML learns from history.
Over time, the model gets better at predicting wins/losses.

Architecture:
  Trade completes --> Log outcome --> Train model --> Predict next signal
                                    (weekly)        (real-time)

The model learns:
- Which RSI combinations lead to wins
- Which time-of-day is most profitable
- Which market conditions favor BUY vs SELL
- When to HOLD instead of trade

Usage:
    trainer = MLTrainer()
    trainer.record_trade(signal_data, outcome)
    trainer.train()  # Retrain model
    prediction = trainer.predict(new_signal)
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np


class MLTrainer:
    """
    Learns from trade history. Predicts win probability for new signals.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data", "autopilot"
            )
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.trades_file = os.path.join(data_dir, "ml_trades.jsonl")
        self.model_file = os.path.join(data_dir, "ml_model.json")
        self._model = None
        self._feature_names = [
            "rsi_d1", "rsi_h4", "rsi_h1", "rsi_m30", "rsi_m15", "rsi_m5", "rsi_m1",
            "hour_utc", "day_of_week",
            "spread", "atr_ratio",
            "macro_agree", "compass_direction",
        ]

    def record_trade(self, signal_data: dict, outcome: dict):
        """
        Record a completed trade for ML training.

        signal_data: RSI values, indicators at time of entry
        outcome: {pnl, win, hold_time, exit_reason}
        """
        entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "signal": signal_data,
            "outcome": outcome,
        }
        with open(self.trades_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def load_trades(self) -> List[dict]:
        """Load all recorded trades."""
        if not os.path.exists(self.trades_file):
            return []
        trades = []
        with open(self.trades_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        trades.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return trades

    def _extract_features(self, signal: dict) -> Optional[List[float]]:
        """Extract ML features from signal data."""
        rsi = signal.get("rsi", {})
        features = []

        # RSI values (7 features)
        for tf in ["D1", "H4", "H1", "M30", "M15", "M5", "M1"]:
            features.append(rsi.get(tf, 50.0))

        # Time features (2 features)
        now = datetime.now(timezone.utc)
        features.append(now.hour)
        features.append(now.weekday())

        # Spread (1 feature)
        features.append(signal.get("spread", 20.0))

        # ATR ratio (1 feature)
        features.append(signal.get("atr_ratio", 1.0))

        # Macro agreement (1 feature)
        d1 = rsi.get("D1", 50)
        h4 = rsi.get("H4", 50)
        features.append(1.0 if (d1 > 50 and h4 > 50) or (d1 < 50 and h4 < 50) else 0.0)

        # Compass direction (1 feature)
        h1 = rsi.get("H1", 50)
        features.append(1.0 if h1 > 50 else -1.0 if h1 < 50 else 0.0)

        return features

    def train(self) -> dict:
        """
        Train ML model on recorded trades.
        Returns training report.
        """
        trades = self.load_trades()
        if len(trades) < 10:
            return {"status": "insufficient_data", "trades": len(trades), "min_needed": 10}

        # Extract features and labels
        X = []
        y = []
        for trade in trades:
            features = self._extract_features(trade.get("signal", {}))
            if features is None:
                continue
            won = trade.get("outcome", {}).get("win", False)
            X.append(features)
            y.append(1 if won else 0)

        if len(X) < 10:
            return {"status": "insufficient_features", "samples": len(X)}

        X = np.array(X)
        y = np.array(y)

        # Simple ensemble: weighted average of feature importances
        # (No sklearn dependency -- pure numpy)
        model = self._train_simple(X, y)

        # Evaluate
        predictions = self._predict_raw(X, model)
        correct = sum(1 for p, t in zip(predictions, y) if (p > 0.5) == (t == 1))
        accuracy = correct / len(y) if len(y) > 0 else 0

        # Win rate by RSI zone
        win_rates = {}
        for trade in trades:
            rsi_m5 = trade.get("signal", {}).get("rsi", {}).get("M5", 50)
            zone = "oversold" if rsi_m5 < 30 else "overbought" if rsi_m5 > 70 else "neutral"
            if zone not in win_rates:
                win_rates[zone] = {"wins": 0, "total": 0}
            win_rates[zone]["total"] += 1
            if trade.get("outcome", {}).get("win", False):
                win_rates[zone]["wins"] += 1

        for zone in win_rates:
            wr = win_rates[zone]
            wr["win_rate"] = wr["wins"] / wr["total"] if wr["total"] > 0 else 0

        # Save model
        self._model = model
        self._save_model(model, accuracy, len(X))

        report = {
            "status": "trained",
            "samples": len(X),
            "accuracy": round(accuracy, 4),
            "win_rates_by_zone": win_rates,
            "total_trades": len(trades),
            "feature_importance": dict(zip(self._feature_names,
                                          [round(float(x), 4) for x in model.get("weights", [])])),
        }
        return report

    def _train_simple(self, X: np.ndarray, y: np.ndarray) -> dict:
        """
        Train a simple linear model (logistic regression approximation).
        No sklearn dependency -- pure numpy.
        """
        # Normalize features
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std[std == 0] = 1  # Avoid division by zero
        X_norm = (X - mean) / std

        # Simple gradient descent logistic regression
        n_features = X_norm.shape[1]
        weights = np.zeros(n_features)
        bias = 0.0
        lr = 0.01
        epochs = 100

        for _ in range(epochs):
            # Forward pass
            z = X_norm @ weights + bias
            pred = 1 / (1 + np.exp(-np.clip(z, -500, 500)))

            # Loss gradient
            error = pred - y
            dw = (X_norm.T @ error) / len(y)
            db = error.mean()

            # Update
            weights -= lr * dw
            bias -= lr * db

        return {
            "weights": weights.tolist(),
            "bias": float(bias),
            "mean": mean.tolist(),
            "std": std.tolist(),
            "feature_names": self._feature_names,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "n_samples": len(y),
        }

    def _predict_raw(self, X: np.ndarray, model: dict) -> List[float]:
        """Raw predictions from model."""
        mean = np.array(model["mean"])
        std = np.array(model["std"])
        weights = np.array(model["weights"])
        bias = model["bias"]

        X_norm = (X - mean) / std
        z = X_norm @ weights + bias
        return (1 / (1 + np.exp(-np.clip(z, -500, 500)))).tolist()

    def predict(self, signal_data: dict) -> dict:
        """
        Predict win probability for a new signal.
        Returns: {probability, confidence, recommendation}
        """
        if self._model is None:
            self._model = self._load_model()

        if self._model is None:
            return {
                "probability": 0.5,
                "confidence": 0.0,
                "recommendation": "NO_MODEL",
                "message": "No trained model yet. Need 10+ trades to train."
            }

        features = self._extract_features(signal_data)
        if features is None:
            return {"probability": 0.5, "confidence": 0.0, "recommendation": "BAD_DATA"}

        X = np.array([features])
        prob = self._predict_raw(X, self._model)[0]

        # Confidence based on distance from 0.5
        confidence = abs(prob - 0.5) * 2  # 0 to 1

        if prob > 0.65:
            rec = "TRADE"
        elif prob > 0.55:
            rec = "SMALL_LOT"
        else:
            rec = "HOLD"

        return {
            "probability": round(prob, 4),
            "confidence": round(confidence, 4),
            "recommendation": rec,
            "message": f"Win probability: {prob:.1%} (confidence: {confidence:.1%})"
        }

    def _save_model(self, model: dict, accuracy: float, n_samples: int):
        """Save trained model."""
        model["accuracy"] = accuracy
        model["n_samples"] = n_samples
        with open(self.model_file, "w") as f:
            json.dump(model, f, indent=2)

    def _load_model(self) -> Optional[dict]:
        """Load saved model."""
        if os.path.exists(self.model_file):
            with open(self.model_file) as f:
                return json.load(f)
        return None

    def get_stats(self) -> dict:
        """Get training stats."""
        trades = self.load_trades()
        model = self._load_model()
        wins = sum(1 for t in trades if t.get("outcome", {}).get("win", False))
        return {
            "total_trades": len(trades),
            "wins": wins,
            "losses": len(trades) - wins,
            "win_rate": wins / len(trades) if trades else 0,
            "model_trained": model is not None,
            "model_accuracy": model.get("accuracy", 0) if model else 0,
            "model_samples": model.get("n_samples", 0) if model else 0,
        }
