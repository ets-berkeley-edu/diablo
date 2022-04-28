# Xena

![Picture of Xena: Warrior Princess](../src/assets/xena.jpg)

## Installation

Xena requires:
* [chromedriver](https://chromedriver.chromium.org/downloads)
or 
* [geckodriver](https://github.com/mozilla/geckodriver/releases)
## Run

```
# Run all Xena tests
tox -e test -- xena

# Run specific test(s)
tox -e test -- xena/tests/test_sign_up_*.py
```
