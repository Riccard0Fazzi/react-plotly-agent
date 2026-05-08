import pandas as pd
import plotly.express as px
from pathlib import Path

# Load dataset
df = pd.read_csv("input.csv")

# Create output folder
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

# Simple plot: count rows by industry
fig = px.histogram(
    df,
    x="Industry",
    title="Number of Entries by Industry"
)

# Save as HTML
output_path = output_dir / "industry_distribution.html"
fig.write_html(output_path)

print(f"Plot saved to: {output_path}")
