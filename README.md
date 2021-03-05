## Guide for productionizing the ML model

This branch contains examples of the essential files and file structure needed to deploy the ML model into production.

`train.py` - The file reads data, trains the model, logs model metrics, and makes predictions. Adapt this file to our project as needed.

`requirements.txt` - Python libraries and their versions needed to run the `train.py` script

`.github/workflows/train_and_predict.yml` - The GitHub Actions configuration file that instructs GitHub to set up a virtual environment with Python 3.7, install the libraries in `requirements.txt`, and run `train.py`. This "workflow" runs automatically whenever there is a `workflow_dispatch` event type or a `push` event type sent to this branch. In production, the `main` branch should be used along with a `workflow_dispatch` event. 