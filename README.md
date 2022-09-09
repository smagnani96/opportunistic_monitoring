# Opportunistic Network Monitoring

Research project on opportunistic network traffic monitoring.

For credits, please reference [this](https://doi.org/10.1109/ACCESS.2022.3202644) publication:

*S. Magnani, F. Risso and D. Siracusa, "A Control Plane Enabling Automated and Fully Adaptive Network Traffic Monitoring with eBPF," in IEEE Access, 2022, doi: 10.1109/ACCESS.2022.3202644.*



## Installation

To install all the required packages for testing listed in the [file](Pipfile), I suggest you to use [pipenv](https://pypi.org/project/pipenv/), a very useful wrapper for Python virtual environments which allows you to easily setup a ready-to-use environment by just typing:

```bash
ubuntu@ubuntu: $ ~ pipenv install
```

The default Python version listed in the file is 3.8, but you can use also older versions and everything should work fine.

Concerning the eBPF programs, you must have a recent Linux kernel >= v5.6, since they use BPF_QUEUEs which have been recently introduced.
