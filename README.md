# GPIO-Setup

This repository contains a basic GPIO-setup

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
sudo apt-get install lirc --yes

sudo modprobe lirc_dev
sudo modprobe lirc_rpi gpio_in_pin=17 gpio_out_pin=23
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Raspberry PI IR Remote Control Setup](https://tutorials-raspberrypi.de/raspberry-pi-ir-remote-control/) - A comprehensive tutorial on setting up an Infrared sensor and -actor
* [Raspberry PI 3 GPIO Board](https://www.elektronik-kompendium.de/sites/raspberry-pi/1907101.htm) - A schema of the Raspberry PI 3 GPIO board

## Authors

* **Timor Kodal** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks to Raspberry PI
