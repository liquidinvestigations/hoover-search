
# Hoover


## Requirements:
* gcc
* postgresql-server
* python3-devel
* python3-virtualenv


## Setup instructions:
1.  Install Python if not already installed. Test using:
    `python --version`

2.  Install [`python-virtualenv`](https://virtualenv.pypa.io/en/latest/installation.html)
    if not already installed. Test using:
    `virtualenv --version`

3.  Install git if not already installed. Test using:
    `git --version`

4.  Clone the repository:
    ```bash
    git clone https://github.com/mgax/hoover.git
    ```

5.  Setup the virtual environment and install the dependencies:
    ```bash
    # Prepare the Python Virtual Environment.
    make prepare

    # Activate the newly created virtualenv.
    source .venv/bin/activate

    # Install mia once inside the Virtual Environment.
    pip install -r requirements.txt
    ```

    NOTES:
    * Every time you need to use hoover, make sure you activate the virtualenv.
    * You can exit the virtualenv by executing `deactivate`

6.  Create a database named `hoover`, and make sure set proper permissions; see `hoover/settings/local.py`

7.  Run the application:
    ```bash
    ./run devserver
    ```
