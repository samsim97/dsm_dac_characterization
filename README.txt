# Getting Started
## Fetching this project
Open a terminal in a directory where you want the project cloned then run:
`git clone ADD_DOT_GIT_LINK_HERE`
## Python environment setup
Assuming VSCode is used, open with VSCode the project directory then create the virtual environment by doing the following steps:
1. Press `Ctrl` + `Shift` + `P`
2. Search for `Python: Create Environment...` then select it and press `Enter`
3. If asked, select the `requirements.txt` file to install the required python packages

# Board setup
For this test, the following boards are used:
- FPGA board
- Red Pitaya for controlling the GPIO that makes the DAC FSM increment by 1

## Connection
See the `fpga_redpitaya_connections.png` file in the root directory of the project for how things are connected.
![fpga_redpitaya_connections](fpga_redpitaya_connections.png)

# How it works