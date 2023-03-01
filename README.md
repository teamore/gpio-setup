# GPIO-Setup

This repository contains a basic GPIO-setup

```
sudo apt-get install lirc --yes

sudo modprobe lirc_dev
sudo modprobe lirc_rpi gpio_in_pin=17 gpio_out_pin=23
```
## Further Readings

* [Raspberry PI IR Remote Control Setup](https://tutorials-raspberrypi.de/raspberry-pi-ir-remote-control/) - A comprehensive tutorial on setting up an Infrared sensor and -actor
* [Raspberry PI 3 GPIO Board](https://www.elektronik-kompendium.de/sites/raspberry-pi/1907101.htm) - A schema of the Raspberry PI 3 GPIO board
* [irrecord Manpage](https://manpages.debian.org/stretch/lirc/irrecord.1.en.html) - Manpage of the irrecord - command to use the IR receiver to decode remote control messages

## Authors

* **Timor Kodal** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks to Raspberry PI
