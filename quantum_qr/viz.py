"""
Visualization helpers for the Quantum QR project.

Provides tools to render statistical outcomes, confidence metrics,
and confusion matrices from evaluation runs.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any


def plot_confusion_matrix(
    results: List[Dict[str, Any]],
    path: str,
    title: str = "Quantum Verifier Confusion Matrix",
) -> None:
    """
    Render a 2x2 authentic/rejected confusion matrix as a labeled heatmap.

    Aggregates the outcomes from an evaluation corpus and plots a
    matplotlib heatmap detailing True Positives, False Positives,
    True Negatives, and False Negatives.

    Args:
        results (List[Dict[str, Any]]): The output list from evaluate_corpus().
        path (str): The filesystem path where the PNG will be saved.
        title (str, optional): The title of the plot.
    """
    # 1. Tally the results
    # For this matrix, "Positive" = Authentic, "Negative" = Tampered/Invalid
    tp = sum(
        1
        for r in results
        if r["expected_verdict"] == "authentic"
        and r["predicted_verdict"] == "authentic"
    )
    fn = sum(
        1
        for r in results
        if r["expected_verdict"] == "authentic"
        and r["predicted_verdict"] != "authentic"
    )
    fp = sum(
        1
        for r in results
        if r["expected_verdict"] == "tampered" and r["predicted_verdict"] == "authentic"
    )
    tn = sum(
        1
        for r in results
        if r["expected_verdict"] == "tampered" and r["predicted_verdict"] != "authentic"
    )

    matrix = np.array([[tp, fn], [fp, tn]])

    # 2. Setup the plot
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.imshow(matrix, interpolation="nearest", cmap=plt.cm.Blues, vmin=0)
    fig.colorbar(cax)

    # 3. Configure axes
    classes = ["Authentic", "Tampered"]
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(classes)
    ax.set_yticklabels(classes)

    ax.set_xlabel("Predicted Label", fontsize=12, fontweight="bold")
    ax.set_ylabel("True Label", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, pad=15)

    # 4. Add text annotations to each cell
    thresh = matrix.max() / 2.0
    labels = [
        ["True Positive", "False Negative\n(False Reject)"],
        ["False Positive\n(False Accept!)", "True Negative"],
    ]

    for i in range(2):
        for j in range(2):
            count = matrix[i, j]
            label = labels[i][j]
            color = "white" if count > thresh else "black"

            # Print the count and the label
            text = f"{count}\n\n{label}"
            ax.text(j, i, text, ha="center", va="center", color=color, fontsize=10)

    # 5. Clean up and save
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Confusion matrix saved to: {path}")
