tackbp2016 -- Slot Filling variant of the Cold-Start track
==========

Slot Filling variant of the cold-start track for tac kbp 2016

----
copied from iesl/relationfactory repo with all the branches and commit history. 

Used the following commands to migrate the old repo with all its history to the new repo (upon discussion with Adam)


git clone --bare https://github.com/iesl/relationfactory.git

cd relationfactory.git

.... create empty git repo... (iesl/tackbp2016-kb)

git push --mirror  https://github.com/iesl/tackbp2016-sf.git

... To check the newly created repo

git clone https://github.com/iesl/tackbp2016-sf.git

