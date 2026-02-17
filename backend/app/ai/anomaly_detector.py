"""Statistical anomaly detection for alert system."""

import statistics
from typing import Optional


class AnomalyDetector:
    """Detects anomalies using simple statistical methods."""

    @staticmethod
    def detect_anomaly(
        current_value: float,
        historical_values: list[float],
        threshold_std: float = 2.0,
    ) -> Optional[dict]:
        """
        Detect if current_value is anomalous vs. historical_values.
        Uses z-score method (> threshold_std standard deviations from mean).
        """
        if len(historical_values) < 3:
            return None

        mean = statistics.mean(historical_values)
        stdev = statistics.stdev(historical_values)

        if stdev == 0:
            return None

        z_score = (current_value - mean) / stdev

        if abs(z_score) > threshold_std:
            direction = "above" if z_score > 0 else "below"
            pct_change = ((current_value - mean) / mean) * 100 if mean != 0 else 0

            return {
                "is_anomaly": True,
                "z_score": round(z_score, 2),
                "direction": direction,
                "current_value": current_value,
                "mean": round(mean, 2),
                "stdev": round(stdev, 2),
                "pct_from_mean": round(pct_change, 1),
                "message": f"Value {current_value:.2f} is {abs(pct_change):.1f}% {direction} the trailing average of {mean:.2f}",
            }

        return None
