curl -kL http://xrl.us/pythonbrewinstall | bash
echo "[[ -s $HOME/.pythonbrew/etc/bashrc ]] && source $HOME/.pythonbrew/etc/bashrc" >> ~/.bashrc

source $HOME/.pythonbrew/etc/bashrc
pythonbrew install 2.7.2 --no-test -j 2
pythonbrew venv init
pythonbrew venv create ~/logbot -p 2.7.2
wget "https://github.com/orf/logbot/tarball/master" --no-check-certificate -O /tmp/logbot.tar.gz
rm -r -f /tmp/logbot_extract
mkdir /tmp/logbot_extract
tar xvfz /tmp/logbot.tar.gz -C /tmp/logbot_extract
mv /tmp/logbot_extract/*-logbot*/* ~/logbot
rm -r -f /tmp/logbot*

cd ~/logbot
source bin/activate
cat REQUIRES | xargs pip install