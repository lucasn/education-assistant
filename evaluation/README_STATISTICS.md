# Evaluation Statistics Notebook

This notebook generates statistical visualizations from evaluation results stored in MongoDB.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure MongoDB is running and accessible (using Docker or local installation)

3. Start Jupyter:
```bash
jupyter notebook
```

4. Open `evaluation_statistics.ipynb`

## Usage

The notebook provides several functions to analyze evaluation results:

### 1. List Available Test Runs

```python
test_run_ids = list_test_run_ids()
```

This will show all available test run IDs and the number of evaluations for each.

### 2. Generate Statistics for a Test Run

```python
stats = generate_evaluation_statistics(test_run_id)
```

This function:
- Queries MongoDB for all evaluations with the given `test_run_id`
- Generates two pie charts:
  - **Correctness Criteria**: Shows the distribution of correctness verdicts (good/satisfactory/unsatisfactory)
  - **Groundedness Criteria**: Shows the distribution of groundedness verdicts (good/satisfactory/unsatisfactory)
- Returns a dictionary with detailed statistics

### 3. Display Statistics Summary

```python
display_statistics_summary(stats)
```

Displays a formatted text summary of the statistics including counts and percentages.

### 4. Compare Multiple Test Runs

```python
comparison_df = compare_test_runs([test_run_id_1, test_run_id_2, test_run_id_3])
```

Creates a comparison table showing statistics across multiple test runs.

## Example Workflow

```python
# 1. List available test runs
test_run_ids = list_test_run_ids()

# 2. Choose a test run ID and generate statistics
my_test_run_id = test_run_ids[0]  # or use a specific ID
stats = generate_evaluation_statistics(my_test_run_id)

# 3. Display the summary
display_statistics_summary(stats)

# 4. Compare multiple runs (optional)
comparison_df = compare_test_runs([test_run_ids[0], test_run_ids[1]])
display(comparison_df)
```

## Chart Colors

The pie charts use the following color scheme:
- **Good**: Light blue (#B4C7E7)
- **Satisfactory**: Light yellow (#F4E5A3)
- **Unsatisfactory**: Light red (#C27575)

## Environment Variables

The notebook uses the same MongoDB connection configuration as the evaluator:

- `MONGO_HOST`: MongoDB host (default: localhost)
- `MONGO_PORT`: MongoDB port (default: 27017)
- `MONGO_USER`: MongoDB user (default: root)
- `MONGO_PASSWORD`: MongoDB password (default: root)

## Notes

- The notebook connects to the `education.evaluation` collection in MongoDB
- Each evaluation must have `test_run_id`, `correctness.verdict`, and `groundedness.verdict` fields
- Verdicts can be: "good", "satisfactory", or "unsatisfactory"
