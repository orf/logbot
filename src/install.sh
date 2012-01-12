# Run this first then start a screen session or a new shell:
#   curl -kL http://xrl.us/pythonbrewinstall | bash

pythonbrew install 2.7.2 --no-test -j 2
pythonbrew venv init
pythonbrew venv create ~/logbot -p 2.7.2
cd ~/logbot
git clone git://github.com/orf/logbot.git
source bin/activate
cat logbot/REQUIRES | xargs ./bin/pip install
deactivate