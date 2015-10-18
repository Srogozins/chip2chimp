# chip2chimp
Human-Computer communications API connector. Currently just a glorified Omegle-Cleverbot chat connector.

## Installation
### Requirements
The code was written for Python version 3.5 and higher.

[Cleverbot](https://github.com/superboum/cleverbot), is required. To install it:
```bash
$ git clone https://github.com/superboum/cleverbot
$ cd cleverbot
$ pip install .
```
Other dependencies are specified in requirements.txt. To install them:
```bash
$ pip install -r requirements.txt
```
## Usage
```bash
$ ./c2c.py [omegle conversation topics]
```
### Examples
```bash
$ ./c2c.py
```
```bash
$ ./c2c.py music programming
```

## TODO
* Chat log files
* Better chat session management UI
* Manual chat input
* Support for more Human/Computer communication APIs
* Multiparty communication
* Porting to Rebol
