#!/usr/bin/env bash

set -e

echo
echo "------------------------------------------"
echo "  Xena welcomes you! "
echo "------------------------------------------"
echo

echo 'What kind of browser do we want to use? Enter 1 or 2. '

browser_options=("chrome" "firefox")

select opt in "${browser_options[@]}"; do
  case ${opt} in
  "chrome")
    browser="chrome"
    break
    ;;
  "firefox")
    browser="firefox"
    break
    ;;
  *)
    echo "Answer truly, or you will browse in vain"
    exit 1
    ;;
  esac
done

headless_options=("regular" "headless")

select opt in "${headless_options[@]}"; do
  case ${opt} in
  "headless")
    headless=true
    break
    ;;
  "regular")
    headless=false
    break
    ;;
  *)
    echo "Answer truly, or I will make you headless"
    exit 1
    ;;
  esac
done

echo
echo "Enter snippet (e.g., 'sign_up' or 'weird') to match the test file names you want to run."
echo "Blank will run all tests."; echo
echo -n "    > "

read test_suite

echo
echo "Enter your username"
echo
printf "    > "

read username

echo
echo "Enter your password"
echo
printf "    > "

read -s password

echo
echo "Xena will now slay the tests for ${test_suite}"

test_suite="*${test_suite}*"
USERNAME="${username}" PASSWORD="${password}" pytest tests/test_${test_suite}.py --browser ${browser} --headless ${headless}

exit 0
