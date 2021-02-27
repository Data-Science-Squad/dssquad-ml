## Guide for productionizing the ML model

This branch contains examples of the essential files and file structure needed to deploy the ML model into production.

`train.py` - The file reads data, trains the model, logs model metrics, and makes predictions. Adapt this file to our project as needed.

`requirements.txt` - Python libraries and their versions needed to run the `train.py` script

`.github/workflows/train_and_predict.yml` - The GitHub Actions configuration file that instructs GitHub to install Python 3.7, install the libraries in `requirements.txt`, and run `train.py`. This sequence of steps runs whenever there is a push to this feature branch, however for production the main branch should be used instead. Customize this script by changing lines 5, 26, and 29.